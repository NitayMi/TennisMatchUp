#!/usr/bin/env python3
"""
Database migration script to add geographic fields
Run this before update_coordinates.py
"""

import sys
import os
import sqlite3

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_database():
    """Add geographic columns to players table"""
    print("🗄️  TennisMatchUp - Database Migration")
    print("=" * 50)
    
    try:
        # Connect to SQLite database
        db_path = 'tennismatchup.db'
        
        if not os.path.exists(db_path):
            print("❌ Database file not found. Run 'python app.py' first to create the database.")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📊 Checking current table structure...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(players)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns: {', '.join(columns)}")
        
        columns_to_add = []
        
        if 'latitude' not in columns:
            columns_to_add.append('latitude')
        
        if 'longitude' not in columns:
            columns_to_add.append('longitude')
        
        if 'location_updated_at' not in columns:
            columns_to_add.append('location_updated_at')
        
        if not columns_to_add:
            print("✅ All geographic columns already exist!")
            conn.close()
            return True
        
        print(f"🔧 Adding columns: {', '.join(columns_to_add)}")
        
        # Add missing columns
        if 'latitude' in columns_to_add:
            cursor.execute("ALTER TABLE players ADD COLUMN latitude REAL")
            print("  ✅ Added latitude column")
        
        if 'longitude' in columns_to_add:
            cursor.execute("ALTER TABLE players ADD COLUMN longitude REAL")
            print("  ✅ Added longitude column")
        
        if 'location_updated_at' in columns_to_add:
            cursor.execute("ALTER TABLE players ADD COLUMN location_updated_at DATETIME")
            print("  ✅ Added location_updated_at column")
        
        # Commit changes
        conn.commit()
        
        # Verify changes
        cursor.execute("PRAGMA table_info(players)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"Updated columns: {', '.join(new_columns)}")
        
        conn.close()
        
        print("✅ Database migration completed successfully!")
        print("Now you can run: python update_coordinates.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n🚀 Next step: python update_coordinates.py")
    else:
        print("\n❌ Please fix the errors and try again")