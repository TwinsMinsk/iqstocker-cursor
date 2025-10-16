# 🚀 Полная инструкция по исправлению деплоя на Railway

## ✅ Что было исправлено

### 1. **Исправлены импорты модулей**
- Убрана ошибка `ModuleNotFoundError: No module named 'src'`
- Все импорты теперь работают корректно

### 2. **Исправлен healthcheck endpoint**
- Теперь использует переменную `PORT` от Railway
- Создан отдельный скрипт `run_healthcheck.py`
- Healthcheck отвечает на правильном порту

### 3. **Обновлена конфигурация Railway**
- Правильные команды запуска для каждого сервиса
- Исправлен `railway.json`
- Обновлен `Dockerfile`

### 4. **Исправлены переменные окружения**
- Убраны localhost URLs
- Правильные переменные для production

## 🔧 Пошаговая настройка Railway

### Шаг 1: Настройте переменные окружения

В Railway dashboard для каждого сервиса установите:

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

**Для Bot сервиса добавьте:**
```
SERVICE_TYPE=bot
```

**Для Admin Panel сервиса добавьте:**
```
SERVICE_TYPE=admin
```

### Шаг 2: Добавьте базы данных

1. **PostgreSQL сервис:**
   - Добавьте PostgreSQL в Railway
   - Railway автоматически предоставит `DATABASE_URL`

2. **Redis сервис:**
   - Добавьте Redis в Railway  
   - Railway автоматически предоставит `REDIS_URL`

### Шаг 3: Перезапустите деплой

1. Перезапустите все сервисы в Railway
2. Проверьте логи Deploy Logs
3. Дождитесь успешного завершения healthcheck

## 🔍 Проверка работоспособности

### 1. Healthcheck endpoint
```
https://your-app.railway.app/health
```

**Ожидаемый ответ:**
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

### 3. API Documentation
```
https://your-app.railway.app/docs
```

## 🐛 Troubleshooting

### Если healthcheck не проходит:

1. **Проверьте логи Deploy Logs:**
   - Должны быть сообщения об успешной инициализации БД
   - Не должно быть ошибок импорта

2. **Проверьте переменные окружения:**
   - Все переменные должны быть установлены
   - PostgreSQL и Redis сервисы должны быть запущены

3. **Проверьте порт:**
   - Railway автоматически устанавливает переменную `PORT`
   - Healthcheck должен отвечать на этом порту

### Если bot не отвечает:

1. **Проверьте BOT_TOKEN:**
   - Токен должен быть действительным
   - Bot должен быть создан в @BotFather

2. **Проверьте подключение к БД:**
   - PostgreSQL сервис должен быть запущен
   - `DATABASE_URL` должен быть установлен

### Если admin panel не работает:

1. **Проверьте админские переменные:**
   - `ADMIN_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`
   - Все должны быть установлены

2. **Проверьте подключение к БД:**
   - Admin panel требует доступ к базе данных

## 📊 Ожидаемые результаты

После правильной настройки:

- ✅ **Healthcheck проходит** - endpoint `/health` возвращает 200
- ✅ **База данных инициализирована** - все таблицы созданы
- ✅ **Bot сервис работает** - отвечает на команды в Telegram
- ✅ **Admin Panel доступен** - веб-интерфейс работает
- ✅ **Все сервисы независимы** - каждый работает на своем порту

## 🎯 Финальная проверка

1. **Healthcheck:** `https://your-app.railway.app/health` → 200 OK
2. **Admin Panel:** `https://your-app.railway.app/admin` → Login page
3. **Bot:** Отправьте `/start` в Telegram → Bot отвечает
4. **Logs:** Все сервисы показывают "healthy" статус

## 📞 Поддержка

Если проблемы остаются:
1. Проверьте логи в Railway dashboard
2. Убедитесь, что все переменные окружения установлены
3. Проверьте, что PostgreSQL и Redis сервисы запущены
4. Перезапустите все сервисы

**Проект готов к production deployment! 🚀**
