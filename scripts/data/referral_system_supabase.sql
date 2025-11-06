-- ============================================================================
-- Referral System Migration for Supabase
-- ============================================================================
-- Этот файл содержит SQL миграцию для создания реферальной системы
-- Скопируйте весь контент и выполните в Supabase SQL Editor
-- ============================================================================

-- Создание ENUM типа для типов наград
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reward_type_enum') THEN
        CREATE TYPE reward_type_enum AS ENUM ('link', 'free_pro', 'free_ultra');
    END IF;
END $$;

-- Создание таблицы referral_rewards
CREATE TABLE IF NOT EXISTS referral_rewards (
    reward_id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    cost INTEGER NOT NULL,
    reward_type reward_type_enum NOT NULL,
    value VARCHAR(512)
);

-- Создание индекса на reward_type для оптимизации запросов
CREATE INDEX IF NOT EXISTS ix_referral_rewards_reward_type 
ON referral_rewards(reward_type);

-- Добавление колонок в таблицу users для реферальной системы
-- Проверяем существование колонок перед добавлением

-- Добавление referrer_id (может быть NULL для пользователей без реферера)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'referrer_id'
    ) THEN
        ALTER TABLE users ADD COLUMN referrer_id INTEGER;
    END IF;
END $$;

-- Добавление referral_balance (баланс баллов, по умолчанию 0)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'referral_balance'
    ) THEN
        ALTER TABLE users ADD COLUMN referral_balance INTEGER NOT NULL DEFAULT 0;
    END IF;
END $$;

-- Добавление referral_bonus_paid (флаг оплаченного бонуса, по умолчанию false)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'referral_bonus_paid'
    ) THEN
        ALTER TABLE users ADD COLUMN referral_bonus_paid BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- Создание foreign key constraint для referrer_id
-- Сначала проверяем, существует ли уже constraint
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_users_referrer_id' 
        AND table_name = 'users'
    ) THEN
        ALTER TABLE users 
        ADD CONSTRAINT fk_users_referrer_id 
        FOREIGN KEY (referrer_id) 
        REFERENCES users(id) 
        ON DELETE SET NULL;
    END IF;
END $$;

-- Создание индекса на referrer_id для оптимизации запросов
CREATE INDEX IF NOT EXISTS ix_users_referrer_id 
ON users(referrer_id);

-- ============================================================================
-- Проверка результата миграции
-- ============================================================================
-- Выполните следующие запросы для проверки:

-- Проверка таблицы referral_rewards
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'referral_rewards'
ORDER BY ordinal_position;

-- Проверка новых колонок в users
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('referrer_id', 'referral_balance', 'referral_bonus_paid')
ORDER BY column_name;

-- Проверка индексов
SELECT 
    indexname, 
    tablename, 
    indexdef
FROM pg_indexes 
WHERE tablename IN ('users', 'referral_rewards')
AND (indexname LIKE '%referral%' OR indexname LIKE '%referrer%')
ORDER BY tablename, indexname;

-- Проверка foreign key constraints
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name = 'users'
AND tc.constraint_name = 'fk_users_referrer_id';
