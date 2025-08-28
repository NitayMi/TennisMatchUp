"""
Authentication decorators for TennisMatchUp
Simple session-based decorators without Flask-Login dependency
"""
from functools import wraps
from flask import session, request, redirect, url_for, flash

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