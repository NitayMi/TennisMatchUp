"""
Player Routes for TennisMatchUp
CLEANED VERSION - All business logic moved to Services
Controllers only handle HTTP concerns
"""
from warnings import filters
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
import json
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from models.user import User
from models.player import Player
from models.court import Court, Booking
from models.message import Message
from models.database import db
from models.shared_booking import SharedBooking
from utils.decorators import login_required, player_required
from services.booking_service import BookingService
from services.matching_engine import MatchingEngine
from services.rule_engine import RuleEngine


player_bp = Blueprint('player', __name__, url_prefix='/player')

@player_bp.route('/dashboard')
@login_required
@player_required
def dashboard():
    """Player dashboard - CLEANED VERSION"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Get dashboard stats using service
    stats_result = BookingService.get_booking_statistics(player.id, 'player', period_days=30)
    stats = stats_result.get('statistics', {}) if stats_result['success'] else {}
    
    # Get recent bookings using service - but we need actual booking objects for template
    today = datetime.now().date()
    
    # Get actual Booking objects instead of dictionaries
    upcoming_bookings = Booking.query.join(Court).filter(
        Booking.player_id == player.id,
        Booking.booking_date >= today
    ).order_by(Booking.booking_date.asc()).limit(10).all()
    
    recent_bookings = Booking.query.join(Court).filter(
        Booking.player_id == player.id,
        Booking.booking_date < today
    ).order_by(Booking.booking_date.desc()).limit(5).all()
    
    # Get matches and messages
    try:
        recent_matches = MatchingEngine.find_matches(player.id, limit=5)
    except:
        recent_matches = []
    
    try:
        unread_messages = Message.query.filter_by(
            recipient_id=player.user_id, 
            is_read=False
        ).count()
    except:
        unread_messages = 0
    
    return render_template('player/dashboard.html', 
                         player=player,
                         stats=stats,
                         upcoming_bookings=upcoming_bookings,
                         recent_bookings=recent_bookings,
                         recent_matches=recent_matches,
                         unread_messages=unread_messages)


@player_bp.route('/book-court')
@login_required
@player_required
def book_court():
    """Show court booking page - CLEANED VERSION"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Debug: בדוק כמה מגרשים יש
    # all_courts = Court.query.all()
    active_courts = Court.query.filter_by(is_active=True).all()
    
    # print(f"DEBUG: Total courts: {len(all_courts)}")
    # print(f"DEBUG: Active courts: {len(active_courts)}")
    # for court in all_courts:
    #     print(f"Court: {court.name}, Active: {court.is_active}")
    
    courts = active_courts  # רק מגרשים פעילים  
    
    # Get booking date from query params
    booking_date = request.args.get('date')
    
    # הוסף את הfilters החסרים
    filters = {
        'location': request.args.get('location'),
        'court_type': request.args.get('court_type'),
        'surface': request.args.get('surface'),
        'max_price': request.args.get('max_price'),
        'date': booking_date
    }
    
    return render_template('player/book_court.html',
                         available_courts=courts,
                         player=player,
                         booking_date=booking_date,
                         filters=filters)


@player_bp.route('/submit-booking', methods=['POST'])
@login_required
@player_required
def submit_booking():
    """Submit booking request - CLEANED VERSION"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Extract form data
    booking_data = {
        'court_id': request.form.get('court_id', type=int),
        'booking_date': request.form.get('booking_date'),
        'start_time': request.form.get('start_time'),
        'end_time': request.form.get('end_time'),
        'notes': request.form.get('notes', '').strip()
    }
    
    # Delegate to service
    result = BookingService.process_booking_request(
        player_id=player.id,
        **booking_data
    )
    
    if result['success']:
        flash(result['message'], 'success')
        return jsonify(result)
    else:
        return jsonify(result), 400

@player_bp.route('/my-bookings')
@login_required
@player_required
def my_bookings():
    """View player bookings - CLEANED VERSION"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Get bookings using service
    result = BookingService.get_player_bookings(
        player_id=player.id,
        limit=50,
        status_filter=request.args.get('status')
    )
    
    bookings = result.get('bookings', []) if result['success'] else []
    
    return render_template('player/my_bookings.html',
                         bookings=bookings,
                         player=player)

