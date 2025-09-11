"""
TennisMatchUp Search Service
Centralized search functionality to maintain MVC separation
"""

from datetime import datetime
from sqlalchemy import func, and_, or_
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court
from models.shared_booking import SharedBooking


class SearchService:
    """Centralized service for platform search operations"""
    
    @staticmethod
    def search_platform_content(query, search_type='all', limit=20):
        """
        Comprehensive platform search functionality
        Extracted from routes/main.py to maintain MVC separation
        """
        try:
            results = {
                'courts': [],
                'players': [],
                'total_count': 0
            }
            
            if not query or len(query.strip()) < 2:
                return {'success': True, 'results': results}
            
            search_term = f"%{query.strip()}%"
            
            # Search courts if requested
            if search_type in ['all', 'courts']:
                court_results = SearchService._search_courts(search_term, limit)
                results['courts'] = court_results
            
            # Search players if requested
            if search_type in ['all', 'players']:
                player_results = SearchService._search_players(search_term, limit)
                results['players'] = player_results
            
            results['total_count'] = len(results['courts']) + len(results['players'])
            
            return {
                'success': True,
                'results': results,
                'query': query.strip()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _search_courts(search_term, limit):
        """Search for courts by name, location, or amenities"""
        try:
            court_query = Court.query.filter(
                Court.is_active == True
            ).filter(
                or_(
                    Court.name.ilike(search_term),
                    Court.location.ilike(search_term),
                    Court.description.ilike(search_term),
                    Court.amenities.ilike(search_term),
                    Court.court_type.ilike(search_term),
                    Court.surface.ilike(search_term)
                )
            ).limit(limit)
            
            courts = court_query.all()
            
            # Format court results
            court_results = []
            for court in courts:
                court_data = {
                    'id': court.id,
                    'name': court.name,
                    'location': court.location,
                    'court_type': court.court_type,
                    'surface': court.surface,
                    'hourly_rate': court.hourly_rate,
                    'description': court.description[:100] + '...' if len(court.description or '') > 100 else court.description,
                    'amenities': court.amenities,
                    'has_lighting': court.has_lighting,
                    'has_parking': court.has_parking,
                    'owner_name': court.owner.full_name if court.owner else 'Unknown',
                    'image_url': court.image_url,
                    'type': 'court'
                }
                court_results.append(court_data)
            
            return court_results
            
        except Exception as e:
            print(f"Error searching courts: {e}")
            return []
    
    @staticmethod
    def _search_players(search_term, limit):
        """Search for players by name, location, or bio"""
        try:
            player_query = db.session.query(Player, User).join(User).filter(
                User.is_active == True,
                User.user_type == 'player'
            ).filter(
                or_(
                    User.full_name.ilike(search_term),
                    Player.preferred_location.ilike(search_term),
                    Player.bio.ilike(search_term),
                    Player.skill_level.ilike(search_term),
                    Player.availability.ilike(search_term)
                )
            ).limit(limit)
            
            player_results_query = player_query.all()
            
            # Format player results
            player_results = []
            for player, user in player_results_query:
                player_data = {
                    'id': player.id,
                    'user_id': user.id,
                    'name': user.full_name,
                    'skill_level': player.skill_level,
                    'preferred_location': player.preferred_location,
                    'availability': player.availability,
                    'bio': player.bio[:100] + '...' if len(player.bio or '') > 100 else player.bio,
                    'created_at': user.created_at,
                    'type': 'player',
                    'compatibility_score': 0  # Could be calculated based on current user
                }
                player_results.append(player_data)
            
            return player_results
            
        except Exception as e:
            print(f"Error searching players: {e}")
            return []
    
    @staticmethod
    def search_courts_advanced(filters, limit=20):
        """
        Advanced court search with multiple filters
        """
        try:
            query = Court.query.filter(Court.is_active == True)
            
            # Location filter
            if filters.get('location'):
                location_term = f"%{filters['location']}%"
                query = query.filter(Court.location.ilike(location_term))
            
            # Court type filter
            if filters.get('court_type'):
                query = query.filter(Court.court_type == filters['court_type'])
            
            # Surface type filter
            if filters.get('surface'):
                query = query.filter(Court.surface == filters['surface'])
            
            # Price range filter
            if filters.get('min_price'):
                query = query.filter(Court.hourly_rate >= filters['min_price'])
            if filters.get('max_price'):
                query = query.filter(Court.hourly_rate <= filters['max_price'])
            
            # Amenity filters
            if filters.get('has_lighting'):
                query = query.filter(Court.has_lighting == True)
            if filters.get('has_parking'):
                query = query.filter(Court.has_parking == True)
            
            # Execute query with limit
            courts = query.order_by(Court.created_at.desc()).limit(limit).all()
            
            return {
                'success': True,
                'courts': courts,
                'count': len(courts)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def search_players_advanced(filters, current_player_id=None, limit=20):
        """
        Advanced player search with compatibility scoring
        """
        try:
            query = db.session.query(Player, User).join(User).filter(
                User.is_active == True,
                User.user_type == 'player'
            )
            
            # Exclude current player
            if current_player_id:
                query = query.filter(Player.id != current_player_id)
            
            # Skill level filter
            if filters.get('skill_level'):
                query = query.filter(Player.skill_level == filters['skill_level'])
            
            # Location filter
            if filters.get('preferred_location'):
                location_term = f"%{filters['preferred_location']}%"
                query = query.filter(Player.preferred_location.ilike(location_term))
            
            # Availability filter
            if filters.get('availability'):
                query = query.filter(Player.availability == filters['availability'])
            
            # Execute query
            players = query.order_by(User.created_at.desc()).limit(limit).all()
            
            # Format results with compatibility scores
            results = []
            for player, user in players:
                player_data = {
                    'player': player,
                    'user': user,
                    'compatibility_score': SearchService._calculate_compatibility(
                        current_player_id, player.id
                    ) if current_player_id else 0
                }
                results.append(player_data)
            
            # Sort by compatibility score if applicable
            if current_player_id:
                results.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            return {
                'success': True,
                'players': results,
                'count': len(results)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _calculate_compatibility(player1_id, player2_id):
        """
        Calculate basic compatibility score between players
        Could be extended with more sophisticated algorithms
        """
        try:
            if not player1_id or not player2_id:
                return 0
            
            player1 = Player.query.get(player1_id)
            player2 = Player.query.get(player2_id)
            
            if not player1 or not player2:
                return 0
            
            # Use existing compatibility method if available
            if hasattr(player1, 'get_compatibility_score'):
                return player1.get_compatibility_score(player2)
            
            # Basic compatibility calculation
            score = 50  # Base score
            
            # Skill level compatibility
            skill_levels = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'professional': 4}
            level1 = skill_levels.get(player1.skill_level, 2)
            level2 = skill_levels.get(player2.skill_level, 2)
            skill_diff = abs(level1 - level2)
            
            if skill_diff == 0:
                score += 30
            elif skill_diff == 1:
                score += 20
            elif skill_diff == 2:
                score += 10
            
            # Location proximity (simplified)
            if (player1.preferred_location and player2.preferred_location and 
                player1.preferred_location.lower() in player2.preferred_location.lower()):
                score += 20
            
            return min(score, 100)  # Cap at 100
            
        except Exception as e:
            print(f"Error calculating compatibility: {e}")
            return 0
    
    @staticmethod
    def get_search_suggestions(query, limit=5):
        """Get search suggestions for autocomplete"""
        try:
            if not query or len(query.strip()) < 2:
                return {'success': True, 'suggestions': []}
            
            search_term = f"%{query.strip()}%"
            suggestions = []
            
            # Get court name suggestions
            court_names = db.session.query(Court.name).filter(
                Court.is_active == True,
                Court.name.ilike(search_term)
            ).limit(limit).all()
            
            for (name,) in court_names:
                suggestions.append({'text': name, 'type': 'court'})
            
            # Get location suggestions
            if len(suggestions) < limit:
                remaining_limit = limit - len(suggestions)
                locations = db.session.query(Court.location).distinct().filter(
                    Court.is_active == True,
                    Court.location.ilike(search_term)
                ).limit(remaining_limit).all()
                
                for (location,) in locations:
                    if location not in [s['text'] for s in suggestions]:
                        suggestions.append({'text': location, 'type': 'location'})
            
            return {
                'success': True,
                'suggestions': suggestions[:limit]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}