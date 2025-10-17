"""Новый менеджер тем с интеграцией мульти-модельного LLM-сервиса."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
import structlog

from config.database import SessionLocal
from database.models import GlobalTheme, TopTheme, User, SubscriptionType, ThemeRequest
from core.ai.llm_service import LLMServiceFactory
from core.ai.providers.base import AbstractLLMProvider

logger = structlog.get_logger(__name__)


class ModernThemeManager:
    """Современный менеджер тем с интеграцией мульти-модельного LLM-сервиса."""
    
    def __init__(self):
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
        """Генерация еженедельных тем с использованием нового LLM-сервиса."""
        
        try:
            logger.info("Starting theme generation", user_id=user_id, count=count)
            
            # Получаем топ-темы пользователя для персонализации
            user_top_themes = self.get_user_top_themes(user_id, limit=10)
            
            # Получаем активный LLM-провайдер
            try:
                llm_provider = LLMServiceFactory.get_active_provider(self.db)
                logger.info("LLM provider obtained", provider=type(llm_provider).__name__)
            except ValueError as e:
                logger.warning("No active LLM provider, using fallback", error=str(e))
                return self._get_fallback_themes(count)
            
            # Генерируем персонализированные темы через LLM
            personal_themes = []
            if user_top_themes:
                try:
                    personal_themes = await llm_provider.generate_personal_themes(
                        user_top_themes=user_top_themes,
                        count=count
                    )
                    logger.info("Personal themes generated", count=len(personal_themes))
                except Exception as e:
                    logger.error("Failed to generate personal themes", error=str(e))
                    personal_themes = []
            
            # Если LLM не сгенерировал темы, используем резервные
            if not personal_themes:
                personal_themes = self._get_fallback_personal_themes(user_top_themes, count)
            
            # Форматируем результат
            formatted_themes = []
            for i, theme in enumerate(personal_themes[:count]):
                formatted_themes.append({
                    "theme": theme,
                    "source": "ai_personalized",
                    "confidence": 0.9,
                    "reason": "Персонализированная тема на основе ваших успешных работ",
                    "predicted_performance": "high",
                    "generated_at": datetime.utcnow().isoformat(),
                    "llm_provider": llm_provider.model_name
                })
            
            logger.info("Theme generation completed", themes_count=len(formatted_themes))
            return formatted_themes
            
        except Exception as e:
            logger.error("Error generating weekly themes", error=str(e))
            return self._get_fallback_themes(count)
    
    def get_user_top_themes(self, user_id: int, limit: int = 10) -> List[str]:
        """Получить топ-темы пользователя из аналитики."""
        
        try:
            top_themes = self.db.query(TopTheme).join(
                TopTheme.csv_analysis
            ).filter(
                TopTheme.csv_analysis.has(user_id=user_id)
            ).order_by(
                desc(TopTheme.revenue)
            ).limit(limit).all()
            
            themes = [theme.theme_name for theme in top_themes]
            logger.info("User top themes retrieved", user_id=user_id, count=len(themes))
            return themes
            
        except Exception as e:
            logger.error("Error getting user top themes", error=str(e))
            return []
    
    def can_request_themes(self, user_id: int) -> bool:
        """Проверить, может ли пользователь запросить новые темы (недельный лимит)."""
        
        try:
            # Получаем последний запрос тем
            last_request = self.db.query(ThemeRequest).filter(
                ThemeRequest.user_id == user_id
            ).order_by(
                desc(ThemeRequest.requested_at)
            ).first()
            
            if not last_request:
                return True  # Первый запрос
            
            # Проверяем, прошла ли неделя
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            # Убеждаемся, что оба datetime имеют timezone
            if last_request.requested_at.tzinfo is None:
                last_request_time = last_request.requested_at.replace(tzinfo=timezone.utc)
            else:
                last_request_time = last_request.requested_at
            
            can_request = last_request_time < week_ago
            logger.info("Theme request eligibility checked", user_id=user_id, can_request=can_request)
            return can_request
            
        except Exception as e:
            logger.error("Error checking theme request eligibility", error=str(e))
            return False
    
    def save_theme_request(self, user_id: int, themes: List[Dict[str, Any]]) -> bool:
        """Сохранить запрос тем в базу данных."""
        
        try:
            # Извлекаем названия тем
            theme_names = [theme.get('theme', str(theme)) for theme in themes]
            
            request = ThemeRequest(
                user_id=user_id,
                themes=theme_names,
                requested_at=datetime.now(timezone.utc)
            )
            
            self.db.add(request)
            self.db.commit()
            
            logger.info("Theme request saved", user_id=user_id, themes_count=len(theme_names))
            return True
            
        except Exception as e:
            logger.error("Error saving theme request", error=str(e))
            self.db.rollback()
            return False
    
    def get_theme_request_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить историю запросов тем пользователя."""
        
        try:
            requests = self.db.query(ThemeRequest).filter(
                ThemeRequest.user_id == user_id
            ).order_by(
                desc(ThemeRequest.requested_at)
            ).limit(10).all()
            
            history = []
            for request in requests:
                history.append({
                    "themes": request.themes,
                    "requested_at": request.requested_at,
                    "formatted_date": request.requested_at.strftime("%d.%m.%Y %H:%M")
                })
            
            logger.info("Theme request history retrieved", user_id=user_id, count=len(history))
            return history
            
        except Exception as e:
            logger.error("Error getting theme request history", error=str(e))
            return []
    
    def get_themes_for_subscription(self, subscription_type: SubscriptionType) -> int:
        """Получить количество тем в зависимости от типа подписки."""
        
        theme_counts = {
            SubscriptionType.FREE: 1,
            SubscriptionType.TEST_PRO: 5,
            SubscriptionType.PRO: 5,
            SubscriptionType.ULTRA: 10
        }
        
        return theme_counts.get(subscription_type, 1)
    
    def _get_fallback_personal_themes(self, user_top_themes: List[str], count: int) -> List[str]:
        """Получить резервные персонализированные темы."""
        
        if not user_top_themes:
            return self._get_fallback_themes(count)
        
        # Базовые темы, связанные с успешными темами пользователя
        related_themes = []
        for theme in user_top_themes[:3]:  # Берем топ-3 темы
            if "бизнес" in theme.lower() or "business" in theme.lower():
                related_themes.extend(["Business Technology", "Corporate Lifestyle", "Office Environment"])
            elif "природа" in theme.lower() or "nature" in theme.lower():
                related_themes.extend(["Nature Landscapes", "Outdoor Activities", "Environmental Concepts"])
            elif "люди" in theme.lower() or "people" in theme.lower():
                related_themes.extend(["Lifestyle Portraits", "Social Interactions", "Human Emotions"])
            elif "еда" in theme.lower() or "food" in theme.lower():
                related_themes.extend(["Food Photography", "Culinary Arts", "Restaurant Scenes"])
            else:
                related_themes.extend([f"{theme} Advanced", f"{theme} Modern", f"{theme} Professional"])
        
        # Убираем дубликаты и возвращаем нужное количество
        unique_themes = list(dict.fromkeys(related_themes))
        return unique_themes[:count]
    
    def _get_fallback_themes(self, count: int) -> List[Dict[str, Any]]:
        """Получить резервные темы при ошибке генерации."""
        
        fallback_themes = [
            "Business & Corporate",
            "Lifestyle & People", 
            "Nature & Landscapes",
            "Food & Beverages",
            "Technology & Innovation",
            "Sports & Fitness",
            "Travel & Adventure",
            "Education & Learning",
            "Health & Wellness",
            "Fashion & Style"
        ]
        
        return [{
            "theme": theme, 
            "source": "fallback", 
            "confidence": 0.5, 
            "reason": "Резервная тема", 
            "predicted_performance": "medium",
            "generated_at": datetime.utcnow().isoformat(),
            "llm_provider": "fallback"
        } for theme in fallback_themes[:count]]


# Глобальный экземпляр менеджера тем
modern_theme_manager = None

def get_modern_theme_manager() -> ModernThemeManager:
    """Получить глобальный экземпляр современного менеджера тем."""
    global modern_theme_manager
    if modern_theme_manager is None:
        modern_theme_manager = ModernThemeManager()
    return modern_theme_manager
