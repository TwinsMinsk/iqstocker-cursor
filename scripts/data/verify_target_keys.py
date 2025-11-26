#!/usr/bin/env python3
"""Verify that all target keys are in database."""

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

target_keys_ru = ['themes_list_pro_ultra', 'themes_list_free']
target_keys_commands = ['get_themes', 'archive_themes', 'back_to_main_menu']

print("Checking LEXICON_RU keys:")
all_ok_ru = True
for key in target_keys_ru:
    entry = db.query(LexiconEntry).filter(
        LexiconEntry.key == key,
        LexiconEntry.category == LexiconCategory.LEXICON_RU
    ).first()
    if entry:
        print(f"  ✅ {key}: EXISTS in DB")
    else:
        print(f"  ❌ {key}: NOT in DB")
        all_ok_ru = False

print("\nChecking LEXICON_COMMANDS_RU keys:")
all_ok_commands = True
for key in target_keys_commands:
    entry = db.query(LexiconEntry).filter(
        LexiconEntry.key == key,
        LexiconEntry.category == LexiconCategory.LEXICON_COMMANDS_RU
    ).first()
    if entry:
        print(f"  ✅ {key}: EXISTS in DB")
    else:
        print(f"  ❌ {key}: NOT in DB")
        all_ok_commands = False

db.close()

if all_ok_ru and all_ok_commands:
    print("\n✅ All target keys are in database!")
    sys.exit(0)
else:
    print("\n❌ Some keys are missing!")
    sys.exit(1)

