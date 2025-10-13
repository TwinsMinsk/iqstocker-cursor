"""Enhanced theme generation with AI integration."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from config.database import SessionLocal
from database.models import GlobalTheme, TopTheme, User, SubscriptionType, ThemeRequest
from core.ai.categorizer import ThemeCategorizer


class EnhancedThemeManager:
    """Enhanced theme manager with AI integration and market analysis."""
    
    def __init__(self):
        self.theme_categorizer = ThemeCategorizer()
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
    ) -> List[str]:
        """Generate weekly themes with enhanced AI analysis."""
        
        try:
            # Get user's top themes from analytics
            user_top_themes = self.get_user_top_themes(user_id)
            
            # Get trending themes from global database
            trending_themes = self.get_trending_themes(limit=20)
            trending_names = [theme.theme_name for theme in trending_themes]
            
            # Get seasonal themes for current month
            seasonal_themes = self.get_seasonal_themes()
            
            # Generate themes using AI
            if user_top_themes:
                # Generate personal themes based on user's success
                personal_themes = await self.theme_categorizer.generate_personal_themes(user_top_themes)
            else:
                # For new users, use trending themes
                personal_themes = trending_names[:3]
            
            # Mix themes: personal + trending + seasonal
            all_themes = []
            
            # Add personal themes (40% of total)
            personal_count = max(1, count // 3)
            all_themes.extend(personal_themes[:personal_count])
            
            # Add trending themes (40% of total)
            trending_count = max(1, count // 3)
            trending_filtered = [t for t in trending_names if t not in all_themes]
            all_themes.extend(trending_filtered[:trending_count])
            
            # Add seasonal themes (20% of total)
            seasonal_count = max(1, count - len(all_themes))
            seasonal_filtered = [t for t in seasonal_themes if t not in all_themes]
            all_themes.extend(seasonal_filtered[:seasonal_count])
            
            # Ensure we have enough themes
            if len(all_themes) < count:
                remaining_count = count - len(all_themes)
                additional_themes = [
                    theme for theme in trending_names 
                    if theme not in all_themes
                ][:remaining_count]
                all_themes.extend(additional_themes)
            
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
    
    def _get_fallback_themes(self, count: int) -> List[str]:
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
        
        return fallback_themes[:count]


# Global enhanced theme manager instance
enhanced_theme_manager = None

def get_enhanced_theme_manager() -> EnhancedThemeManager:
    """Get global enhanced theme manager instance."""
    global enhanced_theme_manager
    if enhanced_theme_manager is None:
        enhanced_theme_manager = EnhancedThemeManager()
    return enhanced_theme_manager
