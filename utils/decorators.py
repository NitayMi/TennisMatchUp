"""
Authentication decorators for TennisMatchUp
Simple session-based decorators without Flask-Login dependency
"""
from functools import wraps
from flask import session, request, redirect, url_for, flash, jsonify

def login_required(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))
        
        if session.get('user_type') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def player_required(f):
    """Decorator to require player privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))
        
        if session.get('user_type') != 'player':
            flash('Player access required', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def owner_required(f):
    """Decorator to require court owner privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))
        
        if session.get('user_type') != 'owner':
            flash('Court owner access required', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def anonymous_required(f):
    """Decorator to require user NOT to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id'):
            # Redirect logged-in users based on their type
            user_type = session.get('user_type')
            if user_type == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user_type == 'player':
                return redirect(url_for('player.dashboard'))
            elif user_type == 'owner':
                return redirect(url_for('owner.dashboard'))
            else:
                return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def api_required(f):
    """Decorator for API endpoints - returns JSON errors instead of redirects"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Authentication required', 'success': False}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def api_admin_required(f):
    """Decorator to require admin privileges for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Authentication required', 'success': False}), 401
        
        if session.get('user_type') != 'admin':
            return jsonify({'error': 'Admin access required', 'success': False}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def api_player_required(f):
    """Decorator to require player privileges for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Authentication required', 'success': False}), 401
        
        if session.get('user_type') != 'player':
            return jsonify({'error': 'Player access required', 'success': False}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def api_owner_required(f):
    """Decorator to require owner privileges for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Authentication required', 'success': False}), 401
        
        if session.get('user_type') != 'owner':
            return jsonify({'error': 'Owner access required', 'success': False}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# הוסף בסוף קובץ utils/decorators.py הקיים שלך:

def api_required(f):
    """Decorator for API endpoints - returns JSON errors instead of redirects"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Authentication required', 'success': False}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# גם צריך להוסיף import של jsonify בתחילת הקובץ:
# from flask import session, request, redirect, url_for, flash, jsonify