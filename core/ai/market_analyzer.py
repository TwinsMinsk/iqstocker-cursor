"""Market trend analysis for stock photography themes."""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import pandas as pd

from config.database import SessionLocal
from database.models import GlobalTheme, TopTheme, CSVAnalysis, AnalyticsReport


class MarketAnalyzer:
    """Analyze market trends and patterns in stock photography."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
    def get_trending_themes(self, period: str = 'week', limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending themes based on usage frequency."""
        try:
            # Calculate time threshold based on period
            if period == 'week':
                time_threshold = datetime.utcnow() - timedelta(days=7)
            elif period == 'month':
                time_threshold = datetime.utcnow() - timedelta(days=30)
            elif period == 'quarter':
                time_threshold = datetime.utcnow() - timedelta(days=90)
            else:
                time_threshold = datetime.utcnow() - timedelta(days=7)
            
            # Get themes with recent usage
            trending_themes = self.db.query(GlobalTheme).filter(
                GlobalTheme.last_updated >= time_threshold
            ).order_by(desc(GlobalTheme.total_sales)).limit(limit).all()
            
            # Calculate trend scores
            trending_data = []
            for theme in trending_themes:
                # Calculate growth rate
                growth_rate = self._calculate_theme_growth_rate(theme.theme_name, period)
                
                # Calculate trend score
                trend_score = self._calculate_trend_score(theme, period)
                
                trending_data.append({
                    "theme_name": theme.theme_name,
                    "usage_count": theme.total_sales,
                    "growth_rate": growth_rate,
                    "trend_score": trend_score,
                    "last_used": theme.last_used,
                    "category": "General"
                })
            
            # Sort by trend score
            trending_data.sort(key=lambda x: x["trend_score"], reverse=True)
            
            return trending_data[:limit]
            
        except Exception as e:
            print(f"Error getting trending themes: {e}")
            return []
    
    def analyze_seasonal_trends(self, month: int) -> Dict[str, Any]:
        """Analyze seasonal trends for a specific month."""
        try:
            # Get themes popular in this month historically (simplified)
            seasonal_themes = self.db.query(GlobalTheme).filter(
                GlobalTheme.total_sales > 0
            ).order_by(desc(GlobalTheme.total_sales)).limit(20).all()
            
            # Analyze seasonal patterns
            seasonal_data = {
                "month": month,
                "month_name": self._get_month_name(month),
                "popular_themes": [],
                "seasonal_categories": {},
                "trend_analysis": {}
            }
            
            # Process seasonal themes
            for theme in seasonal_themes:
                seasonal_data["popular_themes"].append({
                    "theme_name": theme.theme_name,
                    "usage_count": theme.total_sales,
                    "category": "General",
                    "seasonal_strength": self._calculate_seasonal_strength(theme, month)
                })
            
            # Analyze by category
            categories = {}
            for theme in seasonal_themes:
                category = "General"
                if category not in categories:
                    categories[category] = 0
                categories[category] += theme.total_sales
            
            seasonal_data["seasonal_categories"] = categories
            
            # Calculate seasonal trends
            seasonal_data["trend_analysis"] = {
                "total_seasonal_themes": len(seasonal_themes),
                "peak_category": max(categories.items(), key=lambda x: x[1])[0] if categories else "General",
                "seasonal_intensity": self._calculate_seasonal_intensity(month)
            }
            
            return seasonal_data
            
        except Exception as e:
            print(f"Error analyzing seasonal trends: {e}")
            return {"month": month, "error": str(e)}
    
    def get_growth_rate(self, theme_name: str) -> Dict[str, Any]:
        """Calculate growth rate for a specific theme."""
        try:
            # Get theme usage over time
            theme = self.db.query(GlobalTheme).filter(
                GlobalTheme.theme_name == theme_name
            ).first()
            
            if not theme:
                return {"theme_name": theme_name, "growth_rate": 0, "status": "not_found"}
            
            # Calculate growth over different periods
            growth_rates = {}
            
            # Weekly growth
            weekly_growth = self._calculate_theme_growth_rate(theme_name, 'week')
            growth_rates['weekly'] = weekly_growth
            
            # Monthly growth
            monthly_growth = self._calculate_theme_growth_rate(theme_name, 'month')
            growth_rates['monthly'] = monthly_growth
            
            # Quarterly growth
            quarterly_growth = self._calculate_theme_growth_rate(theme_name, 'quarter')
            growth_rates['quarterly'] = quarterly_growth
            
            # Overall trend
            overall_trend = self._calculate_overall_trend(theme)
            
            return {
                "theme_name": theme_name,
                "growth_rates": growth_rates,
                "overall_trend": overall_trend,
                "current_usage": theme.total_sales,
                "last_used": theme.last_updated,
                "status": "active" if theme.total_sales > 0 else "inactive"
            }
            
        except Exception as e:
            print(f"Error calculating growth rate: {e}")
            return {"theme_name": theme_name, "error": str(e)}
    
    def predict_next_trends(self) -> Dict[str, Any]:
        """Predict upcoming trends based on historical data."""
        try:
            # Get recent trending themes
            recent_trends = self.get_trending_themes('month', 50)
            
            # Analyze trend patterns
            trend_clusters = self._cluster_trends(recent_trends)
            
            # Predict future trends
            predictions = []
            
            for cluster in trend_clusters:
                cluster_themes = [t for t in recent_trends if t["theme_name"] in cluster["themes"]]
                
                if cluster_themes:
                    avg_growth = np.mean([t["growth_rate"] for t in cluster_themes])
                    avg_trend_score = np.mean([t["trend_score"] for t in cluster_themes])
                    
                    predictions.append({
                        "cluster_name": cluster["name"],
                        "themes": cluster["themes"],
                        "predicted_growth": avg_growth,
                        "confidence": avg_trend_score,
                        "timeframe": "1-3 months"
                    })
            
            # Sort predictions by confidence
            predictions.sort(key=lambda x: x["confidence"], reverse=True)
            
            return {
                "predictions": predictions[:10],  # Top 10 predictions
                "analysis_period": "last_month",
                "confidence_threshold": 0.6,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error predicting trends: {e}")
            return {"error": str(e)}
    
    def get_market_overview(self) -> Dict[str, Any]:
        """Get comprehensive market overview."""
        try:
            # Get basic statistics
            total_themes = self.db.query(GlobalTheme).count()
            active_themes = self.db.query(GlobalTheme).filter(
                GlobalTheme.total_sales > 0
            ).count()
            
            # Get category distribution (simplified)
            categories = self.db.query(
                func.count(GlobalTheme.id).label('count'),
                func.sum(GlobalTheme.total_sales).label('total_usage')
            ).all()
            
            category_distribution = {}
            if categories:
                cat = categories[0]
                category_distribution["General"] = {
                    "theme_count": cat.count,
                    "total_usage": cat.total_usage or 0
                }
            
            # Get top performing themes
            top_themes = self.db.query(GlobalTheme).order_by(
                desc(GlobalTheme.total_sales)
            ).limit(10).all()
            
            top_performers = []
            for theme in top_themes:
                top_performers.append({
                    "theme_name": theme.theme_name,
                    "usage_count": theme.total_sales,
                    "category": "General",
                    "last_used": theme.last_used
                })
            
            # Get recent trends
            recent_trends = self.get_trending_themes('week', 10)
            
            return {
                "total_themes": total_themes,
                "active_themes": active_themes,
                "category_distribution": category_distribution,
                "top_performers": top_performers,
                "recent_trends": recent_trends,
                "market_health": self._calculate_market_health(),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting market overview: {e}")
            return {"error": str(e)}
    
    def _calculate_theme_growth_rate(self, theme_name: str, period: str) -> float:
        """Calculate growth rate for a theme over a period."""
        try:
            # This is a simplified calculation
            # In a real implementation, you'd compare usage counts over time periods
            
            theme = self.db.query(GlobalTheme).filter(
                GlobalTheme.theme_name == theme_name
            ).first()
            
            if not theme:
                return 0.0
            
            # Simple growth calculation based on recent usage
            if period == 'week':
                return min(50.0, theme.total_sales * 0.1)  # Simulated growth
            elif period == 'month':
                return min(100.0, theme.total_sales * 0.2)
            elif period == 'quarter':
                return min(200.0, theme.total_sales * 0.3)
            else:
                return 0.0
                
        except Exception as e:
            print(f"Error calculating growth rate: {e}")
            return 0.0
    
    def _calculate_trend_score(self, theme: GlobalTheme, period: str) -> float:
        """Calculate trend score for a theme."""
        try:
            # Combine usage count, growth rate, and recency
            usage_score = min(1.0, theme.total_sales / 1000)  # Normalize usage
            growth_score = self._calculate_theme_growth_rate(theme.theme_name, period) / 100
            recency_score = 1.0 if theme.last_updated and theme.last_updated > datetime.utcnow() - timedelta(days=7) else 0.5
            
            # Weighted average
            trend_score = (usage_score * 0.4 + growth_score * 0.4 + recency_score * 0.2)
            return round(trend_score, 3)
            
        except Exception as e:
            print(f"Error calculating trend score: {e}")
            return 0.0
    
    def _calculate_seasonal_strength(self, theme: GlobalTheme, month: int) -> float:
        """Calculate seasonal strength for a theme in a specific month."""
        try:
            # Calculate strength based on sales count (simplified seasonal logic)
            base_strength = min(1.0, theme.total_sales / 500)
            seasonal_multiplier = 1.2  # Simplified seasonal boost
            
            return round(base_strength * seasonal_multiplier, 3)
            
        except Exception as e:
            print(f"Error calculating seasonal strength: {e}")
            return 0.0
    
    def _calculate_seasonal_intensity(self, month: int) -> float:
        """Calculate overall seasonal intensity for a month."""
        try:
            # Count themes that are seasonal for this month (simplified)
            seasonal_count = self.db.query(GlobalTheme).filter(
                GlobalTheme.total_sales > 0
            ).count()
            
            total_themes = self.db.query(GlobalTheme).count()
            
            if total_themes == 0:
                return 0.0
            
            intensity = seasonal_count / total_themes
            return round(intensity, 3)
            
        except Exception as e:
            print(f"Error calculating seasonal intensity: {e}")
            return 0.0
    
    def _calculate_overall_trend(self, theme: GlobalTheme) -> str:
        """Calculate overall trend direction for a theme."""
        try:
            if theme.total_sales > 100:
                return "rising"
            elif theme.total_sales > 50:
                return "stable"
            elif theme.total_sales > 10:
                return "declining"
            else:
                return "low_activity"
        except Exception as e:
            print(f"Error calculating overall trend: {e}")
            return "unknown"
    
    def _cluster_trends(self, trends: List[Dict]) -> List[Dict]:
        """Cluster similar trends together."""
        try:
            if len(trends) < 3:
                return [{"name": "General", "themes": [t["theme_name"] for t in trends]}]
            
            # Simple clustering based on categories
            clusters = {}
            for trend in trends:
                category = trend.get("category", "General")
                if category not in clusters:
                    clusters[category] = []
                clusters[category].append(trend["theme_name"])
            
            cluster_list = []
            for category, themes in clusters.items():
                cluster_list.append({
                    "name": f"{category} Trends",
                    "themes": themes
                })
            
            return cluster_list
            
        except Exception as e:
            print(f"Error clustering trends: {e}")
            return [{"name": "General", "themes": [t["theme_name"] for t in trends]}]
    
    def _calculate_market_health(self) -> str:
        """Calculate overall market health."""
        try:
            # Simple health calculation based on active themes and usage
            active_themes = self.db.query(GlobalTheme).filter(
                GlobalTheme.total_sales > 0
            ).count()
            
            total_themes = self.db.query(GlobalTheme).count()
            
            if total_themes == 0:
                return "unknown"
            
            health_ratio = active_themes / total_themes
            
            if health_ratio > 0.7:
                return "excellent"
            elif health_ratio > 0.5:
                return "good"
            elif health_ratio > 0.3:
                return "fair"
            else:
                return "poor"
                
        except Exception as e:
            print(f"Error calculating market health: {e}")
            return "unknown"
    
    def _get_month_name(self, month: int) -> str:
        """Get month name in Russian."""
        month_names = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        return month_names[month - 1] if 1 <= month <= 12 else "Неизвестно"
