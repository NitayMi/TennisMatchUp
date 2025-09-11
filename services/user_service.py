"""
TennisMatchUp User Service
Centralized user management operations to maintain MVC separation
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court
from services.rule_engine import RuleEngine
from services.geo_service import GeoService


class UserService:
    """Centralized service for user management operations"""
    
    @staticmethod
    def get_filtered_users(user_type=None, status=None, search=None, page=1, per_page=50):
        """
        Get filtered list of users with pagination
        Extracted from routes/admin.py to maintain MVC separation
        """
        try:
            query = User.query
            
            # Apply filters
            if user_type:
                query = query.filter_by(user_type=user_type)
                
            if status is not None:
                is_active = status == 'active'
                query = query.filter_by(is_active=is_active)
                
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        User.full_name.ilike(search_term),
                        User.email.ilike(search_term)
                    )
                )
            
            # Apply pagination
            users = query.order_by(User.created_at.desc()).paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            return {
                'success': True,
                'users': users.items,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': users.total,
                    'pages': users.pages,
                    'has_prev': users.has_prev,
                    'has_next': users.has_next
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_user_with_profile(user_data, profile_data=None):
        """
        Create user with associated profile (Player if applicable)
        Extracted from routes/auth.py to maintain MVC separation
        """
        try:
            # Validate user data using RuleEngine
            validation_result = RuleEngine.validate_user_registration(
                user_data.get('full_name', ''),
                user_data.get('email', ''),
                user_data.get('password', ''),
                user_data.get('phone_number', ''),
                user_data.get('user_type', 'player')
            )
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'errors': validation_result['errors']
                }
            
            # Create user
            user = User(
                full_name=user_data['full_name'],
                email=user_data['email'],
                password=user_data['password'],
                user_type=user_data.get('user_type', 'player'),
                phone_number=user_data.get('phone_number', '')
            )
            
            db.session.add(user)
            db.session.flush()  # Get the user ID
            
            # Create player profile if user is a player
            if user.user_type == 'player' and profile_data:
                player = Player(
                    user_id=user.id,
                    skill_level=profile_data.get('skill_level', 'beginner'),
                    preferred_location=profile_data.get('preferred_location', ''),
                    availability=profile_data.get('availability', 'flexible'),
                    bio=profile_data.get('bio', '')
                )
                
                # Update coordinates if location provided
                if player.preferred_location:
                    coordinates = GeoService.get_coordinates(player.preferred_location)
                    if coordinates:
                        player.latitude = coordinates['lat']
                        player.longitude = coordinates['lng']
                
                db.session.add(player)
            
            db.session.commit()
            
            return {
                'success': True,
                'user': user,
                'message': 'User created successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def update_user_profile(user_id, user_data, profile_data=None):
        """Update user and associated profile data"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Update user fields
            if 'full_name' in user_data:
                user.full_name = user_data['full_name']
            if 'email' in user_data:
                user.email = user_data['email']
            if 'phone_number' in user_data:
                user.phone_number = user_data['phone_number']
            
            # Update player profile if applicable
            if user.user_type == 'player' and profile_data:
                player = Player.query.filter_by(user_id=user_id).first()
                if player:
                    if 'skill_level' in profile_data:
                        player.skill_level = profile_data['skill_level']
                    if 'preferred_location' in profile_data:
                        player.preferred_location = profile_data['preferred_location']
                        # Update coordinates
                        coordinates = GeoService.get_coordinates(player.preferred_location)
                        if coordinates:
                            player.latitude = coordinates['lat']
                            player.longitude = coordinates['lng']
                    if 'availability' in profile_data:
                        player.availability = profile_data['availability']
                    if 'bio' in profile_data:
                        player.bio = profile_data['bio']
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'user': user,
                'message': 'Profile updated successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_active_users_for_messaging(current_user_id, search=None, limit=20):
        """Get active users for messaging functionality"""
        try:
            query = User.query.filter(
                User.id != current_user_id,
                User.is_active == True
            )
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(User.full_name.ilike(search_term))
            
            users = query.order_by(User.full_name).limit(limit).all()
            
            return {
                'success': True,
                'users': users
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def deactivate_user(user_id, reason=None):
        """Deactivate a user account"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            user.is_active = False
            user.updated_at = datetime.utcnow()
            
            # Log deactivation reason if provided
            if reason:
                # Could be extended to log to an audit table
                pass
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'User {user.full_name} has been deactivated'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def reactivate_user(user_id):
        """Reactivate a user account"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            user.is_active = True
            user.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'User {user.full_name} has been reactivated'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_user_statistics():
        """Get comprehensive user statistics"""
        try:
            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            players_count = User.query.filter_by(user_type='player').count()
            owners_count = User.query.filter_by(user_type='owner').count()
            admins_count = User.query.filter_by(user_type='admin').count()
            
            # Recent registrations (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_registrations = User.query.filter(
                User.created_at >= thirty_days_ago
            ).count()
            
            return {
                'success': True,
                'stats': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'inactive_users': total_users - active_users,
                    'players_count': players_count,
                    'owners_count': owners_count,
                    'admins_count': admins_count,
                    'recent_registrations': recent_registrations
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}