"""Enhanced theme generation with AI integration and market analysis."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from config.database import SessionLocal
from database.models import GlobalTheme, TopTheme, User, SubscriptionType, ThemeRequest
from core.ai.categorizer import ThemeCategorizer
from core.ai.sales_predictor import SalesPredictor
from core.ai.recommendation_engine import RecommendationEngine
from core.ai.market_analyzer import MarketAnalyzer
from core.ai.cache_manager import AICacheManager
from core.ai.rate_limiter import AIRateLimiter


class EnhancedThemeManager:
    """Enhanced theme manager with AI integration and market analysis."""
    
    def __init__(self):
        self.theme_categorizer = ThemeCategorizer()
        self.sales_predictor = SalesPredictor()
        self.recommendation_engine = RecommendationEngine()
        self.market_analyzer = MarketAnalyzer()
        self.cache_manager = AICacheManager()
        self.rate_limiter = AIRateLimiter()
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
    async def generate_weekly_themes(
        self, 
        user_id: int, 
        subscription_type: SubscriptionType,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate weekly themes with enhanced AI analysis and predictions."""
        
        try:
            # Check cache first
            cache_key = f"weekly_themes_{user_id}_{count}"
            cached_themes = self.cache_manager.get_cached_result("weekly_themes", cache_key)
            if cached_themes:
                return cached_themes.get("themes", [])
            
            # Get sales predictions for user
            sales_prediction = self.sales_predictor.predict_next_month_sales(user_id)
            
            # Get personalized recommendations
            personalized_recommendations = self.recommendation_engine.get_personalized_themes(user_id, count)
            
            # Get market trends
            market_trends = self.market_analyzer.get_trending_themes('week', 20)
            
            # Get user's top themes from analytics
            user_top_themes = self.get_user_top_themes(user_id)
            
            # Get seasonal themes for current month
            seasonal_themes = self.get_seasonal_themes()
            
            # Generate themes using AI with rate limiting
            async def generate_personal_themes():
                if user_top_themes:
                    return await self.theme_categorizer.generate_personal_themes(user_top_themes)
                else:
                    return [rec["theme"] for rec in personalized_recommendations[:3]]
            
            # Queue AI request with rate limiting
            queue_result = await self.rate_limiter.queue_request(
                "openai", 
                generate_personal_themes, 
                str(user_id)
            )
            
            if queue_result["queued"]:
                personal_themes = await generate_personal_themes()
            else:
                personal_themes = [rec["theme"] for rec in personalized_recommendations[:3]]
            
            # Mix themes with improved algorithm (personal 50%, trending 30%, seasonal 20%)
            all_themes = []
            
            # Add personal themes (50% of total)
            personal_count = max(1, int(count * 0.5))
            for i, theme in enumerate(personal_themes[:personal_count]):
                all_themes.append({
                    "theme": theme,
                    "source": "personal",
                    "confidence": 0.9,
                    "reason": "Основано на ваших успешных темах",
                    "predicted_performance": "high" if sales_prediction.get("confidence") == "high" else "medium"
                })
            
            # Add trending themes (30% of total)
            trending_count = max(1, int(count * 0.3))
            trending_names = [trend["theme_name"] for trend in market_trends]
            for i, theme in enumerate(trending_names[:trending_count]):
                if not any(t["theme"] == theme for t in all_themes):
                    trend_data = next((t for t in market_trends if t["theme_name"] == theme), {})
                    all_themes.append({
                        "theme": theme,
                        "source": "trending",
                        "confidence": trend_data.get("trend_score", 0.7),
                        "reason": f"Трендовая тема (рост: {trend_data.get('growth_rate', 0):.1f}%)",
                        "predicted_performance": "high" if trend_data.get("trend_score", 0) > 0.8 else "medium"
                    })
            
            # Add seasonal themes (20% of total)
            seasonal_count = max(1, count - len(all_themes))
            for i, theme in enumerate(seasonal_themes[:seasonal_count]):
                if not any(t["theme"] == theme for t in all_themes):
                    all_themes.append({
                        "theme": theme,
                        "source": "seasonal",
                        "confidence": 0.8,
                        "reason": "Сезонная тема для текущего месяца",
                        "predicted_performance": "medium"
                    })
            
            # Ensure we have enough themes
            if len(all_themes) < count:
                remaining_count = count - len(all_themes)
                additional_themes = [
                    theme for theme in trending_names 
                    if not any(t["theme"] == theme for t in all_themes)
                ][:remaining_count]
                
                for theme in additional_themes:
                    all_themes.append({
                        "theme": theme,
                        "source": "fallback",
                        "confidence": 0.6,
                        "reason": "Популярная тема",
                        "predicted_performance": "medium"
                    })
            
            # Sort by confidence and predicted performance
            all_themes.sort(key=lambda x: (x["confidence"], x["predicted_performance"]), reverse=True)
            
            # Cache the results
            self.cache_manager.cache_result("weekly_themes", cache_key, {
                "themes": all_themes[:count],
                "generated_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "sales_prediction": sales_prediction
            }, ttl=3600)  # Cache for 1 hour
            
            return all_themes[:count]
            
        except Exception as e:
            print(f"Error generating weekly themes: {e}")
            return self._get_fallback_themes(count)
    
    def get_user_top_themes(self, user_id: int, limit: int = 10) -> List[str]:
        """Get user's top themes from their analytics."""
        
        try:
            top_themes = self.db.query(TopTheme).join(
                TopTheme.csv_analysis
            ).filter(
                TopTheme.csv_analysis.has(user_id=user_id)
            ).order_by(
                desc(TopTheme.revenue)
            ).limit(limit).all()
            
            return [theme.theme_name for theme in top_themes]
            
        except Exception as e:
            print(f"Error getting user top themes: {e}")
            return []
    
    def get_trending_themes(self, limit: int = 20) -> List[GlobalTheme]:
        """Get trending themes from global database."""
        
        try:
            themes = self.db.query(GlobalTheme).order_by(
                desc(GlobalTheme.total_revenue)
            ).limit(limit).all()
            
            return themes
            
        except Exception as e:
            print(f"Error getting trending themes: {e}")
            return []
    
    def get_seasonal_themes(self) -> List[str]:
        """Get seasonal themes for current month."""
        
        try:
            current_month = datetime.now().month
            
            # Seasonal themes by month
            seasonal_themes = {
                1: ["Новогодние праздники", "Зимние сцены", "Зимний спорт", "Уютные моменты"],
                2: ["День Святого Валентина", "Зимние пейзажи", "Домашний уют", "Образование"],
                3: ["Весенние сцены", "Природа пробуждается", "Выпускные", "Весенние активности"],
                4: ["Пасха", "Весенние цветы", "Садоводство", "Весенний спорт"],
                5: ["День матери", "Весенние праздники", "Садоводство", "Весенние активности"],
                6: ["День отца", "Летние сцены", "Отпуск", "Летние цветы"],
                7: ["День независимости", "Летние активности", "Пляж", "Летние праздники"],
                8: ["Летний отдых", "Летние сцены", "Летние цветы", "Летний спорт"],
                9: ["Начало учебного года", "Осенние сцены", "Сбор урожая", "Осенние активности"],
                10: ["Хэллоуин", "Осенние сцены", "Сбор урожая", "Осенние распродажи"],
                11: ["День благодарения", "Осенние сцены", "Черная пятница", "Сбор урожая"],
                12: ["Рождество", "Зимние сцены", "Подарки", "Праздничная атмосфера"]
            }
            
            return seasonal_themes.get(current_month, ["Общие темы"])
            
        except Exception as e:
            print(f"Error getting seasonal themes: {e}")
            return ["Общие темы"]
    
    def can_request_themes(self, user_id: int) -> bool:
        """Check if user can request new themes (weekly limit)."""
        
        try:
            # Get last theme request
            last_request = self.db.query(ThemeRequest).filter(
                ThemeRequest.user_id == user_id
            ).order_by(
                desc(ThemeRequest.requested_at)
            ).first()
            
            if not last_request:
                return True  # First request
            
            # Check if week has passed
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            # Ensure both datetimes are timezone-aware
            if last_request.requested_at.tzinfo is None:
                last_request_time = last_request.requested_at.replace(tzinfo=timezone.utc)
            else:
                last_request_time = last_request.requested_at
            return last_request_time < week_ago
            
        except Exception as e:
            print(f"Error checking theme request eligibility: {e}")
            return False
    
    def save_theme_request(self, user_id: int, themes: List[str]) -> bool:
        """Save theme request to database."""
        
        try:
            request = ThemeRequest(
                user_id=user_id,
                themes=themes,
                requested_at=datetime.now(timezone.utc)
            )
            
            self.db.add(request)
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error saving theme request: {e}")
            self.db.rollback()
            return False
    
    def get_theme_request_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's theme request history."""
        
        try:
            requests = self.db.query(ThemeRequest).filter(
                ThemeRequest.user_id == user_id
            ).order_by(
                desc(ThemeRequest.requested_at)
            ).limit(10).all()
            
            return [
                {
                    "themes": request.themes,
                    "requested_at": request.requested_at
                }
                for request in requests
            ]
            
        except Exception as e:
            print(f"Error getting theme request history: {e}")
            return []
    
    def get_themes_for_subscription(self, subscription_type: SubscriptionType) -> int:
        """Get number of themes based on subscription type."""
        
        if subscription_type == SubscriptionType.FREE:
            return 1
        elif subscription_type == SubscriptionType.TEST_PRO:
            return 5
        elif subscription_type == SubscriptionType.PRO:
            return 5
        elif subscription_type == SubscriptionType.ULTRA:
            return 10
        else:
            return 1
    
    def update_global_themes(self, top_themes: List[TopTheme]):
        """Update global themes database with new top themes."""
        
        try:
            for top_theme in top_themes:
                # Check if theme already exists
                existing_theme = self.db.query(GlobalTheme).filter(
                    GlobalTheme.theme_name == top_theme.theme_name
                ).first()
                
                if existing_theme:
                    # Update existing theme
                    existing_theme.total_sales += top_theme.sales_count
                    existing_theme.total_revenue += top_theme.revenue
                    existing_theme.authors_count += 1
                    existing_theme.last_updated = datetime.now(timezone.utc)
                else:
                    # Create new theme
                    new_theme = GlobalTheme(
                        theme_name=top_theme.theme_name,
                        total_sales=top_theme.sales_count,
                        total_revenue=top_theme.revenue,
                        authors_count=1,
                        last_updated=datetime.now(timezone.utc)
                    )
                    self.db.add(new_theme)
            
            self.db.commit()
            print(f"Updated global themes with {len(top_themes)} themes")
            
        except Exception as e:
            print(f"Error updating global themes: {e}")
            self.db.rollback()
    
    def _get_fallback_themes(self, count: int) -> List[Dict[str, Any]]:
        """Get fallback themes when AI generation fails."""
        
        fallback_themes = [
            "Бизнес и офис",
            "Люди и портреты",
            "Природа и пейзажи",
            "Еда и напитки",
            "Технологии",
            "Спорт и фитнес",
            "Путешествия",
            "Образование",
            "Здоровье и медицина",
            "Мода и стиль"
        ]
        
        return [{"theme": theme, "source": "fallback", "confidence": 0.5, "reason": "Резервная тема", "predicted_performance": "medium"} for theme in fallback_themes[:count]]
    
    async def get_enhanced_theme_analysis(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive theme analysis with AI insights."""
        try:
            # Get sales prediction
            sales_prediction = self.sales_predictor.predict_next_month_sales(user_id)
            
            # Get personalized recommendations
            recommendations = self.recommendation_engine.get_comprehensive_recommendations(user_id)
            
            # Get market trends
            market_trends = self.market_analyzer.get_trending_themes('week', 10)
            
            # Get seasonal analysis
            current_month = datetime.utcnow().month
            seasonal_analysis = self.market_analyzer.analyze_seasonal_trends(current_month)
            
            # Get user's success patterns
            success_patterns = self.recommendation_engine.get_success_patterns(user_id)
            
            return {
                "user_id": user_id,
                "sales_prediction": sales_prediction,
                "recommendations": recommendations,
                "market_trends": market_trends,
                "seasonal_analysis": seasonal_analysis,
                "success_patterns": success_patterns,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting enhanced theme analysis: {e}")
            return {"user_id": user_id, "error": str(e)}
    
    def get_ai_performance_metrics(self) -> Dict[str, Any]:
        """Get AI performance metrics for theme generation."""
        try:
            # Get cache statistics
            cache_stats = self.cache_manager.get_cache_statistics()
            
            # Get rate limit status
            rate_limit_status = self.rate_limiter.get_rate_limit_status("openai")
            
            return {
                "cache_performance": cache_stats,
                "rate_limit_status": rate_limit_status,
                "ai_components": {
                    "theme_categorizer": "active",
                    "sales_predictor": "active", 
                    "recommendation_engine": "active",
                    "market_analyzer": "active",
                    "cache_manager": "active",
                    "rate_limiter": "active"
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting AI performance metrics: {e}")
            return {"error": str(e)}


# Global enhanced theme manager instance
enhanced_theme_manager = None

def get_enhanced_theme_manager() -> EnhancedThemeManager:
    """Get global enhanced theme manager instance."""
    global enhanced_theme_manager
    if enhanced_theme_manager is None:
        enhanced_theme_manager = EnhancedThemeManager()
    return enhanced_theme_manager
