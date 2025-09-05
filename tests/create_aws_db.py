#!/usr/bin/env python3
"""
Create database schema in AWS RDS PostgreSQL
"""

import os
from dotenv import load_dotenv
from app import create_app
from models.database import db

load_dotenv()

def create_aws_database():
    """Create all tables in AWS RDS"""
    
    print("☁️ TennisMatchUp - AWS Database Creation")
    print("=" * 50)
    
    # Set to production mode to use AWS database
    os.environ['FLASK_ENV'] = 'production'
    
    try:
        # Create app with AWS database
        app = create_app()
        
        with app.app_context():
            print("🏗️ Creating all tables in AWS RDS...")
            
            # Drop all tables first (if they exist)
            db.drop_all()
            print("🗑️ Dropped existing tables")
            
            # Create all tables
            db.create_all()
            print("✅ All tables created successfully!")
            
            # Verify tables were created
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"📊 Created {len(tables)} tables:")
            for table in tables:
                print(f"  • {table}")
            
            print("\n🎉 AWS Database ready for use!")
            
            # Test with a simple query
            result = db.session.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"📊 PostgreSQL Version: {version[:50]}...")
            
            return True
            
    except Exception as e:
        print(f"❌ Database creation failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_aws_database()
    if success:
        print("\n✅ Ready to test with: python test_aws_connection.py")
    else:
        print("\n❌ Fix the error and try again")