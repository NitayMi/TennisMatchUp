from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from models.user import User
from models.player import Player
from models.court import Court, Booking
from models.message import Message
from models.database import db
from utils.decorators import login_required, player_required
from services.matching_engine import MatchingEngine
from services.rule_engine import RuleEngine

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
    
    # Get search filters from request
    skill_level = request.args.get('skill_level', player.skill_level)
    preferred_location = request.args.get('location', player.preferred_location)
    availability = request.args.get('availability')
    
    # Use matching engine to find compatible players
    matches = MatchingEngine.find_matches(
        player_id=player.id,
        skill_level=skill_level,
        location=preferred_location,
        availability=availability
    )
    
    return render_template('player/find_matches.html',
                         player=player,
                         matches=matches,
                         filters={
                             'skill_level': skill_level,
                             'location': preferred_location,
                             'availability': availability
                         })

@player_bp.route('/book-court')
@login_required
@player_required
def book_court():
    """Browse and book available courts"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Get search filters
    location = request.args.get('location', player.preferred_location)
    date = request.args.get('date')
    court_type = request.args.get('court_type')
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
    
    # Check availability for each court if date provided
    if date:
        for court in available_courts:
            court.available_slots = court.get_available_slots(date)
    
    return render_template('player/book_court.html',
                         available_courts=available_courts,
                         filters={
                             'location': location,
                             'date': date,
                             'court_type': court_type,
                             'max_price': max_price
                         })

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
    receiver_id = request.form.get('receiver_id', type=int)
    content = request.form.get('content', '').strip()
    
    if not receiver_id or not content:
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    # Validate receiver exists
    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({'success': False, 'error': 'Recipient not found'})
    
    # Create message
    message = Message(
        sender_id=user_id,
        receiver_id=receiver_id,
        content=content
    )
    
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


# Add this new route to your existing routes/player.py file
# Insert this after the existing send_message route

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
        content=content,
        message_type='match_request'
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

@player_bp.route('/respond-to-match/<int:message_id>', methods=['POST'])
@login_required
@player_required
def respond_to_match(message_id):
    """Respond to a match request (accept/decline)"""
    user_id = session['user_id']
    message = Message.query.get_or_404(message_id)
    
    # Validate this message belongs to current user
    if message.receiver_id != user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    response = request.get_json()
    action = response.get('action')  # 'accept' or 'decline'
    reply_message = response.get('message', '')
    
    if action not in ['accept', 'decline']:
        return jsonify({'success': False, 'error': 'Invalid action'})
    
    # Mark original message as read
    message.mark_as_read()
    
    # Create response message
    if action == 'accept':
        content = f"Great! I'd love to play with you. {reply_message}" if reply_message else "Great! I'd love to play with you. When would be a good time?"
        response_type = 'match_accepted'
    else:
        content = f"Thanks for the invitation, but I can't play right now. {reply_message}" if reply_message else "Thanks for the invitation, but I can't play right now."
        response_type = 'match_declined'
    
    response_message = Message(
        sender_id=user_id,
        receiver_id=message.sender_id,
        content=content,
        message_type=response_type
    )
    
    try:
        db.session.add(response_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'action': action,
            'message': f'Response sent successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to send response'})