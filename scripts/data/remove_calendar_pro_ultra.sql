-- SQL script to remove obsolete calendar_pro_ultra entry from lexicon_entries table
-- Execute this in Supabase Dashboard SQL Editor

DELETE FROM lexicon_entries 
WHERE key = 'calendar_pro_ultra' 
AND category = 'LEXICON_RU';

-- Verify deletion
SELECT key, category 
FROM lexicon_entries 
WHERE key LIKE 'calendar%' 
ORDER BY key;

-- Expected result: should show only 3 entries:
-- calendar_free
-- calendar_test_pro_pro
-- calendar_ultra

