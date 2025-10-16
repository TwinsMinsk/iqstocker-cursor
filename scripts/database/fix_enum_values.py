"""Fix enum values in database."""

import os
import sys

# Set environment variables for MVP
os.environ["DATABASE_URL"] = "sqlite:///iqstocker.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ADMIN_SECRET_KEY"] = "test_secret_key_123"
os.environ["ADMIN_PASSWORD"] = "admin123"

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import SessionLocal, engine
from database.models import CSVAnalysis, ContentType
from sqlalchemy import text

def fix_enum_values():
    """Fix enum values in database."""
    
    print("🔧 Исправление значений enum в базе данных")
    print("=" * 50)
    
    # Mapping of Russian values to English
    content_type_mapping = {
        'ФОТО': 'PHOTO',
        'ФОТОГРАФИИ': 'PHOTO',
        'ФОТОГРАФИЯ': 'PHOTO',
        'AI': 'AI',
        'ИЛЛЮСТРАЦИИ': 'ILLUSTRATION',
        'ИЛЛЮСТРАЦИЯ': 'ILLUSTRATION',
        'ВИДЕО': 'VIDEO',
        'ВЕКТОР': 'VECTOR',
        'ВЕКТОРНАЯ': 'VECTOR',
        'ВЕКТОРНАЯ ГРАФИКА': 'VECTOR'
    }
    
    db = SessionLocal()
    
    try:
        # Get all CSV analyses with problematic content_type
        csv_analyses = db.query(CSVAnalysis).all()
        
        print(f"📊 Найдено CSV анализов: {len(csv_analyses)}")
        
        fixed_count = 0
        for analysis in csv_analyses:
            if analysis.content_type and str(analysis.content_type) in content_type_mapping:
                old_value = str(analysis.content_type)
                new_value = content_type_mapping[old_value]
                
                print(f"🔄 Исправление: {old_value} -> {new_value}")
                
                # Update using raw SQL to avoid enum validation
                db.execute(
                    text("UPDATE csv_analyses SET content_type = :new_value WHERE id = :id"),
                    {"new_value": new_value, "id": analysis.id}
                )
                fixed_count += 1
        
        if fixed_count > 0:
            db.commit()
            print(f"✅ Исправлено {fixed_count} записей")
        else:
            print("✅ Нет записей для исправления")
        
        # Verify fixes
        print("\n🔍 Проверка исправлений...")
        csv_analyses = db.query(CSVAnalysis).all()
        
        for analysis in csv_analyses:
            if analysis.content_type:
                print(f"  - ID {analysis.id}: {analysis.content_type}")
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    fix_enum_values()
    
    print("\n" + "=" * 50)
    print("🎉 Исправление завершено!")
    print("Теперь можете протестировать обработку CSV")
    print("=" * 50)
