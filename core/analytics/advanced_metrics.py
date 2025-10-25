"""Advanced metrics calculator for comprehensive analytics."""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
import pandas as pd

from config.database import SessionLocal
from database.models import User, CSVAnalysis, AnalyticsReport, Subscription


class AdvancedMetrics:
    """Calculate advanced metrics for portfolio analysis."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
    def calculate_roi_by_themes(self, user_id: int) -> Dict[str, Any]:
        """Calculate ROI (Return on Investment) by themes."""
        # TopTheme functionality removed
        return {
            "roi_by_themes": [],
            "avg_roi": 0,
            "best_performing_theme": None,
            "worst_performing_theme": None
        }
    
    def calculate_conversion_rates(self, user_id: int) -> Dict[str, Any]:
        """Calculate conversion rates for new vs old works."""
        try:
            # Get user's CSV analyses
            analyses = self.db.query(CSVAnalysis).filter(
                CSVAnalysis.user_id == user_id
            ).order_by(CSVAnalysis.created_at).all()
            
            if not analyses:
                return {
                    "conversion_rates": {},
                    "message": "Недостаточно данных для расчета конверсии"
                }
            
            conversion_data = {
                "new_works": {"total_sales": 0, "total_works": 0, "conversion_rate": 0},
                "old_works": {"total_sales": 0, "total_works": 0, "conversion_rate": 0},
                "overall": {"total_sales": 0, "total_works": 0, "conversion_rate": 0}
            }
            
            for analysis in analyses:
                report = analysis.analytics_report
                if not report:
                    continue
                
                # Get portfolio size and sales data
                portfolio_size = analysis.portfolio_size or 0
                total_sales = report.total_sales or 0
                new_works_percent = float(report.new_works_sales_percent) if report.new_works_sales_percent else 0
                
                # Calculate new vs old works sales
                new_works_sales = total_sales * (new_works_percent / 100)
                old_works_sales = total_sales - new_works_sales
                
                # Estimate new vs old works count (simplified)
                new_works_count = portfolio_size * 0.3  # Assume 30% are new works
                old_works_count = portfolio_size - new_works_count
                
                # Update conversion data
                conversion_data["new_works"]["total_sales"] += new_works_sales
                conversion_data["new_works"]["total_works"] += new_works_count
                conversion_data["old_works"]["total_sales"] += old_works_sales
                conversion_data["old_works"]["total_works"] += old_works_count
                conversion_data["overall"]["total_sales"] += total_sales
                conversion_data["overall"]["total_works"] += portfolio_size
            
            # Calculate conversion rates
            for category in conversion_data:
                data = conversion_data[category]
                if data["total_works"] > 0:
                    data["conversion_rate"] = round((data["total_sales"] / data["total_works"]) * 100, 2)
            
            return {
                "conversion_rates": conversion_data,
                "analysis_periods": len(analyses),
                "message": f"Проанализировано {len(analyses)} периодов"
            }
            
        except Exception as e:
            print(f"Error calculating conversion rates: {e}")
            return {"error": str(e)}
    
    def calculate_portfolio_diversity_index(self, user_id: int) -> Dict[str, Any]:
        """Calculate portfolio diversity index."""
        # TopTheme functionality removed
        return {
            "diversity_index": 0,
            "theme_count": 0,
            "category_distribution": {},
            "message": "TopTheme functionality removed"
        }
    
    def calculate_time_to_sale_metrics(self, user_id: int) -> Dict[str, Any]:
        """Calculate time-to-sale metrics."""
        try:
            # Get user's analyses with timestamps
            analyses = self.db.query(CSVAnalysis).filter(
                CSVAnalysis.user_id == user_id
            ).order_by(CSVAnalysis.created_at).all()
            
            if len(analyses) < 2:
                return {
                    "time_to_sale": {},
                    "message": "Недостаточно данных для анализа времени до продажи"
                }
            
            # Calculate time between analyses and correlate with sales
            time_metrics = []
            
            for i in range(1, len(analyses)):
                prev_analysis = analyses[i-1]
                curr_analysis = analyses[i]
                
                time_diff = (curr_analysis.created_at - prev_analysis.created_at).days
                
                prev_report = prev_analysis.analytics_report
                curr_report = curr_analysis.analytics_report
                
                if prev_report and curr_report:
                    sales_growth = (curr_report.total_sales or 0) - (prev_report.total_sales or 0)
                    
                    time_metrics.append({
                        "period_days": time_diff,
                        "sales_growth": sales_growth,
                        "sales_per_day": sales_growth / time_diff if time_diff > 0 else 0,
                        "date": curr_analysis.created_at
                    })
            
            if not time_metrics:
                return {
                    "time_to_sale": {},
                    "message": "Недостаточно данных для анализа времени"
                }
            
            # Calculate statistics
            periods = [m["period_days"] for m in time_metrics]
            sales_per_day = [m["sales_per_day"] for m in time_metrics]
            
            avg_period = np.mean(periods)
            avg_sales_per_day = np.mean(sales_per_day)
            
            # Estimate time to first sale (simplified)
            estimated_time_to_first_sale = 30  # Default assumption
            
            return {
                "time_to_sale": {
                    "avg_period_days": round(avg_period, 1),
                    "avg_sales_per_day": round(avg_sales_per_day, 2),
                    "estimated_time_to_first_sale": estimated_time_to_first_sale,
                    "total_periods_analyzed": len(time_metrics)
                },
                "period_analysis": time_metrics,
                "message": f"Средний период между анализами: {avg_period:.1f} дней"
            }
            
        except Exception as e:
            print(f"Error calculating time-to-sale metrics: {e}")
            return {"error": str(e)}
    
    def calculate_revenue_per_upload(self, user_id: int) -> Dict[str, Any]:
        """Calculate revenue per upload metrics."""
        try:
            # Get user's analyses
            analyses = self.db.query(CSVAnalysis).filter(
                CSVAnalysis.user_id == user_id
            ).all()
            
            if not analyses:
                return {
                    "revenue_per_upload": {},
                    "message": "Недостаточно данных для анализа доходности загрузок"
                }
            
            upload_metrics = []
            total_uploads = 0
            total_revenue = 0
            
            for analysis in analyses:
                report = analysis.analytics_report
                monthly_uploads = analysis.monthly_uploads or 0
                revenue = float(report.total_revenue) if report and report.total_revenue else 0
                
                if monthly_uploads > 0:
                    revenue_per_upload = revenue / monthly_uploads
                    upload_metrics.append({
                        "month": analysis.month,
                        "year": analysis.year,
                        "monthly_uploads": monthly_uploads,
                        "revenue": revenue,
                        "revenue_per_upload": round(revenue_per_upload, 2),
                        "date": analysis.created_at
                    })
                    
                    total_uploads += monthly_uploads
                    total_revenue += revenue
            
            if not upload_metrics:
                return {
                    "revenue_per_upload": {},
                    "message": "Недостаточно данных о загрузках"
                }
            
            # Calculate overall metrics
            overall_revenue_per_upload = total_revenue / total_uploads if total_uploads > 0 else 0
            avg_monthly_revenue_per_upload = np.mean([m["revenue_per_upload"] for m in upload_metrics])
            
            # Find best and worst months
            best_month = max(upload_metrics, key=lambda x: x["revenue_per_upload"]) if upload_metrics else None
            worst_month = min(upload_metrics, key=lambda x: x["revenue_per_upload"]) if upload_metrics else None
            
            return {
                "revenue_per_upload": {
                    "overall_revenue_per_upload": round(overall_revenue_per_upload, 2),
                    "avg_monthly_revenue_per_upload": round(avg_monthly_revenue_per_upload, 2),
                    "total_uploads": total_uploads,
                    "total_revenue": round(total_revenue, 2),
                    "months_analyzed": len(upload_metrics)
                },
                "monthly_breakdown": upload_metrics,
                "best_month": best_month,
                "worst_month": worst_month,
                "message": f"Средний доход на загрузку: ${avg_monthly_revenue_per_upload:.2f}"
            }
            
        except Exception as e:
            print(f"Error calculating revenue per upload: {e}")
            return {"error": str(e)}
    
    def get_comprehensive_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive advanced metrics for a user."""
        try:
            roi_analysis = self.calculate_roi_by_themes(user_id)
            conversion_analysis = self.calculate_conversion_rates(user_id)
            diversity_analysis = self.calculate_portfolio_diversity_index(user_id)
            time_analysis = self.calculate_time_to_sale_metrics(user_id)
            revenue_analysis = self.calculate_revenue_per_upload(user_id)
            
            return {
                "user_id": user_id,
                "roi_analysis": roi_analysis,
                "conversion_analysis": conversion_analysis,
                "diversity_analysis": diversity_analysis,
                "time_analysis": time_analysis,
                "revenue_analysis": revenue_analysis,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating comprehensive metrics: {e}")
            return {
                "user_id": user_id,
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    def _get_diversity_level(self, diversity_index: float) -> str:
        """Get diversity level description."""
        if diversity_index >= 0.8:
            return "Очень высокое"
        elif diversity_index >= 0.6:
            return "Высокое"
        elif diversity_index >= 0.4:
            return "Среднее"
        elif diversity_index >= 0.2:
            return "Низкое"
        else:
            return "Очень низкое"
