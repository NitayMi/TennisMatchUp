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
import json

player_bp = Blueprint('player', __name__, url_prefix='/player')

@player_bp.route('/dashboard')
@login_required
@player_required
def dashboard():
    """Player dashboard showing matches, bookings, and notifications"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    if not player:
        flash('Player profile not found. Please complete your profile first.', 'error')
        return redirect(url_for('auth.profile'))
    
    # Get recent matches/recommendations
    try:
        recent_matches = MatchingEngine.find_matches(player.id, limit=5)
    except:
        recent_matches = []
    
    # Get upcoming bookings
    upcoming_bookings = Booking.query.filter_by(
        player_id=player.id,
        status='confirmed'
    ).filter(Booking.booking_date >= date.today()).limit(5).all()
    
    # Get recent bookings for history
    recent_bookings = Booking.query.filter_by(
        player_id=player.id
    ).order_by(Booking.created_at.desc()).limit(5).all()
    
    # Get unread messages
    unread_messages = Message.query.filter_by(
        receiver_id=user_id,
        is_read=False
    ).count()
    
    # Calculate stats
    total_bookings = Booking.query.filter_by(player_id=player.id).count()
    matches_this_month = Booking.query.filter_by(
        player_id=player.id,
        status='confirmed'
    ).filter(
        Booking.booking_date >= date.today().replace(day=1)
    ).count()
    
    stats = {
        'total_bookings': total_bookings,
        'matches_this_month': matches_this_month,
        'unread_messages': unread_messages
    }
    
    return render_template('player/dashboard.html',
                         player=player,
                         recent_matches=recent_matches,
                         upcoming_bookings=upcoming_bookings,
                         recent_bookings=recent_bookings,
                         stats=stats)

@player_bp.route('/find-matches')
@login_required
@player_required
def find_matches():
    """Find and match with other players"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    if not player:
        flash('Player profile not found. Please complete your profile first.', 'error')
        return redirect(url_for('auth.profile'))
    
    # Get filter parameters
    skill_level = request.args.get('skill_level')
    location = request.args.get('location')
    availability = request.args.get('availability')
    max_distance = request.args.get('max_distance', type=int)
    
    try:
        # Find compatible players
        matches = MatchingEngine.find_matches(
            player_id=player.id,
            skill_level=skill_level,
            location=location,
            availability=availability,
            limit=20
        )
    except Exception as e:
        print(f"Error finding matches: {e}")
        matches = []
        flash('Error finding matches. Please try again later.', 'warning')
    
    # Get available locations for filter
    available_locations = db.session.query(Player.preferred_location).distinct().filter(
        Player.preferred_location.isnot(None)
    ).all()
    locations = [loc[0] for loc in available_locations if loc[0]]
    
    return render_template('player/find_matches.html',
                         player=player,
                         matches=matches,
                         locations=locations,
                         filters={
                             'skill_level': skill_level,
                             'location': location,
                             'availability': availability,
                             'max_distance': max_distance
                         })

