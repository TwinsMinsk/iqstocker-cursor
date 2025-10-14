# 🚀 Railway Deployment Guide

## Настройка переменных окружения в Railway

### 1. Основные переменные для всех сервисов:

```bash
# Bot Configuration
BOT_TOKEN=7969578689:AAFXOvWZalCZQiTeEohZduYm38fKsSOqqcY

# AI Configuration  
OPENAI_API_KEY=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

# Admin Panel Configuration
ADMIN_SECRET_KEY=gdfg56dgdfFdfr4
ADMIN_USERNAME=IQStocker
ADMIN_PASSWORD=Punkrock77

# Application Configuration
DEBUG=false
ENVIRONMENT=production
PYTHONPATH=/app
PYTHONUNBUFFERED=1
```

### 2. Переменные для каждого сервиса:

#### Bot Service:
```bash
SERVICE_TYPE=bot
```

#### Admin Panel Service:
```bash
SERVICE_TYPE=admin
```

#### Healthcheck Service (по умолчанию):
```bash
SERVICE_TYPE=healthcheck
```

## Настройка базы данных

### 1. Добавьте PostgreSQL сервис в Railway
- Railway автоматически предоставит `DATABASE_URL`
- Не нужно устанавливать эту переменную вручную

### 2. Добавьте Redis сервис в Railway  
- Railway автоматически предоставит `REDIS_URL`
- Не нужно устанавливать эту переменную вручную

## Проверка деплоя

### 1. Healthcheck endpoint
После деплоя проверьте:
```
https://your-app.railway.app/health
```

Должен вернуть:
```json
{
  "status": "healthy",
  "service": "iqstocker-bot",
  "database": "connected",
  "settings": "loaded",
  "admin_panel": "available"
}
```

### 2. Admin Panel
```
https://your-app.railway.app/admin
```

### 3. Логи
Проверьте логи в Railway dashboard для каждого сервиса.

## Troubleshooting

### Если healthcheck не проходит:
1. Проверьте логи Deploy Logs
2. Убедитесь, что все переменные окружения установлены
3. Проверьте, что PostgreSQL и Redis сервисы запущены

### Если bot не отвечает:
1. Проверьте BOT_TOKEN
2. Проверьте подключение к базе данных
3. Проверьте логи Bot сервиса

### Если admin panel не работает:
1. Проверьте ADMIN_SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
2. Проверьте подключение к базе данных
3. Проверьте логи Admin Panel сервиса
