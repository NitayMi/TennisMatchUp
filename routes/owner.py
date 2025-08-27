from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from models.user import User
from models.court import Court, Booking
from models.player import Player
from models.message import Message
from models.database import db
from utils.decorators import login_required, owner_required
from services.rule_engine import RuleEngine
from datetime import datetime, timedelta
import json

owner_bp = Blueprint('owner', __name__, url_prefix='/owner')

@owner_bp.route('/dashboard')
@login_required
@owner_required
def dashboard():
    """Owner dashboard showing courts, bookings, and revenue stats"""
    user_id = session['user_id']
    
    # Get owner's courts
    courts = Court.query.filter_by(owner_id=user_id).all()
    
    # Get recent bookings across all courts
    recent_bookings = db.session.query(Booking).join(Court).filter(
        Court.owner_id == user_id,
        Booking.created_at >= datetime.now() - timedelta(days=7)
    ).order_by(Booking.created_at.desc()).limit(10).all()
    
    # Calculate stats
    total_courts = len(courts)
    active_courts = len([c for c in courts if c.is_active])
    
    # Pending bookings count
    pending_bookings = db.session.query(Booking).join(Court).filter(
        Court.owner_id == user_id,
        Booking.status == 'pending'
    ).count()
    
    # Revenue stats (last 30 days)
    revenue_query = db.session.query(
        db.func.sum(Court.hourly_rate * 
                   db.func.extract('hour', Booking.end_time - Booking.start_time))
    ).join(Booking).filter(
        Court.owner_id == user_id,
        Booking.status == 'confirmed',
        Booking.booking_date >= datetime.now().date() - timedelta(days=30)
    ).scalar()
    
    monthly_revenue = revenue_query or 0
    
    # Unread messages
    unread_messages = Message.query.filter_by(
        receiver_id=user_id,
        is_read=False
    ).count()
    
    stats = {
        'total_courts': total_courts,
        'active_courts': active_courts,
        'pending_bookings': pending_bookings,
        'monthly_revenue': monthly_revenue,
        'unread_messages': unread_messages
    }
    
    return render_template('owner/dashboard.html',
                         courts=courts,
                         recent_bookings=recent_bookings,
                         stats=stats)

@owner_bp.route('/manage-courts')
@login_required
@owner_required
def manage_courts():
    """Manage all courts owned by this user"""
    user_id = session['user_id']
    courts = Court.query.filter_by(owner_id=user_id).order_by(
        Court.is_active.desc(),
        Court.created_at.desc()
    ).all()
    
    return render_template('owner/manage_courts.html', courts=courts)

@owner_bp.route('/add-court', methods=['GET', 'POST'])
@login_required
@owner_required
def add_court():
    """Add a new court"""
    user_id = session['user_id']
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        court_type = request.form.get('court_type')
        surface = request.form.get('surface')
        hourly_rate = request.form.get('hourly_rate', type=float)
        description = request.form.get('description', '').strip()
        amenities = request.form.get('amenities', '').strip()
        
        # Validation
        if not all([name, location, court_type, surface, hourly_rate]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('owner.add_court'))
        
        if hourly_rate <= 0:
            flash('Hourly rate must be greater than 0', 'error')
            return redirect(url_for('owner.add_court'))
        
        # Validate using business rules
        validation_result = RuleEngine.validate_court_creation(
            owner_id=user_id,
            name=name,
            location=location,
            hourly_rate=hourly_rate
        )
        
        if not validation_result['valid']:
            flash(f'Court creation failed: {validation_result["reason"]}', 'error')
            return redirect(url_for('owner.add_court'))
        
        # Create court
        court = Court(
            owner_id=user_id,
            name=name,
            location=location,
            court_type=court_type,
            surface=surface,
            hourly_rate=hourly_rate,
            description=description,
            amenities=amenities,
            is_active=True
        )
        
        db.session.add(court)
        db.session.commit()
        
        flash(f'Court "{name}" added successfully!', 'success')
        return redirect(url_for('owner.manage_courts'))
    
    return render_template('owner/add_court.html')

@owner_bp.route('/edit-court/<int:court_id>', methods=['GET', 'POST'])
@login_required
@owner_required
def edit_court(court_id):
    """Edit an existing court"""
    user_id = session['user_id']
    court = Court.query.filter_by(id=court_id, owner_id=user_id).first_or_404()
    
    if request.method == 'POST':
        court.name = request.form.get('name', court.name)
        court.location = request.form.get('location', court.location)
        court.court_type = request.form.get('court_type', court.court_type)
        court.surface = request.form.get('surface', court.surface)
        court.hourly_rate = request.form.get('hourly_rate', type=float) or court.hourly_rate
        court.description = request.form.get('description', court.description)
        court.amenities = request.form.get('amenities', court.amenities)
        court.is_active = request.form.get('is_active') == 'on'
        
        db.session.commit()
        flash(f'Court "{court.name}" updated successfully!', 'success')
        return redirect(url_for('owner.manage_courts'))
    
    return render_template('owner/edit_court.html', court=court)

