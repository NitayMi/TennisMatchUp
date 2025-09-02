from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from models.user import User
from models.player import Player
from models.court import Court, Booking
from models.message import Message
from models.database import db
from utils.decorators import login_required, player_required
from services.matching_engine import MatchingEngine
from services.rule_engine import RuleEngine
from datetime import datetime, date, time, timedelta

player_bp = Blueprint('player', __name__, url_prefix='/player')

@player_bp.route('/dashboard')
@login_required
@player_required
def dashboard():
    """Player dashboard showing matches, bookings, and notifications"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Get recent matches/recommendations
    recent_matches = MatchingEngine.get_recent_matches(player.id)
    
    # Get upcoming bookings
    upcoming_bookings = Booking.query.filter_by(
        player_id=player.id,
        status='confirmed'
    ).filter(Booking.booking_date >= db.func.current_date()).limit(5).all()
    
    # Get unread messages
    unread_messages = Message.query.filter_by(
        receiver_id=user_id,
        is_read=False
    ).count()
    
    return render_template('player/dashboard.html',
                         player=player,
                         recent_matches=recent_matches,
                         upcoming_bookings=upcoming_bookings,
                         unread_messages=unread_messages)

@player_bp.route('/find-matches')
@login_required
@player_required
def find_matches():
    """Find and match with other players"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    if not player:
        flash('Player profile not found. Please complete your profile first.', 'error')
        return redirect(url_for('player.dashboard'))
    
    # Get search filters from request
    skill_level = request.args.get('skill_level', '').strip()
    location = request.args.get('location', '').strip()
    availability = request.args.get('availability', '').strip()
    
    try:
        # Use matching engine to find compatible players
        matches = MatchingEngine.find_matches(
            player_id=player.id,
            skill_level=skill_level if skill_level else None,
            location=location if location else None,
            availability=availability if availability else None,
            limit=20
        )
        
        # Process matches to ensure safe template rendering
        processed_matches = []
        for match in matches:
            match_data = {
                'player': match.get('player'),
                'user': match.get('user'),
                'compatibility_score': match.get('compatibility_score', 0),
                'common_interests': match.get('common_interests', []),
                'distance': match.get('distance'),
                'recent_activity': None  # Disable for now to avoid errors
            }
            processed_matches.append(match_data)
        
        return render_template('player/find_matches.html',
                             player=player,
                             matches=processed_matches,
                             skill_level=skill_level,
                             location=location,
                             availability=availability)
    
    except Exception as e:
        # Handle errors gracefully in production
        flash('Error occurred while searching for matches. Please try again.', 'error')
        return render_template('player/find_matches.html',
                             player=player,
                             matches=[],
                             skill_level=skill_level,
                             location=location,
                             availability=availability)

# עדכן גם את הנתיב book_court הקיים:

@player_bp.route('/book-court')
@login_required
@player_required
def book_court():
    """Browse and book available courts"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Get search filters
    location = request.args.get('location', '')
    date = request.args.get('date', '')
    court_type = request.args.get('court_type', '')
    max_price = request.args.get('max_price', type=float)
    
    # Build query for available courts
    courts_query = Court.query.filter_by(is_active=True)
    
    if location:
        courts_query = courts_query.filter(Court.location.ilike(f'%{location}%'))
    if court_type:
        courts_query = courts_query.filter_by(court_type=court_type)
    if max_price:
        courts_query = courts_query.filter(Court.hourly_rate <= max_price)
    
    available_courts = courts_query.all()
    
    # Check availability for specific date if provided
    if date:
        for court in available_courts:
            # Get available time slots for this court on this date
            court.available_slots = get_available_slots(court.id, date)
    
    return render_template('player/book_court.html',
                         available_courts=available_courts,
                         filters={
                             'location': location,
                             'date': date,
                             'court_type': court_type,
                             'max_price': max_price
                         },
                         datetime=datetime,
                         player=player)


def get_available_slots(court_id, date_str):
    """Get available time slots for a court on a specific date"""
    from datetime import datetime, time, timedelta
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return []
    
    # Get existing bookings for this court on this date
    existing_bookings = Booking.query.filter(
        Booking.court_id == court_id,
        Booking.booking_date == target_date,
        Booking.status.in_(['confirmed', 'pending'])
    ).all()
    
    # Generate potential time slots (8 AM to 10 PM, 1-hour slots)
    available_slots = []
    for hour in range(8, 22):  # 8 AM to 9 PM (last slot starts at 9 PM)
        slot_start = time(hour, 0)
        slot_end = time(hour + 1, 0)
        
        # Check if this slot conflicts with existing bookings
        has_conflict = False
        for booking in existing_bookings:
            if (slot_start < booking.end_time and slot_end > booking.start_time):
                has_conflict = True
                break
        
        if not has_conflict:
            available_slots.append({
                'start_time': slot_start.strftime('%H:%M'),
                'end_time': slot_end.strftime('%H:%M')
            })
    
    return available_slots

@player_bp.route('/book-court/<int:court_id>', methods=['POST'])
@login_required
@player_required
def create_booking(court_id):
    """Create a booking request for a specific court"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    booking_date = request.form.get('booking_date')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    notes = request.form.get('notes', '')
    
    # Validate booking using rule engine
    validation_result = RuleEngine.validate_booking(
        court_id=court_id,
        player_id=player.id,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time
    )
    
    if not validation_result['valid']:
        flash(f'Booking failed: {validation_result["reason"]}', 'error')
        return redirect(url_for('player.book_court'))
    
    # Create booking request
    booking = Booking(
        court_id=court_id,
        player_id=player.id,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        status='pending',
        notes=notes
    )
    
    db.session.add(booking)
    db.session.commit()
    
    flash('Booking request submitted successfully!', 'success')
    return redirect(url_for('player.my_calendar'))

