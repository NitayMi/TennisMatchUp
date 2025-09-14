"""
API Routes for TennisMatchUp
RESTful endpoints for frontend interactions
"""
from flask import Blueprint, jsonify, request, session
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court, Booking
from models.shared_booking import SharedBooking
from models.message import Message
from services.court_recommendation_engine import CourtRecommendationEngine
from utils.decorators import login_required, api_required
from services.booking_service import BookingService
from services.revenue_service import RevenueService
from services.report_service import ReportService
from services.matching_engine import MatchingEngine
from services.shared_booking_service import SharedBookingService
from services.rule_engine import RuleEngine
from datetime import datetime, timedelta
import json

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ========================= CHAT-RELATED ENDPOINTS =========================

@api_bp.route('/users/available-for-chat')
@login_required
def available_users_for_chat():
    """Get users available for chat (excluding current user)"""
    current_user_id = session.get('user_id')
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    try:
        # Get all active users except current user
        query = User.query.filter(
            User.id != current_user_id,
            User.is_active == True
        )
        
        # Role-based filtering
        if current_user.user_type == 'player':
            # Players can chat with other players and owners
            query = query.filter(User.user_type.in_(['player', 'owner']))
        elif current_user.user_type == 'owner':
            # Owners can chat with players and other owners
            query = query.filter(User.user_type.in_(['player', 'owner']))
        # Admin can chat with everyone (no additional filter)
        
        users = query.order_by(User.full_name).limit(50).all()
        
        user_list = []
        for user in users:
            user_data = {
                'id': user.id,
                'name': user.full_name,
                'user_type': user.user_type,
                'email': user.email if current_user.user_type == 'admin' else None
            }
            user_list.append(user_data)
        
        return jsonify({
            'success': True,
            'users': user_list
        })
        
    except Exception as e:
        from services.rule_engine import RuleEngine
        return jsonify({'success': False, 'error': 'Failed to load users'}), 500

# ========================= BOOKING ENDPOINTS =========================

