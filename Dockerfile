# Этап 1: Сборщик с зависимостями
FROM python:3.11-slim as builder

WORKDIR /app

# Установка зависимостей для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка Python-пакетов
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---
# Этап 2: Финальный, чистый образ
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей для работы
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование установленных Python-пакетов из сборщика
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копирование кода приложения и скрипта-загрузчика
COPY . .

# --- ГЛАВНЫЕ ИЗМЕНЕНИЯ ---

# 1. Делаем наш скрипт-загрузчик исполняемым
RUN chmod +x /app/entrypoint.sh

# 2. Устанавливаем его как точку входа для контейнера
# Railway управляет запуском через railway.json, entrypoint.sh просто передает управление
ENTRYPOINT ["/app/entrypoint.sh"]

# 3. Default command - будет переопределяться Railway через startCommand в railway.json
CMD []
# -------------------------

# Создание необходимых директорий
RUN mkdir -p logs uploads admin/static admin/templates

# Настройка окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Создание и использование пользователя без root-прав для безопасности
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Открытие портов
EXPOSE 8000 5000