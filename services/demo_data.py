"""
Demo data service for TennisMatchUp
Creates realistic test data for development
"""
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court, Booking
from models.message import Message
from datetime import date, time, datetime, timedelta
import random

class DemoDataService:
    """Service for creating demo data"""
    
    @staticmethod
    def create_demo_players(count=15):
        """Create demo players for testing"""
        demo_players = [
            {
                'full_name': 'Sarah Johnson',
                'email': 'sarah.j@demo.com',
                'skill_level': 'intermediate',
                'location': 'Tel Aviv',
                'availability': 'evenings',
                'bio': 'Love playing after work, looking for consistent partner'
            },
            {
                'full_name': 'Michael Chen',
                'email': 'mike.chen@demo.com', 
                'skill_level': 'advanced',
                'location': 'Tel Aviv',
                'availability': 'flexible',
                'bio': 'Competitive player, enjoy both singles and doubles'
            },
            {
                'full_name': 'Emma Rodriguez',
                'email': 'emma.r@demo.com',
                'skill_level': 'beginner',
                'location': 'Haifa',
                'availability': 'weekends',
                'bio': 'New to tennis, eager to learn and improve'
            },
            {
                'full_name': 'David Kim',
                'email': 'david.kim@demo.com',
                'skill_level': 'intermediate',
                'location': 'Jerusalem',
                'availability': 'weekdays',
                'bio': 'Morning player, prefer playing before 10 AM'
            },
            {
                'full_name': 'Lisa Thompson',
                'email': 'lisa.t@demo.com',
                'skill_level': 'professional',
                'location': 'Tel Aviv',
                'availability': 'flexible',
                'bio': 'Former college player, looking for challenging matches'
            },
            {
                'full_name': 'Ahmed Hassan',
                'email': 'ahmed.h@demo.com',
                'skill_level': 'advanced',
                'location': 'Haifa',
                'availability': 'weekends',
                'bio': 'Weekend warrior, love long rallies and baseline play'
            },
            {
                'full_name': 'Rachel Green',
                'email': 'rachel.g@demo.com',
                'skill_level': 'beginner',
                'location': 'Tel Aviv',
                'availability': 'evenings',
                'bio': 'Just started playing, looking for patient partner'
            },
            {
                'full_name': 'Carlos Martinez',
                'email': 'carlos.m@demo.com',
                'skill_level': 'intermediate',
                'location': 'Jerusalem',
                'availability': 'flexible',
                'bio': 'Enjoy both competitive and casual games'
            },
            {
                'full_name': 'Anna Petrov',
                'email': 'anna.p@demo.com',
                'skill_level': 'advanced',
                'location': 'Tel Aviv',
                'availability': 'weekdays',
                'bio': 'Prefer fast-paced games, strong serve and volley'
            },
            {
                'full_name': 'James Wilson',
                'email': 'james.w@demo.com',
                'skill_level': 'intermediate',
                'location': 'Haifa',
                'availability': 'evenings',
                'bio': 'Recreational player, enjoy the social aspect'
            },
            {
                'full_name': 'Yuki Tanaka',
                'email': 'yuki.t@demo.com',
                'skill_level': 'beginner',
                'location': 'Jerusalem',
                'availability': 'weekends',
                'bio': 'Learning the basics, focus on form and technique'
            },
            {
                'full_name': 'Sofia Andersson',
                'email': 'sofia.a@demo.com',
                'skill_level': 'professional',
                'location': 'Haifa',
                'availability': 'flexible',
                'bio': 'Tournament player, always up for practice sessions'
            }
        ]
        
        created_count = 0
        for player_data in demo_players[:count]:
            # Check if user already exists
            existing_user = User.query.filter_by(email=player_data['email']).first()
            if not existing_user:
                # Create user
                user = User(
                    full_name=player_data['full_name'],
                    email=player_data['email'],
                    password='demo123',
                    user_type='player',
                    phone_number=f'+972-50-{random.randint(1000000, 9999999)}'
                )
                db.session.add(user)
                db.session.flush()
                
                # Create player profile
                player = Player(
                    user_id=user.id,
                    skill_level=player_data['skill_level'],
                    preferred_location=player_data['location'],
                    availability=player_data['availability'],
                    bio=player_data['bio']
                )
                db.session.add(player)
                created_count += 1
        
        db.session.commit()
        return created_count
    
    @staticmethod
    def create_demo_courts(count=8):
        """Create demo courts"""
        # Get or create demo owner
        owner = User.query.filter_by(email='owner@demo.com').first()
        if not owner:
            return 0
        
        demo_courts = [
            {
                'name': 'Central Tennis Club',
                'location': 'Tel Aviv',
                'court_type': 'outdoor',
                'surface': 'hard',
                'rate': 120,
                'description': 'Professional outdoor hard courts with excellent lighting'
            },
            {
                'name': 'Seaside Tennis Center',
                'location': 'Tel Aviv',
                'court_type': 'outdoor',
                'surface': 'clay',
                'rate': 100,
                'description': 'Beautiful clay courts near the beach'
            },
            {
                'name': 'Mountain View Courts',
                'location': 'Haifa',
                'court_type': 'outdoor',
                'surface': 'hard',
                'rate': 80,
                'description': 'Scenic mountain view courts with great facilities'
            },
            {
                'name': 'Indoor Tennis Palace',
                'location': 'Tel Aviv',
                'court_type': 'indoor',
                'surface': 'hard',
                'rate': 150,
                'description': 'Premium indoor facility, year-round play'
            },
            {
                'name': 'Garden Tennis Club',
                'location': 'Jerusalem',
                'court_type': 'outdoor',
                'surface': 'grass',
                'rate': 110,
                'description': 'Traditional grass courts in beautiful garden setting'
            },
            {
                'name': 'Sports Complex Courts',
                'location': 'Haifa',
                'court_type': 'indoor',
                'surface': 'hard',
                'rate': 90,
                'description': 'Modern sports complex with multiple courts'
            },
            {
                'name': 'University Tennis Courts',
                'location': 'Jerusalem',
                'court_type': 'outdoor',
                'surface': 'hard',
                'rate': 70,
                'description': 'Well-maintained courts at university campus'
            },
            {
                'name': 'Elite Tennis Academy',
                'location': 'Tel Aviv',
                'court_type': 'indoor',
                'surface': 'artificial',
                'rate': 180,
                'description': 'Professional training facility with top-quality courts'
            }
        ]
        
        created_count = 0
        for court_data in demo_courts[:count]:
            # Check if court already exists
            existing_court = Court.query.filter_by(
                owner_id=owner.id,
                name=court_data['name']
            ).first()
            
            if not existing_court:
                court = Court(
                    owner_id=owner.id,
                    name=court_data['name'],
                    location=court_data['location'],
                    court_type=court_data['court_type'],
                    surface=court_data['surface'],
                    hourly_rate=court_data['rate'],
                    description=court_data['description']
                )
                court.has_lighting = random.choice([True, False])
                court.has_parking = random.choice([True, True, False])  # More likely to have parking
                court.amenities = 'Parking, Lighting, Equipment Rental'
                db.session.add(court)
                created_count += 1
        
        db.session.commit()
        return created_count
    
    @staticmethod
    def create_demo_bookings(count=10):
        """Create demo bookings"""
        players = Player.query.limit(5).all()
        courts = Court.query.limit(3).all()
        
        if not players or not courts:
            return 0
        
        created_count = 0
        for _ in range(count):
            player = random.choice(players)
            court = random.choice(courts)
            
            # Random future date (1-14 days ahead)
            booking_date = date.today() + timedelta(days=random.randint(1, 14))
            
            # Random time slot
            start_hour = random.randint(8, 19)
            duration = random.choice([1, 1.5, 2])
            
            start_time = time(start_hour, 0)
            end_hour = start_hour + int(duration)
            end_minute = int((duration % 1) * 60)
            end_time = time(end_hour, end_minute)
            
            # Random status
            status = random.choice(['confirmed', 'confirmed', 'pending', 'confirmed'])
            
            booking = Booking(
                court_id=court.id,
                player_id=player.id,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time,
                notes=random.choice([
                    'Looking forward to the game!',
                    'Practice session',
                    'Weekly match with friend',
                    'Tournament preparation',
                    ''
                ])
            )
            booking.status = status
            booking.total_cost = booking.calculate_cost()
            
            db.session.add(booking)
            created_count += 1
        
        db.session.commit()
        return created_count
    
    @staticmethod
    def populate_all_demo_data():
        """Create all demo data at once"""
        results = {}
        
        print("Creating demo data...")
        
        # Create players
        results['players'] = DemoDataService.create_demo_players(12)
        print(f"Created {results['players']} demo players")
        
        # Create courts
        results['courts'] = DemoDataService.create_demo_courts(6)
        print(f"Created {results['courts']} demo courts")
        
        # Create bookings
        results['bookings'] = DemoDataService.create_demo_bookings(8)
        print(f"Created {results['bookings']} demo bookings")
        
        print("Demo data creation completed!")
        return results