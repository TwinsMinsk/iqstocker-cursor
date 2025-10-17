"""Dramatiq actors for theme processing and categorization."""

import dramatiq
import pandas as pd
import asyncio
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any
import structlog

from config.database import SessionLocal
from database.models import CSVAnalysis, TopTheme, AssetDetails, GlobalTheme, AnalysisStatus
from core.parser.adobe_stock_playwright import AdobeStockPlaywrightParser
from core.ai.llm_service import LLMServiceFactory

logger = structlog.get_logger()


@dramatiq.actor(max_retries=3, time_limit=600000)  # 10 minutes
def scrape_and_categorize_themes(csv_analysis_id: int):
    """
    Complete pipeline for theme categorization:
    1. Get top assets from CSV
    2. Scrape tags for each asset
    3. Categorize themes through LLM
    4. Save results
    """
    
    logger.info("theme_categorization_started", csv_analysis_id=csv_analysis_id)
    
    db = SessionLocal()
    try:
        # 1. Get CSV analysis
        analysis = db.query(CSVAnalysis).filter(CSVAnalysis.id == csv_analysis_id).first()
        if not analysis:
            logger.error("csv_analysis_not_found", csv_analysis_id=csv_analysis_id)
            return
        
        # Log detailed pipeline start
        logger.info("theme_pipeline_started", 
                    csv_analysis_id=csv_analysis_id,
                    user_id=analysis.user_id,
                    file_path=analysis.file_path)
        
        # Update status to processing
        analysis.status = AnalysisStatus.PROCESSING
        db.commit()
        
        # 2. Get top assets from CSV
        top_assets = _get_top_assets_from_csv(analysis.file_path, limit=10)
        if not top_assets:
            logger.error("no_assets_found", csv_analysis_id=csv_analysis_id)
            analysis.status = AnalysisStatus.FAILED
            db.commit()
            return
        
        logger.info("top_assets_extracted", csv_analysis_id=csv_analysis_id, count=len(top_assets))
        
        # 3. Scrape tags for assets
        parser = AdobeStockPlaywrightParser()
        tags_by_asset = {}
        
        for asset in top_assets:
            asset_id = asset['id']
            
            # Log asset scraping start
            logger.debug("asset_scraping_started",
                         asset_id=asset_id,
                         title=asset['title'],
                         url=f"https://stock.adobe.com/images/{parser._create_slug(asset['title'])}/{asset_id}")
            
            # Check cache first
            cached = db.query(AssetDetails).filter_by(asset_id=asset_id).first()
            if cached and cached.tags:
                tags_by_asset[asset_id] = cached.tags
                logger.info("asset_tags_cached", asset_id=asset_id, tags_count=len(cached.tags))
            else:
                # Scrape tags
                try:
                    tags = asyncio.run(parser.scrape_asset_tags(asset_id, asset['title']))
                    if tags:
                        # Save to cache
                        if cached:
                            cached.tags = tags
                            cached.scraped_at = datetime.utcnow()
                        else:
                            asset_detail = AssetDetails(
                                asset_id=asset_id,
                                title=asset['title'],
                                tags=tags,
                                adobe_url=f"https://stock.adobe.com/images/{parser._create_slug(asset['title'])}/{asset_id}"
                            )
                            db.add(asset_detail)
                        
                        tags_by_asset[asset_id] = tags
                        logger.info("asset_tags_scraped",
                                    asset_id=asset_id,
                                    tags_count=len(tags),
                                    tags_sample=tags[:5])  # первые 5 тегов для проверки
                    else:
                        logger.warning("asset_tags_empty", asset_id=asset_id)
                        
                except Exception as e:
                    logger.error("asset_scraping_failed", asset_id=asset_id, error=str(e))
                    continue
        
        db.commit()
        
        if not tags_by_asset:
            logger.error("no_tags_collected", csv_analysis_id=csv_analysis_id)
            analysis.status = AnalysisStatus.FAILED
            db.commit()
            return
        
        # 4. Categorize themes through LLM
        try:
            llm_provider = LLMServiceFactory.get_active_provider(db)
            
            # Prepare sales data
            sales_data = {
                asset['id']: {
                    'sales': asset['sales'], 
                    'revenue': asset['revenue']
                } 
                for asset in top_assets
            }
            
            # Log LLM request preparation
            logger.debug("llm_request_prepared",
                         provider=type(llm_provider).__name__,
                         assets_count=len(tags_by_asset),
                         total_tags=sum(len(t) for t in tags_by_asset.values()),
                         total_sales=sum(a['sales'] for a in top_assets),
                         total_revenue=sum(a['revenue'] for a in top_assets))
            
            result = asyncio.run(llm_provider.categorize_themes(
                tags_by_asset=tags_by_asset,
                sales_data=sales_data
            ))
            
            logger.info(
                "llm_categorization_success",
                csv_analysis_id=csv_analysis_id,
                themes_count=len(result.themes),
                themes_list=[t['theme'] for t in result.themes[:3]],
                model=result.model_used,
                processing_ms=result.processing_time_ms
            )
            
        except Exception as e:
            logger.error("llm_categorization_failed", csv_analysis_id=csv_analysis_id, error=str(e))
            analysis.status = AnalysisStatus.FAILED
            db.commit()
            return
        
        # 5. Save top themes
        # Clear existing top themes for this analysis
        db.query(TopTheme).filter(TopTheme.csv_analysis_id == csv_analysis_id).delete()
        
        for idx, theme_data in enumerate(result.themes):
            top_theme = TopTheme(
                csv_analysis_id=csv_analysis_id,
                theme_name=theme_data['theme'],
                sales_count=theme_data.get('sales', 0),
                revenue=theme_data.get('revenue', 0.0),
                rank=idx + 1
            )
            db.add(top_theme)
        
        # Update analysis status
        analysis.status = AnalysisStatus.COMPLETED
        analysis.processed_at = datetime.utcnow()
        
        db.commit()
        
        # Log final results
        logger.info("top_themes_saved",
                    csv_analysis_id=csv_analysis_id,
                    themes_saved=len(result.themes),
                    top_theme=result.themes[0]['theme'] if result.themes else None)
        
        logger.info("theme_categorization_completed", csv_analysis_id=csv_analysis_id)
        
        # 6. Update global themes
        update_global_themes.send(csv_analysis_id)
        
    except Exception as e:
        logger.error("theme_categorization_error", csv_analysis_id=csv_analysis_id, error=str(e))
        if 'analysis' in locals():
            analysis.status = AnalysisStatus.FAILED
            db.commit()
    finally:
        db.close()