@player_bp.route('/book-court')
@login_required
@player_required
def book_court():
    """Book a court page"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Get filter parameters
    location = request.args.get('location', '')
    date_filter = request.args.get('date', '')
    court_type = request.args.get('court_type', '')
    surface = request.args.get('surface', '')
    max_rate = request.args.get('max_rate', type=float)
    
    # Build query
    query = Court.query.filter_by(is_active=True)
    
    if location:
        query = query.filter(Court.location.ilike(f'%{location}%'))
    
    if court_type:
        query = query.filter_by(court_type=court_type)
    
    if surface:
        query = query.filter_by(surface=surface)
    
    if max_rate:
        query = query.filter(Court.hourly_rate <= max_rate)
    
    courts = query.order_by(Court.hourly_rate).limit(20).all()
    
    # Get available options for filters
    available_locations = db.session.query(Court.location).distinct().filter(
        Court.is_active == True
    ).all()
    locations = list(set([loc[0] for loc in available_locations if loc[0]]))
    
    court_types = ['indoor', 'outdoor']
    surfaces = ['hard', 'clay', 'grass', 'artificial']
    
    return render_template('player/book_court.html',
                         courts=courts,
                         player=player,
                         locations=locations,
                         court_types=court_types,
                         surfaces=surfaces,
                         filters={
                             'location': location,
                             'date': date_filter,
                             'court_type': court_type,
                             'surface': surface,
                             'max_rate': max_rate
                         })

@player_bp.route('/my-bookings')
@login_required
@player_required
def my_bookings():
    """View all player bookings"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Get status filter
    status_filter = request.args.get('status', 'all')
    
    # Build query
    query = Booking.query.filter_by(player_id=player.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    bookings = query.order_by(Booking.booking_date.desc(), Booking.created_at.desc()).all()
    
    # Group bookings by status for display
    upcoming_bookings = [b for b in bookings if b.booking_date >= date.today() and b.status == 'confirmed']
    pending_bookings = [b for b in bookings if b.status == 'pending']
    past_bookings = [b for b in bookings if b.booking_date < date.today()]
    
    return render_template('player/my_bookings.html',
                         bookings=bookings,
                         upcoming_bookings=upcoming_bookings,
                         pending_bookings=pending_bookings,
                         past_bookings=past_bookings,
                         status_filter=status_filter)

@player_bp.route('/my-calendar')
@login_required
@player_required
def my_calendar():
    """Player calendar view"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    # Get current month or requested month
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    if not month or not year:
        today = date.today()
        month = today.month
        year = today.year
    
    # Get all bookings for the player
    bookings = Booking.query.filter_by(player_id=player.id).filter(
        db.extract('month', Booking.booking_date) == month,
        db.extract('year', Booking.booking_date) == year
    ).all()
    
    # Convert bookings to JSON for JavaScript
    bookings_data = []
    for booking in bookings:
        bookings_data.append({
            'id': booking.id,
            'court_name': booking.court.name,
            'booking_date': booking.booking_date.isoformat(),
            'start_time': booking.start_time.strftime('%H:%M'),
            'end_time': booking.end_time.strftime('%H:%M'),
            'status': booking.status,
            'total_cost': float(booking.total_cost) if booking.total_cost else 0
        })
    
    return render_template('player/my_calendar.html',
                         player=player,
                         bookings=bookings,
                         bookings_data=json.dumps(bookings_data),
                         current_month=month,
                         current_year=year)

@player_bp.route('/messages')
@login_required  
@player_required
def messages():
    """View messages"""
    user_id = session['user_id']
    
    # Get conversation filter
    conversation_with = request.args.get('with', type=int)
    
    if conversation_with:
        # Get messages with specific user
        messages = Message.query.filter(
            db.or_(
                db.and_(Message.sender_id == user_id, Message.receiver_id == conversation_with),
                db.and_(Message.sender_id == conversation_with, Message.receiver_id == user_id)
            )
        ).order_by(Message.created_at.asc()).all()
        
        # Mark messages as read
        Message.query.filter_by(
            sender_id=conversation_with,
            receiver_id=user_id,
            is_read=False
        ).update({'is_read': True})
        db.session.commit()
        
        conversation_user = User.query.get(conversation_with)
    else:
        messages = []
        conversation_user = None
    
    # Get all conversations (users who have sent/received messages)
    sent_to = db.session.query(Message.receiver_id).filter_by(sender_id=user_id).distinct()
    received_from = db.session.query(Message.sender_id).filter_by(receiver_id=user_id).distinct()
    
    conversation_user_ids = set()
    for result in sent_to:
        conversation_user_ids.add(result[0])
    for result in received_from:
        conversation_user_ids.add(result[0])
    
    conversations = User.query.filter(User.id.in_(conversation_user_ids)).all()
    
    return render_template('player/messages.html',
                         messages=messages,
                         conversations=conversations,
                         conversation_user=conversation_user,
                         current_user_id=user_id)

@player_bp.route('/send-message', methods=['POST'])
@login_required
@player_required  
def send_message():
    """Send message to another user"""
    user_id = session['user_id']
    
    receiver_id = request.form.get('receiver_id', type=int)
    content = request.form.get('content', '').strip()
    
    # Validate using rule engine
    validation = RuleEngine.validate_message_sending(user_id, receiver_id, content)
    
    if not validation['valid']:
        flash(f'Message failed: {validation["reason"]}', 'error')
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
        flash('Message sent successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to send message. Please try again.', 'error')
    
    return redirect(url_for('player.messages', **{'with': receiver_id}))

@player_bp.route('/send-match-request', methods=['POST'])
@login_required
@player_required
def send_match_request():
    """Send match request to another player via AJAX"""
    user_id = session['user_id']
    
    # Get data from JSON request
    data = request.get_json()
    target_player_id = data.get('player_id')
    custom_message = data.get('message', '')
    
    if not target_player_id:
        return jsonify({'success': False, 'error': 'Player ID required'})
    
    # Get target user
    target_player = Player.query.get(target_player_id)
    if not target_player:
        return jsonify({'success': False, 'error': 'Player not found'})
    
    target_user = target_player.user
    if not target_user or not target_user.is_active:
        return jsonify({'success': False, 'error': 'Player account not active'})
    
    # Create message content
    current_user = User.query.get(user_id)
    if custom_message:
        content = custom_message
    else:
        content = f"Hi {target_user.full_name}! I'm {current_user.full_name} and I'd like to play tennis with you. Are you available for a match?"
    
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

@player_bp.route('/submit-booking', methods=['POST'])
@login_required
@player_required
def submit_booking():
    """Submit booking request with JSON response"""
    print("=== SUBMIT BOOKING START ===")  # DEBUG
    
    try:
        user_id = session['user_id']
        player = Player.query.filter_by(user_id=user_id).first()
        
        if not player:
            return jsonify({'success': False, 'error': 'Player profile not found'})
        
        print(f"Player found: {player.id}")  # DEBUG
        
        # Get form data
        court_id = request.form.get('court_id', type=int)
        booking_date = request.form.get('booking_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        notes = request.form.get('notes', '').strip()
        
        print(f"Form data: court_id={court_id}, date={booking_date}, start={start_time}, end={end_time}")  # DEBUG
        
        # Validate required fields
        if not all([court_id, booking_date, start_time, end_time]):
            print("Missing required fields")  # DEBUG
            return jsonify({'success': False, 'error': 'All fields are required'})
        
        # Validate court exists
        court = Court.query.get(court_id)
        if not court or not court.is_active:
            print(f"Court not found or inactive: {court_id}")  # DEBUG
            return jsonify({'success': False, 'error': 'Court not found or unavailable'})
        
        print(f"Court found: {court.name}")  # DEBUG
        
        # Validate booking using rule engine
        validation_result = RuleEngine.validate_booking(
            court_id=court_id,
            player_id=player.id,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time
        )
        
        if not validation_result['valid']:
            print(f"Validation failed: {validation_result['reason']}")  # DEBUG
            return jsonify({'success': False, 'error': validation_result['reason']})
        
        # Calculate duration and cost
        start_dt = datetime.strptime(start_time, '%H:%M')
        end_dt = datetime.strptime(end_time, '%H:%M')
        duration_hours = (end_dt - start_dt).total_seconds() / 3600
        total_cost = duration_hours * court.hourly_rate
        
        print(f"Duration: {duration_hours} hours, Cost: {total_cost}")  # DEBUG

        # Create booking
        booking = Booking(
            court_id=court_id,
            player_id=player.id,
            booking_date=datetime.strptime(booking_date, '%Y-%m-%d').date(),
            start_time=datetime.strptime(start_time, '%H:%M').time(),
            end_time=datetime.strptime(end_time, '%H:%M').time(),
            notes=notes
        )

        # Set additional fields
        booking.total_cost = total_cost
        booking.status = 'pending'  # Default status

        print(f"Booking created with cost: {booking.total_cost}")  # DEBUG

        db.session.add(booking)
        db.session.commit()
        
        print(f"Booking created: {booking.id}")  # DEBUG
        
        # Note: Email notifications can be added later
        # try:
        #     CloudService.send_booking_notification(booking)
        # except:
        #     pass  # Don't fail booking if email fails
        
        response = {
            'success': True, 
            'booking_id': booking.id,
            'message': 'Booking request submitted successfully! The court owner will review your request.'
        }
        
        print(f"Returning response: {response}")  # DEBUG
        print("=== SUBMIT BOOKING END ===")  # DEBUG
        
        return jsonify(response)
        
    except Exception as e:
        db.session.rollback()
        print(f"ERROR in submit_booking: {str(e)}")  # DEBUG
        print("=== SUBMIT BOOKING ERROR ===")  # DEBUG
        return jsonify({'success': False, 'error': f'Booking failed: {str(e)}'})

@player_bp.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
@player_required
def cancel_booking(booking_id):
    """Cancel a booking"""
    user_id = session['user_id']
    player = Player.query.filter_by(user_id=user_id).first()
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Validate user owns this booking
    if booking.player_id != player.id:
        flash('You can only cancel your own bookings.', 'error')
        return redirect(url_for('player.my_bookings'))
    
    # Validate booking can be cancelled
    validation = RuleEngine.validate_booking_cancellation(booking_id, user_id, 'player')
    
    if not validation['valid']:
        flash(f'Cannot cancel booking: {validation["reason"]}', 'error')
        return redirect(url_for('player.my_bookings'))
    
    try:
        booking.status = 'cancelled'
        booking.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Booking cancelled successfully.', 'success')
        
        # Note: Refund logic can be added later
        # if booking.total_cost and booking.status == 'confirmed':
        #     RefundService.process_refund(booking)
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to cancel booking. Please try again.', 'error')
    
    return redirect(url_for('player.my_bookings'))

@player_bp.route('/api/available-slots/<int:court_id>')
@login_required
@player_required  
def get_available_slots(court_id):
    """API endpoint to get available time slots for a court on a specific date"""
    booking_date = request.args.get('date')
    
    if not booking_date:
        return jsonify({'error': 'Date parameter required'}), 400
    
    try:
        court = Court.query.get_or_404(court_id)
        
        # Get existing bookings for this date
        existing_bookings = Booking.query.filter_by(
            court_id=court_id,
            booking_date=datetime.strptime(booking_date, '%Y-%m-%d').date()
        ).filter(Booking.status.in_(['confirmed', 'pending'])).all()
        
        # Generate available slots (8 AM to 10 PM, 1-hour slots)
        available_slots = []
        
        for hour in range(8, 22):  # 8 AM to 10 PM
            slot_start = time(hour, 0)
            slot_end = time(hour + 1, 0)
            
            # Check if this slot conflicts with existing bookings
            has_conflict = False
            for booking in existing_bookings:
                if (booking.start_time < slot_end and booking.end_time > slot_start):
                    has_conflict = True
                    break
            
            if not has_conflict:
                available_slots.append({
                    'start_time': slot_start.strftime('%H:%M'),
                    'end_time': slot_end.strftime('%H:%M')
                })
        
        return jsonify({
            'success': True,
            'court_name': court.name,
            'date': booking_date,
            'available_slots': available_slots
        })
        
    except Exception as e:
                # הוסף את ה-routes החסרים הללו לסוף קובץ routes/player.py שלך
        # (לפני השורה האחרונה של הקובץ)

        @player_bp.route('/edit-profile', methods=['GET', 'POST'])
        @login_required
        @player_required
        def edit_profile():
            """Edit player profile"""
            user_id = session['user_id']
            user = User.query.get(user_id)
            player = Player.query.filter_by(user_id=user_id).first()
            
            if request.method == 'POST':
                # Update user info
                user.full_name = request.form.get('full_name', '').strip()
                user.phone_number = request.form.get('phone_number', '').strip()
                
                # Update player info
                player.skill_level = request.form.get('skill_level', '')
                player.preferred_location = request.form.get('preferred_location', '').strip()
                player.availability = request.form.get('availability', '')
                player.bio = request.form.get('bio', '').strip()
                player.playing_style = request.form.get('playing_style', '')
                player.preferred_court_type = request.form.get('preferred_court_type', '')
                player.years_playing = request.form.get('years_playing', type=int)
                player.max_travel_distance = request.form.get('max_travel_distance', type=int)
                
                try:
                    db.session.commit()
                    flash('Profile updated successfully!', 'success')
                    return redirect(url_for('player.dashboard'))
                except Exception as e:
                    db.session.rollback()
                    flash('Error updating profile. Please try again.', 'error')
            
            return render_template('player/edit_profile.html', user=user, player=player)

        @player_bp.route('/profile')
        @login_required
        @player_required
        def profile():
            """View player profile"""
            user_id = session['user_id']
            user = User.query.get(user_id)
            player = Player.query.filter_by(user_id=user_id).first()
            
            # Get profile completion stats
            profile_stats = RuleEngine.validate_player_profile_completion(player)
            
            return render_template('player/profile.html', 
                                user=user, 
                                player=player,
                                profile_stats=profile_stats)

        @player_bp.route('/search')
        @login_required
        @player_required  
        def search():
            """Search for courts and players"""
            # This is a simple search page that combines court and player search
            return render_template('player/search.html')

        @player_bp.route('/matches')
        @login_required
        @player_required
        def matches():
            """Matches page - alias for find_matches"""
            return redirect(url_for('player.find_matches'))

        @player_bp.route('/courts')
        @login_required
        @player_required
        def courts():
            """Courts page - alias for book_court"""
            return redirect(url_for('player.book_court'))
        return jsonify({'error': 'Failed to get available slots'}), 500