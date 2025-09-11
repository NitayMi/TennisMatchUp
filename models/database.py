from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Import all models to ensure they are registered
        from models.user import User
        from models.player import Player
        from models.court import Court, Booking
        from models.message import Message
        from models.shared_booking import SharedBooking
        
        # Create all tables
        db.create_all()
        
        # Create default admin user if it doesn't exist
        create_default_admin()
        
        # Create demo data for development
        create_demo_data()
        
        print("Database initialized successfully!")

def create_default_admin():
    """Create default admin user for development"""
    from models.user import User
    
    admin_email = 'admin@tennismatchup.com'
    admin = User.query.filter_by(email=admin_email).first()
    
    if not admin:
        admin = User(
            full_name='System Administrator',
            email=admin_email,
            password='admin123',
            user_type='admin',
            phone_number='+1-555-0100'
        )
        db.session.add(admin)
        
        # Create basic demo users
        create_basic_demo_users()
        
        db.session.commit()
        print(f"Default admin created: {admin_email} / admin123")
    else:
        print("Admin user already exists")

def create_basic_demo_users():
    """Create basic demo users for testing"""
    from models.user import User
    from models.player import Player
    from models.court import Court
    
    demo_users = [
        {
            'full_name': 'John Player',
            'email': 'player@demo.com',
            'password': 'password123',
            'user_type': 'player',
            'phone_number': '+1-555-0101'
        },
        {
            'full_name': 'Sarah Owner',
            'email': 'owner@demo.com', 
            'password': 'password123',
            'user_type': 'owner',
            'phone_number': '+1-555-0102'
        }
    ]
    
    for user_data in demo_users:
        existing_user = User.query.filter_by(email=user_data['email']).first()
        if not existing_user:
            user = User(**user_data)
            db.session.add(user)
            db.session.flush()  # Get the user ID
            
            # Create player profile if user is a player
            if user.user_type == 'player':
                player = Player(
                    user_id=user.id,
                    skill_level='intermediate',
                    preferred_location='Tel Aviv',
                    availability='flexible',
                    bio='Demo player account for testing'
                )
                db.session.add(player)
            
            # Create demo court if user is an owner
            elif user.user_type == 'owner':
                court = Court(
                    owner_id=user.id,
                    name='Demo Tennis Court',
                    location='Tel Aviv',
                    court_type='outdoor',
                    surface='hard',
                    hourly_rate=80.0,
                    description='Demo court for testing the system'
                )
                court.has_lighting = True
                court.has_parking = True
                court.amenities = 'Lighting, Parking'
                db.session.add(court)

def create_demo_data():
    """Create comprehensive demo data"""
    from services.demo_data import DemoDataService
    
    # Only create demo data if we don't have many users already
    from models.user import User
    user_count = User.query.count()
    
    if user_count <= 3:  # Only admin + basic demo users
        print("Creating comprehensive demo data...")
        try:
            results = DemoDataService.populate_all_demo_data()
            print(f"Demo data created: {results}")
        except Exception as e:
            print(f"Error creating demo data: {e}")
    else:
        print("Demo data already exists, skipping creation")

def reset_database():
    """Reset database (for development only)"""
    db.drop_all()
    db.create_all()
    create_default_admin()
    print("Database reset completed!")

def seed_sample_data():
    """Add sample data for development/testing"""
    from models.user import User
    from models.player import Player
    from models.court import Court, Booking
    from datetime import date, time, datetime, timedelta
    
    # Get demo users
    player_user = User.query.filter_by(email='player@demo.com').first()
    owner_user = User.query.filter_by(email='owner@demo.com').first()
    
    if not player_user or not owner_user:
        print("Demo users not found. Run create_default_admin() first.")
        return
    
    # Get player and court
    player = Player.query.filter_by(user_id=player_user.id).first()
    court = Court.query.filter_by(owner_id=owner_user.id).first()
    
    if player and court:
        # Create sample bookings
        sample_bookings = [
            {
                'court_id': court.id,
                'player_id': player.id,
                'booking_date': date.today() + timedelta(days=1),
                'start_time': time(14, 0),
                'end_time': time(16, 0),
                'status': 'confirmed',
                'notes': 'Looking forward to the game!'
            },
            {
                'court_id': court.id,
                'player_id': player.id,
                'booking_date': date.today() + timedelta(days=3),
                'start_time': time(10, 0),
                'end_time': time(11, 30),
                'status': 'pending',
                'notes': 'Weekend match with friends'
            }
        ]
        
        for booking_data in sample_bookings:
            existing_booking = Booking.query.filter_by(
                court_id=booking_data['court_id'],
                booking_date=booking_data['booking_date'],
                start_time=booking_data['start_time']
            ).first()
            
            if not existing_booking:
                booking = Booking(**booking_data)
                booking.total_cost = booking.calculate_cost()
                db.session.add(booking)
        
        db.session.commit()
        print("Sample data created successfully!")
    
    print("Database seeding completed!")

