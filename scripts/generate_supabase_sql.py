#!/usr/bin/env python3
"""
SQL script to create tariff_limits table - can be executed via Supabase dashboard SQL editor.
This script can be copied and pasted directly into Supabase SQL Editor.
"""

from pathlib import Path

SQL_SCRIPT = """
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
"""

if __name__ == "__main__":
    print("=" * 60)
    print("📋 SQL Script for Supabase SQL Editor")
    print("=" * 60)
    print("\nCopy and paste the following SQL into Supabase SQL Editor:")
    print("\n" + "=" * 60)
    print(SQL_SCRIPT)
    print("=" * 60)
    print("\n💡 Instructions:")
    print("1. Go to your Supabase project dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Create a new query")
    print("4. Copy and paste the SQL above")
    print("5. Click 'Run' to execute")
    print("\n✅ After execution, the table will be created and initialized!")
    
    # Also save to file
    output_file = Path(__file__).parent / "data" / "tariff_limits_supabase.sql"
    output_file.write_text(SQL_SCRIPT, encoding='utf-8')
    print(f"\n💾 SQL script also saved to: {output_file}")

