#!/usr/bin/env python3
from app import create_app
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court
import os

# Set production mode
os.environ['FLASK_ENV'] = 'production'

app = create_app()
with app.app_context():
    print("📊 Database Status Check")
    print("=" * 50)
    
    # Count users by type
    total_users = User.query.count()
    players = User.query.filter_by(user_type='player').count()
    owners = User.query.filter_by(user_type='owner').count()
    admins = User.query.filter_by(user_type='admin').count()
    
    print(f"Total Users: {total_users}")
    print(f"Players: {players}")
    print(f"Owners: {owners}")
    print(f"Admins: {admins}")
    
    # List all players
    print("\n👥 All Players:")
    all_players = User.query.filter_by(user_type='player').all()
    for player in all_players:
        print(f"  • {player.full_name} ({player.email}) - Active: {player.is_active}")
    
    # List all courts
    courts = Court.query.count()
    print(f"\n🎾 Total Courts: {courts}")
    
    # Check specific demo emails
    print("\n🔍 Checking Demo Accounts:")
    demo_emails = [
        'player1@demo.com', 'player2@demo.com', 'player3@demo.com',
        'owner1@demo.com', 'owner2@demo.com'
    ]
    
    for email in demo_emails:
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"  ✅ {email} - {user.full_name}")
        else:
            print(f"  ❌ {email} - NOT FOUND")