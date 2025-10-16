# Развертывание IQStocker на Railway

## 🚀 Полная инструкция по развертыванию

### Предварительные требования

1. **Аккаунт Railway** - зарегистрируйтесь на [railway.app](https://railway.app)
2. **Telegram Bot Token** - получите у [@BotFather](https://t.me/BotFather)
3. **OpenAI API Key** - получите на [platform.openai.com](https://platform.openai.com)
4. **GitHub репозиторий** - загрузите код в GitHub

### Шаг 1: Создание проекта на Railway

1. **Войдите в Railway Dashboard**
2. **Нажмите "New Project"**
3. **Выберите "Deploy from GitHub repo"**
4. **Подключите ваш репозиторий**
5. **Выберите ветку (обычно main/master)**

### Шаг 2: Добавление сервисов

#### 2.1 PostgreSQL Database
1. **В проекте нажмите "+ New"**
2. **Выберите "Database" → "PostgreSQL"**
3. **Дождитесь создания базы данных**
4. **Скопируйте DATABASE_URL из переменных окружения**

#### 2.2 Redis (опционально)
1. **Нажмите "+ New"**
2. **Выберите "Database" → "Redis"**
3. **Скопируйте REDIS_URL**

### Шаг 3: Настройка переменных окружения

В настройках проекта добавьте следующие переменные:

#### Обязательные переменные:
```env
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token_here

# Database (автоматически создается Railway)
DATABASE_URL=postgresql://postgres:password@postgres:5432/iqstocker
REDIS_URL=redis://redis:6379/0

# AI
OPENAI_API_KEY=your_openai_api_key_here

# Admin Panel
ADMIN_SECRET_KEY=generate_random_key_here_minimum_32_chars
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_password_here

# Application
DEBUG=False
LOG_LEVEL=INFO
```

#### Опциональные переменные:
```env
# Webhook (замените на ваш домен)
WEBHOOK_URL=https://your-domain.railway.app/webhook

# Payment Provider (Boosty)
BOOSTY_API_KEY=your_boosty_api_key_here
BOOSTY_CLIENT_ID=your_boosty_client_id_here
BOOSTY_CLIENT_SECRET=your_boosty_client_secret_here
BOOSTY_WEBHOOK_SECRET=your_boosty_webhook_secret_here

# Monitoring
SENTRY_DSN=your_sentry_dsn_here

# Settings
NEW_WORKS_MONTHS=3
TEST_PRO_DURATION_DAYS=14
PRO_DISCOUNT_PERCENT=50
FREE_DISCOUNT_PERCENT=30
```

### Шаг 4: Настройка домена

1. **В настройках проекта найдите "Domains"**
2. **Нажмите "Generate Domain"**
3. **Скопируйте полученный домен**
4. **Обновите WEBHOOK_URL в переменных окружения:**
   ```
   WEBHOOK_URL=https://your-domain.railway.app/webhook
   ```

### Шаг 5: Первый деплой

1. **Railway автоматически начнет сборку при подключении репозитория**
2. **Дождитесь завершения сборки (5-10 минут)**
3. **Проверьте логи на наличие ошибок**

### Шаг 6: Проверка работы

#### 6.1 Проверка бота
1. **Найдите вашего бота в Telegram**
2. **Отправьте команду `/start`**
3. **Проверьте, что бот отвечает**

#### 6.2 Проверка админ-панели
1. **Откройте `https://your-domain.railway.app/admin`**
2. **Войдите с учетными данными из переменных окружения**
3. **Проверьте все разделы**

#### 6.3 Проверка базы данных
1. **В Railway Dashboard откройте PostgreSQL**
2. **Проверьте, что таблицы созданы**
3. **Убедитесь, что есть админский пользователь**

### Шаг 7: Настройка webhook (опционально)

Если используете webhook вместо polling:

1. **В настройках бота найдите "Webhook"**
2. **Установите URL: `https://your-domain.railway.app/webhook`**
3. **Обновите переменную WEBHOOK_URL**

### Мониторинг и логи

#### Просмотр логов:
1. **В Railway Dashboard откройте ваш сервис**
2. **Перейдите на вкладку "Deployments"**
3. **Нажмите на последний деплой**
4. **Просматривайте логи в реальном времени**

#### Мониторинг производительности:
1. **Используйте встроенные метрики Railway**
2. **Настройте Sentry для отслеживания ошибок**
3. **Мониторьте использование ресурсов**

### Обновление бота

1. **Внесите изменения в код**
2. **Запушьте изменения в GitHub**
3. **Railway автоматически пересоберет и перезапустит бота**

### Резервное копирование

#### База данных:
1. **Railway автоматически создает бэкапы PostgreSQL**
2. **Можно настроить дополнительные бэкапы**
3. **Экспортируйте данные через Railway Dashboard**

#### Код:
1. **Всегда храните код в Git**
2. **Используйте теги для версионирования**
3. **Ведите changelog**

### Устранение неполадок

#### Бот не отвечает:
1. **Проверьте BOT_TOKEN**
2. **Проверьте логи на ошибки**
3. **Убедитесь, что все переменные окружения установлены**

#### Ошибки базы данных:
1. **Проверьте DATABASE_URL**
2. **Убедитесь, что PostgreSQL запущен**
3. **Проверьте права доступа**

#### Проблемы с AI:
1. **Проверьте OPENAI_API_KEY**
2. **Убедитесь, что у вас есть кредиты на OpenAI**
3. **Проверьте лимиты API**

#### Админ-панель недоступна:
1. **Проверьте ADMIN_SECRET_KEY и ADMIN_PASSWORD**
2. **Убедитесь, что домен настроен правильно**
3. **Проверьте логи на ошибки**

### Масштабирование

#### Увеличение ресурсов:
1. **В Railway Dashboard откройте настройки сервиса**
2. **Увеличьте CPU/RAM при необходимости**
3. **Настройте автоподстройку**

#### Горизонтальное масштабирование:
1. **Railway поддерживает множественные инстансы**
2. **Настройте load balancer**
3. **Используйте Redis для сессий**

### Безопасность

#### Рекомендации:
1. **Используйте сложные пароли**
2. **Регулярно обновляйте зависимости**
3. **Мониторьте логи на подозрительную активность**
4. **Ограничьте доступ к админ-панели по IP**

#### Переменные окружения:
1. **Никогда не коммитьте секреты в код**
2. **Используйте разные ключи для dev/prod**
3. **Регулярно ротируйте API ключи**

### Стоимость

#### Railway Pricing:
- **Hobby Plan**: $5/месяц - достаточно для MVP
- **Pro Plan**: $20/месяц - для продакшена
- **Team Plan**: $99/месяц - для команды

#### Дополнительные расходы:
- **OpenAI API**: ~$10-50/месяц (зависит от использования)
- **Sentry**: $26/месяц (опционально)

### Поддержка

#### Документация:
- [Railway Docs](https://docs.railway.app)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenAI API](https://platform.openai.com/docs)

#### Сообщество:
- [Railway Discord](https://discord.gg/railway)
- [Telegram Bot Developers](https://t.me/BotSupport)

---

## 🎉 Поздравляем!

Ваш IQStocker бот успешно развернут на Railway! 

Теперь вы можете:
- ✅ Принимать пользователей
- ✅ Обрабатывать платежи
- ✅ Управлять контентом через админ-панель
- ✅ Мониторить работу бота

**Удачного использования! 🚀**
