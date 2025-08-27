"""
Routes package initialization
Imports all blueprints for easy access
"""
from .auth import auth_bp
from .player import player_bp
from .owner import owner_bp
from .admin import admin_bp

__all__ = ['auth_bp', 'player_bp', 'owner_bp', 'admin_bp']