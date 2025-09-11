import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    # For development - SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///tennis_matchup.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Database connection pool settings for PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_timeout': 30,
        'pool_recycle': 3600,  # 1 hour
        'pool_pre_ping': True,
        'max_overflow': 10,
        'pool_size': 5,
        'connect_args': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30s'
        }
    }
    
    # WTForms Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Flask-Login Configuration
    REMEMBER_COOKIE_DURATION = 86400  # 1 day
    
    # AI Service Configuration
    OLLAMA_URL = os.environ.get('OLLAMA_URL') or 'http://localhost:11434'
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL') or 'llama2'
    
    # Cloud Services Configuration
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    OPENCAGE_API_KEY = os.environ.get('OPENCAGE_API_KEY')
    
    # Application Settings
    POSTS_PER_PAGE = 10
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    
    # Business Rules Configuration
    MAX_SKILL_LEVEL_DIFFERENCE = 2
    MAX_PENDING_BOOKINGS = 3
    BOOKING_ADVANCE_HOURS = 2
    OWNER_RESPONSE_HOURS = 24

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///tennis_matchup_dev.db'

class ProductionConfig(Config):
    """Production configuration - AWS RDS PostgreSQL"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://tennisadmin:YOUR_PASSWORD@tennis-matchup-db.xxxxx.us-east-1.rds.amazonaws.com:5432/tennismatchup'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///tennis_matchup_test.db'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}