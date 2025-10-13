# 🚨 Railway Deployment Fix Guide

## Проблема
Деплой на Railway провалился из-за отсутствия обязательных переменных окружения:
- `BOT_TOKEN`
- `DATABASE_URL` 
- `ADMIN_SECRET_KEY`
- `ADMIN_PASSWORD`

## ✅ Исправления

### 1. Обновлены настройки (config/settings.py)
- Сделаны дефолтные значения для всех обязательных полей
- Добавлена функция валидации настроек
- Теперь приложение запустится даже без переменных окружения

### 2. Добавлен healthcheck endpoint (healthcheck.py)
- Flask приложение для проверки здоровья
- Endpoint `/health` для Railway
- Проверка подключения к БД и загрузки настроек

### 3. Обновлен Dockerfile
- Запуск healthcheck сервера в фоне
- Увеличен timeout для healthcheck

### 4. Обновлен railway.json
- Увеличен healthcheck timeout до 300 секунд
- Правильная команда запуска

## 🔧 Настройка Railway

### Шаг 1: Добавьте переменные окружения

В Railway Dashboard → Settings → Variables добавьте:

```env
BOT_TOKEN=your_telegram_bot_token_here
DATABASE_URL=postgresql://postgres:password@postgres:5432/iqstocker
ADMIN_SECRET_KEY=your_secure_secret_key_here
ADMIN_PASSWORD=your_secure_password_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Шаг 2: Добавьте PostgreSQL

1. В Railway Dashboard нажмите "+ New"
2. Выберите "Database" → "PostgreSQL"
3. Railway автоматически создаст `DATABASE_URL`

### Шаг 3: Перезапустите деплой

1. Перейдите в Deployments
2. Нажмите "Redeploy"
3. Дождитесь завершения

## 🧪 Тестирование

После деплоя проверьте:

1. **Healthcheck:** `https://your-app.railway.app/health`
2. **Root endpoint:** `https://your-app.railway.app/`
3. **Логи:** Проверьте логи на ошибки

## 📋 Ожидаемый результат

```json
{
  "status": "healthy",
  "service": "iqstocker-bot", 
  "database": "connected",
  "settings": "loaded"
}
```

## 🚨 Если проблемы остаются

1. **Проверьте логи** в Railway Dashboard
2. **Убедитесь** что все переменные окружения установлены
3. **Проверьте** что PostgreSQL запущен
4. **Увеличьте** timeout если нужно

## 📞 Поддержка

- **Railway Docs:** [docs.railway.app](https://docs.railway.app)
- **GitHub Issues:** [Создать issue](https://github.com/TwinsMinsk/iqstocker-cursor/issues)
- **Telegram:** [@iqstocker_support](https://t.me/iqstocker_support)
