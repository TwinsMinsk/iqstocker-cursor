"""Скрипт для создания бэкапа базы данных Supabase."""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings


def parse_database_url(database_url: str) -> dict:
    """Парсит DATABASE_URL и возвращает компоненты подключения."""
    parsed = urlparse(database_url)
    
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/'),
        'user': parsed.username,
        'password': parsed.password,
    }


def create_backup(database_url: str, output_dir: Path = None) -> Path:
    """
    Создает бэкап базы данных PostgreSQL используя pg_dump.
    
    Args:
        database_url: URL подключения к базе данных
        output_dir: Директория для сохранения бэкапа (по умолчанию backups/)
    
    Returns:
        Path к созданному файлу бэкапа
    """
    # Определяем директорию для бэкапов
    if output_dir is None:
        output_dir = project_root / 'backups'
    else:
        output_dir = Path(output_dir)
    
    # Создаем директорию, если её нет
    output_dir.mkdir(exist_ok=True)
    
    # Генерируем имя файла с временной меткой
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'supabase_backup_{timestamp}.sql'
    backup_path = output_dir / backup_filename
    
    # Парсим DATABASE_URL
    db_params = parse_database_url(database_url)
    
    print(f"🔄 Начинаю создание бэкапа базы данных...")
    print(f"📁 Хост: {db_params['host']}")
    print(f"📊 База данных: {db_params['database']}")
    print(f"💾 Файл бэкапа: {backup_path}")
    
    # Формируем команду pg_dump
    # Используем переменные окружения для пароля (безопаснее)
    env = os.environ.copy()
    env['PGPASSWORD'] = db_params['password']
    
    pg_dump_cmd = [
        'pg_dump',
        '-h', db_params['host'],
        '-p', str(db_params['port']),
        '-U', db_params['user'],
        '-d', db_params['database'],
        '-F', 'c',  # Custom format (сжатый бинарный формат)
        '-f', str(backup_path),
        '--no-owner',  # Не включать команды владения объектами
        '--no-acl',    # Не включать команды прав доступа
    ]
    
    try:
        # Выполняем pg_dump
        result = subprocess.run(
            pg_dump_cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Проверяем размер файла
        file_size = backup_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"✅ Бэкап успешно создан!")
        print(f"📦 Размер файла: {file_size_mb:.2f} MB")
        print(f"📍 Путь: {backup_path.absolute()}")
        
        return backup_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при создании бэкапа:")
        print(f"   Команда: {' '.join(pg_dump_cmd[:6])}...")
        print(f"   Стандартный вывод: {e.stdout}")
        print(f"   Ошибка: {e.stderr}")
        raise
    except FileNotFoundError:
        print("❌ Ошибка: pg_dump не найден в системе.")
        print("   Установите PostgreSQL client tools:")
        print("   - Windows: https://www.postgresql.org/download/windows/")
        print("   - Linux: sudo apt-get install postgresql-client")
        print("   - macOS: brew install postgresql")
        raise


def create_backup_plain(database_url: str, output_dir: Path = None) -> Path:
    """
    Создает бэкап в текстовом формате SQL (plain format).
    
    Args:
        database_url: URL подключения к базе данных
        output_dir: Директория для сохранения бэкапа (по умолчанию backups/)
    
    Returns:
        Path к созданному файлу бэкапа
    """
    # Определяем директорию для бэкапов
    if output_dir is None:
        output_dir = project_root / 'backups'
    else:
        output_dir = Path(output_dir)
    
    # Создаем директорию, если её нет
    output_dir.mkdir(exist_ok=True)
    
    # Генерируем имя файла с временной меткой
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'supabase_backup_{timestamp}.sql'
    backup_path = output_dir / backup_filename
    
    # Парсим DATABASE_URL
    db_params = parse_database_url(database_url)
    
    print(f"🔄 Начинаю создание бэкапа базы данных (текстовый формат)...")
    print(f"📁 Хост: {db_params['host']}")
    print(f"📊 База данных: {db_params['database']}")
    print(f"💾 Файл бэкапа: {backup_path}")
    
    # Формируем команду pg_dump для текстового формата
    env = os.environ.copy()
    env['PGPASSWORD'] = db_params['password']
    
    pg_dump_cmd = [
        'pg_dump',
        '-h', db_params['host'],
        '-p', str(db_params['port']),
        '-U', db_params['user'],
        '-d', db_params['database'],
        '-F', 'p',  # Plain text format
        '--no-owner',
        '--no-acl',
    ]
    
    try:
        # Выполняем pg_dump и сохраняем вывод в файл
        with open(backup_path, 'w', encoding='utf-8') as f:
            result = subprocess.run(
                pg_dump_cmd,
                env=env,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        
        # Проверяем размер файла
        file_size = backup_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"✅ Бэкап успешно создан!")
        print(f"📦 Размер файла: {file_size_mb:.2f} MB")
        print(f"📍 Путь: {backup_path.absolute()}")
        
        return backup_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при создании бэкапа:")
        print(f"   Команда: {' '.join(pg_dump_cmd[:6])}...")
        if e.stderr:
            print(f"   Ошибка: {e.stderr.decode('utf-8', errors='ignore')}")
        raise
    except FileNotFoundError:
        print("❌ Ошибка: pg_dump не найден в системе.")
        print("   Установите PostgreSQL client tools:")
        print("   - Windows: https://www.postgresql.org/download/windows/")
        print("   - Linux: sudo apt-get install postgresql-client")
        print("   - macOS: brew install postgresql")
        raise


def main():
    """Главная функция для запуска скрипта."""
    # Получаем DATABASE_URL из переменных окружения или настроек
    database_url = os.getenv('DATABASE_URL') or settings.database_url
    
    if not database_url:
        print("❌ Ошибка: DATABASE_URL не установлен.")
        print("   Установите переменную окружения DATABASE_URL или настройте её в .env файле.")
        sys.exit(1)
    
    # Проверяем, что это PostgreSQL
    if not database_url.startswith('postgresql://'):
        print("❌ Ошибка: DATABASE_URL должен быть для PostgreSQL.")
        print(f"   Текущий URL: {database_url[:50]}...")
        sys.exit(1)
    
    # Определяем формат бэкапа из аргументов командной строки
    format_type = 'custom'  # По умолчанию custom (сжатый)
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--plain', '-p']:
            format_type = 'plain'
        elif sys.argv[1] in ['--custom', '-c']:
            format_type = 'custom'
        elif sys.argv[1] in ['--help', '-h']:
            print("Использование: python backup_supabase.py [--plain|--custom]")
            print("  --plain, -p   Создать бэкап в текстовом формате SQL")
            print("  --custom, -c   Создать бэкап в сжатом формате (по умолчанию)")
            print("  --help, -h     Показать эту справку")
            sys.exit(0)
    
    try:
        if format_type == 'plain':
            backup_path = create_backup_plain(database_url)
        else:
            backup_path = create_backup(database_url)
        
        print(f"\n✨ Бэкап завершен успешно!")
        print(f"   Для восстановления используйте: pg_restore -d <database> {backup_path}")
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

