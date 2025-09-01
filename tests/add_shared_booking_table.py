#!/usr/bin/env python3
"""
Add shared_bookings table to database
"""

import sys
import os
import sqlite3

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def add_shared_booking_table():
    """Add shared_bookings table"""
    print("🗄️ TennisMatchUp - Adding Shared Bookings Table")
    print("=" * 50)
    
    try:
        # Connect to database
        db_path = 'instance/tennis_matchup.db'
        
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shared_bookings'")
        if cursor.fetchone():
            print("✅ shared_bookings table already exists!")
            conn.close()
            return True
        
        print("🔧 Creating shared_bookings table...")
        
        # Create shared_bookings table
        cursor.execute("""
            CREATE TABLE shared_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player1_id INTEGER NOT NULL,
                player2_id INTEGER NOT NULL,
                court_id INTEGER NOT NULL,
                booking_date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                status VARCHAR(20) DEFAULT 'proposed' NOT NULL,
                total_cost REAL,
                player1_share REAL,
                player2_share REAL,
                cost_split_method VARCHAR(20) DEFAULT 'equal' NOT NULL,
                initiator_notes TEXT,
                partner_notes TEXT,
                alternative_court_id INTEGER,
                alternative_date DATE,
                alternative_start_time TIME,
                alternative_end_time TIME,
                alternative_notes TEXT,
                final_booking_id INTEGER,
                proposed_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                responded_at DATETIME,
                confirmed_at DATETIME,
                expires_at DATETIME,
                FOREIGN KEY (player1_id) REFERENCES players (id),
                FOREIGN KEY (player2_id) REFERENCES players (id),
                FOREIGN KEY (court_id) REFERENCES courts (id),
                FOREIGN KEY (alternative_court_id) REFERENCES courts (id),
                FOREIGN KEY (final_booking_id) REFERENCES bookings (id)
            )
        """)
        
        print("  ✅ Created shared_bookings table")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✅ Shared booking system ready!")
        print("Now you can:")
        print("• Players can propose joint court bookings")
        print("• Partners can accept/counter-propose")
        print("• Cost splitting between players")
        print("• 48-hour expiry on proposals")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_shared_booking_table()
    if success:
        print("\n🚀 Next: Add import to models/__init__.py and test the system")
    else:
        print("\n❌ Please fix the errors and try again")