@player_bp.route('/my-calendar')
@login_required
@player_required
def my_calendar():
    """View personal calendar with bookings and matches"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Get all bookings for this player
    bookings = Booking.query.filter_by(player_id=player.id).order_by(
        Booking.booking_date.desc(),
        Booking.start_time.desc()
    ).limit(50).all()
    
    # Group bookings by status for display
    booking_groups = {
        'confirmed': [b for b in bookings if b.status == 'confirmed'],
        'pending': [b for b in bookings if b.status == 'pending'],
        'cancelled': [b for b in bookings if b.status == 'cancelled']
    }
    
    return render_template('player/my_calendar.html',
                         player=player,
                         bookings=bookings,
                         booking_groups=booking_groups)

@player_bp.route('/messages')
@login_required
@player_required
def messages():
    """View and manage messages"""
    user_id = session['user_id']
    
    # Get all conversations (grouped by other participant)
    conversations = db.session.query(
        Message.sender_id,
        Message.receiver_id,
        db.func.max(Message.created_at).label('last_message_time')
    ).filter(
        db.or_(Message.sender_id == user_id, Message.receiver_id == user_id)
    ).group_by(
        db.case(
            [(Message.sender_id == user_id, Message.receiver_id)],
            else_=Message.sender_id
        )
    ).order_by(db.desc('last_message_time')).all()
    
    # Get full conversation details
    conversation_list = []
    for conv in conversations:
        other_user_id = conv.sender_id if conv.receiver_id == user_id else conv.receiver_id
        other_user = User.query.get(other_user_id)
        
        # Get last message
        last_message = Message.query.filter(
            db.or_(
                db.and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
                db.and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
            )
        ).order_by(Message.created_at.desc()).first()
        
        # Count unread messages
        unread_count = Message.query.filter_by(
            sender_id=other_user_id,
            receiver_id=user_id,
            is_read=False
        ).count()
        
        conversation_list.append({
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    return render_template('player/messages.html',
                         conversations=conversation_list)

@player_bp.route('/chat/<int:other_user_id>')
@login_required
@player_required
def chat(other_user_id):
    """Chat interface with specific user"""
    user_id = session['user_id']
    other_user = User.query.get_or_404(other_user_id)
    
    # Get chat history
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
            db.and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    # Mark messages as read
    Message.query.filter_by(
        sender_id=other_user_id,
        receiver_id=user_id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    return render_template('player/chat.html',
                         other_user=other_user,
                         messages=messages)

@player_bp.route('/send-message', methods=['POST'])
@login_required
@player_required
def send_message():
    """Send a message to another user"""
    user_id = session['user_id']
    
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
        receiver_id = data.get('receiver_id')
        content = data.get('content', '').strip()
    else:
        receiver_id = request.form.get('receiver_id', type=int)
        content = request.form.get('content', '').strip()
    
    if not receiver_id or not content:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Missing required fields'})
        flash('Missing required fields', 'error')
        return redirect(url_for('player.messages'))
    
    # Validate receiver exists
    receiver = User.query.get(receiver_id)
    if not receiver:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Recipient not found'})
        flash('Recipient not found', 'error')
        return redirect(url_for('player.messages'))
    
    # Create message
    message = Message(
        sender_id=user_id,
        receiver_id=receiver_id,
        content=content
    )
    
    try:
        db.session.add(message)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'created_at': message.created_at.isoformat(),
                    'sender_name': session.get('user_name', 'Unknown')
                }
            })
        else:
            flash('Message sent successfully!', 'success')
            return redirect(url_for('player.chat', other_user_id=receiver_id))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': 'Failed to send message'})
        flash('Failed to send message', 'error')
        return redirect(url_for('player.messages'))

@player_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@player_required
def edit_profile():
    """Edit player profile"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    user = User.query.get(user_id)
    
    if request.method == 'POST':
        # Update player information
        player.skill_level = request.form.get('skill_level', player.skill_level)
        player.preferred_location = request.form.get('preferred_location', player.preferred_location)
        player.availability = request.form.get('availability', player.availability)
        player.bio = request.form.get('bio', player.bio)
        
        # Update user information
        user.full_name = request.form.get('full_name', user.full_name)
        user.phone_number = request.form.get('phone_number', user.phone_number)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('player.dashboard'))
    
    return render_template('player/edit_profile.html',
                         player=player,
                         user=user)

