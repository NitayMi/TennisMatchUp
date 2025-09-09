"""
Owner Routes for TennisMatchUp  
CLEANED VERSION - All business logic moved to Services
Controllers only handle HTTP concerns
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from models.user import User
from models.court import Court, Booking
from models.player import Player
from models.message import Message
from models.database import db
from utils.decorators import login_required, owner_required
from services.revenue_service import RevenueService
from services.booking_service import BookingService
from services.rule_engine import RuleEngine
from datetime import datetime, timedelta
from services.geo_service import GeoService

owner_bp = Blueprint('owner', __name__, url_prefix='/owner')

@owner_bp.route('/dashboard')
@login_required
@owner_required
def dashboard():
    """Owner dashboard - CLEANED VERSION"""
    user_id = session['user_id']
    
    # Get dashboard stats using service
    stats_result = RevenueService.calculate_owner_dashboard_stats(user_id)
    
    if stats_result['success']:
        stats = stats_result['stats']
        recent_bookings = stats_result['recent_bookings']
        courts = stats_result['courts']
    else:
        stats = {}
        recent_bookings = []
        courts = []
    
    return render_template('owner/dashboard.html',
                         stats=stats,
                         recent_bookings=recent_bookings,
                         courts=courts)

@owner_bp.route('/manage-courts')
@login_required
@owner_required
def manage_courts():
    """Manage all courts - CLEANED VERSION"""
    user_id = session['user_id']
    
    # Simple query - no business logic in controller
    courts = Court.query.filter_by(owner_id=user_id).order_by(
        Court.is_active.desc(),
        Court.created_at.desc()
    ).all()
    
    return render_template('owner/manage_courts.html', courts=courts)

@owner_bp.route('/add-court', methods=['GET', 'POST'])
@login_required
@owner_required
def add_court():
    """Add a new court - UPDATED WITH AUTO GEOCODING"""
    user_id = session['user_id']
    
    if request.method == 'POST':
        # Extract form data
        court_data = {
            'name': request.form.get('name', '').strip(),
            'location': request.form.get('location', '').strip(), 
            'court_type': request.form.get('court_type', ''),
            'surface': request.form.get('surface', ''),
            'hourly_rate': request.form.get('hourly_rate', type=float),
            'description': request.form.get('description', '').strip()
        }
        
        # Validate using rule engine
        validation = RuleEngine.validate_court_creation(
            owner_id=user_id,
            **court_data
        )
        
        if not validation['valid']:
            flash(validation['reason'], 'error')
            return render_template('owner/add_court.html')
        
        # Create court
        court = Court(
            owner_id=user_id,
            **court_data
        )
        
        try:
            db.session.add(court)
            db.session.flush()  # Get court ID without committing
            
            # AUTOMATIC GEOCODING - NEW FEATURE
            from services.geo_service import GeoService
            
            print(f"🌍 Auto-geocoding court: {court.name} - {court.location}")
            coordinates = GeoService.get_coordinates(court.location)
            
            if coordinates:
                court.latitude = coordinates[0]
                court.longitude = coordinates[1]
                print(f"✅ Geocoded: {coordinates[0]:.4f}, {coordinates[1]:.4f}")
                flash(f'Court "{court.name}" added successfully with location mapping!', 'success')
            else:
                print(f"⚠️ Geocoding failed for: {court.location}")
                flash(f'Court "{court.name}" added successfully (location will be mapped later)', 'warning')
            
            db.session.commit()
            return redirect(url_for('owner.manage_courts'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding court: {str(e)}")
            flash('Error adding court', 'error')
    
    return render_template('owner/add_court.html')



@owner_bp.route('/edit-court/<int:court_id>', methods=['GET', 'POST'])
@login_required
@owner_required
def edit_court(court_id):
    """Edit court details - UPDATED WITH AUTO GEOCODING"""
    user_id = session['user_id']
    
    # Verify ownership
    court = Court.query.filter_by(id=court_id, owner_id=user_id).first_or_404()
    
    if request.method == 'POST':
        old_location = court.location
        
        # Update court data
        court.name = request.form.get('name', '').strip()
        court.location = request.form.get('location', '').strip()
        court.court_type = request.form.get('court_type', '')
        court.surface = request.form.get('surface', '')
        court.hourly_rate = request.form.get('hourly_rate', type=float)
        court.description = request.form.get('description', '').strip()
        court.is_active = 'is_active' in request.form
        
        try:
            # CHECK IF LOCATION CHANGED - NEW LOGIC
            if court.location != old_location:
                from services.geo_service import GeoService
                
                print(f"🌍 Location changed, re-geocoding: {court.location}")
                coordinates = GeoService.get_coordinates(court.location)
                
                if coordinates:
                    court.latitude = coordinates[0]
                    court.longitude = coordinates[1]
                    print(f"✅ Re-geocoded: {coordinates[0]:.4f}, {coordinates[1]:.4f}")
                    flash('Court updated successfully with new location mapping!', 'success')
                else:
                    print(f"⚠️ Re-geocoding failed for: {court.location}")
                    # Keep old coordinates if geocoding fails
                    flash('Court updated successfully (location mapping will be updated later)', 'warning')
            else:
                flash('Court updated successfully!', 'success')
            
            db.session.commit()
            return redirect(url_for('owner.manage_courts'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating court: {str(e)}")
            flash('Error updating court', 'error')
    
    return render_template('owner/edit_court.html', court=court)

@owner_bp.route('/booking-requests')
@login_required
@owner_required
def booking_requests():
    """View booking requests - CLEANED VERSION"""
    user_id = session['user_id']
    
    # Simple query - no business logic
    bookings = db.session.query(Booking).join(Court).filter(
        Court.owner_id == user_id,
        Booking.status.in_(['pending', 'confirmed'])
    ).order_by(Booking.created_at.desc()).all()
    
    return render_template('owner/booking_requests.html', bookings=bookings)

@owner_bp.route('/booking/<int:booking_id>/approve', methods=['POST'])
@login_required
@owner_required
def approve_booking(booking_id):
    """Approve booking request - CLEANED VERSION"""
    user_id = session['user_id']
    
    # Verify booking belongs to this owner
    booking = db.session.query(Booking).join(Court).filter(
        Booking.id == booking_id,
        Court.owner_id == user_id,
        Booking.status == 'pending'
    ).first_or_404()
    
    # Delegate to service
    result = BookingService.update_booking_status(
        booking_id=booking_id,
        new_status='confirmed',
        user_id=user_id,
        user_type='owner'
    )
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('owner.booking_requests'))

@owner_bp.route('/booking/<int:booking_id>/reject', methods=['POST'])
@login_required
@owner_required
def reject_booking(booking_id):
    """Reject booking request - CLEANED VERSION"""
    user_id = session['user_id']
    rejection_reason = request.form.get('reason', 'No reason provided')
    
    # Verify booking belongs to this owner
    booking = db.session.query(Booking).join(Court).filter(
        Booking.id == booking_id,
        Court.owner_id == user_id,
        Booking.status == 'pending'
    ).first_or_404()
    
    # Delegate to service
    result = BookingService.update_booking_status(
        booking_id=booking_id,
        new_status='rejected',
        reason=rejection_reason,
        user_id=user_id,
        user_type='owner'
    )
    
    if result['success']:
        flash(f'Booking rejected for {booking.player.user.full_name}', 'info')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('owner.booking_requests'))

@owner_bp.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
@owner_required
def cancel_booking(booking_id):
    """Cancel confirmed booking - CLEANED VERSION"""
    user_id = session['user_id']
    cancellation_reason = request.form.get('reason', 'Cancelled by owner')
    
    # Verify booking belongs to this owner
    booking = db.session.query(Booking).join(Court).filter(
        Booking.id == booking_id,
        Court.owner_id == user_id,
        Booking.status == 'confirmed'
    ).first_or_404()
    
    # Delegate to service (includes cancellation rules validation)
    result = BookingService.update_booking_status(
        booking_id=booking_id,
        new_status='cancelled',
        reason=cancellation_reason,
        user_id=user_id,
        user_type='owner'
    )
    
    if result['success']:
        flash(f'Booking cancelled for {booking.player.user.full_name}', 'info')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('owner.booking_requests'))

@owner_bp.route('/calendar')
@login_required
@owner_required
def calendar():
    """Owner calendar view - CLEANED VERSION"""
    user_id = session['user_id']
    
    # Calendar data loaded via AJAX through API
    # No business logic in controller
    return render_template('owner/court_calendar.html')

@owner_bp.route('/reports')
@login_required
@owner_required
def reports():
    """View business reports - CLEANED VERSION"""
    user_id = session['user_id']
    
    # Get date range from query params
    period_days = request.args.get('period', 30, type=int)
    
    # Get analytics using service
    analytics_result = RevenueService.get_revenue_analytics(user_id, period_days)
    
    if analytics_result['success']:
        analytics = analytics_result
    else:
        analytics = {'success': False, 'error': 'Failed to load analytics'}
    
    return render_template('owner/reports.html',
                         analytics=analytics,
                         period_days=period_days)

@owner_bp.route('/financial-report')
@login_required
@owner_required
def financial_report():
    """Generate financial report - CLEANED VERSION"""
    user_id = session['user_id']
    
    # Get date range from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        # Default to current month
        today = datetime.now().date()
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    # Generate report using service
    report_result = RevenueService.generate_financial_report(user_id, start_date, end_date)
    
    if report_result['success']:
        report = report_result
    else:
        report = {'success': False, 'error': 'Failed to generate report'}
    
    return render_template('owner/financial_report.html', report=report)

@owner_bp.route('/messages')
@login_required
@owner_required
def messages():
    """View messages - CLEANED VERSION"""
    user_id = session['user_id']
    
    # Simple query - no business logic
    messages_received = Message.query.filter_by(receiver_id=user_id).order_by(
        Message.created_at.desc()
    ).limit(50).all()
    
    messages_sent = Message.query.filter_by(sender_id=user_id).order_by(
        Message.created_at.desc()
    ).limit(50).all()
    
    return render_template('owner/messages.html',
                         messages_received=messages_received,
                         messages_sent=messages_sent)

@owner_bp.route('/revenue/monthly')
@login_required
@owner_required
def monthly_revenue():
    """Get monthly revenue via AJAX - CLEANED VERSION"""
    user_id = session['user_id']
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    # Delegate to service
    result = RevenueService.calculate_monthly_revenue(user_id, month, year)
    
    return jsonify(result)

@owner_bp.route('/revenue/comparison')
@login_required
@owner_required
def revenue_comparison():
    """Get revenue comparison via AJAX - CLEANED VERSION"""
    user_id = session['user_id']
    
    # Delegate to service
    result = RevenueService.get_revenue_comparison(user_id)
    
    return jsonify(result)

@owner_bp.route('/court/<int:court_id>/stats')
@login_required
@owner_required
def court_stats(court_id):
    """Get court statistics - CLEANED VERSION"""
    user_id = session['user_id']
    
    # Verify ownership
    court = Court.query.filter_by(id=court_id, owner_id=user_id).first_or_404()
    
    # Get availability stats using service
    availability_result = BookingService.get_court_availability(
        court_id=court_id,
        check_date=datetime.now().date(),
        days_ahead=30
    )
    
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify(availability_result)
    
    return render_template('owner/court_stats.html', 
                         court=court,
                         availability=availability_result)

@owner_bp.route('/settings')
@login_required
@owner_required
def settings():
    """Owner settings - CLEANED VERSION"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    return render_template('owner/settings.html', user=user)