@dramatiq.actor(max_retries=2, time_limit=300000)  # 5 minutes
def update_global_themes(csv_analysis_id: int):
    """Update global themes database with new top themes."""
    
    logger.info("global_themes_update_started", csv_analysis_id=csv_analysis_id)
    
    db = SessionLocal()
    try:
        # Get top themes for this analysis
        top_themes = db.query(TopTheme).filter(
            TopTheme.csv_analysis_id == csv_analysis_id
        ).all()
        
        if not top_themes:
            logger.warning("no_top_themes_found", csv_analysis_id=csv_analysis_id)
            return
        
        # Update global themes
        for top_theme in top_themes:
            existing_theme = db.query(GlobalTheme).filter(
                GlobalTheme.theme_name == top_theme.theme_name
            ).first()
            
            if existing_theme:
                # Update existing theme
                existing_theme.total_sales += top_theme.sales_count
                existing_theme.total_revenue += top_theme.revenue
                existing_theme.authors_count += 1
                existing_theme.last_updated = datetime.utcnow()
                
                logger.info(
                    "global_theme_updated",
                    theme_name=top_theme.theme_name,
                    total_sales=existing_theme.total_sales,
                    total_revenue=float(existing_theme.total_revenue)
                )
                
                # Log delta changes for debugging
                logger.debug("global_theme_delta",
                             theme_name=top_theme.theme_name,
                             sales_added=top_theme.sales_count,
                             revenue_added=float(top_theme.revenue),
                             new_total_sales=existing_theme.total_sales,
                             new_total_revenue=float(existing_theme.total_revenue))
            else:
                # Create new global theme
                new_theme = GlobalTheme(
                    theme_name=top_theme.theme_name,
                    total_sales=top_theme.sales_count,
                    total_revenue=top_theme.revenue,
                    authors_count=1,
                    last_updated=datetime.utcnow()
                )
                db.add(new_theme)
                
                logger.info(
                    "global_theme_created",
                    theme_name=top_theme.theme_name,
                    sales=top_theme.sales_count,
                    revenue=float(top_theme.revenue)
                )
        
        db.commit()
        logger.info("global_themes_update_completed", csv_analysis_id=csv_analysis_id)
        
    except Exception as e:
        logger.error("global_themes_update_failed", csv_analysis_id=csv_analysis_id, error=str(e))
        db.rollback()
    finally:
        db.close()


def _get_top_assets_from_csv(file_path: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Extract top assets from CSV file by revenue.
    
    Args:
        file_path: Path to CSV file
        limit: Maximum number of assets to return
        
    Returns:
        List of asset dictionaries with id, title, sales, revenue
    """
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Ensure required columns exist
        required_columns = ['Asset ID', 'Title', 'Sales', 'Revenue']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error("csv_missing_columns", file_path=file_path, missing=missing_columns)
            return []
        
        # Clean and process data
        df = df.dropna(subset=['Asset ID', 'Title', 'Sales', 'Revenue'])
        df['Sales'] = pd.to_numeric(df['Sales'], errors='coerce')
        df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
        
        # Remove rows with invalid data
        df = df[(df['Sales'] > 0) & (df['Revenue'] > 0)]
        
        if df.empty:
            logger.warning("csv_no_valid_data", file_path=file_path)
            return []
        
        # Group by Asset ID and aggregate sales/revenue
        grouped = df.groupby(['Asset ID', 'Title']).agg({
            'Sales': 'sum',
            'Revenue': 'sum'
        }).reset_index()
        
        # Sort by revenue and get top assets
        top_assets = grouped.nlargest(limit, 'Revenue')
        
        # Convert to list of dictionaries
        assets = []
        for _, row in top_assets.iterrows():
            assets.append({
                'id': str(row['Asset ID']),
                'title': str(row['Title']),
                'sales': int(row['Sales']),
                'revenue': float(row['Revenue'])
            })
        
        logger.info("top_assets_extracted", file_path=file_path, count=len(assets))
        return assets
        
    except Exception as e:
        logger.error("csv_processing_failed", file_path=file_path, error=str(e))
        return []


@dramatiq.actor(max_retries=1, time_limit=60000)  # 1 minute
def cleanup_old_asset_details():
    """Clean up old asset details to prevent database bloat."""
    
    logger.info("asset_details_cleanup_started")
    
    db = SessionLocal()
    try:
        # Delete asset details older than 6 months
        cutoff_date = datetime.utcnow() - pd.Timedelta(days=180)
        
        deleted_count = db.query(AssetDetails).filter(
            AssetDetails.scraped_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info("asset_details_cleanup_completed", deleted_count=deleted_count)
        
    except Exception as e:
        logger.error("asset_details_cleanup_failed", error=str(e))
        db.rollback()
    finally:
        db.close()
