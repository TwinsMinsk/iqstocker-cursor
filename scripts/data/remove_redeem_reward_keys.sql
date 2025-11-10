-- SQL script to remove obsolete redeem reward entries from lexicon_entries table
-- Execute this in Supabase Dashboard SQL Editor

-- Remove obsolete redeem reward keys
-- Note: redeem_support_request is kept as it's still used in the code
DELETE FROM lexicon_entries 
WHERE key IN (
    'redeem_reward_1',
    'redeem_reward_2',
    'redeem_reward_3',
    'redeem_reward_4',
    'redeem_reward_5',
    'redeem_not_enough_points',
    'redeem_success',
    'redeem_success_discount',
    'redeem_success_free_month',
    'redeem_success_radar',
    'redeem_admin_not_setup_link',
    'redeem_link_sent_privately'
)
AND category = 'LEXICON_RU';

-- Verify deletion - should show remaining redeem keys (if any)
SELECT key, category 
FROM lexicon_entries 
WHERE key LIKE 'redeem%' 
ORDER BY key;

-- Expected result: should show:
-- redeem_menu_header (should exist)
-- redeem_support_request (should exist - still used in code)

