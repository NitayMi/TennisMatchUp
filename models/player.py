from models.database import db
from datetime import datetime

class Player(db.Model):
    """Player profile model for tennis players"""
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    skill_level = db.Column(db.String(20), nullable=False)  # beginner, intermediate, advanced, professional
    preferred_location = db.Column(db.String(100), nullable=True)
    availability = db.Column(db.String(50), nullable=True)  # weekdays, weekends, evenings, flexible
    bio = db.Column(db.Text, nullable=True)
    profile_image_url = db.Column(db.String(500), nullable=True)
    playing_style = db.Column(db.String(50), nullable=True)  # aggressive, defensive, all-court
    preferred_court_type = db.Column(db.String(20), nullable=True)  # clay, hard, grass
    years_playing = db.Column(db.Integer, nullable=True)
    rating = db.Column(db.Float, nullable=True)  # NTRP or similar rating
    is_looking_for_partner = db.Column(db.Boolean, default=True, nullable=False)
    max_travel_distance = db.Column(db.Integer, default=25, nullable=True)  # km
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Geographic fields for accurate matching
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_updated_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    bookings = db.relationship('Booking', backref='player', cascade='all, delete-orphan')
    
    def __init__(self, user_id, skill_level, preferred_location=None, availability=None, bio=None):
        self.user_id = user_id
        self.skill_level = skill_level
        self.preferred_location = preferred_location
        self.availability = availability
        self.bio = bio
        self.is_looking_for_partner = True
    
    def get_skill_level_display(self):
        """Get formatted skill level"""
        skill_mapping = {
            'beginner': 'Beginner',
            'intermediate': 'Intermediate', 
            'advanced': 'Advanced',
            'professional': 'Professional'
        }
        return skill_mapping.get(self.skill_level, self.skill_level.title())
    
    def get_availability_display(self):
        """Get formatted availability"""
        availability_mapping = {
            'weekdays': 'Weekdays',
            'weekends': 'Weekends',
            'evenings': 'Evenings',
            'flexible': 'Flexible'
        }
        return availability_mapping.get(self.availability, self.availability.title() if self.availability else 'Not specified')
    
    def get_compatibility_score(self, other_player):
        """Calculate compatibility score with another player"""
        score = 100
        
        # Skill level compatibility
        skill_levels = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'professional': 4}
        skill_diff = abs(skill_levels.get(self.skill_level, 2) - skill_levels.get(other_player.skill_level, 2))
        score -= skill_diff * 25
        
        # Location compatibility
        if self.preferred_location and other_player.preferred_location:
            if self.preferred_location.lower() != other_player.preferred_location.lower():
                score -= 20
        
        # Availability compatibility
        if self.availability and other_player.availability:
            if self.availability != other_player.availability:
                score -= 15
        
        return max(0, score)
    
    def update_coordinates(self):
        """Update player coordinates based on preferred location"""
        from services.geo_service import GeoService
        
        if self.preferred_location:
            coordinates = GeoService.get_coordinates(self.preferred_location)
            if coordinates:
                self.latitude = coordinates[0]
                self.longitude = coordinates[1]
                self.location_updated_at = datetime.now()
                return True
        return False
    
    def get_coordinates(self):
        """Get player coordinates as tuple"""
        if self.latitude and self.longitude:
            return (self.latitude, self.longitude)
        return None
    
    def distance_to(self, other_player):
        """Calculate distance to another player"""
        from services.geo_service import GeoService
        
        my_coords = self.get_coordinates()
        other_coords = other_player.get_coordinates()
        
        if my_coords and other_coords:
            return GeoService.calculate_distance_km(my_coords, other_coords)
        return None
    
    def to_dict(self):
        """Convert player to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'skill_level': self.skill_level,
            'skill_level_display': self.get_skill_level_display(),
            'preferred_location': self.preferred_location,
            'availability': self.availability,
            'availability_display': self.get_availability_display(),
            'bio': self.bio,
            'profile_image_url': self.profile_image_url,
            'playing_style': self.playing_style,
            'preferred_court_type': self.preferred_court_type,
            'years_playing': self.years_playing,
            'rating': self.rating,
            'is_looking_for_partner': self.is_looking_for_partner,
            'max_travel_distance': self.max_travel_distance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Player {self.user.full_name if self.user else "Unknown"} ({self.skill_level})>'