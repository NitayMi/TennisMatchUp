"""
Business Rule Engine for TennisMatchUp
Centralizes all business logic and validation rules
"""
from datetime import datetime, timedelta
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court, Booking
from models.message import Message

class RuleEngine:
    """Centralized business rules and validation logic"""
    
    # Configuration constants
    MAX_COURTS_PER_OWNER = 10
    MAX_BOOKING_DURATION_HOURS = 4
    MIN_BOOKING_DURATION_MINUTES = 60
    CANCELLATION_NOTICE_HOURS = 24
    MAX_ADVANCE_BOOKING_DAYS = 30
    MAX_SKILL_LEVEL_DIFFERENCE = 1
    MAX_DISTANCE_KM = 50
    MIN_HOURLY_RATE = 10
    MAX_HOURLY_RATE = 500
    
    @staticmethod
    def validate_user_registration(email, user_type, **kwargs):
        """Validate user registration data"""
        result = {'valid': True, 'reason': ''}
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            result['valid'] = False
            result['reason'] = 'Email address already registered'
            return result
        
        # Validate user type
        if user_type not in ['player', 'owner', 'admin']:
            result['valid'] = False
            result['reason'] = 'Invalid user type'
            return result
        
        # Additional validation for specific user types
        if user_type == 'player':
            skill_level = kwargs.get('skill_level')
            if skill_level not in ['beginner', 'intermediate', 'advanced', 'professional']:
                result['valid'] = False
                result['reason'] = 'Invalid skill level'
                return result
        
        return result
    
    @staticmethod
    def validate_court_creation(owner_id, name, location, hourly_rate, **kwargs):
        """Validate court creation"""
        result = {'valid': True, 'reason': ''}
        
        # Check maximum courts per owner
        existing_courts = Court.query.filter_by(owner_id=owner_id).count()
        if existing_courts >= RuleEngine.MAX_COURTS_PER_OWNER:
            result['valid'] = False
            result['reason'] = f'Maximum {RuleEngine.MAX_COURTS_PER_OWNER} courts allowed per owner'
            return result
        
        # Check for duplicate court names by same owner
        duplicate = Court.query.filter_by(
            owner_id=owner_id,
            name=name
        ).first()
        if duplicate:
            result['valid'] = False
            result['reason'] = 'Court name already exists for this owner'
            return result
        
        # Validate hourly rate
        if hourly_rate < RuleEngine.MIN_HOURLY_RATE or hourly_rate > RuleEngine.MAX_HOURLY_RATE:
            result['valid'] = False
            result['reason'] = f'Hourly rate must be between ${RuleEngine.MIN_HOURLY_RATE} and ${RuleEngine.MAX_HOURLY_RATE}'
            return result
        
        # Validate required fields
        if not name or len(name.strip()) < 3:
            result['valid'] = False
            result['reason'] = 'Court name must be at least 3 characters long'
            return result
            
        if not location or len(location.strip()) < 5:
            result['valid'] = False
            result['reason'] = 'Location must be at least 5 characters long'
            return result
        
        return result
    
    @staticmethod
    def validate_booking(court_id, player_id, booking_date, start_time, end_time, **kwargs):
        """Validate booking creation"""
        result = {'valid': True, 'reason': ''}
        
        try:
            # Parse date and times
            if isinstance(booking_date, str):
                booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
            
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, '%H:%M').time()
            
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, '%H:%M').time()
                
        except ValueError:
            result['valid'] = False
            result['reason'] = 'Invalid date or time format'
            return result
        
        # Validate court exists and is active
        court = Court.query.get(court_id)
        if not court or not court.is_active:
            result['valid'] = False
            result['reason'] = 'Court not available'
            return result
        
        # Validate player exists
        player = Player.query.get(player_id)
        if not player:
            result['valid'] = False
            result['reason'] = 'Player not found'
            return result
        
        # Check if booking date is not in the past
        if booking_date < datetime.now().date():
            result['valid'] = False
            result['reason'] = 'Cannot book courts for past dates'
            return result
        
        # Check advance booking limit
        if booking_date > datetime.now().date() + timedelta(days=RuleEngine.MAX_ADVANCE_BOOKING_DAYS):
            result['valid'] = False
            result['reason'] = f'Cannot book more than {RuleEngine.MAX_ADVANCE_BOOKING_DAYS} days in advance'
            return result
        
        # Validate time logic
        if start_time >= end_time:
            result['valid'] = False
            result['reason'] = 'Start time must be before end time'
            return result
        
        # Check minimum booking duration
        start_datetime = datetime.combine(booking_date, start_time)
        end_datetime = datetime.combine(booking_date, end_time)
        duration_minutes = (end_datetime - start_datetime).total_seconds() / 60
        
        if duration_minutes < RuleEngine.MIN_BOOKING_DURATION_MINUTES:
            result['valid'] = False
            result['reason'] = f'Minimum booking duration is {RuleEngine.MIN_BOOKING_DURATION_MINUTES} minutes'
            return result
        
        # Check maximum booking duration
        if duration_minutes > RuleEngine.MAX_BOOKING_DURATION_HOURS * 60:
            result['valid'] = False
            result['reason'] = f'Maximum booking duration is {RuleEngine.MAX_BOOKING_DURATION_HOURS} hours'
            return result
        
        # Check for conflicting bookings
        conflicting_booking = Booking.query.filter(
            Booking.court_id == court_id,
            Booking.booking_date == booking_date,
            Booking.status.in_(['confirmed', 'pending']),
            db.or_(
                # New booking starts during existing booking
                db.and_(Booking.start_time <= start_time, Booking.end_time > start_time),
                # New booking ends during existing booking
                db.and_(Booking.start_time < end_time, Booking.end_time >= end_time),
                # New booking completely overlaps existing booking
                db.and_(Booking.start_time >= start_time, Booking.end_time <= end_time),
                # Existing booking completely overlaps new booking
                db.and__(start_time >= Booking.start_time, end_time <= Booking.end_time)
            )
        ).first()
        
        if conflicting_booking:
            result['valid'] = False
            result['reason'] = f'Time slot conflicts with existing booking from {conflicting_booking.start_time} to {conflicting_booking.end_time}'
            return result
        
        # Check if player is trying to book their own court (if they're also an owner)
        player_user = User.query.get(player.user_id)
        if player_user.user_type == 'owner' and court.owner_id == player.user_id:
            result['valid'] = False
            result['reason'] = 'Cannot book your own court'
            return result
        
        return result
    
    @staticmethod
    def validate_booking_approval(booking_id, owner_id):
        """Validate booking approval by owner"""
        result = {'valid': True, 'reason': ''}
        
        booking = Booking.query.get(booking_id)
        if not booking:
            result['valid'] = False
            result['reason'] = 'Booking not found'
            return result
        
        # Check if booking belongs to this owner
        if booking.court.owner_id != owner_id:
            result['valid'] = False
            result['reason'] = 'Not authorized to approve this booking'
            return result
        
        # Check if booking is still pending
        if booking.status != 'pending':
            result['valid'] = False
            result['reason'] = f'Booking is already {booking.status}'
            return result
        
        # Check if booking date hasn't passed
        if booking.booking_date < datetime.now().date():
            result['valid'] = False
            result['reason'] = 'Cannot approve booking for past date'
            return result
        
        return result
    
    @staticmethod
    def validate_booking_cancellation(booking_id, user_id, user_type):
        """Validate booking cancellation"""
        result = {'valid': True, 'reason': ''}
        
        booking = Booking.query.get(booking_id)
        if not booking:
            result['valid'] = False
            result['reason'] = 'Booking not found'
            return result
        
        # Check authorization
        if user_type == 'player' and booking.player.user_id != user_id:
            result['valid'] = False
            result['reason'] = 'Not authorized to cancel this booking'
            return result
        elif user_type == 'owner' and booking.court.owner_id != user_id:
            result['valid'] = False
            result['reason'] = 'Not authorized to cancel this booking'
            return result
        
        # Check if booking can still be cancelled
        if booking.status not in ['confirmed', 'pending']:
            result['valid'] = False
            result['reason'] = f'Cannot cancel {booking.status} booking'
            return result
        
        # Check cancellation notice period
        booking_datetime = datetime.combine(booking.booking_date, booking.start_time)
        notice_cutoff = datetime.now() + timedelta(hours=RuleEngine.CANCELLATION_NOTICE_HOURS)
        
        if booking_datetime <= notice_cutoff:
            result['valid'] = False
            result['reason'] = f'Must cancel at least {RuleEngine.CANCELLATION_NOTICE_HOURS} hours in advance'
            return result
        
        return result
    
    @staticmethod
    def validate_player_matching(player1_id, player2_id):
        """Validate if two players can be matched"""
        result = {'valid': True, 'reason': '', 'compatibility_score': 0}
        
        player1 = Player.query.get(player1_id)
        player2 = Player.query.get(player2_id)
        
        if not player1 or not player2:
            result['valid'] = False
            result['reason'] = 'Player not found'
            return result
        
        # Can't match with yourself
        if player1_id == player2_id:
            result['valid'] = False
            result['reason'] = 'Cannot match with yourself'
            return result
        
        # Check skill level compatibility
        skill_levels = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'professional': 4}
        skill_diff = abs(skill_levels[player1.skill_level] - skill_levels[player2.skill_level])
        
        if skill_diff > RuleEngine.MAX_SKILL_LEVEL_DIFFERENCE:
            result['valid'] = False
            result['reason'] = f'Skill level difference too large (max {RuleEngine.MAX_SKILL_LEVEL_DIFFERENCE} level)'
            return result
        
        # Calculate compatibility score (0-100)
        compatibility_score = 100
        
        # Reduce score based on skill difference
        compatibility_score -= skill_diff * 20
        
        # Location compatibility (simplified - would use actual distance calculation)
        if player1.preferred_location.lower() != player2.preferred_location.lower():
            compatibility_score -= 30
        
        # Availability overlap (simplified)
        if player1.availability != player2.availability:
            compatibility_score -= 20
        
        result['compatibility_score'] = max(0, compatibility_score)
        
        return result
    
    @staticmethod
    def validate_message_sending(sender_id, receiver_id, content):
        """Validate message sending"""
        result = {'valid': True, 'reason': ''}
        
        # Basic validation
        if sender_id == receiver_id:
            result['valid'] = False
            result['reason'] = 'Cannot send message to yourself'
            return result
        
        if not content or len(content.strip()) < 1:
            result['valid'] = False
            result['reason'] = 'Message content cannot be empty'
            return result
        
        if len(content) > 1000:
            result['valid'] = False
            result['reason'] = 'Message too long (max 1000 characters)'
            return result
        
        # Check if users exist and are active
        sender = User.query.get(sender_id)
        receiver = User.query.get(receiver_id)
        
        if not sender or not sender.is_active:
            result['valid'] = False
            result['reason'] = 'Sender account not valid'
            return result
        
        if not receiver or not receiver.is_active:
            result['valid'] = False
            result['reason'] = 'Recipient account not valid'
            return result
        
        # Check rate limiting (max 50 messages per hour per user)
        hour_ago = datetime.now() - timedelta(hours=1)
        recent_messages = Message.query.filter(
            Message.sender_id == sender_id,
            Message.created_at >= hour_ago
        ).count()
        
        if recent_messages >= 50:
            result['valid'] = False
            result['reason'] = 'Message rate limit exceeded. Try again later.'
            return result
        
        return result
    
    @staticmethod
    def calculate_court_recommendation_score(court, player):
        """Calculate recommendation score for a court for a specific player"""
        score = 100
        
        # Location preference (simplified - would use actual distance)
        if court.location.lower() != player.preferred_location.lower():
            score -= 30
        
        # Price preference (assume players prefer lower prices)
        if court.hourly_rate > 100:
            score -= (court.hourly_rate - 100) / 10
        
        # Court rating (would be implemented with actual ratings)
        # score += court.average_rating * 10
        
        # Availability (would check actual availability)
        if not court.is_active:
            score = 0
        
        return max(0, min(100, score))
    
    @staticmethod
    def get_business_hours():
        """Get standard business hours for court operations"""
        return {
            'open_time': '06:00',
            'close_time': '22:00',
            'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        }
    
    @staticmethod
    def validate_booking_time_slots(start_time, end_time):
        """Validate booking times are within business hours"""
        result = {'valid': True, 'reason': ''}
        
        business_hours = RuleEngine.get_business_hours()
        open_time = datetime.strptime(business_hours['open_time'], '%H:%M').time()
        close_time = datetime.strptime(business_hours['close_time'], '%H:%M').time()
        
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, '%H:%M').time()
        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, '%H:%M').time()
        
        if start_time < open_time:
            result['valid'] = False
            result['reason'] = f'Booking cannot start before {business_hours["open_time"]}'
            return result
        
        if end_time > close_time:
            result['valid'] = False
            result['reason'] = f'Booking cannot end after {business_hours["close_time"]}'
            return result
        
        return result
    
    @staticmethod
    def apply_dynamic_pricing(base_rate, booking_date, start_time, **factors):
        """Apply dynamic pricing based on demand and other factors"""
        final_rate = base_rate
        
        # Weekend surcharge
        if booking_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            final_rate *= 1.2
        
        # Peak hours surcharge (6-9 PM)
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, '%H:%M').time()
        
        if start_time >= datetime.strptime('18:00', '%H:%M').time() and start_time <= datetime.strptime('21:00', '%H:%M').time():
            final_rate *= 1.15
        
        # Holiday surcharge
        is_holiday = factors.get('is_holiday', False)
        if is_holiday:
            final_rate *= 1.3
        
        # High demand surcharge
        demand_factor = factors.get('demand_factor', 1.0)
        final_rate *= demand_factor
        
        return round(final_rate, 2)
    
    @staticmethod
    def check_system_limits():
        """Check various system limits and quotas"""
        limits = {
            'max_users': 10000,
            'max_courts': 1000,
            'max_bookings_per_day': 5000,
            'max_messages_per_day': 50000
        }
        
        current_stats = {
            'users': User.query.count(),
            'courts': Court.query.count(),
            'bookings_today': Booking.query.filter_by(
                booking_date=datetime.now().date()
            ).count(),
            'messages_today': Message.query.filter(
                Message.created_at >= datetime.now().date()
            ).count()
        }
        
        warnings = []
        
        for key, limit in limits.items():
            current_key = key if key in current_stats else key.replace('max_', '')
            if current_stats.get(current_key, 0) >= limit * 0.9:  # 90% threshold
                warnings.append(f'{key} approaching limit: {current_stats.get(current_key, 0)}/{limit}')
        
        return {
            'limits': limits,
            'current': current_stats,
            'warnings': warnings
        }