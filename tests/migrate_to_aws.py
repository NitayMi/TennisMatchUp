#!/usr/bin/env python3
"""
Migrate from SQLite to AWS RDS PostgreSQL
"""

import os
import sqlite3
from dotenv import load_dotenv
from app import create_app
from models.database import db
from sqlalchemy import text

load_dotenv()

def migrate_to_aws():
    """Migrate all data to AWS RDS"""
    
    print("☁️ TennisMatchUp - AWS RDS Migration")
    print("=" * 50)
    
    # Check source database
    sqlite_db = 'instance/tennis_matchup.db'
    if not os.path.exists(sqlite_db):
        print("❌ Local SQLite database not found!")
        return False
    
    # Set to production mode
    os.environ['FLASK_ENV'] = 'production'
    
    try:
        # Create app with AWS database
        app = create_app('production')
        
        with app.app_context():
            print("🏗️ Creating AWS RDS tables...")
            db.create_all()
            print("✅ AWS tables created successfully!")
            
            # Connect to local SQLite
            sqlite_conn = sqlite3.connect(sqlite_db)
            sqlite_conn.row_factory = sqlite3.Row
            
            print("📊 Starting data migration...")
            
            # Migrate each table
            migrate_table(sqlite_conn, 'users', db)
            migrate_table(sqlite_conn, 'players', db) 
            migrate_table(sqlite_conn, 'courts', db)
            migrate_table(sqlite_conn, 'bookings', db)
            migrate_table(sqlite_conn, 'messages', db)
            
            sqlite_conn.close()
            
            # Verify migration
            user_count = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
            print(f"✅ Migrated {user_count} users to AWS RDS")
            
            print("🎉 AWS RDS migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

def migrate_table(sqlite_conn, table_name, db):
    """Generic table migration"""
    from sqlalchemy import text
    
    print(f"  📋 Migrating {table_name}...")
    
    # Get all rows from SQLite
    cursor = sqlite_conn.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    if not rows:
        print(f"    ⚠️ No data in {table_name}")
        return
    
    # Get column names
    columns = [description[0] for description in cursor.description]
    columns_str = ', '.join(columns)
    placeholders = ', '.join([f':{col}' for col in columns])
    
    # Insert into PostgreSQL
    for row in rows:
        row_dict = dict(row)
        
        # Check if record exists (based on id)
        if 'id' in row_dict:
            existing = db.session.execute(
                text(f"SELECT id FROM {table_name} WHERE id = :id"),
                {"id": row_dict['id']}
            ).fetchone()
            
            if existing:
                continue  # Skip if exists
        
        # Insert new record
        try:
            db.session.execute(
                text(f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"),
                row_dict
            )
        except Exception as e:
            print(f"    ⚠️ Error inserting into {table_name}: {str(e)}")
            continue
    
    db.session.commit()
    print(f"    ✅ Migrated {len(rows)} rows to {table_name}")

if __name__ == "__main__":
    migrate_to_aws()