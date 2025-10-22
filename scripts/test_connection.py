import asyncio
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Загружаем .env из корня проекта
try:
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"Загружен .env из: {env_path}")
    else:
        print(f"Файл .env не найден по пути: {env_path}")

    DATABASE_URL = os.environ.get("DATABASE_URL")

    # Важно: SQLAlchemy 2.0 для asyncpg требует замены postgresql:// на postgresql+asyncpg://
    if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

    async def check_connection():
        if not DATABASE_URL:
            print("\nОШИБКА: Переменная DATABASE_URL не найдена в .env или окружении!")
            return

        # Печатаем хост, чтобы скрыть пароль
        host_info = "Не удалось распарсить хост"
        if "@" in DATABASE_URL:
            host_info = DATABASE_URL.split('@')[-1]

        print(f"Попытка подключения к: {host_info}...") 

        try:
            engine = create_async_engine(DATABASE_URL)
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1")) # Используем text() для явного запроса
                print(f"\n✅ ✅ ✅ УСПЕХ! ✅ ✅ ✅")
                print(f"Результат запроса 'SELECT 1': {result.scalar()}")
        except ImportError:
            print("\n--- ОШИБКА ИМПОРТА ---")
            print("Пожалуйста, убедитесь, что установлен 'asyncpg': pip install asyncpg")
        except Exception as e:
            print(f"\n--- ❌ ПРОИЗОШЛА ОШИБКА ПОДКЛЮЧЕНИЯ ❌ ---")
            print(f"Тип ошибки: {type(e)}")
            print(f"Сообщение: {e}")
            print("------------------------------------------")
            print("\nРекомендация: Убедитесь, что вы сохранили .env в кодировке UTF-8 (без BOM).")

    if __name__ == "__main__":
        # Добавим импорт text
        from sqlalchemy import text
        asyncio.run(check_connection())

except Exception as e:
    print(f"Критическая ошибка при инициализации скрипта: {e}")
