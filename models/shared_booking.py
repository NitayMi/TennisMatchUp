from models.database import db
from datetime import datetime, timedelta

class SharedBooking(db.Model):
    """Shared booking model for player pairs"""
    __tablename__ = 'shared_bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Players involved
    player1_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)  # Initiator
    player2_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)  # Partner
    
    # Court and timing
    court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Booking status workflow
    status = db.Column(db.String(20), default='proposed', nullable=False)
    # proposed -> player1 sent proposal to player2
    # counter_proposed -> player2 suggested different time/court
    # accepted -> player2 accepted, ready for final booking
    # confirmed -> actual court booking created
    # cancelled -> either player cancelled
    # expired -> no response within time limit
    
    # Cost sharing
    total_cost = db.Column(db.Float, nullable=True)
    player1_share = db.Column(db.Float, nullable=True)  # Usually 50/50
    player2_share = db.Column(db.Float, nullable=True)
    cost_split_method = db.Column(db.String(20), default='equal', nullable=False)  # equal, custom
    
    # Messages and notes
    initiator_notes = db.Column(db.Text, nullable=True)  # Player1's message
    partner_notes = db.Column(db.Text, nullable=True)    # Player2's response
    
    # Alternative proposals (if player2 counter-proposes)
    alternative_court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=True)
    alternative_date = db.Column(db.Date, nullable=True)
    alternative_start_time = db.Column(db.Time, nullable=True)
    alternative_end_time = db.Column(db.Time, nullable=True)
    alternative_notes = db.Column(db.Text, nullable=True)
    
    # Final booking reference (when confirmed)
    final_booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)
    
    # Timestamps
    proposed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    responded_at = db.Column(db.DateTime, nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # Auto-expire after 48 hours
    
    # Relationships
    player1 = db.relationship('Player', foreign_keys=[player1_id], backref='initiated_shared_bookings')
    player2 = db.relationship('Player', foreign_keys=[player2_id], backref='received_shared_bookings')
    court = db.relationship('Court', foreign_keys=[court_id])
    alternative_court = db.relationship('Court', foreign_keys=[alternative_court_id])
    final_booking = db.relationship('Booking', foreign_keys=[final_booking_id])
    
    def __init__(self, player1_id, player2_id, court_id, booking_date, start_time, end_time, initiator_notes=None):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.court_id = court_id
        self.booking_date = booking_date
        self.start_time = start_time
        self.end_time = end_time
        self.initiator_notes = initiator_notes
        self.status = 'proposed'
        
        # Set expiry time (48 hours from now)
        self.expires_at = datetime.utcnow() + timedelta(hours=48)
        
        # Calculate cost
        self.calculate_cost()
    
    def calculate_cost(self):
        """Calculate total cost and split between players"""
        if self.court:
            # Calculate duration in hours
            duration = datetime.combine(datetime.today(), self.end_time) - \
                      datetime.combine(datetime.today(), self.start_time)
            hours = duration.total_seconds() / 3600
            
            # Total cost
            self.total_cost = self.court.hourly_rate * hours
            
            # Default equal split
            if self.cost_split_method == 'equal':
                self.player1_share = self.total_cost / 2
                self.player2_share = self.total_cost / 2
    
    def accept_proposal(self, partner_notes=None):
        """Player2 accepts the original proposal"""
        self.status = 'accepted'
        self.partner_notes = partner_notes
        self.responded_at = datetime.utcnow()
        return True
    
    def counter_propose(self, alternative_court_id=None, alternative_date=None, 
                       alternative_start_time=None, alternative_end_time=None, 
                       alternative_notes=None):
        """Player2 suggests alternative time/court"""
        self.status = 'counter_proposed'
        self.alternative_court_id = alternative_court_id or self.court_id
        self.alternative_date = alternative_date or self.booking_date
        self.alternative_start_time = alternative_start_time or self.start_time
        self.alternative_end_time = alternative_end_time or self.end_time
        self.alternative_notes = alternative_notes
        self.responded_at = datetime.utcnow()
        return True
    
    def accept_counter_proposal(self):
        """Player1 accepts Player2's counter-proposal"""
        # Move alternative to main booking details
        if self.alternative_court_id:
            self.court_id = self.alternative_court_id
        if self.alternative_date:
            self.booking_date = self.alternative_date
        if self.alternative_start_time:
            self.start_time = self.alternative_start_time
        if self.alternative_end_time:
            self.end_time = self.alternative_end_time
        
        # Clear alternatives
        self.alternative_court_id = None
        self.alternative_date = None
        self.alternative_start_time = None
        self.alternative_end_time = None
        
        self.status = 'accepted'
        self.calculate_cost()  # Recalculate with new details
        return True
    
    def confirm_booking(self):
        """Create final court booking after both players agree"""
        from models.court import Booking
        
        if self.status != 'accepted':
            return False, "Booking must be accepted by both players first"
        
        # Check court availability one more time
        if not self.court.is_available(self.booking_date, self.start_time, self.end_time):
            return False, "Court is no longer available for this time slot"
        
        # Create final booking (in player1's name but shared)
        final_booking = Booking(
            court_id=self.court_id,
            player_id=self.player1_id,  # Primary booker
            booking_date=self.booking_date,
            start_time=self.start_time,
            end_time=self.end_time,
            notes=f"Shared booking with {self.player2.user.full_name}. {self.initiator_notes or ''}"
        )
        final_booking.total_cost = self.total_cost
        final_booking.status = 'pending'  # ← הוסף את זה אחרי היצירה
        
        db.session.add(final_booking)
        db.session.flush()  # Get the booking ID
        
        # Update shared booking
        self.final_booking_id = final_booking.id
        self.status = 'confirmed'
        self.confirmed_at = datetime.utcnow()
        
        return True, final_booking
    
    def cancel(self, cancelled_by_player_id, reason=None):
        """Cancel the shared booking"""
        self.status = 'cancelled'
        self.partner_notes = f"Cancelled by player {cancelled_by_player_id}. {reason or ''}"
        self.responded_at = datetime.utcnow()
        return True
    
    def is_expired(self):
        """Check if proposal has expired"""
        return datetime.utcnow() > self.expires_at if self.expires_at else False
    
    def get_other_player(self, current_player_id):
        """Get the other player in this shared booking"""
        if current_player_id == self.player1_id:
            return self.player2
        elif current_player_id == self.player2_id:
            return self.player1
        return None
    
    def get_status_color(self):
        """Get color class for status - compatible with template expectations"""
        color_mapping = {
            'proposed': 'warning',
            'counter_proposed': 'info',
            'accepted': 'primary',
            'confirmed': 'success',
            'cancelled': 'danger',
            'expired': 'secondary',
            'rejected': 'secondary'
        }
        return color_mapping.get(self.status, 'secondary')
    
    def get_status_display(self):
        """Get formatted status - compatible with template expectations"""
        status_mapping = {
            'proposed': 'Proposed',
            'counter_proposed': 'Counter Proposed',
            'accepted': 'Accepted',
            'confirmed': 'Confirmed',
            'cancelled': 'Cancelled',
            'expired': 'Expired',
            'rejected': 'Rejected'
        }
        return status_mapping.get(self.status, self.status.title())
    
    def get_duration_display(self):
        """Get formatted duration - compatible with template expectations"""
        from datetime import datetime, date
        start_datetime = datetime.combine(date.today(), self.start_time)
        end_datetime = datetime.combine(date.today(), self.end_time)
        duration = end_datetime - start_datetime
        
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return "0m"
    
    def get_current_proposal(self):
        """Get the currently active proposal details"""
        if self.status == 'counter_proposed':
            return {
                'court_id': self.alternative_court_id or self.court_id,
                'court': self.alternative_court or self.court,
                'date': self.alternative_date or self.booking_date,
                'start_time': self.alternative_start_time or self.start_time,
                'end_time': self.alternative_end_time or self.end_time,
                'notes': self.alternative_notes
            }
        else:
            return {
                'court_id': self.court_id,
                'court': self.court,
                'date': self.booking_date,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'notes': self.initiator_notes
            }
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        current_proposal = self.get_current_proposal()
        
        return {
            'id': self.id,
            'player1': {
                'id': self.player1.id,
                'name': self.player1.user.full_name,
                'email': self.player1.user.email
            },
            'player2': {
                'id': self.player2.id,
                'name': self.player2.user.full_name,
                'email': self.player2.user.email
            },
            'court': {
                'id': current_proposal['court'].id,
                'name': current_proposal['court'].name,
                'location': current_proposal['court'].location,
                'hourly_rate': current_proposal['court'].hourly_rate
            },
            'booking_details': {
                'date': current_proposal['date'].isoformat() if current_proposal['date'] else None,
                'start_time': current_proposal['start_time'].strftime('%H:%M') if current_proposal['start_time'] else None,
                'end_time': current_proposal['end_time'].strftime('%H:%M') if current_proposal['end_time'] else None
            },
            'cost': {
                'total': self.total_cost,
                'player1_share': self.player1_share,
                'player2_share': self.player2_share
            },
            'status': self.status,
            'messages': {
                'initiator_notes': self.initiator_notes,
                'partner_notes': self.partner_notes,
                'alternative_notes': self.alternative_notes
            },
            'timestamps': {
                'proposed_at': self.proposed_at.isoformat() if self.proposed_at else None,
                'responded_at': self.responded_at.isoformat() if self.responded_at else None,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None,
                'is_expired': self.is_expired()
            }
        }
    
    def __repr__(self):
        return f'<SharedBooking {self.player1.user.full_name} + {self.player2.user.full_name} @ {self.court.name}>'