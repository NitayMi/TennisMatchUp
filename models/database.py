from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

def init_db():
    """Initialize database tables"""
    from models.user import User
    from models.player import PlayerProfile
    from models.court import Court, BookingRequest
    from models.message import Message
    
    # Create all tables
    db.create_all()
    
    # Create default admin user if none exists
    admin = User.query.filter_by(user_type='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@tennismatchup.com',
            user_type='admin',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Created default admin user: admin/admin123")
    
    print("Database initialized successfully!")

class TimestampMixin:
    """Mixin to add timestamp fields to models"""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)