from models.database import db
from datetime import datetime, date, time

class Court(db.Model):
    """Court model for tennis courts"""
    __tablename__ = 'courts'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(300), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    court_type = db.Column(db.String(20), nullable=False)  # outdoor, indoor
    surface = db.Column(db.String(20), nullable=False)  # clay, hard, grass, artificial
    hourly_rate = db.Column(db.Float, nullable=False)
    amenities = db.Column(db.Text, nullable=True)  # JSON string or comma-separated
    has_lighting = db.Column(db.Boolean, default=False, nullable=False)
    has_parking = db.Column(db.Boolean, default=False, nullable=False)
    has_equipment_rental = db.Column(db.Boolean, default=False, nullable=False)
    has_changing_rooms = db.Column(db.Boolean, default=False, nullable=False)
    max_players = db.Column(db.Integer, default=4, nullable=False)
    advance_booking_days = db.Column(db.Integer, default=30, nullable=False)
    cancellation_policy = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)  # ⟵ שדה חדש: קישור יחיד לתמונה
    image_urls = db.Column(db.Text, nullable=True)  # JSON array of image URLs
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    bookings = db.relationship('Booking', backref='court', cascade='all, delete-orphan')
    
    def __init__(self, owner_id, name, location, court_type, surface, hourly_rate, description=None, image_url=None):
        self.owner_id = owner_id
        self.name = name
        self.location = location
        self.court_type = court_type
        self.surface = surface
        self.hourly_rate = hourly_rate
        self.description = description
        self.is_active = True
        self.image_url = image_url  # ⟵ אתחול שדה חדש   
    
    def get_surface_display(self):
        """Get formatted surface type"""
        surface_mapping = {
            'clay': 'Clay',
            'hard': 'Hard Court',
            'grass': 'Grass',
            'artificial': 'Artificial Grass'
        }
        return surface_mapping.get(self.surface, self.surface.title())
    
    def get_court_type_display(self):
        """Get formatted court type"""
        type_mapping = {
            'outdoor': 'Outdoor',
            'indoor': 'Indoor'
        }
        return type_mapping.get(self.court_type, self.court_type.title())
    
    def get_available_slots(self, booking_date, duration_hours=1):
        """Get available time slots for a specific date"""
        if isinstance(booking_date, str):
            booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
        
        # Get existing bookings for this date
        existing_bookings = Booking.query.filter(
            Booking.court_id == self.id,
            Booking.booking_date == booking_date,
            Booking.status.in_(['confirmed', 'pending'])
        ).order_by(Booking.start_time).all()
        
        # Generate available slots (8 AM to 9 PM)
        available_slots = []
        start_hour = 8
        end_hour = 21
        
        for hour in range(start_hour, end_hour):
            slot_start = time(hour, 0)
            slot_end = time(hour + duration_hours, 0) if hour + duration_hours <= 24 else time(23, 59)
            
            # Check if this slot conflicts with any booking
            conflict = False
            for booking in existing_bookings:
                if (slot_start < booking.end_time and slot_end > booking.start_time):
                    conflict = True
                    break
            
            if not conflict and hour + duration_hours <= end_hour:
                available_slots.append({
                    'start_time': slot_start.strftime('%H:%M'),
                    'end_time': slot_end.strftime('%H:%M'),
                    'duration': duration_hours
                })
        
        return available_slots
    
    def is_available(self, booking_date, start_time, end_time):
        """Check if court is available for specific time slot"""
        if isinstance(booking_date, str):
            booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, '%H:%M').time()
        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, '%H:%M').time()
        
        # Check for conflicting bookings
        conflicting_bookings = Booking.query.filter(
            Booking.court_id == self.id,
            Booking.booking_date == booking_date,
            Booking.status.in_(['confirmed', 'pending']),
            db.or_(
                db.and_(Booking.start_time <= start_time, Booking.end_time > start_time),
                db.and_(Booking.start_time < end_time, Booking.end_time >= end_time),
                db.and_(Booking.start_time >= start_time, Booking.end_time <= end_time)
            )
        ).count()
        
        return conflicting_bookings == 0
    
    def get_utilization_rate(self, days_back=30):
        """Get court utilization rate for the past period"""
        start_date = date.today() - datetime.timedelta(days=days_back)
        
        total_bookings = Booking.query.filter(
            Booking.court_id == self.id,
            Booking.booking_date >= start_date,
            Booking.status == 'confirmed'
        ).count()
        
        # Simplified calculation: assume 14 available hours per day
        total_possible_slots = days_back * 14
        return (total_bookings / total_possible_slots * 100) if total_possible_slots > 0 else 0
    
    def to_dict(self):
        """Convert court to dictionary"""
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'name': self.name,
            'description': self.description,
            'location': self.location,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'court_type': self.court_type,
            'court_type_display': self.get_court_type_display(),
            'surface': self.surface,
            'surface_display': self.get_surface_display(),
            'hourly_rate': self.hourly_rate,
            'amenities': self.amenities,
            'has_lighting': self.has_lighting,
            'has_parking': self.has_parking,
            'has_equipment_rental': self.has_equipment_rental,
            'has_changing_rooms': self.has_changing_rooms,
            'max_players': self.max_players,
            'advance_booking_days': self.advance_booking_days,
            'cancellation_policy': self.cancellation_policy,
            'is_active': self.is_active,
            'image_url': self.image_url,
            'image_urls': self.image_urls,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Court {self.name} in {self.location}>'


