from flask import Blueprint, render_template, request, session, redirect, url_for
from models.user import User
from models.player import Player
from models.court import Court, Booking
from models.database import db
from services.matching_engine import MatchingEngine
from services.search_service import SearchService
from services.report_service import ReportService
from datetime import datetime, timedelta
from sqlalchemy import func


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    if session.get('user_id'):
        # Redirect logged-in users to their dashboard only if they have valid profile
        user_type = session.get('user_type')
        try:
            if user_type == 'player':
                # Verify player exists before redirecting
                from models.player import Player
                player = Player.query.filter_by(user_id=session['user_id']).first()
                if player:
                    return redirect(url_for('player.dashboard'))
            elif user_type == 'owner':
                return redirect(url_for('owner.dashboard'))
            elif user_type == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        except Exception as e:
            # If there's an error with redirects, continue to home page
            print(f"Dashboard redirect error: {e}")
            pass
    
    # Get platform statistics using ReportService
    stats_result = ReportService.get_platform_statistics()
    stats = stats_result.get('statistics', {}) if stats_result.get('success') else {
        'total_users': 0, 'total_courts': 0, 'total_bookings': 0, 'cities_count': 0
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
    """Global search functionality - Clean MVC version using SearchService"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')  # courts, players, all
    location = request.args.get('location', '').strip()
    
    # Use SearchService for all search operations
    search_result = SearchService.search_platform_content(query, search_type, limit=20)
    
    if not search_result['success']:
        # Fallback to empty results on error
        results = {
            'courts': [],
            'players': [],
            'query': query,
            'location': location,
            'error': search_result.get('error', 'Search error occurred')
        }
    else:
        results = search_result['results']
        results['query'] = query
        results['location'] = location
    
    # Apply location filter if provided
    if location and search_result['success']:
        # Filter courts by location
        results['courts'] = [c for c in results['courts'] 
                           if location.lower() in c.get('location', '').lower()]
        
        # Filter players by preferred location 
        results['players'] = [p for p in results['players'] 
                            if location.lower() in p.get('preferred_location', '').lower()]
    
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