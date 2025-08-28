from models.database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """User model for all user types"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    user_type = db.Column(db.String(20), nullable=False)  # player, owner, admin
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    player_profile = db.relationship('Player', backref='user', uselist=False, cascade='all, delete-orphan')
    owned_courts = db.relationship('Court', backref='owner', cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', cascade='all, delete-orphan')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', cascade='all, delete-orphan')
    
    def __init__(self, full_name, email, password, user_type, phone_number=None):
        self.full_name = full_name
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.user_type = user_type
        self.phone_number = phone_number
        self.is_active = True
    
    def check_password(self, password):
        """Check if provided password matches stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """Set new password"""
        self.password_hash = generate_password_hash(password)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'user_type': self.user_type,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<User {self.full_name} ({self.email})>'