from flask import Flask, session, render_template
# Note: Using built-in Flask sessions instead of flask_session for simplicity
# from flask_session import Session
import os
from datetime import timedelta

# Import database and config
from models.database import db, init_db
from config import Config

# Import blueprints
from routes.main import main_bp
from routes.auth import auth_bp
from routes.player import player_bp
from routes.owner import owner_bp
from routes.admin import admin_bp
from routes.shared_booking import shared_booking_bp
from routes.api import api_bp  # NEW: Import API routes
from routes.ai import ai_bp
from routes.messaging import messaging_bp

# Import template filters
from utils.template_filters import register_filters

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Set session configuration (using built-in Flask sessions)
    app.config['SESSION_PERMANENT'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.secret_key = app.config.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Initialize database
    init_db(app)

    # Enable migrations
    from flask_migrate import Migrate
    Migrate(app, db)
    
    # Register template filters
    register_filters(app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(player_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(shared_booking_bp)
    app.register_blueprint(api_bp)  # NEW: Register API routes
    app.register_blueprint(ai_bp)   # NEW: Register AI routes
    app.register_blueprint(messaging_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403
    
    # Context processors
    @app.context_processor
    def inject_user_info():
        """Inject user info into all templates"""
        return dict(session=session)
    
    return app


if __name__ == '__main__':
    # Create the Flask app
    app = create_app()
    
    print("TennisMatchUp Server Starting...")
    print("=" * 50)
    print("Available Routes:")
    print("• Home: http://localhost:5000")
    print("• Login: http://localhost:5000/auth/login")
    print("• Register: http://localhost:5000/auth/register")
    print("• API Docs: http://localhost:5000/api")
    print("• Admin: admin@tennismatchup.com / admin123")
    print("• Player Demo: player@demo.com / password123")
    print("• Owner Demo: owner@demo.com / password123")
    print("=" * 50)
    
    # Run the development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )

app = create_app()