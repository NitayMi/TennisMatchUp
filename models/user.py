from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db, TimestampMixin

class User(UserMixin, db.Model, TimestampMixin):
    """Base user model for all user types"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.Enum('player', 'owner', 'admin', name='user_types'), 
                         nullable=False, default='player')
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Profile information
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    city = db.Column(db.String(50))
    profile_picture = db.Column(db.String(200))  # URL to profile image
    
    # Relationships
    player_profile = db.relationship('PlayerProfile', backref='user', uselist=False, 
                                   cascade='all, delete-orphan')
    owned_courts = db.relationship('Court', backref='owner', lazy='dynamic',
                                 cascade='all, delete-orphan')
    booking_requests = db.relationship('BookingRequest', backref='player', lazy='dynamic')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id',
                                   backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id',
                                       backref='receiver', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_player(self):
        """Check if user is a player"""
        return self.user_type == 'player'
    
    def is_owner(self):
        """Check if user is a court owner"""
        return self.user_type == 'owner'
    
    def is_system_admin(self):
        """Check if user is system admin"""
        return self.user_type == 'admin' or self.is_admin
    
    def get_display_name(self):
        """Get display name for user"""
        return self.full_name or self.username
    
    def get_unread_messages_count(self):
        """Get count of unread messages"""
        return self.received_messages.filter_by(is_read=False).count()
    
    def can_access_admin_panel(self):
        """Check if user can access admin panel"""
        return self.is_admin or self.user_type == 'admin'
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'user_type': self.user_type,
            'full_name': self.full_name,
            'city': self.city,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }