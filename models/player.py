from models.database import db, TimestampMixin
from sqlalchemy import CheckConstraint

class PlayerProfile(db.Model, TimestampMixin):
    """Extended profile for tennis players"""
    __tablename__ = 'player_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Tennis-specific information
    skill_level = db.Column(db.Integer, nullable=False, default=1)  # 1-10 scale
    playing_style = db.Column(db.Enum('offensive', 'defensive', 'all_around', 
                                    name='playing_styles'), default='all_around')
    dominant_hand = db.Column(db.Enum('right', 'left', 'ambidextrous', 
                                     name='dominant_hands'), default='right')
    
    # Availability and preferences
    preferred_times = db.Column(db.Text)  # JSON string of preferred days/times
    bio = db.Column(db.Text)
    max_travel_distance = db.Column(db.Integer, default=10)  # km
    
    # Player statistics
    matches_played = db.Column(db.Integer, default=0)
    matches_won = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    
    # Preferences
    preferred_court_type = db.Column(db.Enum('hard', 'clay', 'grass', 'indoor', 'any', 
                                           name='court_types'), default='any')
    budget_range = db.Column(db.String(20))  # e.g., "50-100"
    
    # Relationships
    sent_match_requests = db.relationship('MatchRequest', foreign_keys='MatchRequest.requester_id',
                                        backref='requester', lazy='dynamic')
    received_match_requests = db.relationship('MatchRequest', foreign_keys='MatchRequest.target_id',
                                            backref='target', lazy='dynamic')
    
    __table_args__ = (
        CheckConstraint('skill_level >= 1 AND skill_level <= 10', 
                       name='valid_skill_level'),
        CheckConstraint('matches_won <= matches_played', 
                       name='valid_win_count'),
    )
    
    def __repr__(self):
        return f'<PlayerProfile {self.user.username}, Level {self.skill_level}>'
    
    def get_win_rate(self):
        """Calculate win rate percentage"""
        if self.matches_played == 0:
            return 0.0
        return round((self.matches_won / self.matches_played) * 100, 1)
    
    def get_skill_description(self):
        """Get human-readable skill level"""
        skill_map = {
            1: "Beginner",
            2: "Novice", 
            3: "Beginner+",
            4: "Intermediate-",
            5: "Intermediate",
            6: "Intermediate+", 
            7: "Advanced-",
            8: "Advanced",
            9: "Expert",
            10: "Professional"
        }
        return skill_map.get(self.skill_level, "Unknown")
    
    def can_match_with(self, other_player, max_level_diff=2):
        """Check if this player can match with another player"""
        if not isinstance(other_player, PlayerProfile):
            return False
        
        # Check skill level compatibility
        level_diff = abs(self.skill_level - other_player.skill_level)
        if level_diff > max_level_diff:
            return False
        
        return True
    
    def get_pending_requests_count(self):
        """Get count of pending match requests sent by this player"""
        return self.sent_match_requests.filter_by(status='pending').count()
    
    def get_received_requests_count(self):
        """Get count of pending requests received by this player"""
        return self.received_match_requests.filter_by(status='pending').count()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'skill_level': self.skill_level,
            'skill_description': self.get_skill_description(),
            'playing_style': self.playing_style,
            'dominant_hand': self.dominant_hand,
            'bio': self.bio,
            'matches_played': self.matches_played,
            'matches_won': self.matches_won,
            'win_rate': self.get_win_rate(),
            'city': self.user.city,
            'display_name': self.user.get_display_name()
        }

class MatchRequest(db.Model, TimestampMixin):
    """Match requests between players"""
    __tablename__ = 'match_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('player_profiles.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('player_profiles.id'), nullable=False)
    
    status = db.Column(db.Enum('pending', 'accepted', 'declined', 'cancelled', 
                              name='match_statuses'), default='pending')
    message = db.Column(db.Text)
    
    # Proposed match details
    preferred_date = db.Column(db.Date)
    preferred_time = db.Column(db.Time)
    suggested_court_id = db.Column(db.Integer, db.ForeignKey('courts.id'))
    
    # Response details
    response_message = db.Column(db.Text)
    responded_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<MatchRequest {self.requester.user.username} -> {self.target.user.username}>'
    
    def is_pending(self):
        """Check if request is still pending"""
        return self.status == 'pending'
    
    def can_be_responded_to(self):
        """Check if request can still be responded to"""
        return self.status == 'pending'
    
    def accept(self, response_message=None):
        """Accept the match request"""
        if self.can_be_responded_to():
            self.status = 'accepted'
            self.response_message = response_message
            self.responded_at = db.func.now()
            return True
        return False
    
    def decline(self, response_message=None):
        """Decline the match request"""
        if self.can_be_responded_to():
            self.status = 'declined' 
            self.response_message = response_message
            self.responded_at = db.func.now()
            return True
        return False