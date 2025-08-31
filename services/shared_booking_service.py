"""
Shared Booking Service for TennisMatchUp
Manages the two-step booking process between matched players
"""
from datetime import datetime, timedelta, date, time as dt_time
from models.database import db
from models.player import Player
from models.court import Court, Booking
from models.shared_booking import SharedBooking
from services.matching_engine import MatchingEngine
from services.geo_service import GeoService
from sqlalchemy import and_, or_

class SharedBookingService:
    """Manages shared booking workflow between players"""
    
    @staticmethod
    def suggest_courts_for_pair(player1_id, player2_id, max_courts=5):
        """Suggest optimal courts for two players"""
        player1 = Player.query.get(player1_id)
        player2 = Player.query.get(player2_id)
        
        if not player1 or not player2:
            return []
        
        # Get coordinates for both players
        p1_coords = player1.get_coordinates()
        p2_coords = player2.get_coordinates()
        
        if not p1_coords or not p2_coords:
            return []
        
        # Use MatchingEngine's court suggestion algorithm
        court_suggestions = MatchingEngine.suggest_meeting_points(
            p1_coords, p2_coords, max_courts
        )
        
        return court_suggestions
    
    @staticmethod
    def create_booking_proposal(player1_id, player2_id, court_id, booking_date, 
                               start_time, end_time, notes=None):
        """Player1 proposes a joint booking to Player2"""
        
        # Validate inputs
        validation = SharedBookingService._validate_booking_proposal(
            player1_id, player2_id, court_id, booking_date, start_time, end_time
        )
        
        if not validation['valid']:
            return {'success': False, 'error': validation['reason']}
        
        # Check for existing proposals between these players
        existing = SharedBooking.query.filter(
            or_(
                and_(SharedBooking.player1_id == player1_id, SharedBooking.player2_id == player2_id),
                and_(SharedBooking.player1_id == player2_id, SharedBooking.player2_id == player1_id)
            ),
            SharedBooking.status.in_(['proposed', 'counter_proposed'])
        ).first()
        
        if existing:
            return {'success': False, 'error': 'There is already a pending proposal between you'}
        
        # Create shared booking proposal
        shared_booking = SharedBooking(
            player1_id=player1_id,
            player2_id=player2_id,
            court_id=court_id,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            initiator_notes=notes
        )
        
        try:
            db.session.add(shared_booking)
            db.session.commit()
            
            return {
                'success': True,
                'shared_booking_id': shared_booking.id,
                'proposal': shared_booking.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': 'Failed to create proposal'}
    
    @staticmethod
    def respond_to_proposal(shared_booking_id, responding_player_id, action, 
                           notes=None, alternative_court_id=None, alternative_date=None,
                           alternative_start_time=None, alternative_end_time=None):
        """Player2 responds to proposal: accept, counter_propose, or decline"""
        
        shared_booking = SharedBooking.query.get(shared_booking_id)
        if not shared_booking:
            return {'success': False, 'error': 'Proposal not found'}
        
        # Validate responding player
        if shared_booking.player2_id != responding_player_id:
            return {'success': False, 'error': 'Not authorized to respond to this proposal'}
        
        # Check if already responded or expired
        if shared_booking.status not in ['proposed', 'counter_proposed']:
            return {'success': False, 'error': 'This proposal is no longer active'}
        
        if shared_booking.is_expired():
            shared_booking.status = 'expired'
            db.session.commit()
            return {'success': False, 'error': 'This proposal has expired'}
        
        try:
            if action == 'accept':
                shared_booking.accept_proposal(notes)
                result = {'success': True, 'action': 'accepted', 'message': 'Proposal accepted! Ready for final booking.'}
                
            elif action == 'counter_propose':
                shared_booking.counter_propose(
                    alternative_court_id, alternative_date,
                    alternative_start_time, alternative_end_time, notes
                )
                result = {'success': True, 'action': 'counter_proposed', 'message': 'Counter-proposal sent!'}
                
            elif action == 'decline':
                shared_booking.cancel(responding_player_id, notes)
                result = {'success': True, 'action': 'declined', 'message': 'Proposal declined.'}
                
            else:
                return {'success': False, 'error': 'Invalid action'}
            
            db.session.commit()
            result['proposal'] = shared_booking.to_dict()
            return result
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': 'Failed to process response'}
    
    @staticmethod
    def finalize_booking(shared_booking_id, confirming_player_id):
        """Create final court booking after both players agree"""
        
        shared_booking = SharedBooking.query.get(shared_booking_id)
        if not shared_booking:
            return {'success': False, 'error': 'Shared booking not found'}
        
        # Validate confirming player (must be player1 if responding to counter-proposal)
        if shared_booking.status == 'counter_proposed' and confirming_player_id != shared_booking.player1_id:
            return {'success': False, 'error': 'Only the original proposer can confirm counter-proposals'}
        
        if shared_booking.status == 'accepted' and confirming_player_id not in [shared_booking.player1_id, shared_booking.player2_id]:
            return {'success': False, 'error': 'Not authorized to confirm this booking'}
        
        # Handle counter-proposal acceptance
        if shared_booking.status == 'counter_proposed':
            shared_booking.accept_counter_proposal()
        
        # Create final booking
        success, result = shared_booking.confirm_booking()
        
        if success:
            try:
                db.session.commit()
                return {
                    'success': True,
                    'booking_id': result.id,
                    'message': 'Court booked successfully! Both players will receive confirmation.',
                    'booking_details': {
                        'court_name': shared_booking.court.name,
                        'date': shared_booking.booking_date.isoformat(),
                        'time': f"{shared_booking.start_time.strftime('%H:%M')} - {shared_booking.end_time.strftime('%H:%M')}",
                        'total_cost': shared_booking.total_cost,
                        'cost_per_player': shared_booking.player1_share
                    }
                }
            except Exception as e:
                db.session.rollback()
                return {'success': False, 'error': 'Failed to save final booking'}
        else:
            return {'success': False, 'error': result}
    
    @staticmethod
    def get_player_shared_bookings(player_id, include_expired=False):
        """Get all shared bookings for a player"""
        
        query = SharedBooking.query.filter(
            or_(
                SharedBooking.player1_id == player_id,
                SharedBooking.player2_id == player_id
            )
        )
        
        if not include_expired:
            query = query.filter(SharedBooking.status != 'expired')
        
        shared_bookings = query.order_by(SharedBooking.proposed_at.desc()).all()
        
        # Add role information for each booking
        booking_list = []
        for sb in shared_bookings:
            booking_data = sb.to_dict()
            booking_data['user_role'] = 'initiator' if sb.player1_id == player_id else 'partner'
            booking_data['other_player'] = sb.get_other_player(player_id)
            booking_list.append(booking_data)
        
        return booking_list
    
    @staticmethod
    def get_pending_proposals_for_player(player_id):
        """Get proposals awaiting response from player"""
        
        proposals = SharedBooking.query.filter(
            SharedBooking.player2_id == player_id,
            SharedBooking.status.in_(['proposed', 'counter_proposed'])
        ).filter(
            SharedBooking.expires_at > datetime.utcnow()
        ).order_by(SharedBooking.proposed_at.desc()).all()
        
        return [proposal.to_dict() for proposal in proposals]
    
    @staticmethod
    def cleanup_expired_proposals():
        """Mark expired proposals as expired (run periodically)"""
        
        expired_count = SharedBooking.query.filter(
            SharedBooking.status.in_(['proposed', 'counter_proposed']),
            SharedBooking.expires_at <= datetime.utcnow()
        ).update({'status': 'expired'})
        
        if expired_count > 0:
            db.session.commit()
        
        return expired_count
    
    @staticmethod
    def _validate_booking_proposal(player1_id, player2_id, court_id, booking_date, start_time, end_time):
        """Validate booking proposal parameters"""
        result = {'valid': True, 'reason': ''}
        
        # Basic validation
        if player1_id == player2_id:
            result['valid'] = False
            result['reason'] = 'Cannot book with yourself'
            return result
        
        # Validate players exist
        player1 = Player.query.get(player1_id)
        player2 = Player.query.get(player2_id)
        
        if not player1 or not player2:
            result['valid'] = False
            result['reason'] = 'One or both players not found'
            return result
        
        # Validate court exists and is active
        court = Court.query.get(court_id)
        if not court or not court.is_active:
            result['valid'] = False
            result['reason'] = 'Court not available'
            return result
        
        # Validate date and time
        if isinstance(booking_date, str):
            try:
                booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
            except:
                result['valid'] = False
                result['reason'] = 'Invalid date format'
                return result
        
        if booking_date <= date.today():
            result['valid'] = False
            result['reason'] = 'Booking date must be in the future'
            return result
        
        # Validate time slot
        if isinstance(start_time, str):
            try:
                start_time = datetime.strptime(start_time, '%H:%M').time()
            except:
                result['valid'] = False
                result['reason'] = 'Invalid start time format'
                return result
                
        if isinstance(end_time, str):
            try:
                end_time = datetime.strptime(end_time, '%H:%M').time()
            except:
                result['valid'] = False
                result['reason'] = 'Invalid end time format'
                return result
        
        if start_time >= end_time:
            result['valid'] = False
            result['reason'] = 'End time must be after start time'
            return result
        
        # Check court availability
        if not court.is_available(booking_date, start_time, end_time):
            result['valid'] = False
            result['reason'] = 'Court is not available for this time slot'
            return result
        
        return result
    
    @staticmethod
    def get_booking_statistics():
        """Get statistics about shared bookings"""
        
        total_proposals = SharedBooking.query.count()
        confirmed_bookings = SharedBooking.query.filter_by(status='confirmed').count()
        pending_proposals = SharedBooking.query.filter(
            SharedBooking.status.in_(['proposed', 'counter_proposed'])
        ).count()
        
        # Success rate
        success_rate = (confirmed_bookings / total_proposals * 100) if total_proposals > 0 else 0
        
        return {
            'total_proposals': total_proposals,
            'confirmed_bookings': confirmed_bookings,
            'pending_proposals': pending_proposals,
            'success_rate': round(success_rate, 1)
        }