@owner_bp.route('/court-calendar')
@login_required
@owner_required
def court_calendar():
    """View calendar for all courts"""
    user_id = session['user_id']
    
    # Get selected court and date from query params
    selected_court_id = request.args.get('court_id', type=int)
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Get owner's courts
    courts = Court.query.filter_by(owner_id=user_id, is_active=True).all()
    
    if not courts:
        flash('You need to add at least one active court first', 'info')
        return redirect(url_for('owner.add_court'))
    
    # Default to first court if none selected
    if not selected_court_id:
        selected_court_id = courts[0].id
    
    selected_court = Court.query.get(selected_court_id)
    
    # Get bookings for selected court and date
    try:
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        date_obj = datetime.now().date()
        selected_date = date_obj.strftime('%Y-%m-%d')
    
    bookings = Booking.query.filter_by(
        court_id=selected_court_id,
        booking_date=date_obj
    ).order_by(Booking.start_time).all()
    
    # Generate time slots for the day (8 AM to 10 PM)
    time_slots = []
    for hour in range(8, 22):  # 8 AM to 9 PM (last slot starts at 9 PM)
        time_str = f"{hour:02d}:00"
        slot_booking = next((b for b in bookings 
                           if b.start_time.strftime('%H:%M') <= time_str < b.end_time.strftime('%H:%M')), 
                          None)
        time_slots.append({
            'time': time_str,
            'booking': slot_booking,
            'is_available': slot_booking is None
        })
    
    return render_template('owner/court_calendar.html',
                         courts=courts,
                         selected_court=selected_court,
                         selected_date=selected_date,
                         bookings=bookings,
                         time_slots=time_slots)

@owner_bp.route('/booking-requests')
@login_required
@owner_required
def booking_requests():
    """Manage booking requests for all courts"""
    user_id = session['user_id']
    
    # Get filter parameters
    status_filter = request.args.get('status', 'pending')
    court_id_filter = request.args.get('court_id', type=int)
    
    # Build query for bookings
    query = db.session.query(Booking).join(Court).filter(Court.owner_id == user_id)
    
    if status_filter and status_filter != 'all':
        query = query.filter(Booking.status == status_filter)
    
    if court_id_filter:
        query = query.filter(Booking.court_id == court_id_filter)
    
    bookings = query.order_by(
        Booking.status == 'pending',  # Pending first
        Booking.booking_date.desc(),
        Booking.start_time.desc()
    ).limit(50).all()
    
    # Get courts for filter dropdown
    courts = Court.query.filter_by(owner_id=user_id).all()
    
    return render_template('owner/booking_requests.html',
                         bookings=bookings,
                         courts=courts,
                         filters={
                             'status': status_filter,
                             'court_id': court_id_filter
                         })

@owner_bp.route('/booking/<int:booking_id>/approve', methods=['POST'])
@login_required
@owner_required
def approve_booking(booking_id):
    """Approve a booking request"""
    user_id = session['user_id']
    
    # Verify booking belongs to this owner
    booking = db.session.query(Booking).join(Court).filter(
        Booking.id == booking_id,
        Court.owner_id == user_id,
        Booking.status == 'pending'
    ).first_or_404()
    
    # Validate approval using business rules
    validation_result = RuleEngine.validate_booking_approval(
        booking_id=booking_id,
        owner_id=user_id
    )
    
    if not validation_result['valid']:
        flash(f'Cannot approve booking: {validation_result["reason"]}', 'error')
        return redirect(url_for('owner.booking_requests'))
    
    booking.status = 'confirmed'
    booking.approved_at = datetime.now()
    
    db.session.commit()
    
    # TODO: Send notification to player (email/SMS)
    
    flash(f'Booking approved for {booking.player.user.full_name}', 'success')
    return redirect(url_for('owner.booking_requests'))

@owner_bp.route('/booking/<int:booking_id>/reject', methods=['POST'])
@login_required
@owner_required
def reject_booking(booking_id):
    """Reject a booking request"""
    user_id = session['user_id']
    
    # Verify booking belongs to this owner
    booking = db.session.query(Booking).join(Court).filter(
        Booking.id == booking_id,
        Court.owner_id == user_id,
        Booking.status == 'pending'
    ).first_or_404()
    
    rejection_reason = request.form.get('reason', 'No reason provided')
    
    booking.status = 'rejected'
    booking.rejection_reason = rejection_reason
    booking.rejected_at = datetime.now()
    
    db.session.commit()
    
    # TODO: Send notification to player
    
    flash(f'Booking rejected for {booking.player.user.full_name}', 'info')
    return redirect(url_for('owner.booking_requests'))

