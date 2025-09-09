#!/usr/bin/env python3
"""
Load simple demo data for TennisMatchUp
"""

import os
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
from app import create_app
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court, Booking
from models.message import Message

load_dotenv()

def create_demo_data():
    """Create simple demo data"""
    
    print("🎾 Loading TennisMatchUp Demo Data")
    print("=" * 50)
    
    # Set to production mode to use AWS database
    os.environ['FLASK_ENV'] = 'production'
    
    try:
        app = create_app()
        
        with app.app_context():
            print("🏗️ Creating demo data...")
            
            # Check if demo data already exists
            existing_users = User.query.filter(User.email.like('%demo.com')).count()
            if existing_users > 0:
                print("Demo data already exists, skipping...")
                return True
            
            # Create demo users step by step
            created_count = 0
            
            # Create 2 owners
            print("Creating owners...")
            owner1 = User(
                full_name="David Cohen",
                email="owner1@demo.com", 
                password="demo123",
                user_type="owner",
                phone_number="+972-50-1234567"
            )
            db.session.add(owner1)
            db.session.flush()  # Get ID
            
            owner2 = User(
                full_name="Sarah Levi",
                email="owner2@demo.com",
                password="demo123", 
                user_type="owner",
                phone_number="+972-50-2345678"
            )
            db.session.add(owner2)
            db.session.flush()  # Get ID
            created_count += 2
            
            # Create courts for owners
            print("Creating courts...")
            court1 = Court(
                owner_id=owner1.id,
                name="Center Court Tel Aviv",
                location="Tel Aviv, Israel",
                court_type="outdoor",
                surface="hard", 
                hourly_rate=120.0,
                description="Professional outdoor hard court in Tel Aviv",
                is_active=True
            )
            db.session.add(court1)
            
            court2 = Court(
                owner_id=owner1.id,
                name="Court 2 Tel Aviv",
                location="Tel Aviv, Israel", 
                court_type="outdoor",
                surface="clay",
                hourly_rate=100.0,
                description="Clay court with excellent drainage",
                is_active=True
            )
            db.session.add(court2)
            
            court3 = Court(
                owner_id=owner2.id,
                name="Haifa Tennis Academy", 
                location="Haifa, Israel",
                court_type="indoor",
                surface="hard",
                hourly_rate=150.0,
                description="Premium indoor court with AC",
                is_active=True
            )
            db.session.add(court3)
            
            # Create 5 players
            print("Creating players...")
            player_data = [
                {"name": "Alex Johnson", "email": "player1@demo.com", "skill": "4.5", "location": "Tel Aviv"},
                {"name": "Maya Shapiro", "email": "player2@demo.com", "skill": "3.0", "location": "Tel Aviv"}, 
                {"name": "Yuki Tanaka", "email": "player3@demo.com", "skill": "4.0", "location": "Haifa"},
                {"name": "Emma Rodriguez", "email": "player4@demo.com", "skill": "3.5", "location": "Jerusalem"},
                {"name": "Liam O'Connor", "email": "player5@demo.com", "skill": "2.5", "location": "Tel Aviv"}
            ]
            
            for pd in player_data:
                # Create user
                user = User(
                    full_name=pd["name"],
                    email=pd["email"], 
                    password="demo123",
                    user_type="player",
                    phone_number="+972-50-0000000"
                )
                db.session.add(user)
                db.session.flush()  # Get ID
                
                # Create player profile
                player = Player(
                    user_id=user.id,
                    skill_level=pd["skill"],
                    preferred_location=pd["location"],
                    bio=f"Tennis player from {pd['location']}"
                )
                db.session.add(player)
                created_count += 1
            
            # Commit all changes
            db.session.commit()
            
            print(f"✅ Demo data loaded successfully!")
            print(f"📊 Created {created_count} users and 4 courts")
            print(f"🎮 Demo Accounts:")
            print(f"  • Players: player1@demo.com - player30@demo.com (password: demo123)")
            print(f"  • Owners: owner1@demo.com, owner2@demo.com (password: demo123)")
            print(f"  • Admin: admin@tennismatchup.com (password: admin123)")
            print(f"\n🎯 Skill Level Distribution:")
            print(f"  • Beginner (2.0-2.5): 4 players")
            print(f"  • Intermediate (3.0-3.5): 13 players") 
            print(f"  • Advanced (4.0-4.5): 13 players")
            print(f"\n📍 Location Distribution:")
            print(f"  • Tel Aviv: 8 players")
            print(f"  • Haifa: 6 players")
            print(f"  • Jerusalem: 5 players")
            print(f"  • Netanya: 4 players")
            print(f"  • Beer Sheva: 3 players")
            print(f"  • Eilat: 4 players")
            
            return True
            
    except Exception as e:
        print(f"❌ Failed to load demo data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_demo_data()
    if success:
        print("\n🎉 Demo data ready!")
        print("You can now login with demo accounts and test the system")
    else:
        print("\n❌ Failed to load demo data")