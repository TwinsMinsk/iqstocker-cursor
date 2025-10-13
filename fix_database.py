"""Fix database issues."""

import os
import sys

# Set environment variables for MVP
os.environ["DATABASE_URL"] = "sqlite:///iqstocker.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ADMIN_SECRET_KEY"] = "test_secret_key_123"
os.environ["ADMIN_PASSWORD"] = "admin123"

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import engine, Base
from database.models import *

def fix_database():
    """Fix database issues."""
    
    print("🔧 Исправление проблем с базой данных")
    print("=" * 50)
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Все таблицы созданы/обновлены")
        
        # Check if tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"📊 Найдено таблиц: {len(tables)}")
        for table in tables:
            print(f"  - {table}")
        
        # Test database connection
        from config.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Test query
            users = db.query(User).count()
            print(f"👥 Пользователей в базе: {users}")
            
            # Test CSV analysis
            csv_analyses = db.query(CSVAnalysis).count()
            print(f"📊 CSV анализов: {csv_analyses}")
            
            # Test analytics reports
            analytics_reports = db.query(AnalyticsReport).count()
            print(f"📈 Отчетов аналитики: {analytics_reports}")
            
            # Test top themes
            top_themes = db.query(TopTheme).count()
            print(f"🏆 Топ тем: {top_themes}")
            
        finally:
            db.close()
        
        print("✅ База данных работает корректно")
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении базы данных: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_database()
    
    print("\n" + "=" * 50)
    print("🎉 Исправление завершено!")
    print("Теперь можете запустить бота: python run_bot_venv.py")
    print("=" * 50)
