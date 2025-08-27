from functools import wraps
from flask import session, redirect, url_for, flash, abort
from flask_login import current_user, login_required

def role_required(*roles):
    """Decorator to require specific user roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('auth.login'))
            
            user_role = current_user.user_type
            if user_role not in roles and not current_user.is_admin:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.can_access_admin_panel():
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def player_required(f):
    """Decorator to require player role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if current_user.user_type != 'player' and not current_user.is_admin:
            flash('Player access required.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def owner_required(f):
    """Decorator to require owner role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if current_user.user_type != 'owner' and not current_user.is_admin:
            flash('Court owner access required.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function