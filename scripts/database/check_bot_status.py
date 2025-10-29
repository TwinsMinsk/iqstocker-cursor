#!/usr/bin/env python3
"""
Скрипт для проверки статуса бота и пользователей.
"""

import os
import sys
import asyncio
from pathlib import Path

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Загружаем переменные окружения
env_file = Path("local.env")
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

async def check_bot_status():
    """Проверяем статус бота."""
    
    print("🤖 Проверяем статус бота...")
    
    try:
        from aiogram import Bot
        from config.settings import settings
        
        bot = Bot(token=settings.bot_token)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"✅ Бот активен: @{bot_info.username} ({bot_info.first_name})")
        print(f"   ID: {bot_info.id}")
        print(f"   Токен: {settings.bot_token[:10]}...")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к боту: {e}")
        return False

def check_database_users():
    """Проверяем пользователей в базе данных."""
    
    print("\n👥 Проверяем пользователей в базе данных...")
    
    try:
        from config.database import SessionLocal
        from database.models import User, SubscriptionType, Limits
        
        db = SessionLocal()
        try:
            # Получаем всех пользователей
            users = db.query(User).all()
            print(f"✅ Найдено пользователей: {len(users)}")
            
            if users:
                for user in users:
                    print(f"   👤 Пользователь {user.id}:")
                    print(f"      Telegram ID: {user.telegram_id}")
                    print(f"      Username: @{user.username}")
                    print(f"      Имя: {user.first_name}")
                    print(f"      Подписка: {user.subscription_type}")
                    
                    # Проверяем лимиты
                    limits = db.query(Limits).filter(Limits.user_id == user.id).first()
                    if limits:
                        print(f"      Лимиты аналитики: {limits.analytics_remaining}")
                    else:
                        print(f"      ❌ Лимиты не найдены")
            else:
                print("❌ Пользователи не найдены")
                print("💡 Создайте пользователя через команду /start")
            
            return len(users) > 0
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Ошибка проверки пользователей: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_csv_analyses():
    """Проверяем анализы CSV в базе данных."""
    
    print("\n📊 Проверяем анализы CSV в базе данных...")
    
    try:
        from config.database import SessionLocal
        from database.models import CSVAnalysis, AnalysisStatus
        
        db = SessionLocal()
        try:
            # Получаем все анализы
            analyses = db.query(CSVAnalysis).all()
            print(f"✅ Найдено анализов: {len(analyses)}")
            
            if analyses:
                for analysis in analyses:
                    print(f"   📈 Анализ {analysis.id}:")
                    print(f"      Пользователь: {analysis.user_id}")
                    print(f"      Статус: {analysis.status}")
                    print(f"      Файл: {analysis.file_path}")
                    print(f"      Создан: {analysis.created_at}")
                    if analysis.processed_at:
                        print(f"      Обработан: {analysis.processed_at}")
            else:
                print("ℹ️  Анализы не найдены")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Ошибка проверки анализов: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_test_user():
    """Создаем тестового пользователя."""
    
    print("\n👤 Создаем тестового пользователя...")
    
    try:
        from config.database import SessionLocal
        from database.models import User, SubscriptionType, Limits
        from datetime import datetime, timezone
        
        db = SessionLocal()
        try:
            # Проверяем, есть ли уже пользователь с telegram_id = 811079407
            existing_user = db.query(User).filter(User.telegram_id == 811079407).first()
            
            if existing_user:
                print(f"✅ Пользователь уже существует: {existing_user.username}")
                return True
            
            # Создаем нового пользователя
            # Use naive datetime for database compatibility (TIMESTAMP WITHOUT TIME ZONE)
            expires_at = datetime.utcnow().replace(year=2030)
            test_user = User(
                telegram_id=811079407,
                username="test_user",
                first_name="Test User",
                subscription_type=SubscriptionType.PRO,
                subscription_expires_at=expires_at
            )
            db.add(test_user)
            db.flush()  # Получаем ID
            
            # Создаем лимиты
            limits = Limits(
                user_id=test_user.id,
                analytics_total=10,
                analytics_used=0,
                themes_total=10,
                themes_used=0,
                top_themes_total=10,
                top_themes_used=0
            )
            db.add(limits)
            db.commit()
            
            print(f"✅ Тестовый пользователь создан:")
            print(f"   ID: {test_user.id}")
            print(f"   Telegram ID: {test_user.telegram_id}")
            print(f"   Username: @{test_user.username}")
            print(f"   Подписка: {test_user.subscription_type}")
            print(f"   Лимиты аналитики: {limits.analytics_remaining}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Ошибка создания пользователя: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Главная функция."""
    
    print("🔍 Проверка статуса бота и пользователей")
    print("=" * 60)
    
    # Проверяем статус бота
    bot_ok = await check_bot_status()
    
    # Проверяем пользователей
    users_ok = check_database_users()
    
    # Проверяем анализы
    analyses_ok = check_csv_analyses()
    
    # Если нет пользователей, создаем тестового
    if not users_ok:
        print("\n⚠️  Пользователи не найдены, создаем тестового...")
        create_test_user()
    
    print("\n" + "=" * 60)
    print("📋 РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
    print(f"🤖 Бот: {'✅ OK' if bot_ok else '❌ Проблема'}")
    print(f"👥 Пользователи: {'✅ OK' if users_ok else '❌ Проблема'}")
    print(f"📊 Анализы: {'✅ OK' if analyses_ok else '❌ Проблема'}")
    
    if bot_ok and users_ok:
        print("\n🎉 Все проверки пройдены!")
        print("💡 Теперь попробуйте отправить CSV файл боту.")
        print("💡 Если бот не отвечает, проверьте:")
        print("   - Запущен ли бот (python run_local_bot.py)")
        print("   - Правильный ли токен в local.env")
        print("   - Есть ли интернет соединение")
    else:
        print("\n❌ Обнаружены проблемы.")
        print("💡 Исправьте ошибки и повторите проверку.")

if __name__ == "__main__":
    asyncio.run(main())