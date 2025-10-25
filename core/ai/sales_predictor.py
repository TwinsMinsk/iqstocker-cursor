"""Sales prediction system using historical data analysis."""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import pandas as pd

from config.database import SessionLocal
from database.models import User, CSVAnalysis, AnalyticsReport


class SalesPredictor:
    """Predict sales trends and provide recommendations."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
    def get_user_sales_history(self, user_id: int, months: int = 12) -> List[Dict[str, Any]]:
        """Get user's sales history for analysis."""
        try:
            # Get completed CSV analyses for the user
            analyses = self.db.query(CSVAnalysis).join(AnalyticsReport).filter(
                and_(
                    CSVAnalysis.user_id == user_id,
                    CSVAnalysis.status == 'COMPLETED',
                    CSVAnalysis.created_at >= datetime.utcnow() - timedelta(days=months * 30)
                )
            ).order_by(CSVAnalysis.created_at).all()
            
            sales_history = []
            for analysis in analyses:
                report = analysis.analytics_report
                if report:
                    sales_history.append({
                        'date': analysis.created_at,
                        'month': analysis.month,
                        'year': analysis.year,
                        'sales': report.total_sales,
                        'revenue': float(report.total_revenue) if report.total_revenue else 0,
                        'portfolio_sold_percent': float(report.portfolio_sold_percent) if report.portfolio_sold_percent else 0,
                        'new_works_percent': float(report.new_works_sales_percent) if report.new_works_sales_percent else 0
                    })
            
            return sales_history
        except Exception as e:
            print(f"Error getting sales history: {e}")
            return []
    
    def predict_next_month_sales(self, user_id: int) -> Dict[str, Any]:
        """Predict sales for next month using linear regression."""
        try:
            sales_history = self.get_user_sales_history(user_id)
            
            if len(sales_history) < 3:
                return {
                    "predicted_sales": 0,
                    "predicted_revenue": 0.0,
                    "confidence": "low",
                    "message": "Недостаточно данных для прогноза. Нужно минимум 3 месяца аналитики."
                }
            
            # Prepare data for regression
            df = pd.DataFrame(sales_history)
            df['month_number'] = df['year'] * 12 + df['month']
            df = df.sort_values('month_number')
            
            # Use polynomial features for better trend detection
            X = df[['month_number']].values
            y_sales = df['sales'].values
            y_revenue = df['revenue'].values
            
            # Create polynomial features
            poly_features = PolynomialFeatures(degree=2)
            X_poly = poly_features.fit_transform(X)
            
            # Train models
            model_sales = LinearRegression()
            model_revenue = LinearRegression()
            
            model_sales.fit(X_poly, y_sales)
            model_revenue.fit(X_poly, y_revenue)
            
            # Predict next month
            next_month_number = df['month_number'].max() + 1
            next_month_poly = poly_features.transform([[next_month_number]])
            
            predicted_sales = max(0, int(model_sales.predict(next_month_poly)[0]))
            predicted_revenue = max(0.0, float(model_revenue.predict(next_month_poly)[0]))
            
            # Calculate confidence based on R² score
            sales_r2 = model_sales.score(X_poly, y_sales)
            revenue_r2 = model_revenue.score(X_poly, y_revenue)
            avg_r2 = (sales_r2 + revenue_r2) / 2
            
            if avg_r2 > 0.8:
                confidence = "high"
            elif avg_r2 > 0.6:
                confidence = "medium"
            else:
                confidence = "low"
            
            # Calculate growth trend
            recent_sales = df['sales'].tail(3).mean()
            older_sales = df['sales'].head(3).mean()
            growth_rate = ((recent_sales - older_sales) / older_sales * 100) if older_sales > 0 else 0
            
            return {
                "predicted_sales": predicted_sales,
                "predicted_revenue": round(predicted_revenue, 2),
                "confidence": confidence,
                "growth_rate": round(growth_rate, 1),
                "r2_score": round(avg_r2, 3),
                "data_points": len(sales_history),
                "message": f"Прогноз основан на {len(sales_history)} месяцах данных. Уверенность: {confidence}."
            }
            
        except Exception as e:
            print(f"Error predicting sales: {e}")
            return {
                "predicted_sales": 0,
                "predicted_revenue": 0.0,
                "confidence": "low",
                "message": f"Ошибка прогнозирования: {str(e)}"
            }
    
    def calculate_growth_trend(self, user_id: int) -> Dict[str, Any]:
        """Calculate growth trend analysis."""
        try:
            sales_history = self.get_user_sales_history(user_id, months=6)
            
            if len(sales_history) < 2:
                return {
                    "trend": "insufficient_data",
                    "growth_rate": 0,
                    "message": "Недостаточно данных для анализа тренда"
                }
            
            df = pd.DataFrame(sales_history)
            df = df.sort_values('date')
            
            # Calculate month-over-month growth
            df['sales_growth'] = df['sales'].pct_change() * 100
            df['revenue_growth'] = df['revenue'].pct_change() * 100
            
            # Calculate average growth
            avg_sales_growth = df['sales_growth'].mean()
            avg_revenue_growth = df['revenue_growth'].mean()
            
            # Determine trend
            if avg_sales_growth > 10:
                trend = "growing"
            elif avg_sales_growth > 0:
                trend = "stable_growth"
            elif avg_sales_growth > -10:
                trend = "stable"
            else:
                trend = "declining"
            
            # Calculate volatility
            volatility = df['sales_growth'].std()
            
            return {
                "trend": trend,
                "growth_rate": round(avg_sales_growth, 1),
                "revenue_growth_rate": round(avg_revenue_growth, 1),
                "volatility": round(volatility, 1),
                "months_analyzed": len(sales_history),
                "message": f"Тренд: {trend}, рост продаж: {avg_sales_growth:.1f}% в месяц"
            }
            
        except Exception as e:
            print(f"Error calculating growth trend: {e}")
            return {
                "trend": "error",
                "growth_rate": 0,
                "message": f"Ошибка анализа тренда: {str(e)}"
            }
    
    def suggest_upload_strategy(self, user_id: int) -> Dict[str, Any]:
        """Suggest optimal upload strategy based on historical data."""
        try:
            sales_history = self.get_user_sales_history(user_id)
            growth_trend = self.calculate_growth_trend(user_id)
            
            if not sales_history:
                return {
                    "strategy": "start_uploading",
                    "recommended_uploads": 20,
                    "message": "Начните с загрузки 20 работ в месяц для получения первых данных"
                }
            
            # Get latest analysis
            latest_analysis = sales_history[-1]
            
            # Calculate optimal uploads based on performance
            portfolio_sold_percent = latest_analysis['portfolio_sold_percent']
            new_works_percent = latest_analysis['new_works_percent']
            
            # Base recommendation on portfolio performance
            if portfolio_sold_percent > 5:
                strategy = "increase_uploads"
                recommended_uploads = min(50, int(latest_analysis['sales'] * 2))
            elif portfolio_sold_percent > 2:
                strategy = "maintain_uploads"
                recommended_uploads = int(latest_analysis['sales'] * 1.5)
            else:
                strategy = "focus_quality"
                recommended_uploads = max(10, int(latest_analysis['sales'] * 1.2))
            
            # Adjust based on growth trend
            if growth_trend['trend'] == 'growing':
                recommended_uploads = int(recommended_uploads * 1.2)
            elif growth_trend['trend'] == 'declining':
                recommended_uploads = int(recommended_uploads * 0.8)
            
            # Adjust based on new works performance
            if new_works_percent > 30:
                message = f"Отличные результаты новых работ ({new_works_percent:.1f}%)! Увеличивайте загрузки."
            elif new_works_percent > 20:
                message = f"Хорошие результаты новых работ ({new_works_percent:.1f}%). Продолжайте текущий темп."
            else:
                message = f"Низкие продажи новых работ ({new_works_percent:.1f}%). Фокусируйтесь на качестве."
            
            return {
                "strategy": strategy,
                "recommended_uploads": recommended_uploads,
                "current_performance": {
                    "portfolio_sold_percent": portfolio_sold_percent,
                    "new_works_percent": new_works_percent,
                    "monthly_sales": latest_analysis['sales']
                },
                "growth_trend": growth_trend['trend'],
                "message": message
            }
            
        except Exception as e:
            print(f"Error suggesting upload strategy: {e}")
            return {
                "strategy": "error",
                "recommended_uploads": 20,
                "message": f"Ошибка анализа стратегии: {str(e)}"
            }
    
    def get_seasonal_patterns(self, user_id: int) -> Dict[str, Any]:
        """Analyze seasonal patterns in user's sales."""
        try:
            sales_history = self.get_user_sales_history(user_id, months=24)
            
            if len(sales_history) < 6:
                return {
                    "patterns": {},
                    "message": "Недостаточно данных для анализа сезонности"
                }
            
            df = pd.DataFrame(sales_history)
            
            # Group by month to find seasonal patterns
            monthly_avg = df.groupby('month').agg({
                'sales': 'mean',
                'revenue': 'mean'
            }).round(2)
            
            # Find best and worst months
            best_month = monthly_avg['sales'].idxmax()
            worst_month = monthly_avg['sales'].idxmin()
            
            # Calculate seasonal variation
            seasonal_variation = (monthly_avg['sales'].max() - monthly_avg['sales'].min()) / monthly_avg['sales'].mean() * 100
            
            patterns = {}
            for month in range(1, 13):
                month_name = [
                    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
                ][month - 1]
                
                if month in monthly_avg.index:
                    patterns[month_name] = {
                        "avg_sales": int(monthly_avg.loc[month, 'sales']),
                        "avg_revenue": float(monthly_avg.loc[month, 'revenue'])
                    }
                else:
                    patterns[month_name] = {
                        "avg_sales": 0,
                        "avg_revenue": 0.0
                    }
            
            return {
                "patterns": patterns,
                "best_month": best_month,
                "worst_month": worst_month,
                "seasonal_variation": round(seasonal_variation, 1),
                "message": f"Лучший месяц: {best_month}, худший: {worst_month}. Сезонность: {seasonal_variation:.1f}%"
            }
            
        except Exception as e:
            print(f"Error analyzing seasonal patterns: {e}")
            return {
                "patterns": {},
                "message": f"Ошибка анализа сезонности: {str(e)}"
            }
    
    def get_comprehensive_prediction(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive sales prediction and recommendations."""
        try:
            prediction = self.predict_next_month_sales(user_id)
            growth_trend = self.calculate_growth_trend(user_id)
            upload_strategy = self.suggest_upload_strategy(user_id)
            seasonal_patterns = self.get_seasonal_patterns(user_id)
            
            return {
                "user_id": user_id,
                "prediction": prediction,
                "growth_trend": growth_trend,
                "upload_strategy": upload_strategy,
                "seasonal_patterns": seasonal_patterns,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating comprehensive prediction: {e}")
            return {
                "user_id": user_id,
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
