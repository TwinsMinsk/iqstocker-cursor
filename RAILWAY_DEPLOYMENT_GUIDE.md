# 🚂 Railway Deployment Guide для IQStocker

## 📋 Резюме изменений

Все изменения были внесены для корректного деплоя трех независимых сервисов на Railway:

1. **Bot Service** - Aiogram телеграм бот
2. **Web Service** - FastAPI админ-панель  
3. **Worker Service** - Dramatiq воркер для фоновых задач

## ✅ Выполненные изменения

### 1. Обновлен `railway.json`
- ✅ Исправлены пути к скриптам запуска
- ✅ Переименованы сервисы (iqstocker-bot → bot, admin-panel → web)
- ✅ Каждый сервис теперь имеет правильную команду запуска

**Файл:** `railway.json`

### 2. Создан скрипт миграций
- ✅ Новый файл `scripts/deployment/run_migrations.py`
- ✅ Выполняет `alembic upgrade head` перед запуском любого сервиса
- ✅ Проверяет наличие DATABASE_URL

### 3. Созданы скрипты запуска сервисов
- ✅ `scripts/deployment/start_bot.py` - запускает бота с миграциями
- ✅ `scripts/deployment/start_web.py` - запускает админ-панель с миграциями
- ✅ Обновлен `scripts/deployment/start_worker.py` - запускает воркер с миграциями

### 4. Упрощен `entrypoint.sh`
- ✅ Удалена сложная логика
- ✅ Теперь просто передает управление команде из Railway

### 5. Обновлены настройки
- ✅ `config/settings.py` - использует только переменные окружения
- ✅ `database/alembic.ini` - читает DATABASE_URL из env
- ✅ `database/migrations/env.py` - уже правильно настроен

### 6. Обновлен `Dockerfile`
- ✅ Добавлен пустой CMD для корректной работы с Railway

## 🔧 Требуемые переменные окружения в Railway

### Для всех сервисов:
```bash
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://user:password@host:port/0
```

### Для Bot Service:
```bash
BOT_TOKEN=your_telegram_bot_token
```

### Для Web Service:
```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
ADMIN_SECRET_KEY=your_secret_key
```

### Для Worker Service:
```bash
REDIS_URL=redis://user:password@host:port/0
```

### Опционально (для AI функций):
```bash
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

## 📦 Структура сервисов на Railway

### 1. Bot Service
- **Имя:** `bot`
- **Команда запуска:** `python scripts/deployment/start_bot.py`
- **Что запускается:** Aiogram бот из `bot/main.py`
- **Порт:** Railway автоматически присвоит порт

### 2. Web Service (Admin Panel)
- **Имя:** `web`
- **Команда запуска:** `python scripts/deployment/start_web.py`
- **Healthcheck:** `/health`
- **Что запускается:** FastAPI админ-панель из `admin_panel/main.py`
- **Порт:** Railway автоматически присвоит порт

### 3. Worker Service
- **Имя:** `worker`
- **Команда запуска:** `python scripts/deployment/start_worker.py`
- **Что запускается:** Dramatiq worker из `workers/actors.py`
- **Требует:** Redis для брокера сообщений

## 🔄 Процесс деплоя

### Этап 1: Сборка (Railway)
1. Railway читает `railway.json`
2. Запускает `Dockerfile` для создания Docker образа
3. Устанавливает все зависимости из `requirements.txt`

### Этап 2: Миграции
Каждый сервис:
1. Выполняет `python scripts/deployment/run_migrations.py`
2. Запускает `alembic upgrade head`
3. Применяет все миграции из `database/migrations/versions/`

### Этап 3: Запуск сервисов
1. **Bot** запускает `python -m bot.main`
2. **Web** запускает `python scripts/runners/run_admin_fastapi.py`
3. **Worker** запускает `dramatiq workers.actors`

## 🎯 Критически важные файлы

| Файл | Назначение |
|------|------------|
| `railway.json` | Конфигурация Railway для всех сервисов |
| `Dockerfile` | Сборка Docker образа |
| `entrypoint.sh` | Точка входа контейнера (упрощенная) |
| `scripts/deployment/run_migrations.py` | Выполнение миграций |
| `scripts/deployment/start_bot.py` | Запуск бота |
| `scripts/deployment/start_web.py` | Запуск админ-панели |
| `scripts/deployment/start_worker.py` | Запуск воркера |
| `database/migrations/env.py` | Конфигурация Alembic |
| `config/settings.py` | Настройки приложения |

## ⚠️ Важные замечания

### 1. Порты
- Railway автоматически присваивает порты для каждого сервиса
- Используйте переменную `$PORT` в коде, если нужно

### 2. Переменные окружения
- **ВСЕ** переменные должны быть установлены в настройках Railway проекта
- Не используйте `.env` файлы в production

### 3. База данных
- Используйте Supabase PostgreSQL
- Railway автоматически обеспечивает DATABASE_URL
- Миграции применяются автоматически при каждом деплое

### 4. Redis
- Добавьте Redis сервис в Railway (опционально)
- Или используйте внешний Redis (Supabase Redis или Upstash)

## 🚀 Инструкции по деплою

### Шаг 1: Настройка переменных окружения
1. Откройте ваш проект в Railway
2. Перейдите в Settings → Environment
3. Добавьте все необходимые переменные (см. выше)

### Шаг 2: Подключение к Supabase
1. Получите DATABASE_URL из Supabase
2. Добавьте его в Railway как `DATABASE_URL`
3. Добавьте Redis URL (если используете)

### Шаг 3: Деплой
1. Railway автоматически обнаружит `railway.json`
2. Создаст три сервиса (bot, web, worker)
3. Выполнит сборку и запустит все сервисы

### Шаг 4: Проверка
1. Проверьте логи в Railway для каждого сервиса
2. Убедитесь, что миграции выполнены успешно
3. Проверьте healthcheck для web сервиса

## 🐛 Отладка

### Проверка логов
```bash
# В Railway Dashboard откройте логи каждого сервиса
# Ищите строки:
✅ Migrations completed successfully!
🚀 Starting bot/web/worker...
```

### Проверка миграций
Если миграции не применяются:
1. Проверьте, что DATABASE_URL установлен
2. Проверьте, что файлы миграций существуют в `database/migrations/versions/`
3. Проверьте логи на наличие ошибок Alembic

### Проверка подключений
```bash
# В логах должны быть:
📡 Redis URL: redis://...
📊 Database URL: postgresql://...
```

## 📝 Следующие шаги

1. ✅ Все конфигурационные файлы обновлены
2. ⏳ Настройте переменные окружения в Railway
3. ⏳ Подключите Supabase PostgreSQL
4. ⏳ Подключите Redis (опционально)
5. ⏳ Деплой на Railway

## 🎉 Готово!

Проект готов к деплою на Railway. Все три сервиса будут:
- ✅ Собираться через Dockerfile
- ✅ Применять миграции автоматически
- ✅ Использовать Supabase для базы данных
- ✅ Запускаться независимо друг от друга

Удачи с деплоем! 🚀