@player_bp.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
@player_required
def cancel_booking(booking_id):
    """Cancel booking - CLEANED VERSION"""
    user_id = session['user_id']
    reason = request.form.get('reason', 'Cancelled by player')
    
    # Delegate to service
    result = BookingService.update_booking_status(
        booking_id=booking_id,
        new_status='cancelled',
        reason=reason,
        user_id=user_id,
        user_type='player'
    )
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('player.my_bookings'))

@player_bp.route('/my-calendar')
@login_required
@player_required
def my_calendar():
    """Player calendar view - UNIFIED VERSION"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    if not player:
        return render_template('player/my_calendar.html',
                             player=None,
                             bookings=[],
                             booking_groups={'confirmed': [], 'pending': [], 'cancelled': []},
                             bookings_json='[]')
    
    # Date range for calendar
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now() + timedelta(days=90)
    
    # UNIFIED BOOKING DATA COLLECTION
    all_bookings_data = []
    
    # 1. Regular bookings
    regular_bookings = Booking.query.join(Court).options(joinedload(Booking.court)).filter(
        Booking.player_id == player.id,
        Booking.booking_date.between(start_date.date(), end_date.date())
    ).all()
    
    for b in regular_bookings:
        try:
            all_bookings_data.append({
                'id': b.id,
                'type': 'regular',
                'booking_date': b.booking_date.isoformat(),
                'start_time': b.start_time.strftime('%H:%M'),
                'end_time': b.end_time.strftime('%H:%M'),
                'status': b.status,
                'court': {
                    'id': b.court.id,
                    'name': b.court.name,
                    'location': b.court.location or 'Unknown Location'
                },
                'total_cost': float(b.total_cost or b.calculate_cost()),
                'partner': None  # Regular bookings have no partner
            })
        except Exception as e:
            print(f"Error processing regular booking {b.id}: {e}")
            continue
    
    # 2. Shared bookings
    shared_bookings = SharedBooking.query.filter(
        or_(
            SharedBooking.player1_id == player.id,
            SharedBooking.player2_id == player.id
        ),
        SharedBooking.status.in_(['accepted', 'confirmed']),
        SharedBooking.booking_date.between(start_date.date(), end_date.date())
    ).all()
    
    for sb in shared_bookings:
        try:
            partner_name = sb.get_other_player(player.id).user.full_name
            all_bookings_data.append({
                'id': f"shared_{sb.id}",
                'type': 'shared',
                'booking_date': sb.booking_date.isoformat(),
                'start_time': sb.start_time.strftime('%H:%M'),
                'end_time': sb.end_time.strftime('%H:%M'),
                'status': 'shared',
                'court': {
                    'id': sb.court.id,
                    'name': sb.court.name,
                    'location': sb.court.location
                },
                'total_cost': float(sb.total_cost),
                'partner': partner_name
            })
        except Exception as e:
            print(f"Error processing shared booking {sb.id}: {e}")
            continue
    
    # Group for template stats (only regular bookings for stats)
    booking_groups = {
        'confirmed': [b for b in regular_bookings if b.status == 'confirmed'],
        'pending': [b for b in regular_bookings if b.status == 'pending'],
        'cancelled': [b for b in regular_bookings if b.status == 'cancelled']
    }
    
    # Sort by date and time
    all_bookings_data.sort(key=lambda x: (x['booking_date'], x['start_time']))
    
    return render_template('player/my_calendar.html',
                         player=player,
                         bookings=regular_bookings,  # For template compatibility
                         booking_groups=booking_groups,
                         bookings_json=json.dumps(all_bookings_data))

@player_bp.route('/find-matches')
@login_required
@player_required
def find_matches():
    """Find compatible players - CLEANED VERSION"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Get matches using service
    matches = MatchingEngine.find_matches(
        player_id=player.id,
        skill_level=request.args.get('skill_level'),
        location=request.args.get('location'),
        limit=request.args.get('limit', 10, type=int)
    )
    
    return render_template('player/find_matches.html',
                         matches=matches,
                         player=player)

