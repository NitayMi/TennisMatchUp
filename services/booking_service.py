"""
Booking Service for TennisMatchUp
Centralizes all booking-related business logic
"""
from datetime import datetime, timedelta, date, time as dt_time
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court, Booking
from models.message import Message
from services.rule_engine import RuleEngine
from services.cloud_service import CloudService
from services.email_service import EmailService
from sqlalchemy import and_, or_, func
import json


class BookingService:
    """Centralized booking business logic service"""
    
    @staticmethod
    def calculate_booking_cost(court_id, start_time, end_time):
        """Calculate total cost for a booking"""
        try:
            court = Court.query.get(court_id)
            if not court:
                return {'success': False, 'error': 'Court not found'}
            
            # Parse time strings if needed
            if isinstance(start_time, str):
                start_dt = datetime.strptime(start_time, '%H:%M')
            else:
                start_dt = datetime.combine(datetime.today(), start_time)
                
            if isinstance(end_time, str):
                end_dt = datetime.strptime(end_time, '%H:%M')
            else:
                end_dt = datetime.combine(datetime.today(), end_time)
            
            duration_hours = (end_dt - start_dt).total_seconds() / 3600
            total_cost = duration_hours * court.hourly_rate
            
            return {
                'success': True,
                'duration_hours': duration_hours,
                'hourly_rate': court.hourly_rate,
                'total_cost': total_cost,
                'formatted_cost': f"${total_cost:.2f}"
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Calculation error: {str(e)}'}
    
    @staticmethod
    def validate_booking_time(court_id, booking_date, start_time, end_time):
        """Validate if booking time slot is available"""
        try:
            # Convert strings to proper types
            if isinstance(booking_date, str):
                booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, '%H:%M').time()
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, '%H:%M').time()
            
            # Use RuleEngine for validation
            validation = RuleEngine.validate_booking(
                court_id=court_id,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time
            )
            
            return validation
            
        except Exception as e:
            return {'valid': False, 'reason': f'Validation error: {str(e)}'}
    
    @staticmethod
    def process_booking_request(player_id, court_id, booking_date, start_time, end_time, notes=None):
        """Create a new booking request"""
        try:
            # Validate inputs first
            validation = BookingService.validate_booking_time(court_id, booking_date, start_time, end_time)
            if not validation['valid']:
                return {'success': False, 'error': validation['reason']}
            
            # Calculate cost
            cost_result = BookingService.calculate_booking_cost(court_id, start_time, end_time)
            if not cost_result['success']:
                return {'success': False, 'error': cost_result['error']}
            
            # Convert strings to proper types
            if isinstance(booking_date, str):
                booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, '%H:%M').time()
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, '%H:%M').time()
            
            # Create booking
            booking = Booking(
                court_id=court_id,
                player_id=player_id,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time,
                notes=notes
            )
            
            # Set calculated cost
            booking.total_cost = cost_result['total_cost']
            
            db.session.add(booking)
            db.session.commit()
            
            # Send notification (async/background task would be better)
            try:
                BookingService._send_booking_notification(booking)
            except Exception as e:
                pass  # Don't fail booking if notification fails
            
            return {
                'success': True,
                'booking_id': booking.id,
                'total_cost': cost_result['total_cost'],
                'message': 'Booking request submitted successfully!'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Booking failed: {str(e)}'}
    
    @staticmethod
    def get_booking_details(booking_id):
        """Get comprehensive booking details"""
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return {'success': False, 'error': 'Booking not found'}
            
            return {
                'success': True,
                'booking': {
                    'id': booking.id,
                    'court_name': booking.court.name,
                    'court_location': booking.court.location,
                    'player_name': booking.player.user.full_name,
                    'booking_date': booking.booking_date.isoformat(),
                    'start_time': booking.start_time.strftime('%H:%M'),
                    'end_time': booking.end_time.strftime('%H:%M'),
                    'duration': booking.get_duration_display(),
                    'status': booking.status,
                    'status_display': booking.get_status_display(),
                    'status_color': booking.get_status_color(),
                    'total_cost': booking.total_cost or booking.calculate_cost(),
                    'notes': booking.notes,
                    'created_at': booking.created_at.isoformat()
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Error retrieving booking: {str(e)}'}
    
    @staticmethod
    def get_player_bookings(player_id, limit=10, status_filter=None):
        """Get bookings for a specific player"""
        try:
            query = Booking.query.filter_by(player_id=player_id)
            
            if status_filter:
                query = query.filter_by(status=status_filter)
            
            bookings = query.order_by(Booking.created_at.desc()).limit(limit).all()
            
            booking_list = []
            for booking in bookings:
                booking_list.append({
                    'id': booking.id,
                    'court_name': booking.court.name,
                    'court_location': booking.court.location,
                    'booking_date': booking.booking_date.isoformat(),
                    'start_time': booking.start_time.strftime('%H:%M'),
                    'end_time': booking.end_time.strftime('%H:%M'),
                    'duration_display': booking.get_duration_display(),
                    'status': booking.status,
                    'status_display': booking.get_status_display(),
                    'status_color': booking.get_status_color(),
                    'total_cost': booking.total_cost or booking.calculate_cost(),
                    'created_at': booking.created_at.isoformat()
                })
            
            return {
                'success': True,
                'bookings': booking_list,
                'count': len(booking_list)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Error retrieving bookings: {str(e)}'}
    
    @staticmethod
    def update_booking_status(booking_id, new_status, reason=None, user_id=None, user_type=None):
        """Update booking status with validation"""
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return {'success': False, 'error': 'Booking not found'}
            
            # Validate status change based on current status and user type
            validation = RuleEngine.validate_status_change(
                current_status=booking.status,
                new_status=new_status,
                user_type=user_type,
                booking_id=booking_id
            )
            
            if not validation['valid']:
                return {'success': False, 'error': validation['reason']}
            
            old_status = booking.status
            booking.status = new_status
            
            # Set status-specific fields
            if new_status == 'confirmed':
                booking.confirmed_at = datetime.utcnow()
            elif new_status == 'cancelled':
                booking.cancelled_at = datetime.utcnow()
                booking.cancellation_reason = reason
            elif new_status == 'rejected':
                booking.rejected_at = datetime.utcnow()
                booking.rejection_reason = reason
            
            db.session.commit()
            
            # Send status change notification
            try:
                BookingService._send_status_change_notification(booking, old_status, new_status, reason)
            except Exception as e:
                pass  # Don't fail update if notification fails
            
            return {
                'success': True,
                'message': f'Booking status updated to {new_status}',
                'booking_id': booking.id,
                'new_status': new_status
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Status update failed: {str(e)}'}
    
    @staticmethod
    def get_court_availability(court_id, check_date, days_ahead=7):
        """Get court availability for scheduling"""
        try:
            court = Court.query.get(court_id)
            if not court:
                return {'success': False, 'error': 'Court not found'}
            
            # Convert string date if needed
            if isinstance(check_date, str):
                check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
            
            end_date = check_date + timedelta(days=days_ahead)
            
            # Get existing bookings
            existing_bookings = db.session.query(Booking).filter(
                Booking.court_id == court_id,
                Booking.booking_date.between(check_date, end_date),
                Booking.status.in_(['confirmed', 'pending'])
            ).all()
            
            # Create availability calendar
            availability = {}
            current_date = check_date
            
            while current_date <= end_date:
                date_str = current_date.isoformat()
                day_bookings = [b for b in existing_bookings if b.booking_date == current_date]
                
                # Create hourly availability (8 AM to 10 PM)
                hourly_slots = {}
                for hour in range(8, 22):
                    slot_start = dt_time(hour, 0)
                    slot_end = dt_time(hour + 1, 0)
                    
                    # Check if slot is booked
                    is_booked = any(
                        (booking.start_time <= slot_start < booking.end_time) or
                        (booking.start_time < slot_end <= booking.end_time) or
                        (slot_start <= booking.start_time < slot_end)
                        for booking in day_bookings
                    )
                    
                    hourly_slots[f"{hour:02d}:00"] = {
                        'available': not is_booked,
                        'hour': hour,
                        'formatted': f"{hour:02d}:00-{hour+1:02d}:00"
                    }
                
                availability[date_str] = {
                    'date': date_str,
                    'day_name': current_date.strftime('%A'),
                    'slots': hourly_slots,
                    'total_bookings': len(day_bookings)
                }
                
                current_date += timedelta(days=1)
            
            return {
                'success': True,
                'court_id': court_id,
                'court_name': court.name,
                'availability': availability,
                'date_range': {
                    'start': check_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Availability check failed: {str(e)}'}
    
    @staticmethod
    def get_booking_statistics(user_id, user_type, period_days=30):
        """Get booking statistics for dashboards"""
        try:
            start_date = datetime.now() - timedelta(days=period_days)
            
            if user_type == 'player':
                query = db.session.query(Booking).filter(
                    Booking.player_id == user_id,
                    Booking.created_at >= start_date
                )
            elif user_type == 'owner':
                query = db.session.query(Booking).join(Court).filter(
                    Court.owner_id == user_id,
                    Booking.created_at >= start_date
                )
            else:  # admin
                query = db.session.query(Booking).filter(
                    Booking.created_at >= start_date
                )
            
            bookings = query.all()
            
            # Calculate statistics
            stats = {
                'total_bookings': len(bookings),
                'confirmed': len([b for b in bookings if b.status == 'confirmed']),
                'pending': len([b for b in bookings if b.status == 'pending']),
                'cancelled': len([b for b in bookings if b.status == 'cancelled']),
                'total_revenue': sum(b.total_cost or b.calculate_cost() for b in bookings if b.status == 'confirmed'),
                'avg_booking_value': 0,
                'popular_times': {},
                'busy_days': {}
            }
            
            if stats['confirmed'] > 0:
                confirmed_bookings = [b for b in bookings if b.status == 'confirmed']
                stats['avg_booking_value'] = stats['total_revenue'] / stats['confirmed']
                
                # Popular times analysis
                time_counts = {}
                for booking in confirmed_bookings:
                    hour = booking.start_time.hour
                    time_counts[hour] = time_counts.get(hour, 0) + 1
                
                stats['popular_times'] = dict(sorted(time_counts.items(), key=lambda x: x[1], reverse=True)[:5])
                
                # Busy days analysis
                day_counts = {}
                for booking in confirmed_bookings:
                    day_name = booking.booking_date.strftime('%A')
                    day_counts[day_name] = day_counts.get(day_name, 0) + 1
                
                stats['busy_days'] = dict(sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3])
            
            return {
                'success': True,
                'period_days': period_days,
                'statistics': stats
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Statistics calculation failed: {str(e)}'}
    
    @staticmethod
    def _send_booking_notification(booking):
        """Send booking confirmation notification"""
        try:
            # Create message for court owner
            owner = booking.court.owner
            message_content = f"""
New booking request for {booking.court.name}

Player: {booking.player.user.full_name}
Date: {booking.booking_date.strftime('%B %d, %Y')}
Time: {booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}
Duration: {booking.get_duration_display()}
Cost: ${booking.total_cost:.2f}

{booking.notes if booking.notes else 'No special requests.'}

Please review and approve this booking request.
            """.strip()
            
            notification = Message(
                sender_id=booking.player_id,
                receiver_id=owner.id,
                content=message_content,
                message_type='booking_request'
            )
            
            db.session.add(notification)
            db.session.commit()
            
            # Try to send email notification if CloudService is available
            try:
                EmailService.send_booking_approval_notification(booking)
            except:
                pass  # Email is optional
                
        except Exception as e:
            # Don't fail the booking if notification fails
            pass
    
    @staticmethod
    def _send_status_change_notification(booking, old_status, new_status, reason=None):
        """Send status change notification"""
        try:
            status_messages = {
                'confirmed': f"Your booking for {booking.court.name} has been confirmed!",
                'cancelled': f"Your booking for {booking.court.name} has been cancelled.",
                'rejected': f"Your booking request for {booking.court.name} was not approved."
            }
            
            message_content = status_messages.get(new_status, f"Booking status updated to {new_status}")
            
            if reason:
                message_content += f"\n\nReason: {reason}"
            
            message_content += f"""
            
Booking Details:
Date: {booking.booking_date.strftime('%B %d, %Y')}
Time: {booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}
Court: {booking.court.name}
            """
            
            notification = Message(
                sender_id=booking.court.owner_id,
                receiver_id=booking.player.user_id,
                content=message_content,
                message_type='booking_update'
            )
            
            db.session.add(notification)
            db.session.commit()
            
        except Exception as e:
            # Don't fail the status update if notification fails
            pass