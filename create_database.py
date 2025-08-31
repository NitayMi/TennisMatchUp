#!/usr/bin/env python3
"""
Force database creation for TennisMatchUp
Run this to ensure database file is created
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.database import db
from models.user import User
from models.player import Player

def main():
    """Force database creation"""
    print("🗄️ TennisMatchUp - Force Database Creation")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            print("📊 Creating all database tables...")
            
            # Force creation of all tables
            db.create_all()
            
            # Make a simple query to force file creation
            user_count = User.query.count()
            print(f"✅ Database created successfully! Users: {user_count}")
            
            # Check where database was created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            print(f"Database URL: {db.engine.url}")
            
            # List all tables
            tables = inspector.get_table_names()
            print(f"Tables created: {', '.join(tables)}")
            
            # Check current directory for .db files
            print("\nChecking for database files...")
            for file in os.listdir('.'):
                if file.endswith('.db'):
                    print(f"  Found: {file}")
            
            # Check instance directory
            if os.path.exists('instance'):
                print("Checking instance directory...")
                for file in os.listdir('instance'):
                    if file.endswith('.db'):
                        print(f"  Found in instance/: {file}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error creating database: {str(e)}")
            return 1

if __name__ == "__main__":
    exit(main())