class Booking(db.Model):
    """Booking model for court reservations"""
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, confirmed, cancelled, rejected
    notes = db.Column(db.Text, nullable=True)
    total_cost = db.Column(db.Float, nullable=True)
    payment_status = db.Column(db.String(20), default='pending', nullable=False)  # pending, paid, refunded
    cancellation_reason = db.Column(db.Text, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __init__(self, court_id, player_id, booking_date, start_time, end_time, notes=None):
        self.court_id = court_id
        self.player_id = player_id
        self.booking_date = booking_date
        self.start_time = start_time
        self.end_time = end_time
        self.notes = notes
        self.status = 'pending'
        self.payment_status = 'pending'
    
    def calculate_cost(self):
        """Calculate total cost for this booking"""
        if not self.court:
            return 0
        
        start_datetime = datetime.combine(date.today(), self.start_time)
        end_datetime = datetime.combine(date.today(), self.end_time)
        duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
        
        return self.court.hourly_rate * duration_hours
    
    def get_duration_display(self):
        """Get formatted duration"""
        start_datetime = datetime.combine(date.today(), self.start_time)
        end_datetime = datetime.combine(date.today(), self.end_time)
        duration = end_datetime - start_datetime
        
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"
    
    def get_status_display(self):
        """Get formatted status"""
        status_mapping = {
            'pending': 'Pending Approval',
            'confirmed': 'Confirmed',
            'cancelled': 'Cancelled',
            'rejected': 'Rejected'
        }
        return status_mapping.get(self.status, self.status.title())
    
    def get_status_color(self):
        """Get color class for status"""
        color_mapping = {
            'pending': 'warning',
            'confirmed': 'success',
            'cancelled': 'danger',
            'rejected': 'secondary'
        }
        return color_mapping.get(self.status, 'secondary')
    
    def can_cancel(self, user_id, user_type):
        """Check if booking can be cancelled by user"""
        if self.status not in ['confirmed', 'pending']:
            return False
        
        # Player can cancel their own bookings
        if user_type == 'player' and self.player.user_id == user_id:
            return True
        
        # Owner can cancel bookings for their courts
        if user_type == 'owner' and self.court.owner_id == user_id:
            return True
        
        # Admin can cancel any booking
        if user_type == 'admin':
            return True
        
        return False
    
    def to_dict(self):
        """Convert booking to dictionary"""
        return {
            'id': self.id,
            'court_id': self.court_id,
            'player_id': self.player_id,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'status': self.status,
            'status_display': self.get_status_display(),
            'status_color': self.get_status_color(),
            'notes': self.notes,
            'total_cost': self.total_cost or self.calculate_cost(),
            'duration_display': self.get_duration_display(),
            'payment_status': self.payment_status,
            'cancellation_reason': self.cancellation_reason,
            'rejection_reason': self.rejection_reason,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejected_at': self.rejected_at.isoformat() if self.rejected_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Booking {self.id}: {self.court.name if self.court else "Unknown Court"} on {self.booking_date}>'