@owner_bp.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
@owner_required
def cancel_booking(booking_id):
    """Cancel a confirmed booking"""
    user_id = session['user_id']
    
    # Verify booking belongs to this owner
    booking = db.session.query(Booking).join(Court).filter(
        Booking.id == booking_id,
        Court.owner_id == user_id,
        Booking.status == 'confirmed'
    ).first_or_404()
    
    # Check if cancellation is allowed (e.g., not too close to booking time)
    validation_result = RuleEngine.validate_booking_cancellation(
        booking_id=booking_id,
        user_id=user_id,
        user_type='owner'
    )
    
    if not validation_result['valid']:
        flash(f'Cannot cancel booking: {validation_result["reason"]}', 'error')
        return redirect(url_for('owner.booking_requests'))
    
    cancellation_reason = request.form.get('reason', 'Cancelled by owner')
    
    booking.status = 'cancelled'
    booking.cancellation_reason = cancellation_reason
    booking.cancelled_at = datetime.now()
    
    db.session.commit()
    
    # TODO: Send notification to player and handle refund if applicable
    
    flash(f'Booking cancelled for {booking.player.user.full_name}', 'info')
    return redirect(url_for('owner.booking_requests'))

@owner_bp.route('/reports')
@login_required
@owner_required
def reports():
    """View business reports and analytics"""
    user_id = session['user_id']
    
    # Date range for reports
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Revenue by court
    revenue_by_court = db.session.query(
        Court.name,
        Court.id,
        db.func.count(Booking.id).label('booking_count'),
        db.func.sum(Court.hourly_rate * 
                   db.func.extract('hour', Booking.end_time - Booking.start_time)).label('revenue')
    ).join(Booking).filter(
        Court.owner_id == user_id,
        Booking.status == 'confirmed',
        Booking.booking_date.between(start_date, end_date)
    ).group_by(Court.id, Court.name).all()
    
    # Booking status distribution
    status_stats = db.session.query(
        Booking.status,
        db.func.count(Booking.id).label('count')
    ).join(Court).filter(
        Court.owner_id == user_id,
        Booking.booking_date.between(start_date, end_date)
    ).group_by(Booking.status).all()
    
    # Popular time slots
    popular_times = db.session.query(
        db.func.extract('hour', Booking.start_time).label('hour'),
        db.func.count(Booking.id).label('booking_count')
    ).join(Court).filter(
        Court.owner_id == user_id,
        Booking.status == 'confirmed',
        Booking.booking_date.between(start_date, end_date)
    ).group_by(db.func.extract('hour', Booking.start_time)).all()
    
    # Calculate totals
    total_revenue = sum([r.revenue or 0 for r in revenue_by_court])
    total_bookings = sum([r.booking_count for r in revenue_by_court])
    
    return render_template('owner/reports.html',
                         revenue_by_court=revenue_by_court,
                         status_stats=status_stats,
                         popular_times=popular_times,
                         totals={
                             'revenue': total_revenue,
                             'bookings': total_bookings
                         },
                         date_range={
                             'start': start_date,
                             'end': end_date
                         })

@owner_bp.route('/messages')
@login_required
@owner_required
def messages():
    """View and manage messages with players"""
    user_id = session['user_id']
    
    # Get all conversations (similar to player messages)
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
    
    return render_template('owner/messages.html',
                         conversations=conversation_list)

@owner_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@owner_required
def edit_profile():
    """Edit owner profile"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if request.method == 'POST':
        # Update user information
        user.full_name = request.form.get('full_name', user.full_name)
        user.phone_number = request.form.get('phone_number', user.phone_number)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('owner.dashboard'))
    
    return render_template('owner/edit_profile.html', user=user)

@owner_bp.route('/api/court-availability/<int:court_id>')
@login_required  
@owner_required
def get_court_availability(court_id):
    """API endpoint to get court availability for a specific date"""
    user_id = session['user_id']
    
    # Verify court ownership
    court = Court.query.filter_by(id=court_id, owner_id=user_id).first_or_404()
    
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Get bookings for that date
    bookings = Booking.query.filter_by(
        court_id=court_id,
        booking_date=date_obj,
        status__in=['confirmed', 'pending']
    ).all()
    
    # Convert to JSON format
    booking_data = []
    for booking in bookings:
        booking_data.append({
            'id': booking.id,
            'start_time': booking.start_time.strftime('%H:%M'),
            'end_time': booking.end_time.strftime('%H:%M'),
            'status': booking.status,
            'player_name': booking.player.user.full_name,
            'notes': booking.notes
        })
    
    return jsonify({
        'court_name': court.name,
        'date': date_str,
        'bookings': booking_data
    })