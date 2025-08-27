from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from models.database import db
from models.user import User
from models.player import PlayerProfile

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username')
        password = request.form.get('password')
        remember_me = bool(request.form.get('remember_me'))
        
        if not username_or_email or not password:
            flash('Username/email and password are required.', 'error')
            return render_template('auth/login.html')
        
        # Find user by username or email
        user = User.query.filter(
            db.or_(User.username == username_or_email, 
                   User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember_me)
            
            # Store user info in session for easy access
            session['user_type'] = user.user_type
            session['user_id'] = user.id
            
            flash(f'Welcome back, {user.get_display_name()}!', 'success')
            
            # Redirect to appropriate dashboard
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                if user.user_type == 'admin':
                    next_page = url_for('admin.dashboard')
                elif user.user_type == 'owner':
                    next_page = url_for('owner.dashboard')
                else:
                    next_page = url_for('player.dashboard')
            
            return redirect(next_page)
        else:
            flash('Invalid username/email or password.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        user_type = request.form.get('user_type', 'player')
        full_name = request.form.get('full_name', '').strip()
        city = request.form.get('city', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Basic validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if user_type not in ['player', 'owner']:
            errors.append('Please select a valid user type.')
        
        # Check for existing users
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        try:
            # Create new user
            user = User(
                username=username,
                email=email,
                user_type=user_type,
                full_name=full_name,
                city=city,
                phone=phone
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.flush()  # Flush to get the user ID
            
            # Create player profile if user is a player
            if user_type == 'player':
                skill_level = request.form.get('skill_level', 1, type=int)
                playing_style = request.form.get('playing_style', 'all_around')
                dominant_hand = request.form.get('dominant_hand', 'right')
                bio = request.form.get('bio', '').strip()
                
                profile = PlayerProfile(
                    user_id=user.id,
                    skill_level=max(1, min(10, skill_level)),
                    playing_style=playing_style,
                    dominant_hand=dominant_hand,
                    bio=bio
                )
                db.session.add(profile)
            
            db.session.commit()
            
            # Log the user in automatically
            login_user(user)
            session['user_type'] = user.user_type
            session['user_id'] = user.id
            
            flash(f'Registration successful! Welcome to TennisMatchUp, {user.get_display_name()}!', 'success')
            
            # Redirect to appropriate dashboard
            if user_type == 'owner':
                return redirect(url_for('owner.dashboard'))
            else:
                return redirect(url_for('player.dashboard'))
                
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            print(f"Registration error: {str(e)}")  # For debugging
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    user_name = current_user.get_display_name()
    logout_user()
    
    # Clear session data
    session.pop('user_type', None)
    session.pop('user_id', None)
    session.pop('is_impersonating', None)
    session.pop('original_user_id', None)
    
    flash(f'Goodbye, {user_name}! You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        # Update basic user info
        current_user.full_name = request.form.get('full_name', '').strip()
        current_user.city = request.form.get('city', '').strip() 
        current_user.phone = request.form.get('phone', '').strip()
        
        # Update player-specific info if applicable
        if current_user.is_player() and current_user.player_profile:
            profile = current_user.player_profile
            profile.bio = request.form.get('bio', '').strip()
            
            skill_level = request.form.get('skill_level', type=int)
            if skill_level and 1 <= skill_level <= 10:
                profile.skill_level = skill_level
            
            playing_style = request.form.get('playing_style')
            if playing_style in ['offensive', 'defensive', 'all_around']:
                profile.playing_style = playing_style
            
            dominant_hand = request.form.get('dominant_hand')
            if dominant_hand in ['right', 'left', 'ambidextrous']:
                profile.dominant_hand = dominant_hand
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error updating profile. Please try again.', 'error')
        print(f"Profile update error: {str(e)}")
    
    return redirect(url_for('auth.profile'))