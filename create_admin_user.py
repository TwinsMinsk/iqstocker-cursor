#!/usr/bin/env python3
"""Create test admin user."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import SessionLocal
from database.models import User, SubscriptionType


def create_admin_user():
    """Create test admin user."""
    db = SessionLocal()
    try:
        # Check if admin user exists
        existing_user = db.query(User).filter(User.username == "admin").first()
        
        if not existing_user:
            # Create admin user
            admin_user = User(
                telegram_id=123456789,
                username="admin",
                first_name="Admin",
                last_name="User",
                subscription_type=SubscriptionType.PRO
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
