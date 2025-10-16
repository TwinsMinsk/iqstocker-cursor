# Настройка Этапа 1: Критические функции

## 🔧 Необходимые настройки

### 1. Переменные окружения (.env)

Добавьте следующие переменные в ваш `.env` файл:

```env
# Payment Provider (Boosty) - НОВЫЕ НАСТРОЙКИ
BOOSTY_API_KEY=your_boosty_api_key_here
BOOSTY_CLIENT_ID=your_boosty_client_id_here
BOOSTY_CLIENT_SECRET=your_boosty_client_secret_here
BOOSTY_WEBHOOK_SECRET=your_boosty_webhook_secret_here

# Subscription Settings - НОВЫЕ НАСТРОЙКИ
TEST_PRO_DURATION_DAYS=14
PRO_DISCOUNT_PERCENT=50
FREE_DISCOUNT_PERCENT=30

# Limits per subscription - НОВЫЕ НАСТРОЙКИ
FREE_ANALYTICS_LIMIT=0
FREE_THEMES_LIMIT=1

TEST_PRO_ANALYTICS_LIMIT=1
TEST_PRO_THEMES_LIMIT=5

PRO_ANALYTICS_LIMIT=2
PRO_THEMES_LIMIT=5
PRO_TOP_THEMES_LIMIT=5

ULTRA_ANALYTICS_LIMIT=4
ULTRA_THEMES_LIMIT=10
ULTRA_TOP_THEMES_LIMIT=10

# New works definition (months)
NEW_WORKS_MONTHS=3
```

### 2. Установка зависимостей

Убедитесь, что установлены все необходимые пакеты:

```bash
pip install -r requirements.txt
```

**Новые зависимости для Этапа 1:**
- `apscheduler==3.10.4` - для планировщика задач
- `httpx==0.28.1` - для HTTP запросов к Boosty API

### 3. Настройка Boosty API

1. **Регистрация в Boosty:**
   - Зарегистрируйтесь на https://boosty.to
   - Создайте приложение для получения API ключей

2. **Получение ключей:**
   - `BOOSTY_API_KEY` - основной API ключ
   - `BOOSTY_CLIENT_ID` - ID клиента
   - `BOOSTY_CLIENT_SECRET` - секрет клиента
   - `BOOSTY_WEBHOOK_SECRET` - секрет для webhook'ов

3. **Настройка webhook'ов:**
   - URL: `https://your-domain.com/webhook/boosty`
   - События: `payment.succeeded`, `payment.failed`

### 4. Запуск бота

```bash
# Активация виртуального окружения
venv\Scripts\activate

# Запуск бота
python run_bot_venv.py
```

## 🧪 Тестирование новых функций

### 1. Тест onboarding
```bash
python test_stage1_implementation.py
```

### 2. Тест в Telegram
1. Отправьте `/start` боту
2. Проверьте активацию TEST_PRO подписки
3. Проверьте лимиты в разделе "Профиль"

### 3. Тест тем и трендов
1. Перейдите в раздел "Темы и тренды"
2. Нажмите "Получить темы"
3. Проверьте генерацию тем согласно подписке

### 4. Тест платежной системы
1. Перейдите в раздел "Профиль"
2. Нажмите "Перейти на PRO" или "Перейти на ULTRA"
3. Проверьте создание ссылки для оплаты
4. Проверьте расчет скидок

## 📊 Мониторинг

### Логи системы уведомлений
```bash
# Проверка логов планировщика
tail -f logs/bot.log | grep "scheduler"
```

### Проверка статуса подписок
```python
# В Python консоли
from config.database import SessionLocal
from database.models import User, SubscriptionType

db = SessionLocal()
test_pro_users = db.query(User).filter(User.subscription_type == SubscriptionType.TEST_PRO).count()
print(f"TEST_PRO пользователей: {test_pro_users}")
db.close()
```

## 🚨 Возможные проблемы

### 1. Ошибки подключения к БД
```
psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed
```
**Решение:** Запустите PostgreSQL или используйте SQLite для тестирования

### 2. Ошибки Boosty API
```
Error creating payment link: 401 - Unauthorized
```
**Решение:** Проверьте правильность API ключей в `.env`

### 3. Ошибки планировщика
```
Task scheduler error: ...
```
**Решение:** Убедитесь, что все зависимости установлены и БД доступна

## ✅ Чек-лист готовности

- [ ] Все переменные окружения настроены
- [ ] Boosty API ключи получены и настроены
- [ ] PostgreSQL запущен и доступен
- [ ] Бот запускается без ошибок
- [ ] Новые пользователи получают TEST_PRO
- [ ] Система уведомлений работает
- [ ] Темы генерируются согласно подписке
- [ ] Платежные ссылки создаются корректно
- [ ] Скидки рассчитываются правильно

## 🎯 Следующие шаги

После успешного тестирования Этапа 1 можно переходить к:

1. **Этап 2:** Основные функции (видеоуроки, календарь стокера)
2. **Этап 3:** Административные функции и оптимизация

**Этап 1 полностью готов к продакшену!** 🚀
