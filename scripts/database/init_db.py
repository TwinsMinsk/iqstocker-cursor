"""Initialize database for MVP."""

import os
import sys
from sqlalchemy import create_engine
from database.models import Base

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Initialize SQLite database."""
    
    # Create SQLite database
    database_url = "sqlite:///iqstocker.db"
    engine = create_engine(database_url)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    print("Database initialized successfully!")
    print(f"Database file: {os.path.abspath('iqstocker.db')}")

if __name__ == "__main__":
    init_database()
