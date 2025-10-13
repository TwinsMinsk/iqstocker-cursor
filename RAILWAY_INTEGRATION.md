# Railway Integration Guide

## 🚀 Быстрое развертывание на Railway

### Автоматическое развертывание

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/iqstocker-bot)

### Ручное развертывание

1. **Подключите репозиторий к Railway:**
   - Войдите в [Railway](https://railway.app)
   - Нажмите "New Project"
   - Выберите "Deploy from GitHub repo"
   - Подключите репозиторий: `TwinsMinsk/iqstocker-cursor`

2. **Добавьте сервисы:**
   - PostgreSQL Database
   - Redis (опционально)

3. **Настройте переменные окружения:**
   ```env
   BOT_TOKEN=your_telegram_bot_token
   OPENAI_API_KEY=your_openai_api_key
   ADMIN_SECRET_KEY=your_secret_key
   ADMIN_PASSWORD=your_password
   ```

4. **Деплой:**
   - Railway автоматически соберет и запустит проект
   - БД будет инициализирована автоматически

### Переменные окружения

| Переменная | Описание | Обязательная |
|------------|----------|--------------|
| `BOT_TOKEN` | Токен Telegram бота | ✅ |
| `DATABASE_URL` | URL PostgreSQL (автоматически) | ✅ |
| `REDIS_URL` | URL Redis (опционально) | ❌ |
| `OPENAI_API_KEY` | Ключ OpenAI API | ✅ |
| `ADMIN_SECRET_KEY` | Секретный ключ админки | ✅ |
| `ADMIN_PASSWORD` | Пароль админки | ✅ |
| `BOOSTY_API_KEY` | Ключ Boosty API | ❌ |
| `SENTRY_DSN` | DSN Sentry для мониторинга | ❌ |

### Мониторинг

- **Логи:** Доступны в Railway Dashboard
- **Метрики:** CPU, RAM, Network usage
- **Health Check:** `/health` endpoint

### Масштабирование

- **Автоматическое:** Railway автоматически масштабирует при нагрузке
- **Ручное:** Настройте в Railway Dashboard
- **Горизонтальное:** Множественные инстансы с load balancer

### Обновления

Railway автоматически обновляет проект при push в main ветку.

### Поддержка

- **Railway Docs:** [docs.railway.app](https://docs.railway.app)
- **Telegram Support:** [@iqstocker_support](https://t.me/iqstocker_support)
- **GitHub Issues:** [Создать issue](https://github.com/TwinsMinsk/iqstocker-cursor/issues)
