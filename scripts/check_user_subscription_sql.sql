-- SQL скрипт для проверки подписки пользователя 1105557180
-- Выполните этот запрос в админ-панели или через psql

-- 1. Информация о пользователе
SELECT 
    u.id as user_id,
    u.telegram_id,
    u.subscription_type,
    u.subscription_expires_at,
    u.created_at
FROM users u
WHERE u.telegram_id = 1105557180;

-- 2. ВСЕ подписки пользователя (сортировка от новых к старым)
SELECT 
    s.id,
    s.subscription_type,
    s.payment_id,
    s.amount,
    s.started_at,
    s.expires_at,
    s.created_at,
    CASE 
        WHEN s.started_at = (
            SELECT MAX(started_at) 
            FROM subscriptions 
            WHERE user_id = s.user_id 
            AND subscription_type = 'ULTRA'
        ) THEN '✅ ПОСЛЕДНЯЯ (оставляем)'
        ELSE '❌ ДУБЛИКАТ (удалить)'
    END as action
FROM subscriptions s
JOIN users u ON s.user_id = u.id
WHERE u.telegram_id = 1105557180
ORDER BY s.started_at DESC;

-- 3. Количество ULTRA подписок
SELECT 
    COUNT(*) as total_ultra_subscriptions,
    STRING_AGG(s.id::text, ', ') as subscription_ids
FROM subscriptions s
JOIN users u ON s.user_id = u.id
WHERE u.telegram_id = 1105557180
  AND s.subscription_type = 'ULTRA';

-- 4. Проверка дубликатов по payment_id
SELECT 
    payment_id,
    COUNT(*) as count,
    STRING_AGG(s.id::text, ', ') as subscription_ids,
    STRING_AGG(s.started_at::text, ', ') as started_dates
FROM subscriptions s
JOIN users u ON s.user_id = u.id
WHERE u.telegram_id = 1105557180
  AND payment_id IS NOT NULL
GROUP BY payment_id
HAVING COUNT(*) > 1;

-- 5. Лимиты пользователя
SELECT 
    l.analytics_used,
    l.analytics_total,
    l.themes_used,
    l.themes_total,
    l.current_tariff_started_at,
    CASE 
        WHEN l.analytics_total = 2 AND l.themes_total = 4 THEN '✅ Корректно для ULTRA'
        ELSE '⚠️ НЕ соответствует ULTRA (ожидается: analytics=2, themes=4)'
    END as limits_status
FROM limits l
JOIN users u ON l.user_id = u.id
WHERE u.telegram_id = 1105557180;

-- 6. Сводка: что нужно сделать
SELECT 
    (SELECT COUNT(*) FROM subscriptions s 
     JOIN users u ON s.user_id = u.id 
     WHERE u.telegram_id = 1105557180 
     AND s.subscription_type = 'ULTRA') as total_ultra_subscriptions,
    CASE 
        WHEN (SELECT COUNT(*) FROM subscriptions s 
              JOIN users u ON s.user_id = u.id 
              WHERE u.telegram_id = 1105557180 
              AND s.subscription_type = 'ULTRA') > 1 
        THEN '⚠️ Нужно удалить дубликаты (оставить последнюю)'
        ELSE '✅ Все в порядке, дубликатов нет'
    END as recommendation;

