-- SQL запрос для проверки пользователя 1105557180
-- Выполните этот запрос в админ-панели или через psql

-- 1. Информация о пользователе
SELECT 
    id,
    telegram_id,
    subscription_type,
    subscription_expires_at,
    created_at
FROM users
WHERE telegram_id = 1105557180;

-- 2. Все подписки пользователя
SELECT 
    s.id,
    s.subscription_type,
    s.payment_id,
    s.amount,
    s.started_at,
    s.expires_at,
    s.created_at
FROM subscriptions s
JOIN users u ON s.user_id = u.id
WHERE u.telegram_id = 1105557180
ORDER BY s.started_at DESC;

-- 3. Проверка дубликатов payment_id
SELECT 
    payment_id,
    COUNT(*) as count,
    STRING_AGG(s.id::text, ', ') as subscription_ids
FROM subscriptions s
JOIN users u ON s.user_id = u.id
WHERE u.telegram_id = 1105557180
  AND payment_id IS NOT NULL
GROUP BY payment_id
HAVING COUNT(*) > 1;

-- 4. Лимиты пользователя
SELECT 
    l.analytics_used,
    l.analytics_total,
    l.themes_used,
    l.themes_total,
    l.current_tariff_started_at
FROM limits l
JOIN users u ON l.user_id = u.id
WHERE u.telegram_id = 1105557180;

-- 5. Сравнение с ожидаемыми лимитами для ULTRA
-- (Нужно знать значения из настроек, обычно: analytics=2, themes=4)
SELECT 
    l.analytics_total as current_analytics,
    2 as expected_analytics,  -- Замените на реальное значение из настроек
    l.analytics_total - 2 as analytics_diff,
    l.themes_total as current_themes,
    4 as expected_themes,  -- Замените на реальное значение из настроек
    l.themes_total - 4 as themes_diff
FROM limits l
JOIN users u ON l.user_id = u.id
WHERE u.telegram_id = 1105557180
  AND u.subscription_type = 'ULTRA';

