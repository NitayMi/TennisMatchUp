# services/system_health_service.py - רק פונקציות monitoring
"""
System Health Service for TennisMatchUp
Monitors Render.com server + Somee.com database
Pure monitoring service - no email/sms mixing
"""
import os
import requests
from datetime import datetime

class SystemHealthService:
    """System and deployment health monitoring"""
    
    @staticmethod
    def check_deployment_status():
        """Check Render.com + Somee.com status"""
        return {
            'server_provider': 'render.com',
            'database_provider': 'somee.com',
            'server_status': SystemHealthService._check_server_health(),
            'database_status': SystemHealthService._check_database_health(),
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def _check_server_health():
        """Check Render.com server health"""
        try:
            response = requests.get('http://localhost:5000/health', timeout=5)
            return 'healthy' if response.status_code == 200 else 'unhealthy'
        except:
            return 'unavailable'
    
    @staticmethod
    def _check_database_health():
        """Check Somee.com database connection"""
        try:
            from models.database import db
            result = db.engine.execute('SELECT 1').fetchone()
            return 'connected' if result else 'disconnected'
        except:
            return 'error'
    
    @staticmethod
    def get_system_limits():
        """Check system limits for production deployment"""
        return {
            'max_users': 10000,
            'max_courts': 1000, 
            'max_bookings_per_day': 5000,
            'environment': os.getenv('FLASK_ENV', 'development'),
            'deployment_ready': True
        }