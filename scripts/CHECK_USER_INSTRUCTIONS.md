# Инструкция по проверке и исправлению пользователя

## Пользователь: telegram_id = 1105557180

### Проблема
У пользователя лимиты удвоились из-за двойной обработки платежа (вручную + webhook от Tribute).

### Ожидаемые лимиты для ULTRA:
- Analytics: **2**
- Themes: **4**

---

## Вариант 1: Запуск скрипта на Railway (рекомендуется)

### Шаг 1: Подключитесь к Railway

1. Установите Railway CLI (если еще не установлен):
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. Подключитесь к проекту:
   ```bash
   railway link
   ```

### Шаг 2: Запустите скрипт проверки

```bash
railway run python scripts/check_user_subscription.py
```

Это покажет:
- Текущие лимиты пользователя
- Количество подписок
- Дубликаты payment_id
- Проблемы с лимитами

### Шаг 3: Запустите скрипт исправления

```bash
railway run python scripts/fix_user_subscription.py
```

Это:
- Удалит дубликаты подписок (оставит последнюю)
- Исправит лимиты на правильные значения
- Инвалидирует кеш

---

## Вариант 2: Через админ-панель (SQL запросы)

### 1. Проверка текущего состояния

Выполните SQL запросы из файла `scripts/check_user_sql.sql` в админ-панели или через psql.

### 2. Исправление лимитов

```sql
-- Исправить лимиты для пользователя 1105557180
UPDATE limits
SET 
    analytics_total = 2,
    themes_total = 4
WHERE user_id = (
    SELECT id FROM users WHERE telegram_id = 1105557180
)
AND EXISTS (
    SELECT 1 FROM users 
    WHERE users.id = limits.user_id 
    AND users.subscription_type = 'ULTRA'
);
```

### 3. Удаление дубликатов подписок

Сначала проверьте, какие подписки есть:

```sql
SELECT 
    s.id,
    s.payment_id,
    s.started_at,
    s.subscription_type
FROM subscriptions s
JOIN users u ON s.user_id = u.id
WHERE u.telegram_id = 1105557180
ORDER BY s.started_at DESC;
```

Затем удалите старые (оставьте только последнюю):

```sql
-- Удалить все подписки кроме последней
DELETE FROM subscriptions
WHERE id IN (
    SELECT s.id
    FROM subscriptions s
    JOIN users u ON s.user_id = u.id
    WHERE u.telegram_id = 1105557180
    AND s.id NOT IN (
        SELECT id 
        FROM subscriptions 
        WHERE user_id = (SELECT id FROM users WHERE telegram_id = 1105557180)
        ORDER BY started_at DESC 
        LIMIT 1
    )
);
```

---

## Вариант 3: Через Python с DATABASE_URL

Если у вас есть DATABASE_URL от Railway:

```powershell
# Windows PowerShell
$env:DATABASE_URL="postgresql://user:password@host:port/database"
python scripts/check_user_subscription.py

# Затем исправление
python scripts/fix_user_subscription.py
```

---

## Что проверить после исправления

1. ✅ Лимиты должны быть: analytics=2, themes=4
2. ✅ Должна быть только одна подписка ULTRA
3. ✅ Нет дубликатов payment_id
4. ✅ subscription_expires_at установлена правильно

---

## Защита от повторения проблемы

После исправления нужно добавить проверку на дубликаты в `core/subscriptions/payment_handler.py`:

```python
# После строки 68, перед созданием subscription:
# Проверка на дубликат платежа
existing_subscription_query = select(Subscription).where(
    Subscription.payment_id == payment_id
)
existing_result = await session.execute(existing_subscription_query)
existing_subscription = existing_result.scalar_one_or_none()

if existing_subscription:
    print(f"⚠️  Платеж с payment_id={payment_id} уже был обработан ранее (Subscription ID: {existing_subscription.id})")
    print(f"   Пропускаем обработку, чтобы избежать дублирования")
    return True  # Возвращаем True, так как платеж уже обработан
```