@player_bp.route('/send-match-request', methods=['POST'])
@login_required
@player_required
def send_match_request():
    """Send match request to another player - UPDATED FOR INTEGRATION"""
    user_id = session['user_id']
    target_player_id = request.form.get('target_player_id', type=int)
    message_content = request.form.get('message', '').strip()
    
    if not target_player_id:
        return jsonify({'success': False, 'error': 'Target player required'}), 400
    
    # Get target user
    target_player = Player.query.get(target_player_id)
    if not target_player:
        return jsonify({'success': False, 'error': 'Player not found'}), 404
    
    # Create default message if none provided
    if not message_content:
        user = User.query.get(user_id)
        message_content = f"Hi! I'm {user.full_name} and I'd like to play tennis with you. Are you available for a match?"
    
    # Use MessagingService instead of direct Message creation
    from services.messaging_service import MessagingService
    
    result = MessagingService.send_message(
        sender_id=user_id,
        receiver_id=target_player.user_id,
        content=message_content,
        message_type='match_request'
    )
    
    if result['success']:
        # Direct to messaging conversation
        conversation_url = url_for('messaging.conversation', other_user_id=target_player.user_id)
        
        return jsonify({
            'success': True,
            'message': f'Match request sent to {target_player.user.full_name}!',
            'conversation_url': conversation_url,
            'message_id': result['message_id']
        })
    else:
        return jsonify(result), 500

@player_bp.route('/messages')
@login_required
@player_required
def messages():
    """Redirect to messaging system"""
    return redirect(url_for('messaging.inbox'))

@player_bp.route('/profile')
@login_required
@player_required
def profile():
    """View/Edit profile - CLEANED VERSION"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    player = Player.query.filter_by(user_id=user_id).first()
    
    return render_template('player/profile.html', user=user, player=player)

@player_bp.route('/update-profile', methods=['POST'])
@login_required
@player_required
def update_profile():
    """Update profile - CLEANED VERSION"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Update basic user info
    user.full_name = request.form.get('full_name', '').strip()
    user.phone_number = request.form.get('phone_number', '').strip()
    
    # Update player-specific info
    player.skill_level = request.form.get('skill_level')
    player.preferred_location = request.form.get('preferred_location', '').strip()
    player.bio = request.form.get('bio', '').strip()
    
    try:
        db.session.commit()
        flash('Profile updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating profile', 'error')
    
    return redirect(url_for('player.profile'))

@player_bp.route('/get-court-availability')
@login_required
@player_required
def get_court_availability():
    """Get court availability via AJAX - CLEANED VERSION"""
    court_id = request.args.get('court_id', type=int)
    date = request.args.get('date')
    
    if not court_id or not date:
        return jsonify({'success': False, 'error': 'Missing parameters'}), 400
    
    # Delegate to service
    result = BookingService.get_court_availability(
        court_id=court_id,
        check_date=date,
        days_ahead=1
    )
    
    return jsonify(result)

@player_bp.route('/calculate-cost')
@login_required
@player_required
def calculate_cost():
    """Calculate booking cost via AJAX - CLEANED VERSION"""
    court_id = request.args.get('court_id', type=int)
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    if not all([court_id, start_time, end_time]):
        return jsonify({'success': False, 'error': 'Missing parameters'}), 400
    
    # Delegate to service
    result = BookingService.calculate_booking_cost(court_id, start_time, end_time)
    
    return jsonify(result)

@player_bp.route('/search-courts')
@login_required
@player_required
def search_courts():
    """Search courts with filters - CLEANED VERSION"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Get search parameters
    search_params = {
        'location': request.args.get('location'),
        'court_type': request.args.get('court_type'),
        'max_distance': request.args.get('max_distance', 25, type=int),
        'max_price': request.args.get('max_price', type=int),
        'date': request.args.get('date'),
        'time': request.args.get('time')
    }
    
    # Use matching engine for search
    courts = MatchingEngine.recommend_courts(
        player_id=player.id,
        **{k: v for k, v in search_params.items() if v is not None}
    )
    
    return render_template('player/search_results.html',
                         courts=courts,
                         search_params=search_params)

@player_bp.route('/settings')
@login_required
@player_required
def settings():
    """Player settings page - CLEANED VERSION"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    player = Player.query.filter_by(user_id=user_id).first()
    
    return render_template('player/settings.html', user=user, player=player)