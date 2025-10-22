#!/usr/bin/env python3
"""Initialize system messages for admin panel."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import SessionLocal
from database.models import SystemMessage, LLMSettings, LLMProviderType


def init_system_messages():
    """Initialize system messages in database."""
    db = SessionLocal()
    try:
        # Check if themes_cooldown_message exists
        existing_message = db.query(SystemMessage).filter(
            SystemMessage.key == "themes_cooldown_message"
        ).first()
        
        if not existing_message:
            # Create default cooldown message
            cooldown_message = SystemMessage(
                key="themes_cooldown_message",
                text="Вы уже запрашивали темы недавно. Попробуйте через {days} дн."
            )
            db.add(cooldown_message)
            print("Created themes_cooldown_message")
        else:
            print("themes_cooldown_message already exists")
        
        # Check if LLMSettings exists
        existing_llm = db.query(LLMSettings).filter(
            LLMSettings.is_active == True
        ).first()
        
        if not existing_llm:
            # Create default LLM settings
            llm_settings = LLMSettings(
                provider_name=LLMProviderType.GEMINI,
                api_key_encrypted="dummy_key",
                is_active=True,
                theme_request_interval_days=7
            )
            db.add(llm_settings)
            print("Created default LLMSettings")
        else:
            print("LLMSettings already exists")
        
        db.commit()
        print("System messages initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing system messages: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_system_messages()
