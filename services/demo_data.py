from models.database import db
from models.user import User
from models.player import Player
from models.court import Court
from models.message import Message
import random
from datetime import datetime, date, time, timedelta

class DemoDataService:
    """Service to populate demo data for testing and development"""
    
    @staticmethod
    def populate_all_demo_data():
        """Populate all types of demo data"""
        results = {}
        
        try:
            # Create demo players
            players_created = DemoDataService.create_demo_players()
            results['players'] = players_created
            
            # Create demo courts
            courts_created = DemoDataService.create_demo_courts()
            results['courts'] = courts_created
            
            # Create demo messages
            messages_created = DemoDataService.create_demo_messages()
            results['messages'] = messages_created
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            results['error'] = str(e)
            
        return results
    
    @staticmethod
    def create_demo_players():
        """Create diverse demo tennis players"""
        
        demo_players = [
            # Tel Aviv Players
            {
                'full_name': 'Sarah Cohen',
                'email': 'sarah.cohen@demo.com',
                'password': 'password123',
                'phone_number': '+972-50-123-4567',
                'skill_level': 'intermediate',
                'preferred_location': 'Tel Aviv',
                'availability': 'weekends',
                'bio': 'Love playing doubles! Looking for consistent playing partners for weekend matches.'
            },
            {
                'full_name': 'David Levy',
                'email': 'david.levy@demo.com', 
                'password': 'password123',
                'phone_number': '+972-50-765-4321',
                'skill_level': 'advanced',
                'preferred_location': 'Tel Aviv',
                'availability': 'evenings',
                'bio': 'Former university player. Enjoy competitive singles and coaching others.'
            },
            {
                'full_name': 'Maya Goldstein',
                'email': 'maya.gold@demo.com',
                'password': 'password123',
                'phone_number': '+972-54-111-2233',
                'skill_level': 'beginner',
                'preferred_location': 'Tel Aviv',
                'availability': 'flexible',
                'bio': 'Just started playing tennis this year. Looking for patient players to practice with!'
            },
            
            # Haifa Players  
            {
                'full_name': 'Ron Shapira',
                'email': 'ron.shapira@demo.com',
                'password': 'password123',
                'phone_number': '+972-52-888-9999',
                'skill_level': 'professional',
                'preferred_location': 'Haifa',
                'availability': 'weekdays',
                'bio': 'Tennis coach with 15+ years experience. Always up for challenging matches.'
            },
            {
                'full_name': 'Noa Ben-David',
                'email': 'noa.bd@demo.com',
                'password': 'password123',
                'phone_number': '+972-53-445-6677',
                'skill_level': 'intermediate',
                'preferred_location': 'Haifa',
                'availability': 'evenings',
                'bio': 'Played in high school, getting back into tennis. Love the mental game!'
            },
            
            # Jerusalem Players
            {
                'full_name': 'Alex Rosenberg', 
                'email': 'alex.rose@demo.com',
                'password': 'password123',
                'phone_number': '+972-50-333-4455',
                'skill_level': 'advanced',
                'preferred_location': 'Jerusalem',
                'availability': 'weekends',
                'bio': 'Aggressive baseline player. Looking for competitive weekend matches.'
            },
            {
                'full_name': 'Shira Mizrahi',
                'email': 'shira.m@demo.com',
                'password': 'password123',
                'phone_number': '+972-54-777-8888',
                'skill_level': 'beginner',
                'preferred_location': 'Jerusalem',
                'availability': 'flexible',
                'bio': 'New to tennis but love the sport! Happy to practice with anyone patient.'
            },
            
            # Ramat Gan Players
            {
                'full_name': 'Yael Katz',
                'email': 'yael.katz@demo.com',
                'password': 'password123',
                'phone_number': '+972-52-666-7777',
                'skill_level': 'intermediate',
                'preferred_location': 'Ramat Gan',
                'availability': 'weekdays',
                'bio': 'Work flexible hours, can play during the day. Prefer doubles format.'
            },
            {
                'full_name': 'Omer Tal',
                'email': 'omer.tal@demo.com',
                'password': 'password123',
                'phone_number': '+972-50-999-0000',
                'skill_level': 'advanced',
                'preferred_location': 'Ramat Gan',
                'availability': 'evenings',
                'bio': 'Playing for 10 years. Serve and volley style, looking for fast-paced matches.'
            },
            
            # Diverse Players
            {
                'full_name': 'Emma Johnson',
                'email': 'emma.j@demo.com',
                'password': 'password123',
                'phone_number': '+972-54-123-9876',
                'skill_level': 'intermediate',
                'preferred_location': 'Tel Aviv',
                'availability': 'flexible',
                'bio': 'American expat who loves tennis. Always looking for fun social matches!'
            },
            {
                'full_name': 'Chen Wang',
                'email': 'chen.wang@demo.com',
                'password': 'password123',
                'phone_number': '+972-53-246-8135',
                'skill_level': 'advanced',
                'preferred_location': 'Herzliya',
                'availability': 'weekends',
                'bio': 'Tech worker who plays tennis for stress relief. Consistent and reliable player.'
            },
            {
                'full_name': 'Antonio Silva',
                'email': 'antonio.s@demo.com',
                'password': 'password123',
                'phone_number': '+972-52-147-2583',
                'skill_level': 'professional',
                'preferred_location': 'Tel Aviv',
                'availability': 'weekdays',
                'bio': 'Former professional player from Brazil. Now teaching and playing recreationally.'
            },
            {
                'full_name': 'Rachel Green',
                'email': 'rachel.green@demo.com',
                'password': 'password123',
                'phone_number': '+972-50-369-2581',
                'skill_level': 'beginner',
                'preferred_location': 'Netanya',
                'availability': 'weekends',
                'bio': 'Just picked up tennis after moving to Israel. Looking for beginner-friendly groups.'
            }
        ]
        
        created_count = 0
        
        for player_data in demo_players:
            # Check if user already exists
            existing_user = User.query.filter_by(email=player_data['email']).first()
            if not existing_user:
                # Create user
                user = User(
                    full_name=player_data['full_name'],
                    email=player_data['email'],
                    password=player_data['password'],
                    user_type='player',
                    phone_number=player_data.get('phone_number')
                )
                db.session.add(user)
                db.session.flush()  # Get user ID
                
                # Create player profile
                player = Player(
                    user_id=user.id,
                    skill_level=player_data['skill_level'],
                    preferred_location=player_data['preferred_location'],
                    availability=player_data['availability'],
                    bio=player_data['bio']
                )
                
                # Add some additional optional fields with randomization
                player.years_playing = random.randint(1, 20)
                player.max_travel_distance = random.randint(10, 50)
                
                # Set playing style based on skill level
                styles = ['aggressive', 'defensive', 'all-court']
                if player_data['skill_level'] in ['advanced', 'professional']:
                    player.playing_style = random.choice(['aggressive', 'all-court'])
                else:
                    player.playing_style = random.choice(styles)
                
                # Set court preferences
                surfaces = ['hard', 'clay', 'grass']
                player.preferred_court_type = random.choice(surfaces)
                
                db.session.add(player)
                created_count += 1
                
        return created_count
    
    @staticmethod
    def create_demo_courts():
        """Create demo tennis courts for testing"""
        
        # Get some owners (create if needed)
        demo_owners = [
            {
                'full_name': 'Tennis Club Manager',
                'email': 'manager@tennisclub.com',
                'password': 'password123',
                'phone_number': '+972-50-100-2000'
            },
            {
                'full_name': 'Sports Center Owner',
                'email': 'owner@sportscenter.com',
                'password': 'password123',
                'phone_number': '+972-52-200-3000'
            }
        ]
        
        owners_created = 0
        for owner_data in demo_owners:
            existing_owner = User.query.filter_by(email=owner_data['email']).first()
            if not existing_owner:
                owner = User(
                    full_name=owner_data['full_name'],
                    email=owner_data['email'],
                    password=owner_data['password'],
                    user_type='owner',
                    phone_number=owner_data.get('phone_number')
                )
                db.session.add(owner)
                owners_created += 1
        
        db.session.flush()  # Get owner IDs
        
        # Get all owners
        all_owners = User.query.filter_by(user_type='owner').all()
        if not all_owners:
            return 0
        
        demo_courts = [
            {
                'name': 'Hayarkon Tennis Center',
                'location': 'Tel Aviv',
                'court_type': 'outdoor',
                'surface': 'hard',
                'hourly_rate': 120.0,
                'description': 'Professional outdoor hard court with excellent lighting and parking.',
                'amenities': 'Lighting, Parking, Equipment Rental, Showers'
            },
            {
                'name': 'Ramat Aviv Indoor Courts',
                'location': 'Tel Aviv', 
                'court_type': 'indoor',
                'surface': 'hard',
                'hourly_rate': 150.0,
                'description': 'Climate-controlled indoor facility, perfect for year-round play.',
                'amenities': 'Air Conditioning, Parking, Pro Shop, Showers'
            },
            {
                'name': 'Haifa Bay Tennis Club',
                'location': 'Haifa',
                'court_type': 'outdoor',
                'surface': 'clay',
                'hourly_rate': 100.0,
                'description': 'Beautiful clay courts with sea view. Traditional European-style tennis.',
                'amenities': 'Sea View, Parking, Restaurant, Equipment Rental'
            },
            {
                'name': 'Jerusalem Sports Complex',
                'location': 'Jerusalem',
                'court_type': 'outdoor',
                'surface': 'hard',
                'hourly_rate': 90.0,
                'description': 'Community sports facility with well-maintained courts.',
                'amenities': 'Lighting, Parking, Cafeteria'
            },
            {
                'name': 'Herzliya Premium Courts',
                'location': 'Herzliya',
                'court_type': 'outdoor',
                'surface': 'grass',
                'hourly_rate': 200.0,
                'description': 'Exclusive grass courts for the ultimate tennis experience.',
                'amenities': 'Grass Courts, Valet Parking, Clubhouse, Pro Shop'
            }
        ]
        
        courts_created = 0
        for court_data in demo_courts:
            # Check if court already exists
            existing_court = Court.query.filter_by(
                name=court_data['name'],
                location=court_data['location']
            ).first()
            
            if not existing_court:
                # Assign to a random owner
                owner = random.choice(all_owners)
                
                court = Court(
                    owner_id=owner.id,
                    name=court_data['name'],
                    location=court_data['location'],
                    court_type=court_data['court_type'],
                    surface=court_data['surface'],
                    hourly_rate=court_data['hourly_rate'],
                    description=court_data['description']
                )
                
                # Set amenities and features
                court.amenities = court_data['amenities']
                court.has_lighting = 'Lighting' in court_data['amenities']
                court.has_parking = 'Parking' in court_data['amenities']
                court.has_equipment_rental = 'Equipment Rental' in court_data['amenities']
                court.has_changing_rooms = 'Showers' in court_data['amenities']
                court.is_active = True
                
                db.session.add(court)
                courts_created += 1
                
        return courts_created
    
    @staticmethod
    def create_demo_messages():
        """Create some demo messages between players"""
        
        # Get some players for messaging
        players = User.query.filter_by(user_type='player').limit(5).all()
        
        if len(players) < 2:
            return 0
        
        messages_created = 0
        
        # Create some example conversations
        demo_messages = [
            {
                'sender_email': 'sarah.cohen@demo.com',
                'receiver_email': 'david.levy@demo.com',
                'content': 'Hi David! I saw your profile and we seem to have similar availability. Would you like to play doubles this weekend?'
            },
            {
                'sender_email': 'david.levy@demo.com', 
                'receiver_email': 'sarah.cohen@demo.com',
                'content': 'Hi Sarah! That sounds great. I know a nice court in Tel Aviv. Are you free Saturday morning?'
            },
            {
                'sender_email': 'maya.gold@demo.com',
                'receiver_email': 'shira.m@demo.com',
                'content': 'Hey! I noticed you\'re also a beginner. Want to practice together sometime?'
            },
            {
                'sender_email': 'ron.shapira@demo.com',
                'receiver_email': 'alex.rose@demo.com',
                'content': 'Looking for a challenging match this week. Interested in playing?'
            }
        ]
        
        for msg_data in demo_messages:
            sender = User.query.filter_by(email=msg_data['sender_email']).first()
            receiver = User.query.filter_by(email=msg_data['receiver_email']).first()
            
            if sender and receiver:
                message = Message(
                    sender_id=sender.id,
                    receiver_id=receiver.id,
                    content=msg_data['content']
                )
                
                # Make some messages older
                message.created_at = datetime.utcnow() - timedelta(
                    hours=random.randint(1, 48)
                )
                
                db.session.add(message)
                messages_created += 1
                
        return messages_created
    
    @staticmethod
    def reset_demo_data():
        """Reset all demo data (use with caution!)"""
        
        # Delete all non-admin users and their related data
        demo_users = User.query.filter(User.user_type != 'admin').all()
        
        for user in demo_users:
            # Delete related data first
            if user.player_profile:
                db.session.delete(user.player_profile)
            
            # Delete courts owned by this user
            for court in user.owned_courts:
                db.session.delete(court)
            
            # Delete messages
            Message.query.filter(
                db.or_(Message.sender_id == user.id, Message.receiver_id == user.id)
            ).delete()
            
            # Delete user
            db.session.delete(user)
        
        db.session.commit()
        
        return len(demo_users)