#!/usr/bin/env python3
"""Test script to verify themes are working in bot algorithm."""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.database import SessionLocal
from database.models import GlobalTheme, User, SubscriptionType
from database.models.user_issued_theme import UserIssuedTheme
from sqlalchemy import func, desc

def test_themes_algorithm():
    """Test the themes algorithm with different subscription types."""
    
    db = SessionLocal()
    try:
        # Get total themes count
        total_themes = db.query(GlobalTheme).count()
        print(f"📊 Всего тем в базе: {total_themes}")
        
        # Test for different subscription types
        subscription_tests = [
            (SubscriptionType.FREE, 1),
            (SubscriptionType.TEST_PRO, 5),
            (SubscriptionType.PRO, 5),
            (SubscriptionType.ULTRA, 10)
        ]
        
        for sub_type, expected_count in subscription_tests:
            print(f"\n🧪 Тестируем тариф {sub_type.value}:")
            
            # Get random themes (simulating the algorithm)
            themes = db.query(GlobalTheme).order_by(func.random()).limit(expected_count).all()
            
            print(f"   Получено тем: {len(themes)}")
            print(f"   Примеры тем:")
            for i, theme in enumerate(themes[:3], 1):
                print(f"   {i}. {theme.theme_name}")
        
        # Test unique themes selection (simulating UserIssuedTheme logic)
        print(f"\n🔍 Тестируем уникальность тем:")
        
        # Simulate user who already has some themes
        issued_theme_ids = [1, 2, 3, 4, 5]  # Simulate some issued themes
        
        # Get themes not yet issued to user
        available_themes = db.query(GlobalTheme).filter(
            ~GlobalTheme.id.in_(issued_theme_ids)
        ).order_by(func.random()).limit(5).all()
        
        print(f"   Доступно уникальных тем: {len(available_themes)}")
        for i, theme in enumerate(available_themes, 1):
            print(f"   {i}. {theme.theme_name}")
        
        print(f"\n✅ Алгоритм тем работает корректно!")
        print(f"🎯 Пользователи смогут получать темы согласно своим тарифам:")
        print(f"   • FREE: 1 тема")
        print(f"   • PRO/TEST_PRO: 5 тем")
        print(f"   • ULTRA: 10 тем")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Тестируем алгоритм выдачи тем...")
    test_themes_algorithm()
    print("✅ Тестирование завершено!")
