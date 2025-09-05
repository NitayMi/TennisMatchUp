#!/usr/bin/env python3
"""
Add rich demo data to existing database - NO DELETION
Adds more courts, players, and creates realistic bookings
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
import random

load_dotenv()

def add_rich_data():
    print("Adding Rich Demo Data - NO DELETION")
    print("=" * 50)
    
    os.environ['FLASK_ENV'] = 'production'
    
    try:
        app = create_app()
        
        with app.app_context():
            # Check current state
            current_users = User.query.count()
            current_players = User.query.filter_by(user_type='player').count()
            current_owners = User.query.filter_by(user_type='owner').count()
            current_courts = Court.query.count()
            
            print(f"Current state:")
            print(f"  Users: {current_users}")
            print(f"  Players: {current_players}")
            print(f"  Owners: {current_owners}")
            print(f"  Courts: {current_courts}")
            
            added_owners = 0
            added_players = 0
            added_courts = 0
            
            # Add more diverse owners with courts
            new_owners_data = [
                {
                    'name': 'Michael Goldberg',
                    'email': 'mgoldberg@tennis.com',
                    'phone': '+972-50-3456789',
                    'courts': [
                        {
                            'name': 'Royal Tennis Club Jerusalem',
                            'location': 'Jerusalem, Israel',
                            'court_type': 'outdoor',
                            'surface': 'grass',
                            'hourly_rate': 200.0,
                            'description': 'Exclusive grass court in Jerusalem. Championship quality playing surface.'
                        },
                        {
                            'name': 'Practice Court Jerusalem',
                            'location': 'Jerusalem, Israel', 
                            'court_type': 'outdoor',
                            'surface': 'hard',
                            'hourly_rate': 90.0,
                            'description': 'Budget-friendly practice court. Perfect for training sessions.'
                        }
                    ]
                },
                {
                    'name': 'Rachel Mizrahi',
                    'email': 'rmizrahi@beachtennis.com',
                    'phone': '+972-50-4567890',
                    'courts': [
                        {
                            'name': 'Eilat Resort Courts',
                            'location': 'Eilat, Israel',
                            'court_type': 'outdoor',
                            'surface': 'hard',
                            'hourly_rate': 180.0,
                            'description': 'Luxury resort tennis courts with Red Sea views. Perfect for vacation tennis.'
                        }
                    ]
                },
                {
                    'name': 'Yossi Kaplan',
                    'email': 'ykaplan@netanyatennis.com',
                    'phone': '+972-50-5678901',
                    'courts': [
                        {
                            'name': 'Netanya Beach Club',
                            'location': 'Netanya, Israel',
                            'court_type': 'outdoor',
                            'surface': 'clay',
                            'hourly_rate': 140.0,
                            'description': 'Beautiful clay courts near the beach. Ocean breeze for perfect playing conditions.'
                        },
                        {
                            'name': 'Indoor Court Netanya',
                            'location': 'Netanya, Israel',
                            'court_type': 'indoor',
                            'surface': 'hard',
                            'hourly_rate': 160.0,
                            'description': 'Climate-controlled indoor court. Play year-round regardless of weather.'
                        }
                    ]
                },
                {
                    'name': 'Amir Rosenberg',
                    'email': 'arosenberg@beershevatennis.com',
                    'phone': '+972-50-6789012',
                    'courts': [
                        {
                            'name': 'Desert Tennis Academy',
                            'location': 'Beer Sheva, Israel',
                            'court_type': 'indoor',
                            'surface': 'hard',
                            'hourly_rate': 130.0,
                            'description': 'Modern indoor facility in the desert. Professional coaching available.'
                        }
                    ]
                }
            ]
            
            # Create new owners and courts
            for owner_data in new_owners_data:
                # Check if owner exists
                if User.query.filter_by(email=owner_data['email']).first():
                    continue
                    
                owner = User(
                    full_name=owner_data['name'],
                    email=owner_data['email'],
                    password='demo123',
                    user_type='owner',
                    phone_number=owner_data['phone']
                )
                db.session.add(owner)
                db.session.flush()
                added_owners += 1
                
                for court_data in owner_data['courts']:
                    court = Court(
                        owner_id=owner.id,
                        name=court_data['name'],
                        location=court_data['location'],
                        court_type=court_data['court_type'],
                        surface=court_data['surface'],
                        hourly_rate=court_data['hourly_rate'],
                        description=court_data['description']
                    )
                    court.is_active = True
                    db.session.add(court)
                    added_courts += 1
                
                print(f"  Added owner: {owner_data['name']} with {len(owner_data['courts'])} courts")
            
            # Add diverse players from different cities and skill levels
            new_players_data = [
                # Advanced players (4.0-4.5)
                {"name": "Elena Petrov", "email": "elena.petrov@gmail.com", "skill": "4.5", "location": "Tel Aviv", "bio": "Former professional player, now enjoys competitive matches"},
                {"name": "Marcus Chen", "email": "marcus.chen@outlook.com", "skill": "4.0", "location": "Haifa", "bio": "Tournament player seeking strong opponents"},
                {"name": "Isabella Santos", "email": "isabella.santos@yahoo.com", "skill": "4.5", "location": "Jerusalem", "bio": "Tennis coach and competitive player"},
                {"name": "Ahmed Hassan", "email": "ahmed.hassan@gmail.com", "skill": "4.0", "location": "Eilat", "bio": "University tennis team captain"},
                {"name": "Sofia Volkova", "email": "sofia.volkova@hotmail.com", "skill": "4.5", "location": "Netanya", "bio": "Former national team member"},
                
                # Intermediate players (3.0-3.5)
                {"name": "David Martinez", "email": "david.martinez@gmail.com", "skill": "3.5", "location": "Tel Aviv", "bio": "Weekend warrior looking for fun matches"},
                {"name": "Leah Kim", "email": "leah.kim@outlook.com", "skill": "3.0", "location": "Haifa", "bio": "Improving player seeking regular practice partners"},
                {"name": "Ryan O'Connor", "email": "ryan.oconnor@yahoo.com", "skill": "3.5", "location": "Jerusalem", "bio": "Business professional who plays evenings"},
                {"name": "Maya Goldstein", "email": "maya.goldstein@gmail.com", "skill": "3.0", "location": "Beer Sheva", "bio": "Medical student with flexible schedule"},
                {"name": "Carlos Rodriguez", "email": "carlos.rodriguez@hotmail.com", "skill": "3.5", "location": "Netanya", "bio": "Enthusiastic player improving technique"},
                {"name": "Anna Popov", "email": "anna.popov@gmail.com", "skill": "3.0", "location": "Eilat", "bio": "Resort worker who plays after shifts"},
                
                # Beginner/Recreational players (2.0-2.5)
                {"name": "Tom Wilson", "email": "tom.wilson@outlook.com", "skill": "2.5", "location": "Tel Aviv", "bio": "New to tennis, eager to learn and improve"},
                {"name": "Sarah Brown", "email": "sarah.brown@yahoo.com", "skill": "2.0", "location": "Haifa", "bio": "Complete beginner taking lessons"},
                {"name": "Michael Taylor", "email": "michael.taylor@gmail.com", "skill": "2.5", "location": "Jerusalem", "bio": "Returning to tennis after many years"},
                {"name": "Luna Zhang", "email": "luna.zhang@hotmail.com", "skill": "2.0", "location": "Beer Sheva", "bio": "University student learning tennis for fun"},
                {"name": "Gabriel Silva", "email": "gabriel.silva@gmail.com", "skill": "2.5", "location": "Netanya", "bio": "Casual player who enjoys social games"},
                
                # Mixed skill levels for variety
                {"name": "Yuki Tanaka", "email": "yuki.tanaka@outlook.com", "skill": "3.5", "location": "Tel Aviv", "bio": "Japanese exchange student, loves tennis"},
                {"name": "Omar Ali", "email": "omar.ali@yahoo.com", "skill": "4.0", "location": "Haifa", "bio": "Engineering student with competitive spirit"},
                {"name": "Zoe Anderson", "email": "zoe.anderson@gmail.com", "skill": "3.0", "location": "Eilat", "bio": "Travel blogger who plays tennis worldwide"},
                {"name": "Hassan Ibrahim", "email": "hassan.ibrahim@hotmail.com", "skill": "3.5", "location": "Beer Sheva", "bio": "Local business owner, plays weekends"},
                {"name": "Emma Thompson", "email": "emma.thompson@outlook.com", "skill": "4.0", "location": "Jerusalem", "bio": "Teacher who plays after school hours"}
            ]
            
            # Create new players
            for player_data in new_players_data:
                # Check if player exists
                if User.query.filter_by(email=player_data['email']).first():
                    continue
                    
                user = User(
                    full_name=player_data['name'],
                    email=player_data['email'],
                    password='demo123',
                    user_type='player',
                    phone_number='+972-50-0000000'
                )
                db.session.add(user)
                db.session.flush()
                
                player = Player(
                    user_id=user.id,
                    skill_level=player_data['skill'],
                    preferred_location=player_data['location'],
                    bio=player_data['bio']
                )
                db.session.add(player)
                added_players += 1
                
            db.session.commit()
            
            print(f"\nSuccessfully added:")
            print(f"  New owners: {added_owners}")
            print(f"  New courts: {added_courts}")
            print(f"  New players: {added_players}")
            
            # Final counts
            total_users = User.query.count()
            total_players = User.query.filter_by(user_type='player').count()
            total_owners = User.query.filter_by(user_type='owner').count()
            total_courts = Court.query.count()
            
            print(f"\nTotal in database now:")
            print(f"  Users: {total_users}")
            print(f"  Players: {total_players}")
            print(f"  Owners: {total_owners}")
            print(f"  Courts: {total_courts}")
            
            print(f"\nSkill level distribution:")
            beginner = User.query.join(Player).filter(Player.skill_level.in_(['2.0', '2.5'])).count()
            intermediate = User.query.join(Player).filter(Player.skill_level.in_(['3.0', '3.5'])).count()
            advanced = User.query.join(Player).filter(Player.skill_level.in_(['4.0', '4.5'])).count()
            
            print(f"  Beginner (2.0-2.5): {beginner} players")
            print(f"  Intermediate (3.0-3.5): {intermediate} players")
            print(f"  Advanced (4.0-4.5): {advanced} players")
            
            print(f"\nYou can now test the matching algorithm with diverse players!")
            return True
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    add_rich_data()