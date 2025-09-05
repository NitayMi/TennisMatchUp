#!/usr/bin/env python3
"""
Test connection to AWS RDS PostgreSQL
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def test_aws_connection():
    """Test connection to AWS RDS"""
    
    print("☁️ Testing AWS RDS PostgreSQL Connection")
    print("=" * 50)
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return False
    
    try:
        print("🔗 Connecting to AWS RDS...")
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Test connection
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected successfully!")
            print(f"📊 PostgreSQL Version: {version[:80]}...")
            
            # Test creating a table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50)
                )
            """))
            
            conn.execute(text("INSERT INTO test_table (name) VALUES ('TennisMatchUp Test')"))
            
            result = conn.execute(text("SELECT * FROM test_table"))
            row = result.fetchone()
            print(f"✅ Test data: {row}")
            
            conn.execute(text("DROP TABLE test_table"))
            print("✅ AWS RDS connection test passed!")
            
            conn.commit()
            return True
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\n🔧 Common fixes:")
        print("1. Check security group allows your IP")
        print("2. Verify database endpoint is correct")
        print("3. Ensure database is publicly accessible")
        return False

if __name__ == "__main__":
    test_aws_connection()