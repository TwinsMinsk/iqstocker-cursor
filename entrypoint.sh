#!/bin/sh
# entrypoint.sh
# 
# Упрощенный entrypoint для Railway.
# Railway управляет запуском через railway.json,
# поэтому этот скрипт просто передает управление команде.

echo "🚀 IQStocker - Starting service..."
echo "📦 Running command: $@"

# Передаем управление команде из railway.json
exec "$@"
