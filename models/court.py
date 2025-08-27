from models.database import db, TimestampMixin
from sqlalchemy import CheckConstraint
from datetime import datetime, timedelta

class Court(db.Model, TimestampMixin):
    """Tennis court model"""
    __tablename__ = 'courts'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Court information
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    court_type = db.Column(db.Enum('hard', 'clay', 'grass', 'indoor', name='court_types'), 
                          default='hard')
    description = db.Column(db.Text)
    
    # Pricing and availability
    hourly_rate = db.Column(db.Numeric(8, 2), nullable=False, default=0.0)
    currency = db.Column(db.String(3), default='ILS')
    
    # Features and amenities
    has_lighting = db.Column(db.Boolean, default=False)
    has_parking = db.Column(db.Boolean, default=False) 
    has_shower = db.Column(db.Boolean, default=False)
    max_players = db.Column(db.Integer, default=4)
    
    # Operational settings
    is_active = db.Column(db.Boolean, default=True)
    auto_approve_bookings = db.Column(db.Boolean, default=False)
    advance_booking_days = db.Column(db.Integer, default=30)  # How far ahead can book
    min_booking_notice = db.Column(db.Integer, default=2)  # Minimum hours notice
    
    # Contact and images
    contact_phone = db.Column(db.String(20))
    image_urls = db.Column(db.Text)  # JSON string of image URLs
    
    # Relationships
    booking_requests = db.relationship('BookingRequest', backref='court', lazy='dynamic',
                                     cascade='all, delete-orphan')
    match_suggestions = db.relationship('MatchRequest', backref='suggested_court',
                                      foreign_keys='MatchRequest.suggested_court_id')
    
    __table_args__ = (
        CheckConstraint('hourly_rate >= 0', name='positive_rate'),
        CheckConstraint('advance_booking_days > 0', name='positive_advance_days'),
        CheckConstraint('min_booking_notice >= 0', name='positive_notice_hours'),
    )
    
    def __repr__(self):
        return f'<Court {self.name} - {self.owner.username}>'
    
    def get_display_rate(self):
        """Get formatted hourly rate"""
        return f"₪{self.hourly_rate}/hour"
    
    def is_available_at(self, date, start_time, duration_hours=1):
        """Check if court is available at specific date/time"""
        if not self.is_active:
            return False
            
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Check for conflicting bookings
        conflicting = self.booking_requests.filter(
            BookingRequest.requested_date == date,
            BookingRequest.status == 'approved',
            db.or_(
                db.and_(BookingRequest.start_time <= start_time, 
                       BookingRequest.end_time > start_time),
                db.and_(BookingRequest.start_time < end_time,
                       BookingRequest.end_time >= end_time),
                db.and_(BookingRequest.start_time >= start_time,
                       BookingRequest.end_time <= end_time)
            )
        ).first()
        
        return conflicting is None
    
    def get_bookings_for_date(self, date):
        """Get all approved bookings for a specific date"""
        return self.booking_requests.filter(
            BookingRequest.requested_date == date,
            BookingRequest.status == 'approved'
        ).order_by(BookingRequest.start_time).all()
    
    def get_pending_requests_count(self):
        """Get count of pending booking requests"""
        return self.booking_requests.filter_by(status='pending').count()
    
    def get_monthly_revenue(self, year, month):
        """Calculate revenue for a specific month"""
        bookings = self.booking_requests.filter(
            db.extract('year', BookingRequest.requested_date) == year,
            db.extract('month', BookingRequest.requested_date) == month,
            BookingRequest.status == 'approved'
        ).all()
        
        total = sum(booking.get_total_cost() for booking in bookings)
        return float(total)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'court_type': self.court_type,
            'hourly_rate': float(self.hourly_rate),
            'display_rate': self.get_display_rate(),
            'description': self.description,
            'has_lighting': self.has_lighting,
            'has_parking': self.has_parking,
            'has_shower': self.has_shower,
            'owner_name': self.owner.get_display_name(),
            'is_active': self.is_active,
            'auto_approve': self.auto_approve_bookings
        }

class BookingRequest(db.Model, TimestampMixin):
    """Booking requests for tennis courts"""
    __tablename__ = 'booking_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=False)
    
    # Booking details
    requested_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    duration_hours = db.Column(db.Integer, nullable=False, default=1)
    
    # Request information
    status = db.Column(db.Enum('pending', 'approved', 'declined', 'cancelled', 
                              name='booking_statuses'), default='pending')
    player_notes = db.Column(db.Text)
    
    # Owner response
    owner_response = db.Column(db.Text)
    responded_at = db.Column(db.DateTime)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Additional players for the booking
    additional_players = db.Column(db.Text)  # JSON string of player names/contacts
    
    # Financial
    quoted_price = db.Column(db.Numeric(8, 2))  # Price quoted by owner
    paid_amount = db.Column(db.Numeric(8, 2), default=0.0)
    payment_status = db.Column(db.Enum('unpaid', 'partial', 'paid', name='payment_statuses'), 
                              default='unpaid')
    
    # Relationships
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
    
    __table_args__ = (
        CheckConstraint('duration_hours > 0', name='positive_duration'),
        CheckConstraint('quoted_price >= 0', name='positive_price'),
        CheckConstraint('paid_amount >= 0', name='positive_payment'),
    )
    
    def __repr__(self):
        return f'<BookingRequest {self.player.username} @ {self.court.name} on {self.requested_date}>'
    
    @property
    def end_time(self):
        """Calculate end time based on start time and duration"""
        start_datetime = datetime.combine(datetime.today(), self.start_time)
        end_datetime = start_datetime + timedelta(hours=self.duration_hours)
        return end_datetime.time()
    
    def get_total_cost(self):
        """Calculate total cost based on court rate and duration"""
        if self.quoted_price:
            return float(self.quoted_price)
        return float(self.court.hourly_rate) * self.duration_hours
    
    def get_display_time_range(self):
        """Get formatted time range string"""
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
    
    def is_pending(self):
        """Check if booking is still pending"""
        return self.status == 'pending'
    
    def can_be_cancelled(self):
        """Check if booking can be cancelled by player"""
        if self.status not in ['pending', 'approved']:
            return False
        
        # Can cancel if booking is in the future
        booking_datetime = datetime.combine(self.requested_date, self.start_time)
        return booking_datetime > datetime.now()
    
    def approve(self, owner, response_message=None, quoted_price=None):
        """Approve the booking request"""
        if self.status == 'pending':
            self.status = 'approved'
            self.owner_response = response_message
            self.responded_at = datetime.utcnow()
            self.approved_by_id = owner.id
            
            if quoted_price:
                self.quoted_price = quoted_price
            else:
                self.quoted_price = self.get_total_cost()
                
            return True
        return False
    
    def decline(self, owner, response_message):
        """Decline the booking request"""
        if self.status == 'pending':
            self.status = 'declined'
            self.owner_response = response_message
            self.responded_at = datetime.utcnow()
            self.approved_by_id = owner.id
            return True
        return False
    
    def cancel(self):
        """Cancel the booking (by player or owner)"""
        if self.can_be_cancelled():
            self.status = 'cancelled'
            return True
        return False
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'court_name': self.court.name,
            'court_location': self.court.location,
            'player_name': self.player.get_display_name(),
            'requested_date': self.requested_date.isoformat(),
            'time_range': self.get_display_time_range(),
            'duration_hours': self.duration_hours,
            'status': self.status,
            'total_cost': self.get_total_cost(),
            'player_notes': self.player_notes,
            'owner_response': self.owner_response,
            'payment_status': self.payment_status
        }