@api_bp.route('/bookings', methods=['GET'])
@login_required
def get_bookings():
    """Get bookings for current user"""
    try:
        user_id = session['user_id']
        user_type = session.get('user_type', 'player')
        
        if user_type == 'player':
            player = Player.query.filter_by(user_id=user_id).first()
            if not player:
                return jsonify({'success': False, 'error': 'Player not found'}), 404
            
            result = BookingService.get_player_bookings(
                player.id,
                limit=request.args.get('limit', 20, type=int),
                status_filter=request.args.get('status')
            )
        else:
            # For owners/admins, implement different logic
            result = {'success': False, 'error': 'Not implemented for this user type'}
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/bookings/<int:booking_id>', methods=['GET'])
@login_required
def get_booking(booking_id):
    """Get specific booking details"""
    try:
        result = BookingService.get_booking_details(booking_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/bookings', methods=['POST'])
@login_required
def create_booking():
    """Create a new booking"""
    try:
        user_id = session['user_id']
        player = Player.query.filter_by(user_id=user_id).first()
        
        if not player:
            return jsonify({'success': False, 'error': 'Player not found'}), 404
        
        data = request.get_json()
        
        result = BookingService.process_booking_request(
            player_id=player.id,
            court_id=data.get('court_id'),
            booking_date=data.get('booking_date'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            notes=data.get('notes')
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/bookings/<int:booking_id>/status', methods=['PUT'])
@login_required
def update_booking_status(booking_id):
    """Update booking status"""
    try:
        user_id = session['user_id']
        user_type = session.get('user_type')
        data = request.get_json()
        
        result = BookingService.update_booking_status(
            booking_id=booking_id,
            new_status=data.get('status'),
            reason=data.get('reason'),
            user_id=user_id,
            user_type=user_type
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/courts/<int:court_id>/availability', methods=['GET'])
@login_required
def get_court_availability(court_id):
    """Get court availability calendar"""
    try:
        check_date = request.args.get('date', datetime.now().date().isoformat())
        days_ahead = request.args.get('days', 7, type=int)
        
        result = BookingService.get_court_availability(
            court_id=court_id,
            check_date=check_date,
            days_ahead=days_ahead
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================= MATCHING ENDPOINTS =========================

@api_bp.route('/matches/find', methods=['GET'])
@login_required
def find_matches():
    """Find compatible players"""
    try:
        user_id = session['user_id']
        player = Player.query.filter_by(user_id=user_id).first()
        
        if not player:
            return jsonify({'success': False, 'error': 'Player not found'}), 404
        
        matches = MatchingEngine.find_matches(
            player_id=player.id,
            skill_level=request.args.get('skill_level'),
            location=request.args.get('location'),
            limit=request.args.get('limit', 10, type=int)
        )
        
        return jsonify({
            'success': True,
            'matches': matches,
            'count': len(matches)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/matches/courts', methods=['GET'])
@login_required
def find_courts():
    """Find available courts"""
    try:
        user_id = session['user_id']
        player = Player.query.filter_by(user_id=user_id).first()
        
        if not player:
            return jsonify({'success': False, 'error': 'Player not found'}), 404
        
        courts = CourtRecommendationEngine.find_recommended_courts(
            player_id=player.id,
            location=request.args.get('location'),
            max_distance=request.args.get('max_distance', 25, type=int),
            limit=request.args.get('limit', 10, type=int)
        )
        
        return jsonify({
            'success': True,
            'courts': courts,
            'count': len(courts)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================= SHARED BOOKING ENDPOINTS =========================

@api_bp.route('/shared-bookings/propose', methods=['POST'])
@login_required
def propose_shared_booking():
    """Propose a shared booking"""
    try:
        user_id = session['user_id']
        player = Player.query.filter_by(user_id=user_id).first()
        
        if not player:
            return jsonify({'success': False, 'error': 'Player not found'}), 404
        
        data = request.get_json()
        
        result = SharedBookingService.create_booking_proposal(
            player1_id=player.id,
            player2_id=data.get('partner_id'),
            court_id=data.get('court_id'),
            booking_date=data.get('booking_date'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            notes=data.get('notes')
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/shared-bookings/<int:booking_id>/respond', methods=['POST'])
@login_required
def respond_to_shared_booking(booking_id):
    """Respond to a shared booking proposal"""
    try:
        user_id = session['user_id']
        data = request.get_json()
        action = data.get('action')  # 'accept', 'counter', 'reject'
        
        shared_booking = SharedBooking.query.get(booking_id)
        if not shared_booking:
            return jsonify({'success': False, 'error': 'Shared booking not found'}), 404
        
        # Verify user is the intended recipient
        if shared_booking.player2.user_id != user_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        if action == 'accept':
            result = shared_booking.accept_proposal(data.get('notes'))
        elif action == 'counter':
            result = shared_booking.counter_propose(
                alternative_court_id=data.get('court_id'),
                alternative_date=data.get('booking_date'),
                alternative_start_time=data.get('start_time'),
                alternative_end_time=data.get('end_time'),
                alternative_notes=data.get('notes')
            )
        else:  # reject
            result = shared_booking.reject_proposal(data.get('reason'))
        
        if result:
            db.session.commit()
            return jsonify({'success': True, 'message': f'Proposal {action}ed successfully'})
        else:
            return jsonify({'success': False, 'error': f'Failed to {action} proposal'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================= REVENUE ENDPOINTS =========================

@api_bp.route('/revenue/monthly', methods=['GET'])
@login_required
def get_monthly_revenue():
    """Get monthly revenue for owner"""
    try:
        user_id = session['user_id']
        user_type = session.get('user_type')
        
        if user_type not in ['owner', 'admin']:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        
        result = RevenueService.calculate_monthly_revenue(
            owner_id=user_id,
            month=month,
            year=year
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/revenue/analytics', methods=['GET'])
@login_required
def get_revenue_analytics():
    """Get comprehensive revenue analytics"""
    try:
        user_id = session['user_id']
        user_type = session.get('user_type')
        
        if user_type not in ['owner', 'admin']:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        period_days = request.args.get('period', 90, type=int)
        
        result = RevenueService.get_revenue_analytics(
            owner_id=user_id,
            period_days=period_days
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================= ADMIN ENDPOINTS =========================

@api_bp.route('/admin/stats', methods=['GET'])
@login_required
def get_admin_stats():
    """Get admin dashboard statistics"""
    try:
        user_type = session.get('user_type')
        
        if user_type != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        result = ReportService.generate_admin_dashboard_stats()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/admin/performance', methods=['GET'])
@login_required
def get_system_performance():
    """Get system performance metrics"""
    try:
        user_type = session.get('user_type')
        
        if user_type != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        period_days = request.args.get('period', 30, type=int)
        
        result = ReportService.system_performance_metrics(period_days)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/admin/insights', methods=['GET'])
@login_required
def get_business_insights():
    """Get business insights and recommendations"""
    try:
        user_type = session.get('user_type')
        
        if user_type != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        period_days = request.args.get('period', 90, type=int)
        
        result = ReportService.generate_business_insights(period_days)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================= UTILITY ENDPOINTS =========================

@api_bp.route('/calculate-cost', methods=['POST'])
@login_required
def calculate_booking_cost():
    """Calculate booking cost"""
    try:
        data = request.get_json()
        
        result = BookingService.calculate_booking_cost(
            court_id=data.get('court_id'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time')
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/validate-booking', methods=['POST'])
@login_required
def validate_booking():
    """Validate booking parameters"""
    try:
        data = request.get_json()
        
        result = BookingService.validate_booking_time(
            court_id=data.get('court_id'),
            booking_date=data.get('booking_date'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time')
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/search', methods=['GET'])
@login_required
def search_platform():
    """Global search across courts and players"""
    try:
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'all')  # 'courts', 'players', 'all'
        limit = request.args.get('limit', 10, type=int)
        
        if not query or len(query) < 2:
            return jsonify({'success': False, 'error': 'Search query too short'}), 400
        
        results = {'courts': [], 'players': []}
        
        if search_type in ['courts', 'all']:
            courts = Court.query.filter(
                Court.is_active == True,
                db.or_(
                    Court.name.ilike(f'%{query}%'),
                    Court.location.ilike(f'%{query}%'),
                    Court.description.ilike(f'%{query}%')
                )
            ).limit(limit).all()
            
            results['courts'] = [{
                'id': court.id,
                'name': court.name,
                'location': court.location,
                'hourly_rate': court.hourly_rate,
                'court_type': court.court_type,
                'surface': court.surface,
                'description': court.description,
                'owner_name': court.owner.full_name
            } for court in courts]
        
        if search_type in ['players', 'all']:
            players = db.session.query(Player, User).join(User).filter(
                User.is_active == True,
                db.or_(
                    User.full_name.ilike(f'%{query}%'),
                    Player.preferred_location.ilike(f'%{query}%')
                )
            ).limit(limit).all()
            
            results['players'] = [{
                'id': player.id,
                'name': user.full_name,
                'skill_level': player.skill_level,
                'preferred_location': player.preferred_location,
                'bio': player.bio
            } for player, user in players]
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'total_results': len(results['courts']) + len(results['players'])
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================= STATISTICS ENDPOINTS =========================

@api_bp.route('/stats/booking-stats', methods=['GET'])
@login_required
def get_booking_statistics():
    """Get booking statistics for current user"""
    try:
        user_id = session['user_id']
        user_type = session.get('user_type')
        period_days = request.args.get('period', 30, type=int)
        
        result = BookingService.get_booking_statistics(
            user_id=user_id,
            user_type=user_type,
            period_days=period_days
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/stats/top-performers', methods=['GET'])
@login_required
def get_top_performers():
    """Get top performing users and courts"""
    try:
        user_type = session.get('user_type')
        
        if user_type != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        period_days = request.args.get('period', 30, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        result = ReportService.get_top_performers(
            period_days=period_days,
            limit=limit
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================= NOTIFICATION ENDPOINTS =========================

@api_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get user notifications"""
    try:
        user_id = session['user_id']
        limit = request.args.get('limit', 20, type=int)
        unread_only = request.args.get('unread_only', False, type=bool)
        
        query = Message.query.filter_by(receiver_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        messages = query.order_by(Message.created_at.desc()).limit(limit).all()
        
        notifications = []
        for message in messages:
            notifications.append({
                'id': message.id,
                'sender_name': message.sender.full_name,
                'content': message.content[:100] + ('...' if len(message.content) > 100 else ''),
                'full_content': message.content,
                'is_read': message.is_read,
                'message_type': getattr(message, 'message_type', 'general'),
                'created_at': message.created_at.isoformat(),
                'created_at_formatted': message.created_at.strftime('%B %d at %H:%M')
            })
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications),
            'unread_count': len([n for n in notifications if not n['is_read']])
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/notifications/<int:message_id>/read', methods=['POST'])
@login_required
def mark_notification_read(message_id):
    """Mark notification as read"""
    try:
        user_id = session['user_id']
        
        message = Message.query.filter_by(
            id=message_id,
            receiver_id=user_id
        ).first()
        
        if not message:
            return jsonify({'success': False, 'error': 'Notification not found'}), 404
        
        message.is_read = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification marked as read'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================= CALENDAR ENDPOINTS =========================

@api_bp.route('/calendar/events', methods=['GET'])
@login_required
def get_calendar_events():
    """Get calendar events for user"""
    try:
        user_id = session['user_id']
        user_type = session.get('user_type')
        
        start_date = request.args.get('start', datetime.now().date().isoformat())
        end_date = request.args.get('end', (datetime.now().date() + timedelta(days=30)).isoformat())
        
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        events = []
        
        if user_type == 'player':
            player = Player.query.filter_by(user_id=user_id).first()
            if player:
                bookings = Booking.query.filter(
                    Booking.player_id == player.id,
                    Booking.booking_date.between(start_date, end_date)
                ).all()
                
                for booking in bookings:
                    events.append({
                        'id': f"booking-{booking.id}",
                        'title': f"Tennis at {booking.court.name}",
                        'start': f"{booking.booking_date}T{booking.start_time}",
                        'end': f"{booking.booking_date}T{booking.end_time}",
                        'color': {
                            'confirmed': '#28a745',
                            'pending': '#ffc107',
                            'cancelled': '#dc3545'
                        }.get(booking.status, '#6c757d'),
                        'status': booking.status,
                        'court_name': booking.court.name,
                        'location': booking.court.location,
                        'cost': booking.total_cost or booking.calculate_cost()
                    })
        
        elif user_type == 'owner':
            # Owner sees all bookings for their courts
            owner_bookings = db.session.query(Booking).join(Court).filter(
                Court.owner_id == user_id,
                Booking.booking_date.between(start_date, end_date)
            ).all()
            
            for booking in owner_bookings:
                events.append({
                    'id': f"booking-{booking.id}",
                    'title': f"{booking.player.user.full_name} - {booking.court.name}",
                    'start': f"{booking.booking_date}T{booking.start_time}",
                    'end': f"{booking.booking_date}T{booking.end_time}",
                    'color': {
                        'confirmed': '#28a745',
                        'pending': '#ffc107',
                        'cancelled': '#dc3545'
                    }.get(booking.status, '#6c757d'),
                    'status': booking.status,
                    'player_name': booking.player.user.full_name,
                    'court_name': booking.court.name,
                    'cost': booking.total_cost or booking.calculate_cost()
                })
        
        return jsonify({
            'success': True,
            'events': events,
            'count': len(events),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================= VALIDATION ENDPOINTS =========================

@api_bp.route('/validate/court-time', methods=['POST'])
@login_required
def validate_court_time():
    """Validate if court time slot is available"""
    try:
        data = request.get_json()
        
        result = RuleEngine.validate_booking(
            court_id=data.get('court_id'),
            booking_date=data.get('booking_date'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            player_id=session.get('player_id')
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================= ERROR HANDLERS =========================

@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({'success': False, 'error': 'API endpoint not found'}), 404

@api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'success': False, 'error': 'Bad request'}), 400

@api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'success': False, 'error': 'Authentication required'}), 401

@api_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'success': False, 'error': 'Access forbidden'}), 403

@api_bp.errorhandler(500)
def internal_server_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ========================= MESSAGING ENDPOINTS =========================

@api_bp.route('/messages/conversation/<int:other_user_id>', methods=['GET'])
@login_required
def get_conversation_messages(other_user_id):
    """Get messages in conversation with another user"""
    try:
        user_id = session['user_id']
        since_id = request.args.get('since', 0, type=int)
        
        # Get messages between current user and other user
        messages = Message.get_conversation_messages(user_id, other_user_id)
        
        # Filter messages since last check (for polling)
        if since_id > 0:
            messages = [msg for msg in messages if msg.id > since_id]
        
        # Convert to dict format
        messages_data = []
        for message in messages:
            msg_dict = message.to_dict()
            msg_dict['is_from_me'] = message.sender_id == user_id
            messages_data.append(msg_dict)
        
        # Check typing status (implement simple in-memory storage)
        typing_info = {
            'is_typing': False,
            'user_id': None
        }
        
        return jsonify({
            'success': True,
            'messages': messages_data,
            'typing_info': typing_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    """Send a new message"""
    try:
        user_id = session['user_id']
        data = request.json
        
        receiver_id = data.get('receiver_id')
        content = data.get('content', '').strip()
        
        if not receiver_id or not content:
            return jsonify({'success': False, 'error': 'Receiver and content required'}), 400
        
        # Use MessagingService for sending
        from services.messaging_service import MessagingService
        
        result = MessagingService.send_message(
            sender_id=user_id,
            receiver_id=receiver_id,
            content=content,
            message_type='text'
        )
        
        if result['success']:
            # Get the full message object to return
            message = Message.query.get(result['message_id'])
            if message:
                msg_dict = message.to_dict()
                msg_dict['is_from_me'] = True
                
                return jsonify({
                    'success': True,
                    'message': msg_dict
                })
        
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/messages/mark-read/<int:other_user_id>', methods=['POST'])
@login_required
def mark_conversation_read(other_user_id):
    """Mark all messages in conversation as read"""
    try:
        user_id = session['user_id']
        
        # Mark conversation as read
        Message.mark_conversation_as_read(user_id, other_user_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/messages/typing', methods=['POST'])
@login_required
def update_typing_status():
    """Update typing status for real-time indicator"""
    try:
        user_id = session['user_id']
        data = request.json
        
        receiver_id = data.get('receiver_id')
        is_typing = data.get('is_typing', False)
        
        # For now, just return success
        # In production, you'd store this in Redis or similar
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500