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
    MAX_COURTS_PER_OWNER = 15
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
    def validate_booking(court_id, player_id, booking_date, start_time, end_time, exclude_booking_id=None):
        """Comprehensive booking validation using business rules"""
        
        # 1. Validate basic requirements
        if not all([court_id, player_id, booking_date, start_time, end_time]):
            return {'valid': False, 'reason': 'All booking fields are required'}
        
        # 2. Validate court exists and is active
        from models.court import Court
        court = Court.query.get(court_id)
        if not court:
            return {'valid': False, 'reason': 'Court not found'}
        if not court.is_active:
            return {'valid': False, 'reason': 'Court is not available for booking'}
        
        # 3. Validate player exists
        from models.player import Player
        player = Player.query.get(player_id)
        if not player:
            return {'valid': False, 'reason': 'Player not found'}
        
        # 4. Validate date is not in the past
        from datetime import datetime, date
        try:
            if isinstance(booking_date, str):
                booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()
            else:
                booking_date_obj = booking_date
                
            if booking_date_obj < date.today():
                return {'valid': False, 'reason': 'Cannot book courts in the past'}
                
            # Check advance booking limit (court's advance_booking_days)
            days_ahead = (booking_date_obj - date.today()).days
            if court.advance_booking_days and days_ahead > court.advance_booking_days:
                return {
                    'valid': False, 
                    'reason': f'Cannot book more than {court.advance_booking_days} days in advance'
                }
                
        except ValueError:
            return {'valid': False, 'reason': 'Invalid date format'}
        
        # 5. Validate time range using business rules
        if isinstance(start_time, str) and isinstance(end_time, str):
            time_validation = RuleEngine.validate_booking_time_range(start_time, end_time, player_id)
            if not time_validation['valid']:
                return time_validation
        
        # 6. Check for booking conflicts
        conflict_check = RuleEngine.validate_booking_conflicts(
            court_id, 
            booking_date if isinstance(booking_date, str) else booking_date.isoformat(),
            start_time if isinstance(start_time, str) else start_time.strftime('%H:%M'),
            end_time if isinstance(end_time, str) else end_time.strftime('%H:%M'),
            exclude_booking_id
        )
        
        if not conflict_check['valid']:
            return conflict_check
        
        # 7. Check player's booking limits (business rule: max 3 pending bookings)
        from models.court import Booking
        player_pending_bookings = Booking.query.filter(
            Booking.player_id == player_id,
            Booking.status == 'pending'
        ).count()
        
        if player_pending_bookings >= 3:
            return {
                'valid': False, 
                'reason': 'You have reached the maximum limit of 3 pending bookings'
            }
        
        # 8. All validations passed
        return {
            'valid': True,
            'court': court,
            'player': player,
            'duration_hours': time_validation.get('duration_hours', 1) if 'time_validation' in locals() else 1
        }

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
    
    @staticmethod
    def check_court_availability(court_id, date_str):
        """Check court availability for a specific date"""
        try:
            from datetime import datetime
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Get existing bookings
            from models.court import Booking
            existing_bookings = Booking.query.filter(
                Booking.court_id == court_id,
                Booking.booking_date == target_date,
                Booking.status.in_(['confirmed', 'pending'])
            ).count()
            
            # Calculate available slots (13 total slots from 8 AM to 9 PM)
            total_possible_slots = 13
            available_slots = max(0, total_possible_slots - existing_bookings)
            
            return {
                'available': available_slots > 0,
                'available_slots': available_slots,
                'existing_bookings': existing_bookings,
                'date': target_date.isoformat()
            }
            
        except Exception as e:
            return {
                'available': False,
                'available_slots': 0,
                'existing_bookings': 0,
                'error': str(e)
            }

    @staticmethod
    def validate_booking_time_range(start_time_str, end_time_str):
        """Validate booking time range meets business rules"""
        try:
            from datetime import datetime, time
            
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            # Business rules for time validation
            opening_time = time(6, 0)   # 6 AM
            closing_time = time(22, 0)  # 10 PM
            
            # Check operating hours
            if start_time < opening_time or end_time > closing_time:
                return {
                    'valid': False,
                    'reason': f'Court operates from {opening_time.strftime("%I:%M %p")} to {closing_time.strftime("%I:%M %p")}'
                }
            
            # Check minimum duration (1 hour)
            start_datetime = datetime.combine(datetime.today(), start_time)
            end_datetime = datetime.combine(datetime.today(), end_time)
            duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
            
            if duration_hours < 1:
                return {
                    'valid': False,
                    'reason': 'Minimum booking duration is 1 hour'
                }
            
            # Check maximum duration (4 hours)
            if duration_hours > 4:
                return {
                    'valid': False,
                    'reason': 'Maximum booking duration is 4 hours'
                }
            
            return {
                'valid': True,
                'duration_hours': duration_hours
            }
            
        except ValueError:
            return {
                'valid': False,
                'reason': 'Invalid time format'
            }

    @staticmethod
    def validate_booking_conflicts(court_id, booking_date_str, start_time_str, end_time_str, exclude_booking_id=None):
        """Check for booking conflicts with existing bookings"""
        try:
            from datetime import datetime
            from models.court import Booking
            
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            # Query for conflicting bookings
            conflicts_query = Booking.query.filter(
                Booking.court_id == court_id,
                Booking.booking_date == booking_date,
                Booking.status.in_(['confirmed', 'pending']),
                # Check for time overlap
                Booking.start_time < end_time,
                Booking.end_time > start_time
            )
            
            # Exclude current booking if editing
            if exclude_booking_id:
                conflicts_query = conflicts_query.filter(Booking.id != exclude_booking_id)
            
            conflicts = conflicts_query.all()
            
            if conflicts:
                conflict_times = [
                    f"{conflict.start_time.strftime('%H:%M')}-{conflict.end_time.strftime('%H:%M')}"
                    for conflict in conflicts
                ]
                return {
                    'valid': False,
                    'reason': f'Time slot conflicts with existing booking(s): {", ".join(conflict_times)}',
                    'conflicts': conflicts
                }
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'reason': f'Error checking conflicts: {str(e)}'
            }
    
    @staticmethod
    def validate_status_change(current_status, new_status, user_type=None, booking_id=None):
        """Validate booking status change based on business rules"""
        result = {'valid': True, 'reason': ''}
        
        # Valid status transitions
        valid_transitions = {
            'pending': ['confirmed', 'rejected', 'cancelled'],
            'confirmed': ['cancelled'],
            'rejected': [],  # Final state
            'cancelled': []  # Final state
        }
        
        # Check if transition is allowed
        if new_status not in valid_transitions.get(current_status, []):
            result['valid'] = False
            result['reason'] = f'Cannot change from {current_status} to {new_status}'
            return result
        
        # User type specific validations
        if user_type == 'owner':
            # Owners can approve (pending->confirmed) and reject (pending->rejected)
            if current_status == 'pending' and new_status in ['confirmed', 'rejected']:
                result['valid'] = True
            # Owners can cancel confirmed bookings
            elif current_status == 'confirmed' and new_status == 'cancelled':
                result['valid'] = True
            else:
                result['valid'] = False
                result['reason'] = f'Owners cannot change booking from {current_status} to {new_status}'
                return result
        
        elif user_type == 'player':
            # Players can only cancel their own bookings
            if new_status == 'cancelled' and current_status in ['pending', 'confirmed']:
                result['valid'] = True
            else:
                result['valid'] = False
                result['reason'] = f'Players cannot change booking from {current_status} to {new_status}'
                return result
        
        # Additional business rule validations
        if booking_id and new_status == 'confirmed':
            # Check for date conflicts when confirming
            from models.court import Booking
            booking = Booking.query.get(booking_id)
            if booking:
                # Check if booking date hasn't passed
                from datetime import datetime, date
                if booking.booking_date < date.today():
                    result['valid'] = False
                    result['reason'] = 'Cannot approve booking for past date'
                    return result
                
                # Check for conflicts with other confirmed bookings
                conflicts = Booking.query.filter(
                    Booking.court_id == booking.court_id,
                    Booking.booking_date == booking.booking_date,
                    Booking.status == 'confirmed',
                    Booking.id != booking_id,
                    Booking.start_time < booking.end_time,
                    Booking.end_time > booking.start_time
                ).first()
                
                if conflicts:
                    result['valid'] = False
                    result['reason'] = 'Time slot conflicts with another confirmed booking'
                    return result
        
        return result