"""
Add source field to calendar_entries table
"""

import sqlite3
import os

def add_source_field():
    """Add source field to calendar_entries table"""
    
    # Path to database
    db_path = "iqstocker.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if source column already exists
        cursor.execute("PRAGMA table_info(calendar_entries)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'source' in columns:
            print("✅ Source column already exists in calendar_entries table")
            conn.close()
            return True
        
        # Add source column
        print("Adding source column to calendar_entries table...")
        cursor.execute("ALTER TABLE calendar_entries ADD COLUMN source VARCHAR(50) DEFAULT 'manual'")
        
        # Update existing records to have 'manual' as source
        cursor.execute("UPDATE calendar_entries SET source = 'manual' WHERE source IS NULL")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✅ Successfully added source column to calendar_entries table")
        return True
        
    except Exception as e:
        print(f"❌ Error adding source column: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("🔧 Adding source field to calendar_entries table...")
    success = add_source_field()
    
    if success:
        print("🎉 Database update completed successfully!")
        print("You can now restart the admin panel.")
    else:
        print("❌ Database update failed. Please check the error above.")