@owner_bp.route('/update-settings', methods=['POST'])
@login_required
@owner_required
def update_settings():
    """Update owner settings - CLEANED VERSION"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Update basic info
    user.full_name = request.form.get('full_name', '').strip()
    user.phone_number = request.form.get('phone_number', '').strip()
    
    try:
        db.session.commit()
        flash('Settings updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating settings', 'error')
    
    return redirect(url_for('owner.settings'))


@owner_bp.route('/court/<int:court_id>/toggle-status', methods=['POST'])
@login_required
@owner_required
def toggle_court_status(court_id):
    """Toggle court active status - owner version"""
    user_id = session['user_id']
    
    # Verify ownership
    court = Court.query.filter_by(id=court_id, owner_id=user_id).first_or_404()
    
    court.is_active = not court.is_active
    action = "activated" if court.is_active else "deactivated"
    
    try:
        db.session.commit()
        flash(f'Court "{court.name}" has been {action}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating court status', 'error')
    
    return redirect(url_for('owner.manage_courts'))


@owner_bp.route('/delete-court/<int:court_id>', methods=['POST'])
@login_required
@owner_required
def delete_court(court_id):
    """Delete court - CLEANED VERSION"""
    user_id = session['user_id']
    
    # Verify ownership
    court = Court.query.filter_by(id=court_id, owner_id=user_id).first_or_404()
    
    # Check if court has active bookings
    active_bookings = Booking.query.filter(
        Booking.court_id == court_id,
        Booking.status.in_(['confirmed', 'pending']),
        Booking.booking_date >= datetime.now().date()
    ).count()
    
    if active_bookings > 0:
        flash(f'Cannot delete court "{court.name}" - it has {active_bookings} active bookings', 'error')
        return redirect(url_for('owner.edit_court', court_id=court_id))
    
    court_name = court.name
    
    try:
        # Cancel all future pending bookings
        future_bookings = Booking.query.filter(
            Booking.court_id == court_id,
            Booking.booking_date >= datetime.now().date()
        ).all()
        
        for booking in future_bookings:
            booking.status = 'cancelled'
            booking.cancellation_reason = 'Court deleted by owner'
        
        db.session.delete(court)
        db.session.commit()
        flash(f'Court "{court_name}" has been deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting court', 'error')
    
    return redirect(url_for('owner.manage_courts'))