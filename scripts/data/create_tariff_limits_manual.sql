-- SQL script to create tariff_limits table manually
-- Run this in your PostgreSQL database if migration fails
-- 
-- To execute this script:
--   1. Connect to your PostgreSQL database
--   2. Run: psql -d your_database -f scripts/data/create_tariff_limits_manual.sql
--   3. Or copy-paste the SQL commands below into your database client

CREATE TABLE IF NOT EXISTS tariff_limits (
    id SERIAL PRIMARY KEY,
    subscription_type VARCHAR(20) NOT NULL UNIQUE,
    analytics_limit INTEGER NOT NULL DEFAULT 0,
    themes_limit INTEGER NOT NULL DEFAULT 4,
    theme_cooldown_days INTEGER NOT NULL DEFAULT 7,
    test_pro_duration_days INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_tariff_limits_subscription_type ON tariff_limits(subscription_type);

-- Insert initial data (values from config/settings.py defaults)
-- Adjust these values if your settings.py has different defaults
INSERT INTO tariff_limits (subscription_type, analytics_limit, themes_limit, theme_cooldown_days, test_pro_duration_days)
VALUES 
    ('FREE', 0, 4, 7, NULL),
    ('TEST_PRO', 1, 2, 7, 14),
    ('PRO', 1, 4, 7, NULL),
    ('ULTRA', 2, 4, 7, NULL)
ON CONFLICT (subscription_type) DO NOTHING;

-- Verify the data was inserted
SELECT * FROM tariff_limits ORDER BY subscription_type;

