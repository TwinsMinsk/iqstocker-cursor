@echo off
REM Скрипт для создания бэкапа базы данных Supabase
REM Использование: backup_db.bat [--plain]

cd /d %~dp0\..
poetry run python scripts/database/backup_supabase.py %*

