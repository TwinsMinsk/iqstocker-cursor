
-- Create tariff_limits table
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

-- Create unique index
CREATE UNIQUE INDEX IF NOT EXISTS ix_tariff_limits_subscription_type 
ON tariff_limits(subscription_type);

-- Insert initial data
INSERT INTO tariff_limits (subscription_type, analytics_limit, themes_limit, theme_cooldown_days, test_pro_duration_days)
VALUES 
    ('FREE', 0, 4, 7, NULL),
    ('TEST_PRO', 1, 2, 7, 14),
    ('PRO', 1, 4, 7, NULL),
    ('ULTRA', 2, 4, 7, NULL)
ON CONFLICT (subscription_type) DO NOTHING;

-- Verify data
SELECT * FROM tariff_limits ORDER BY subscription_type;
