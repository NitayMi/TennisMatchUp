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
from services.court_recommendation_engine import CourtRecommendationEngine
from services.dashboard_service import DashboardService


player_bp = Blueprint('player', __name__, url_prefix='/player')

@player_bp.route('/dashboard')
@login_required
@player_required
def dashboard():
    """Player dashboard - CLEANED VERSION"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Use DashboardService for comprehensive dashboard data
    dashboard_data = DashboardService.get_player_dashboard_data(player.id)
    
    if not dashboard_data['success']:
        # Instead of redirecting, provide fallback data to prevent redirect loop
        flash(f'Error loading dashboard data: {dashboard_data["error"]}', 'warning')
        dashboard_data = {
            'stats': {'total_bookings': 0, 'confirmed_bookings': 0, 'pending_bookings': 0},
            'upcoming_bookings': [],
            'recommended_courts': [],
            'recent_invites': []
        }
    
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
                         stats=dashboard_data['stats'],
                         upcoming_bookings=dashboard_data['upcoming_bookings'],
                         recommended_courts=dashboard_data['recommended_courts'],
                         recent_invites=dashboard_data['recent_invites'],
                         recent_matches=recent_matches,
                         unread_messages=unread_messages)


@player_bp.route('/book-court')
@login_required
@player_required
def book_court():
    """Show court booking page - ENHANCED with smart recommendations"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Get query parameters
    booking_date = request.args.get('date')
    sort_by = request.args.get('sort', 'recommended')  # Default to recommended
    show_all = request.args.get('show_all', '').lower() == 'true'
    
    # Build filters
    filters = {
        'location': request.args.get('location'),
        'court_type': request.args.get('court_type'),
        'surface': request.args.get('surface'),
        'max_price': request.args.get('max_price'),
        'date': booking_date
    }
    # Remove empty filters
    filters = {k: v for k, v in filters.items() if v}
    
    # Get courts using smart recommendation engine
    if show_all:
        # Show all courts with basic sorting - no recommendation scoring
        court_results = CourtRecommendationEngine.get_all_courts_with_basic_sorting(
            filters=filters,
            sort_by=sort_by,
            limit=100
        )
    else:
        # Use smart recommendations
        court_results = CourtRecommendationEngine.find_recommended_courts(
            player_id=player.id,
            filters=filters,
            sort_by=sort_by,
            limit=50
        )
    
    # Extract courts and metadata for template
    courts_with_metadata = []
    for result in court_results:
        court_data = {
            'court': result['court'],
            'total_score': result['total_score'],
            'distance_km': result['distance_km'],
            'score_data': result['score_data']
        }
        # Add recommendation explanation if using recommendations
        if not show_all and result['total_score'] > 0:
            court_data['recommendation_reasons'] = CourtRecommendationEngine.get_recommendation_explanation(
                result['score_data']
            )
        courts_with_metadata.append(court_data)
    
    # Get sort options for template
    sort_options = CourtRecommendationEngine.get_sort_options()
    
    return render_template('player/book_court.html',
                         available_courts=[c['court'] for c in courts_with_metadata],
                         courts_metadata=courts_with_metadata,
                         player=player,
                         booking_date=booking_date,
                         filters=filters,
                         sort_by=sort_by,
                         sort_options=sort_options,
                         show_all=show_all,
                         total_courts=len(courts_with_metadata))


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
    """Player calendar view - Clean MVC version using DashboardService"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    if not player:
        return render_template('player/my_calendar.html',
                             player=None,
                             bookings=[],
                             booking_groups={'confirmed': [], 'pending': [], 'cancelled': []},
                             bookings_json='[]')
    
    # Use DashboardService for unified calendar data
    calendar_data = DashboardService.get_unified_calendar_data(player.id)
    
    if not calendar_data['success']:
        flash(f'Error loading calendar: {calendar_data["error"]}', 'error')
        return render_template('player/my_calendar.html',
                             player=player,
                             bookings=[],
                             booking_groups={'confirmed': [], 'pending': [], 'cancelled': []},
                             bookings_json='[]')
    
    # Create booking groups for template compatibility using actual booking objects
    all_booking_objects = calendar_data['booking_objects']
    regular_bookings = [b for b in all_booking_objects if hasattr(b, 'player_id')]  # Regular bookings have player_id
    
    booking_groups = {
        'confirmed': [b for b in regular_bookings if b.status == 'confirmed'],
        'pending': [b for b in regular_bookings if b.status == 'pending'],
        'cancelled': [b for b in regular_bookings if b.status == 'cancelled']
    }
    
    return render_template('player/my_calendar.html',
                         player=player,
                         bookings=regular_bookings,  # Actual booking objects for template
                         booking_groups=booking_groups,
                         bookings_json=calendar_data['bookings_json'])

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