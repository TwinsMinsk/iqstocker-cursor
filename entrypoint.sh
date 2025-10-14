#!/bin/sh
# entrypoint.sh

# Этот скрипт будет выполняться при каждом запуске контейнера.

echo "--- Running database initialization ---"
# Выполняем скрипт инициализации базы данных
python init_railway_db.py
echo "--- Database initialization finished ---"

# Команда exec "$@" запускает основную команду,
# переданную контейнеру. В нашем случае, это будет
# startCommand из файла railway.json для каждого сервиса.
echo "--- Starting main process: $@ ---"
exec "$@"
