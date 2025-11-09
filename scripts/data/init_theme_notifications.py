#!/usr/bin/env python3
"""Initialize theme notification messages in lexicon database."""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.database import SessionLocal
from database.models.lexicon_entry import LexiconEntry, LexiconCategory
from bot.lexicon.lexicon_ru import LEXICON_RU


def init_theme_notifications():
    """Initialize theme notification messages in database."""
    db = SessionLocal()
    try:
        # Messages to initialize
        notification_keys = [
            'themes_limit_burn_reminder_3_days',
            'themes_limit_burn_reminder_1_day'
        ]
        
        added_count = 0
        updated_count = 0
        
        for key in notification_keys:
            # Get default text from lexicon
            default_text = LEXICON_RU.get(key, "")
            
            if not default_text:
                print(f"⚠️  Warning: Key '{key}' not found in LEXICON_RU")
                continue
            
            # Check if entry exists
            existing_entry = db.query(LexiconEntry).filter(
                LexiconEntry.key == key,
                LexiconEntry.category == LexiconCategory.LEXICON_RU
            ).first()
            
            if existing_entry:
                # Update if text is different
                if existing_entry.value != default_text:
                    existing_entry.value = default_text
                    updated_count += 1
                    print(f"✅ Updated: {key}")
                else:
                    print(f"ℹ️  Already exists: {key}")
            else:
                # Create new entry
                new_entry = LexiconEntry(
                    key=key,
                    value=default_text,
                    category=LexiconCategory.LEXICON_RU
                )
                db.add(new_entry)
                added_count += 1
                print(f"✅ Created: {key}")
        
        db.commit()
        print(f"\n📊 Summary:")
        print(f"   - Added: {added_count} entries")
        print(f"   - Updated: {updated_count} entries")
        print(f"✅ Theme notification messages initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing theme notifications: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_theme_notifications()

