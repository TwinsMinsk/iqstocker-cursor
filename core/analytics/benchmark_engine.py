"""Benchmark engine for comparing user performance against industry standards."""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
import pandas as pd

from config.database import SessionLocal
from database.models import User, CSVAnalysis, AnalyticsReport, TopTheme, Subscription, SubscriptionType


class BenchmarkEngine:
    """Compare user performance against industry benchmarks."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
    def get_industry_benchmarks(self) -> Dict[str, Any]:
        """Get industry benchmark data."""
        try:
            # Calculate benchmarks from all users' data
            all_reports = self.db.query(AnalyticsReport).join(CSVAnalysis).all()
            
            if not all_reports:
                return self._get_default_benchmarks()
            
            # Extract metrics
            portfolio_sold_percents = []
            new_works_percents = []
            total_revenues = []
            total_sales = []
            
            for report in all_reports:
                if report.portfolio_sold_percent:
                    portfolio_sold_percents.append(float(report.portfolio_sold_percent))
                if report.new_works_sales_percent:
                    new_works_percents.append(float(report.new_works_sales_percent))
                if report.total_revenue:
                    total_revenues.append(float(report.total_revenue))
                if report.total_sales:
                    total_sales.append(report.total_sales)
            
            # Calculate percentiles
            benchmarks = {
                "portfolio_sold_percent": {
                    "p25": np.percentile(portfolio_sold_percents, 25) if portfolio_sold_percents else 0,
                    "p50": np.percentile(portfolio_sold_percents, 50) if portfolio_sold_percents else 0,
                    "p75": np.percentile(portfolio_sold_percents, 75) if portfolio_sold_percents else 0,
                    "p90": np.percentile(portfolio_sold_percents, 90) if portfolio_sold_percents else 0,
                    "mean": np.mean(portfolio_sold_percents) if portfolio_sold_percents else 0
                },
                "new_works_percent": {
                    "p25": np.percentile(new_works_percents, 25) if new_works_percents else 0,
                    "p50": np.percentile(new_works_percents, 50) if new_works_percents else 0,
                    "p75": np.percentile(new_works_percents, 75) if new_works_percents else 0,
                    "p90": np.percentile(new_works_percents, 90) if new_works_percents else 0,
                    "mean": np.mean(new_works_percents) if new_works_percents else 0
                },
                "total_revenue": {
                    "p25": np.percentile(total_revenues, 25) if total_revenues else 0,
                    "p50": np.percentile(total_revenues, 50) if total_revenues else 0,
                    "p75": np.percentile(total_revenues, 75) if total_revenues else 0,
                    "p90": np.percentile(total_revenues, 90) if total_revenues else 0,
                    "mean": np.mean(total_revenues) if total_revenues else 0
                },
                "total_sales": {
                    "p25": np.percentile(total_sales, 25) if total_sales else 0,
                    "p50": np.percentile(total_sales, 50) if total_sales else 0,
                    "p75": np.percentile(total_sales, 75) if total_sales else 0,
                    "p90": np.percentile(total_sales, 90) if total_sales else 0,
                    "mean": np.mean(total_sales) if total_sales else 0
                }
            }
            
            return {
                "benchmarks": benchmarks,
                "sample_size": len(all_reports),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error calculating industry benchmarks: {e}")
            return self._get_default_benchmarks()
    
    def get_user_percentile_ranking(self, user_id: int) -> Dict[str, Any]:
        """Get user's percentile ranking against all users."""
        try:
            # Get user's latest report
            user_analysis = self.db.query(CSVAnalysis).filter(
                CSVAnalysis.user_id == user_id
            ).order_by(desc(CSVAnalysis.created_at)).first()
            
            if not user_analysis or not user_analysis.analytics_report:
                return {
                    "user_id": user_id,
                    "percentile_rankings": {},
                    "message": "Недостаточно данных для расчета рейтинга"
                }
            
            user_report = user_analysis.analytics_report
            
            # Get all reports for comparison
            all_reports = self.db.query(AnalyticsReport).join(CSVAnalysis).filter(
                CSVAnalysis.id != user_analysis.id
            ).all()
            
            if not all_reports:
                return {
                    "user_id": user_id,
                    "percentile_rankings": {},
                    "message": "Недостаточно данных для сравнения"
                }
            
            # Calculate percentiles for each metric
            user_metrics = {
                "portfolio_sold_percent": float(user_report.portfolio_sold_percent) if user_report.portfolio_sold_percent else 0,
                "new_works_percent": float(user_report.new_works_sales_percent) if user_report.new_works_sales_percent else 0,
                "total_revenue": float(user_report.total_revenue) if user_report.total_revenue else 0,
                "total_sales": user_report.total_sales or 0
            }
            
            percentile_rankings = {}
            
            for metric, user_value in user_metrics.items():
                # Get all values for this metric
                all_values = []
                for report in all_reports:
                    if metric == "portfolio_sold_percent" and report.portfolio_sold_percent:
                        all_values.append(float(report.portfolio_sold_percent))
                    elif metric == "new_works_percent" and report.new_works_sales_percent:
                        all_values.append(float(report.new_works_sales_percent))
                    elif metric == "total_revenue" and report.total_revenue:
                        all_values.append(float(report.total_revenue))
                    elif metric == "total_sales" and report.total_sales:
                        all_values.append(report.total_sales)
                
                if all_values:
                    # Calculate percentile
                    percentile = (sum(1 for x in all_values if x <= user_value) / len(all_values)) * 100
                    percentile_rankings[metric] = {
                        "user_value": user_value,
                        "percentile": round(percentile, 1),
                        "sample_size": len(all_values),
                        "rank_description": self._get_rank_description(percentile)
                    }
            
            return {
                "user_id": user_id,
                "percentile_rankings": percentile_rankings,
                "overall_percentile": self._calculate_overall_percentile(percentile_rankings),
                "sample_size": len(all_reports),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error calculating percentile ranking: {e}")
            return {"user_id": user_id, "error": str(e)}
    
    def get_subscription_benchmarks(self, subscription_type: SubscriptionType) -> Dict[str, Any]:
        """Get benchmarks specific to subscription type."""
        try:
            # Get users with this subscription type
            users = self.db.query(User).filter(
                User.subscription_type == subscription_type
            ).all()
            
            if not users:
                return {
                    "subscription_type": subscription_type.value,
                    "benchmarks": {},
                    "message": "Недостаточно пользователей с этой подпиской"
                }
            
            user_ids = [user.id for user in users]
            
            # Get reports for these users
            reports = self.db.query(AnalyticsReport).join(CSVAnalysis).filter(
                CSVAnalysis.user_id.in_(user_ids)
            ).all()
            
            if not reports:
                return {
                    "subscription_type": subscription_type.value,
                    "benchmarks": {},
                    "message": "Недостаточно данных для расчета бенчмарков"
                }
            
            # Calculate subscription-specific benchmarks
            metrics = {
                "portfolio_sold_percent": [],
                "new_works_percent": [],
                "total_revenue": [],
                "total_sales": []
            }
            
            for report in reports:
                if report.portfolio_sold_percent:
                    metrics["portfolio_sold_percent"].append(float(report.portfolio_sold_percent))
                if report.new_works_sales_percent:
                    metrics["new_works_percent"].append(float(report.new_works_sales_percent))
                if report.total_revenue:
                    metrics["total_revenue"].append(float(report.total_revenue))
                if report.total_sales:
                    metrics["total_sales"].append(report.total_sales)
            
            benchmarks = {}
            for metric, values in metrics.items():
                if values:
                    benchmarks[metric] = {
                        "mean": round(np.mean(values), 2),
                        "median": round(np.median(values), 2),
                        "std": round(np.std(values), 2),
                        "min": round(np.min(values), 2),
                        "max": round(np.max(values), 2),
                        "count": len(values)
                    }
            
            return {
                "subscription_type": subscription_type.value,
                "benchmarks": benchmarks,
                "user_count": len(users),
                "report_count": len(reports),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error calculating subscription benchmarks: {e}")
            return {"subscription_type": subscription_type.value, "error": str(e)}
    
    def compare_user_to_benchmarks(self, user_id: int) -> Dict[str, Any]:
        """Compare user performance to industry benchmarks."""
        try:
            # Get user's percentile ranking
            percentile_data = self.get_user_percentile_ranking(user_id)
            
            # Get industry benchmarks
            industry_benchmarks = self.get_industry_benchmarks()
            
            # Get user's latest report
            user_analysis = self.db.query(CSVAnalysis).filter(
                CSVAnalysis.user_id == user_id
            ).order_by(desc(CSVAnalysis.created_at)).first()
            
            if not user_analysis or not user_analysis.analytics_report:
                return {
                    "user_id": user_id,
                    "comparison": {},
                    "message": "Недостаточно данных для сравнения"
                }
            
            user_report = user_analysis.analytics_report
            user_subscription = user_analysis.user.subscription_type
            
            # Get subscription-specific benchmarks
            subscription_benchmarks = self.get_subscription_benchmarks(user_subscription)
            
            # Create comparison
            comparison = {}
            
            metrics_to_compare = [
                "portfolio_sold_percent",
                "new_works_percent", 
                "total_revenue",
                "total_sales"
            ]
            
            for metric in metrics_to_compare:
                user_value = None
                if metric == "portfolio_sold_percent":
                    user_value = float(user_report.portfolio_sold_percent) if user_report.portfolio_sold_percent else 0
                elif metric == "new_works_percent":
                    user_value = float(user_report.new_works_sales_percent) if user_report.new_works_sales_percent else 0
                elif metric == "total_revenue":
                    user_value = float(user_report.total_revenue) if user_report.total_revenue else 0
                elif metric == "total_sales":
                    user_value = user_report.total_sales or 0
                
                if user_value is not None:
                    industry_benchmark = industry_benchmarks["benchmarks"].get(metric, {})
                    subscription_benchmark = subscription_benchmarks["benchmarks"].get(metric, {})
                    
                    comparison[metric] = {
                        "user_value": user_value,
                        "industry_median": industry_benchmark.get("p50", 0),
                        "industry_mean": industry_benchmark.get("mean", 0),
                        "subscription_mean": subscription_benchmark.get("mean", 0),
                        "vs_industry": self._compare_to_benchmark(user_value, industry_benchmark.get("p50", 0)),
                        "vs_subscription": self._compare_to_benchmark(user_value, subscription_benchmark.get("mean", 0)),
                        "percentile": percentile_data["percentile_rankings"].get(metric, {}).get("percentile", 0)
                    }
            
            return {
                "user_id": user_id,
                "subscription_type": user_subscription.value,
                "comparison": comparison,
                "overall_performance": self._calculate_overall_performance(comparison),
                "recommendations": self._generate_recommendations(comparison),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error comparing user to benchmarks: {e}")
            return {"user_id": user_id, "error": str(e)}
    
    def track_goals(self, user_id: int, goals: Dict[str, Any]) -> Dict[str, Any]:
        """Track user progress towards goals."""
        try:
            # Get user's latest performance
            comparison = self.compare_user_to_benchmarks(user_id)
            
            if "error" in comparison:
                return comparison
            
            goal_tracking = {}
            
            for goal_name, goal_value in goals.items():
                if goal_name in comparison["comparison"]:
                    user_value = comparison["comparison"][goal_name]["user_value"]
                    progress = (user_value / goal_value * 100) if goal_value > 0 else 0
                    
                    goal_tracking[goal_name] = {
                        "goal_value": goal_value,
                        "current_value": user_value,
                        "progress_percent": round(min(100, progress), 1),
                        "achieved": user_value >= goal_value,
                        "remaining": max(0, goal_value - user_value)
                    }
            
            return {
                "user_id": user_id,
                "goal_tracking": goal_tracking,
                "overall_progress": self._calculate_overall_goal_progress(goal_tracking),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error tracking goals: {e}")
            return {"user_id": user_id, "error": str(e)}
    
    def _get_default_benchmarks(self) -> Dict[str, Any]:
        """Get default benchmark values when no data is available."""
        return {
            "benchmarks": {
                "portfolio_sold_percent": {"p25": 1.0, "p50": 2.5, "p75": 5.0, "p90": 8.0, "mean": 3.2},
                "new_works_percent": {"p25": 15.0, "p50": 25.0, "p75": 35.0, "p90": 45.0, "mean": 28.0},
                "total_revenue": {"p25": 50.0, "p50": 150.0, "p75": 300.0, "p90": 500.0, "mean": 200.0},
                "total_sales": {"p25": 5, "p50": 15, "p75": 30, "p90": 50, "mean": 20}
            },
            "sample_size": 0,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _get_rank_description(self, percentile: float) -> str:
        """Get rank description based on percentile."""
        if percentile >= 90:
            return "Топ 10%"
        elif percentile >= 75:
            return "Топ 25%"
        elif percentile >= 50:
            return "Выше среднего"
        elif percentile >= 25:
            return "Ниже среднего"
        else:
            return "Требует улучшения"
    
    def _calculate_overall_percentile(self, percentile_rankings: Dict) -> float:
        """Calculate overall percentile from individual metrics."""
        if not percentile_rankings:
            return 0
        
        percentiles = [data["percentile"] for data in percentile_rankings.values()]
        return round(np.mean(percentiles), 1)
    
    def _compare_to_benchmark(self, user_value: float, benchmark_value: float) -> str:
        """Compare user value to benchmark."""
        if benchmark_value == 0:
            return "Нет данных для сравнения"
        
        ratio = user_value / benchmark_value
        
        if ratio >= 1.5:
            return "Значительно выше"
        elif ratio >= 1.2:
            return "Выше"
        elif ratio >= 0.8:
            return "На уровне"
        elif ratio >= 0.5:
            return "Ниже"
        else:
            return "Значительно ниже"
    
    def _calculate_overall_performance(self, comparison: Dict) -> str:
        """Calculate overall performance rating."""
        if not comparison:
            return "Недостаточно данных"
        
        ratings = []
        for metric_data in comparison.values():
            percentile = metric_data.get("percentile", 0)
            if percentile >= 75:
                ratings.append("excellent")
            elif percentile >= 50:
                ratings.append("good")
            elif percentile >= 25:
                ratings.append("fair")
            else:
                ratings.append("poor")
        
        # Majority rating
        if ratings.count("excellent") >= len(ratings) / 2:
            return "Отличная"
        elif ratings.count("good") >= len(ratings) / 2:
            return "Хорошая"
        elif ratings.count("fair") >= len(ratings) / 2:
            return "Удовлетворительная"
        else:
            return "Требует улучшения"
    
    def _generate_recommendations(self, comparison: Dict) -> List[str]:
        """Generate recommendations based on comparison."""
        recommendations = []
        
        for metric, data in comparison.items():
            percentile = data.get("percentile", 0)
            
            if percentile < 25:
                if metric == "portfolio_sold_percent":
                    recommendations.append("Увеличьте количество загрузок для повышения продаж портфолио")
                elif metric == "new_works_percent":
                    recommendations.append("Фокусируйтесь на создании новых работ для увеличения продаж")
                elif metric == "total_revenue":
                    recommendations.append("Улучшите качество контента для увеличения доходов")
                elif metric == "total_sales":
                    recommendations.append("Увеличьте активность загрузок для роста продаж")
        
        if not recommendations:
            recommendations.append("Продолжайте текущую стратегию - показатели выше среднего")
        
        return recommendations
    
    def _calculate_overall_goal_progress(self, goal_tracking: Dict) -> float:
        """Calculate overall goal progress."""
        if not goal_tracking:
            return 0
        
        progress_values = [data["progress_percent"] for data in goal_tracking.values()]
        return round(np.mean(progress_values), 1)
