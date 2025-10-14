# Railway Deployment Fix - Clean Version

## ✅ Исправления для Railway

### 1. Исправлены импорты модулей
- Убрана ошибка `ModuleNotFoundError: No module named 'src'`
- Все импорты теперь работают корректно

### 2. Исправлен healthcheck endpoint  
- Теперь использует переменную `PORT` от Railway
- Создан отдельный скрипт `run_healthcheck.py`
- Healthcheck отвечает на правильном порту

### 3. Обновлена конфигурация Railway
- Правильные команды запуска для каждого сервиса
- Исправлен `railway.json`
- Обновлен `Dockerfile`

### 4. Исправлены переменные окружения
- Убраны localhost URLs
- Правильные переменные для production

## 🔧 Настройка переменных окружения

**Общие переменные (для всех сервисов):**
```
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE
ADMIN_SECRET_KEY=gdfg56dgdfFdfr4
ADMIN_USERNAME=IQStocker
ADMIN_PASSWORD=Punkrock77
DEBUG=false
ENVIRONMENT=production
PYTHONPATH=/app
PYTHONUNBUFFERED=1
```

**Для Bot сервиса:**
```
SERVICE_TYPE=bot
```

**Для Admin Panel сервиса:**
```
SERVICE_TYPE=admin
```

## 🚀 Результат

После применения этих исправлений:
- ✅ Ошибка `ModuleNotFoundError` исчезнет
- ✅ Healthcheck будет проходить
- ✅ Все сервисы запустятся успешно
- ✅ Bot будет отвечать в Telegram
- ✅ Admin Panel будет доступен
