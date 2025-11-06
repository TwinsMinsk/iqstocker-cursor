#!/usr/bin/env python3
"""Test script to check DATABASE_URL loading."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

print("=" * 60)
print("DATABASE_URL Debug Script")
print("=" * 60)

# Проверяем текущую директорию
print(f"\n1. Current working directory: {os.getcwd()}")

# Проверяем путь к .env
project_root = Path(__file__).parent.parent if Path(__file__).parent.name == 'scripts' else Path('.')
env_path = project_root / '.env'
print(f"\n2. Project root: {project_root.resolve()}")
print(f"3. .env path: {env_path.resolve()}")
print(f"4. .env exists: {env_path.exists()}")

# Проверяем DATABASE_URL до загрузки .env
print(f"\n5. DATABASE_URL before load_dotenv: {os.getenv('DATABASE_URL', 'NOT SET')[:80]}...")

# Загружаем .env с overwrite=True
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"\n6. .env loaded with override=True")
else:
    print(f"\n6. .env file NOT FOUND!")

# Проверяем DATABASE_URL после загрузки .env
db_url = os.getenv('DATABASE_URL', 'NOT SET')
print(f"\n7. DATABASE_URL after load_dotenv: {db_url[:80]}...")

# Проверяем все переменные окружения
print(f"\n8. All DATABASE_URL related vars:")
for key, value in os.environ.items():
    if 'DATABASE' in key.upper():
        print(f"   {key}={value[:60]}...")

# Проверяем, что происходит в env.py
print(f"\n9. Testing env.py loading:")
sys.path.insert(0, str(project_root))
try:
    # Имитируем то, что делает env.py
    PROJECT_ROOT = Path(__file__).parent.parent if Path(__file__).parent.name == 'scripts' else Path('.')
    env_path_test = PROJECT_ROOT / '.env'
    if env_path_test.exists():
        load_dotenv(dotenv_path=env_path_test, override=True)
    db_url_test = os.environ.get("DATABASE_URL")
    print(f"   DATABASE_URL from env.py logic: {db_url_test[:80] if db_url_test else 'NOT SET'}...")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 60)

