"""
Admin Routes for TennisMatchUp
CLEANED VERSION - All business logic moved to Services
Controllers only handle HTTP concerns
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from models.user import User
from models.player import Player
from models.court import Court, Booking
from models.message import Message
from models.database import db
from utils.decorators import login_required, admin_required
from services.report_service import ReportService
from services.rule_engine import RuleEngine
from datetime import datetime, timedelta
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard - CLEANED VERSION"""
    
    # Get dashboard stats using service
    stats_result = ReportService.generate_admin_dashboard_stats()
    
    if stats_result['success']:
        stats = stats_result['stats']
        
        # Get top performers using service
        top_performers = ReportService.get_top_performers(period_days=30, limit=5)
        
        if top_performers['success']:
            top_players = top_performers['top_players']
            top_courts = top_performers['top_courts']
        else:
            top_players = []
            top_courts = []
            
        # Recent activity (simple query - no business logic)
        recent_bookings = Booking.query.order_by(
            Booking.created_at.desc()
        ).limit(10).all()
    else:
        stats = {}
        top_players = []
        top_courts = []
        recent_bookings = []
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         top_players=top_players,
                         top_courts=top_courts,
                         recent_bookings=recent_bookings)

@admin_bp.route('/user-management')
@login_required
@admin_required
def user_management():
    """Manage all system users"""
    
    # Get filter parameters
    user_type = request.args.get('type', 'all')
    status = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    query = User.query
    
    if user_type != 'all':
        query = query.filter(User.user_type == user_type)
    
    if status == 'active':
        query = query.filter(User.is_active == True)
    elif status == 'inactive':
        query = query.filter(User.is_active == False)
    
    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.phone_number.ilike(f'%{search}%')
            )
        )
    
    # Paginate results
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/user_management.html',
                         users=users,
                         filters={
                             'type': user_type,
                             'status': status,
                             'search': search
                         })

