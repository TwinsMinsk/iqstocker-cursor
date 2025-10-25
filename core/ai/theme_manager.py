"""Theme manager for global themes and personal theme generation."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from config.database import SessionLocal
from database.models import GlobalTheme, User, SubscriptionType
from core.ai.categorizer import ThemeCategorizer


class ThemeManager:
    """Manager for themes and trends."""
    
    def __init__(self):
        self.theme_categorizer = ThemeCategorizer()
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
    # def update_global_themes(self, top_themes: List[TopTheme]):
    #     """Update global themes database with new top themes."""
    #     # TopTheme functionality removed
    #     pass
    
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
    
    def get_user_top_themes(self, user_id: int, limit: int = 10) -> List[str]:
        """Get user's top themes from their analytics."""
        # TopTheme functionality removed - return empty list
        return []
    
    async def generate_personal_themes(
        self, 
        user_id: int, 
        subscription_type: SubscriptionType,
        count: int = 5
    ) -> List[str]:
        """Generate personal themes for user based on their history and trends."""
        
        try:
            # Get user's top themes
            user_top_themes = self.get_user_top_themes(user_id)
            
            # Get trending themes
            trending_themes = self.get_trending_themes(limit=20)
            trending_names = [theme.theme_name for theme in trending_themes]
            
            # Generate personal themes using AI
            if user_top_themes:
                personal_themes = await self.theme_categorizer.generate_personal_themes(user_top_themes)
            else:
                # If user has no history, use trending themes
                personal_themes = trending_names[:count]
            
            # Mix with trending themes if needed
            if len(personal_themes) < count:
                remaining_count = count - len(personal_themes)
                additional_themes = [
                    theme for theme in trending_names 
                    if theme not in personal_themes
                ][:remaining_count]
                personal_themes.extend(additional_themes)
            
            return personal_themes[:count]
            
        except Exception as e:
            print(f"Error generating personal themes: {e}")
            return []
    
    def get_theme_request_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's theme request history."""
        
        try:
            from database.models import ThemeRequest
            
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
    
    def can_request_themes(self, user_id: int) -> bool:
        """Check if user can request new themes (weekly limit)."""
        
        try:
            from database.models import ThemeRequest
            
            # Get last theme request
            last_request = self.db.query(ThemeRequest).filter(
                ThemeRequest.user_id == user_id
            ).order_by(
                desc(ThemeRequest.requested_at)
            ).first()
            
            if not last_request:
                return True  # First request
            
            # Check if week has passed
            week_ago = datetime.utcnow() - timedelta(days=7)
            return last_request.requested_at < week_ago
            
        except Exception as e:
            print(f"Error checking theme request eligibility: {e}")
            return False
    
    def save_theme_request(self, user_id: int, themes: List[str]) -> bool:
        """Save theme request to database."""
        
        try:
            from database.models import ThemeRequest
            
            request = ThemeRequest(
                user_id=user_id,
                themes=themes,
                requested_at=datetime.utcnow()
            )
            
            self.db.add(request)
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error saving theme request: {e}")
            self.db.rollback()
            return False
    
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
