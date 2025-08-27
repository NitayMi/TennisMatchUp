from flask import Blueprint, render_template, request, session, redirect, url_for
from models.user import User
from models.player import Player
from models.court import Court, Booking
from models.database import db
from services.matching_engine import MatchingEngine
from datetime import datetime, timedelta
from sqlalchemy import func


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    if session.get('user_id'):
        # Redirect logged-in users to their dashboard
        user_type = session.get('user_type')
        if user_type == 'player':
            return redirect(url_for('player.dashboard'))
        elif user_type == 'owner':
            return redirect(url_for('owner.dashboard'))
        elif user_type == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('main.dashboard'))
    
    # Get some stats for landing page
    stats = {
        'total_users': User.query.count(),
        'total_courts': Court.query.filter_by(is_active=True).count(),
        'total_bookings': Booking.query.count(),
        'cities_count': db.session.query(func.count(func.distinct(Court.location))).scalar() or 0
    }
    
    # Get featured courts
    featured_courts = Court.query.filter_by(is_active=True).limit(6).all()
    
    return render_template('index.html', stats=stats, featured_courts=featured_courts)

@main_bp.route('/dashboard')
def dashboard():
    """Generic dashboard - redirects based on user type"""
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    
    user_type = session.get('user_type')
    if user_type == 'player':
        return redirect(url_for('player.dashboard'))
    elif user_type == 'owner':
        return redirect(url_for('owner.dashboard'))
    elif user_type == 'admin':
        return redirect(url_for('admin.dashboard'))
    else:
        # Fallback dashboard
        user = User.query.get(session['user_id'])
        return render_template('dashboard.html', user=user)

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@main_bp.route('/search')
def search():
    """Global search functionality"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')  # courts, players, all
    location = request.args.get('location', '').strip()
    
    results = {
        'courts': [],
        'players': [],
        'query': query,
        'location': location
    }
    
    if query:
        if search_type in ['all', 'courts']:
            # Search courts
            court_query = Court.query.filter(Court.is_active == True)
            court_query = court_query.filter(
                db.or_(
                    Court.name.ilike(f'%{query}%'),
                    Court.location.ilike(f'%{query}%'),
                    Court.description.ilike(f'%{query}%')
                )
            )
            
            if location:
                court_query = court_query.filter(Court.location.ilike(f'%{location}%'))
            
            results['courts'] = court_query.limit(20).all()
        
        if search_type in ['all', 'players'] and session.get('user_id'):
            # Search players (only for logged-in users)
            player_query = Player.query.join(User).filter(User.is_active == True)
            player_query = player_query.filter(
                db.or_(
                    User.full_name.ilike(f'%{query}%'),
                    Player.preferred_location.ilike(f'%{query}%'),
                    Player.bio.ilike(f'%{query}%')
                )
            )
            
            if location:
                player_query = player_query.filter(Player.preferred_location.ilike(f'%{location}%'))
            
            results['players'] = player_query.limit(20).all()
    
    return render_template('search_results.html', **results)

@main_bp.route('/api/stats')
def api_stats():
    """API endpoint for real-time statistics"""
    stats = {
        'users': User.query.count(),
        'active_courts': Court.query.filter_by(is_active=True).count(),
        'today_bookings': Booking.query.filter_by(
            booking_date=datetime.now().date()
        ).count(),
        'this_week_bookings': Booking.query.filter(
            Booking.booking_date >= datetime.now().date() - timedelta(days=7)
        ).count()
    }
    
    return stats

@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'database': 'connected'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'database': 'disconnected'
        }, 500

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')