"""Fix database directly using raw SQL."""

import os
import sys
import sqlite3

def fix_database_direct():
    """Fix database directly using raw SQL."""
    
    print("🔧 Прямое исправление базы данных")
    print("=" * 50)
    
    db_path = "iqstocker.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    # Connect to SQLite directly
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current values
        cursor.execute("SELECT id, content_type FROM csv_analyses")
        rows = cursor.fetchall()
        
        print(f"📊 Найдено записей: {len(rows)}")
        
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
        
        fixed_count = 0
        for row_id, content_type in rows:
            if content_type and content_type in content_type_mapping:
                old_value = content_type
                new_value = content_type_mapping[old_value]
                
                print(f"🔄 Исправление ID {row_id}: {old_value} -> {new_value}")
                
                cursor.execute(
                    "UPDATE csv_analyses SET content_type = ? WHERE id = ?",
                    (new_value, row_id)
                )
                fixed_count += 1
        
        if fixed_count > 0:
            conn.commit()
            print(f"✅ Исправлено {fixed_count} записей")
        else:
            print("✅ Нет записей для исправления")
        
        # Verify fixes
        print("\n🔍 Проверка исправлений...")
        cursor.execute("SELECT id, content_type FROM csv_analyses")
        rows = cursor.fetchall()
        
        for row_id, content_type in rows:
            if content_type:
                print(f"  - ID {row_id}: {content_type}")
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database_direct()
    
    print("\n" + "=" * 50)
    print("🎉 Исправление завершено!")
    print("Теперь можете протестировать обработку CSV")
    print("=" * 50)
