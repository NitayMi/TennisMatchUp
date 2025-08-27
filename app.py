import os
from flask import Flask, render_template, session, redirect, url_for
from flask_login import LoginManager, current_user
from config import config
from models.database import db, init_db
from models.user import User

# Import routes
from routes.auth import auth_bp
from routes.player import player_bp
from routes.owner import owner_bp
from routes.admin import admin_bp
from routes.api import api_bp

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(player_bp, url_prefix='/player')
    app.register_blueprint(owner_bp, url_prefix='/owner')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        init_db()
    
    # Main routes
    @app.route('/')
    def index():
        """Home page - redirect based on user type"""
        if current_user.is_authenticated:
            if current_user.user_type == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif current_user.user_type == 'owner':
                return redirect(url_for('owner.dashboard'))
            else:  # player
                return redirect(url_for('player.dashboard'))
        return render_template('auth/login.html')
    
    @app.route('/dashboard')
    def dashboard():
        """Generic dashboard route"""
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Redirect to appropriate dashboard
        if current_user.user_type == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.user_type == 'owner':
            return redirect(url_for('owner.dashboard'))
        else:
            return redirect(url_for('player.dashboard'))
    
    # Context processors for templates
    @app.context_processor
    def inject_user_info():
        """Make user information available in all templates"""
        return {
            'current_user': current_user,
            'user_type': current_user.user_type if current_user.is_authenticated else None,
            'is_impersonating': session.get('is_impersonating', False),
            'original_user_id': session.get('original_user_id')
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)