@admin_bp.route('/user/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """View detailed user information"""
    user = User.query.get_or_404(user_id)
    
    # Get user-specific data based on type
    player_data = None
    owner_data = None
    
    if user.user_type == 'player':
        player_data = Player.query.filter_by(user_id=user_id).first()
        # Get player's booking history
        bookings = Booking.query.filter_by(player_id=player_data.id).order_by(
            Booking.created_at.desc()
        ).limit(10).all()
        player_data.recent_bookings = bookings
        
    elif user.user_type == 'owner':
        # Get owner's courts and bookings
        courts = Court.query.filter_by(owner_id=user_id).all()
        total_bookings = db.session.query(Booking).join(Court).filter(
            Court.owner_id == user_id
        ).count()
        owner_data = {
            'courts': courts,
            'total_bookings': total_bookings
        }
    
    # Get user's messages
    messages_sent = Message.query.filter_by(sender_id=user_id).count()
    messages_received = Message.query.filter_by(receiver_id=user_id).count()
    
    return render_template('admin/user_detail.html',
                         user=user,
                         player_data=player_data,
                         owner_data=owner_data,
                         message_stats={
                             'sent': messages_sent,
                             'received': messages_received
                         })

@admin_bp.route('/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Activate or deactivate a user"""
    user = User.query.get_or_404(user_id)
    
    # Don't allow deactivating other admins
    if user.user_type == 'admin' and user.id != session['user_id']:
        flash('Cannot modify other admin accounts', 'error')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    user.is_active = not user.is_active
    action = "activated" if user.is_active else "deactivated"
    
    db.session.commit()
    
    flash(f'User {user.full_name} has been {action}', 'success')
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/user/<int:user_id>/impersonate', methods=['POST'])
@login_required
@admin_required
def impersonate_user(user_id):
    """Impersonate another user for testing purposes"""
    user = User.query.get_or_404(user_id)
    
    if not user.is_active:
        flash('Cannot impersonate inactive user', 'error')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    # Don't allow impersonating other admins
    if user.user_type == 'admin':
        flash('Cannot impersonate other admin users', 'error')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    # Store original admin info for returning later
    session['original_user_id'] = session['user_id']
    session['original_user_type'] = session['user_type']
    session['original_user_name'] = session['user_name']
    
    # Switch to target user
    session['user_id'] = user.id
    session['user_type'] = user.user_type
    session['user_name'] = user.full_name
    session['is_impersonating'] = True
    
    flash(f'Now impersonating {user.full_name}', 'info')
    
    # Redirect to appropriate dashboard
    if user.user_type == 'player':
        return redirect(url_for('player.dashboard'))
    elif user.user_type == 'owner':
        return redirect(url_for('owner.dashboard'))
    else:
        return redirect(url_for('main.dashboard'))

@admin_bp.route('/stop-impersonation', methods=['POST'])
@login_required
def stop_impersonation():
    """Stop impersonating and return to admin account"""
    if not session.get('is_impersonating'):
        flash('Not currently impersonating', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Restore original admin session
    session['user_id'] = session['original_user_id']
    session['user_type'] = session['original_user_type']
    session['user_name'] = session['original_user_name']
    
    # Clean up impersonation data
    session.pop('original_user_id', None)
    session.pop('original_user_type', None) 
    session.pop('original_user_name', None)
    session.pop('is_impersonating', None)
    
    flash('Stopped impersonation, returned to admin account', 'info')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/system-reports')
@login_required
@admin_required
def system_reports():
    """View comprehensive system reports - CLEANED VERSION"""
    
    # Date range for reports
    days_back = request.args.get('days', 30, type=int)
    
    # Get performance metrics using service
    performance_result = ReportService.system_performance_metrics(days_back)
    
    if performance_result['success']:
        metrics = performance_result['metrics']
        registration_data = metrics.get('registration_trends', {}).get('daily_data', [])
        booking_data = metrics.get('booking_trends', {}).get('daily_data', [])
        revenue_data = metrics.get('revenue_trends', {}).get('daily_data', [])
        court_utilization = metrics.get('court_performance', [])
        location_stats = metrics.get('popular_locations', [])
        problem_courts = metrics.get('problem_areas', [])
        date_range = metrics.get('period', {})
    else:
        registration_data = []
        booking_data = []
        revenue_data = []
        court_utilization = []
        location_stats = []
        problem_courts = []
        date_range = {'days': days_back}
    
    return render_template('admin/system_reports.html',
                         registration_data=registration_data,
                         booking_data=booking_data,
                         revenue_data=revenue_data,
                         court_utilization=court_utilization,
                         location_stats=location_stats,
                         problem_courts=problem_courts,
                         date_range=date_range)

@admin_bp.route('/court-management')
@login_required
@admin_required
def court_management():
    """Manage all courts in the system"""
    
    # Get filter parameters
    status = request.args.get('status', 'all')
    location = request.args.get('location', '').strip()
    owner_id = request.args.get('owner_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    query = Court.query.join(User, Court.owner_id == User.id)
    
    if status == 'active':
        query = query.filter(Court.is_active == True)
    elif status == 'inactive':
        query = query.filter(Court.is_active == False)
    
    if location:
        query = query.filter(Court.location.ilike(f'%{location}%'))
        
    if owner_id:
        query = query.filter(Court.owner_id == owner_id)
    
    courts = query.order_by(Court.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get all owners for filter dropdown
    owners = User.query.filter_by(user_type='owner').order_by(User.full_name).all()
    
    return render_template('admin/court_management.html',
                         courts=courts,
                         owners=owners,
                         filters={
                             'status': status,
                             'location': location,
                             'owner_id': owner_id
                         })

@admin_bp.route('/court/<int:court_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_court_status(court_id):
    """Activate or deactivate a court"""
    court = Court.query.get_or_404(court_id)
    
    court.is_active = not court.is_active
    action = "activated" if court.is_active else "deactivated"
    
    db.session.commit()
    
    flash(f'Court "{court.name}" has been {action}', 'success')
    return redirect(url_for('admin.court_management'))

@admin_bp.route('/messages/broadcast', methods=['GET', 'POST'])
@login_required
@admin_required
def broadcast_message():
    """Send broadcast message to all users or specific user types"""
    
    if request.method == 'POST':
        recipient_type = request.form.get('recipient_type', 'all')
        subject = request.form.get('subject', '').strip()
        content = request.form.get('content', '').strip()
        
        if not subject or not content:
            flash('Subject and content are required', 'error')
            return redirect(url_for('admin.broadcast_message'))
        
        # Get recipient users
        if recipient_type == 'all':
            recipients = User.query.filter(User.user_type != 'admin').all()
        else:
            recipients = User.query.filter_by(user_type=recipient_type).all()
        
        # Create messages
        sender_id = session['user_id']
        message_count = 0
        
        for recipient in recipients:
            message = Message(
                sender_id=sender_id,
                receiver_id=recipient.id,
                content=f"**{subject}**\n\n{content}",
                is_broadcast=True
            )
            db.session.add(message)
            message_count += 1
        
        db.session.commit()
        
        flash(f'Broadcast message sent to {message_count} users', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/broadcast_message.html')

@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API endpoint for dashboard statistics - CLEANED VERSION"""
    
    # Get stats using service
    stats_result = ReportService.generate_admin_dashboard_stats()
    
    if stats_result['success']:
        return jsonify(stats_result)
    else:
        return jsonify({'success': False, 'error': 'Failed to load statistics'}), 500