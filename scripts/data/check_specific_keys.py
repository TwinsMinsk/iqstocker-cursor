#!/usr/bin/env python3
"""Check specific lexicon keys in database."""

import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from config.database import SessionLocal
from database.models.lexicon_entry import LexiconEntry, LexiconCategory

db = SessionLocal()
keys_to_check = ['themes_list_pro_ultra', 'themes_list_free']

print("Checking keys in LEXICON_RU:")
for key in keys_to_check:
    entry = db.query(LexiconEntry).filter(
        LexiconEntry.key == key,
        LexiconEntry.category == LexiconCategory.LEXICON_RU
    ).first()
    if entry:
        print(f"  ✅ {key}: EXISTS in DB")
    else:
        print(f"  ❌ {key}: NOT in DB")

db.close()

