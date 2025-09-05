from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.database import db
from models.user import User
from models.player import Player
from services.rule_engine import RuleEngine
from services.cloud_service import CloudService
from services.email_service import EmailService
from utils.helpers import validate_email, validate_phone

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        # Validate input
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return render_template('auth/login.html')
        
        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('auth/login.html')
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html')
            
            # Create session
            session['user_id'] = user.id
            session['user_name'] = user.full_name
            session['user_type'] = user.user_type
            session['is_impersonating'] = False
            
            # Set session permanence
            if remember_me:
                session.permanent = True
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # Redirect based on user type
            if user.user_type == 'player':
                return redirect(url_for('player.dashboard'))
            elif user.user_type == 'owner':
                return redirect(url_for('owner.dashboard'))
            elif user.user_type == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone_number = request.form.get('phone_number', '').strip()
        user_type = request.form.get('user_type', '').strip()
        terms = request.form.get('terms') == 'on'
        
        # Player-specific fields
        skill_level = request.form.get('skill_level', '').strip()
        preferred_location = request.form.get('preferred_location', '').strip()
        availability = request.form.get('availability', '').strip()
        bio = request.form.get('bio', '').strip()
        
        # Validation
        errors = []
        
        if not full_name or len(full_name) < 2:
            errors.append('Full name must be at least 2 characters long')
        
        if not email or not validate_email(email):
            errors.append('Please enter a valid email address')
        
        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if phone_number and not validate_phone(phone_number):
            errors.append('Please enter a valid phone number')
        
        if user_type not in ['player', 'owner']:
            errors.append('Please select a valid user type')
        
        if user_type == 'player':
            if not skill_level or skill_level not in ['beginner', 'intermediate', 'advanced', 'professional']:
                errors.append('Please select a valid skill level')
        
        if not terms:
            errors.append('You must accept the terms and conditions')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists')
        
        # Business rules validation
        validation_result = RuleEngine.validate_user_registration(
            email=email, 
            user_type=user_type,
            skill_level=skill_level if user_type == 'player' else None
        )
        if not validation_result['valid']:
            errors.append(validation_result['reason'])
        
        # If there are errors, show them
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        try:
            # Create user
            user = User(
                full_name=full_name,
                email=email,
                password=password,
                user_type=user_type,
                phone_number=phone_number if phone_number else None
            )
            
            db.session.add(user)
            db.session.flush()  # Get user ID before committing
            
            # Create player profile if user is a player
            if user_type == 'player':
                player = Player(
                    user_id=user.id,
                    skill_level=skill_level,
                    preferred_location=preferred_location if preferred_location else None,
                    availability=availability if availability else None,
                    bio=bio if bio else None
                )
                db.session.add(player)
            
            db.session.commit()
            
            # Send welcome email
            try:
                CloudService.send_welcome_email(user)
            except:
                pass  # Don't fail registration if email fails
            
            # Auto-login after registration
            session['user_id'] = user.id
            session['user_name'] = user.full_name
            session['user_type'] = user.user_type
            session['is_impersonating'] = False
            
            flash(f'Welcome to TennisMatchUp, {user.full_name}!', 'success')
            
            # Redirect based on user type
            if user_type == 'player':
                return redirect(url_for('player.dashboard'))
            elif user_type == 'owner':
                return redirect(url_for('owner.dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {str(e)}")
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    user_name = session.get('user_name', 'User')
    
    # Clear session
    session.clear()
    
    flash(f'Goodbye, {user_name}!', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email or not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            try:
                # Generate reset token (in production, save to database with expiration)
                reset_token = f"reset_{user.id}_{user.email}"  # Simplified for demo
                
                # Send reset email
                EmailService.send_password_reset(user, reset_token)
                flash('Password reset instructions have been sent to your email', 'success')
            except:
                flash('Failed to send reset email. Please try again.', 'error')
        else:
            # Don't reveal if email exists or not
            flash('If an account with this email exists, password reset instructions have been sent', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Password reset form"""
    token = request.args.get('token') or request.form.get('token')
    
    if not token:
        flash('Invalid or missing reset token', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    # In production, validate token from database
    # For demo, just check format
    if not token.startswith('reset_'):
        flash('Invalid reset token', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not password or len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Extract user info from token (simplified for demo)
        try:
            parts = token.split('_')
            user_id = int(parts[1])
            user = User.query.get(user_id)
            
            if user:
                user.set_password(password)
                db.session.commit()
                
                flash('Your password has been reset successfully', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Invalid reset token', 'error')
        except:
            flash('Invalid reset token', 'error')
    
    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """Change password for logged-in users"""
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_password:
            flash('Please enter your current password', 'error')
            return render_template('auth/change_password.html')
        
        if not user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return render_template('auth/change_password.html')
        
        if not new_password or len(new_password) < 8:
            flash('New password must be at least 8 characters long', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('auth/change_password.html')
        
        if current_password == new_password:
            flash('New password must be different from current password', 'error')
            return render_template('auth/change_password.html')
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        flash('Your password has been changed successfully', 'success')
        
        # Redirect based on user type
        if user.user_type == 'player':
            return redirect(url_for('player.dashboard'))
        elif user.user_type == 'owner':
            return redirect(url_for('owner.dashboard'))
        elif user.user_type == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('main.dashboard'))
    
    return render_template('auth/change_password.html')

@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """Edit user profile"""
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Update basic user info
        user.full_name = request.form.get('full_name', user.full_name).strip()
        phone_number = request.form.get('phone_number', '').strip()
        
        if phone_number and not validate_phone(phone_number):
            flash('Please enter a valid phone number', 'error')
            return render_template('auth/profile.html', user=user)
        
        user.phone_number = phone_number if phone_number else None
        
        # Update player-specific info
        if user.user_type == 'player' and user.player_profile:
            player = user.player_profile
            player.preferred_location = request.form.get('preferred_location', player.preferred_location)
            player.availability = request.form.get('availability', player.availability)
            player.bio = request.form.get('bio', player.bio)
            
            skill_level = request.form.get('skill_level')
            if skill_level in ['beginner', 'intermediate', 'advanced', 'professional']:
                player.skill_level = skill_level
        
        try:
            db.session.commit()
            flash('Profile updated successfully', 'success')
        except:
            db.session.rollback()
            flash('Failed to update profile', 'error')
    
    return render_template('auth/profile.html', user=user)