@player_bp.route('/send-match-request', methods=['POST'])
@login_required
@player_required
def send_match_request():
    """Send a match request to another player"""
    user_id = session['user_id']
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'})
    
    target_player_id = data.get('player_id')
    custom_message = data.get('message', '')
    
    if not target_player_id:
        return jsonify({'success': False, 'error': 'Player ID is required'})
    
    # Validate target player exists
    target_player = Player.query.get(target_player_id)
    if not target_player:
        return jsonify({'success': False, 'error': 'Player not found'})
    
    target_user = target_player.user
    sender = User.query.get(user_id)
    
    # Validate using business rules
    validation = RuleEngine.validate_player_matching(user_id, target_player_id)
    if not validation['valid']:
        return jsonify({'success': False, 'error': validation['reason']})
    
    # Create match request message
    if custom_message:
        content = custom_message
    else:
        content = f"Hi {target_user.full_name}! I'd like to play tennis with you. Are you available for a match?"
    
    # Create the message
    message = Message(
        sender_id=user_id,
        receiver_id=target_user.id,
        content=content
    )
    
    try:
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Match request sent to {target_user.full_name}!',
            'message_id': message.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to send match request'})

@player_bp.route('/settings')
@login_required
@player_required
def settings():
    """Player settings page"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    player = Player.query.filter_by(user_id=user_id).first()
    
    return render_template('player/settings.html', user=user, player=player)

# הוסף את הנתיב הזה בקובץ routes/player.py

@player_bp.route('/submit-booking', methods=['POST'])
@login_required
@player_required
def submit_booking():
    """Submit booking request with JSON response"""
    try:
        user_id = session['user_id']
        player = Player.query.filter_by(user_id=user_id).first()
        
        # Get form data
        court_id = request.form.get('court_id', type=int)
        booking_date = request.form.get('booking_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        notes = request.form.get('notes', '').strip()
        
        # Validate required fields
        if not all([court_id, booking_date, start_time, end_time]):
            return jsonify({'success': False, 'error': 'All fields are required'})
        
        # Validate court exists
        court = Court.query.get(court_id)
        if not court or not court.is_active:
            return jsonify({'success': False, 'error': 'Court not found or unavailable'})
        
        # Validate booking using rule engine
        validation_result = RuleEngine.validate_booking(
            court_id=court_id,
            player_id=player.id,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time
        )
        
        if not validation_result['valid']:
            return jsonify({'success': False, 'error': validation_result['reason']})
        
        # Calculate duration and cost
        from datetime import datetime, timedelta
        start_dt = datetime.strptime(start_time, '%H:%M')
        end_dt = datetime.strptime(end_time, '%H:%M')
        duration_hours = (end_dt - start_dt).total_seconds() / 3600
        total_cost = duration_hours * court.hourly_rate
        
        # Create booking
        booking = Booking(
            court_id=court_id,
            player_id=player.id,
            booking_date=datetime.strptime(booking_date, '%Y-%m-%d').date(),
            start_time=datetime.strptime(start_time, '%H:%M').time(),
            end_time=datetime.strptime(end_time, '%H:%M').time(),
            status='pending',
            notes=notes,
            total_cost=total_cost
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Optional: Send notification to court owner
        from services.cloud_service import CloudService
        try:
            CloudService.send_booking_approval_notification(booking)
        except:
            pass  # Continue even if email fails
        
        return jsonify({
            'success': True, 
            'booking_id': booking.id,
            'message': 'Booking request submitted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'An error occurred while processing your request'})
