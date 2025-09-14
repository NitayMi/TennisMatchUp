"""
Court Recommendation Engine for TennisMatchUp
Smart court matching algorithm similar to MatchingEngine for players
Following MVC principles with complete business logic abstraction
"""
from datetime import datetime, date, time
from models.database import db
from models.court import Court, Booking
from models.player import Player
from models.user import User
from services.geo_service import GeoService
from services.rule_engine import RuleEngine
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload

class CourtRecommendationEngine:
    """Intelligent court recommendation system with geographic precision"""
    
    @staticmethod
    def find_recommended_courts(player_id, filters=None, sort_by='recommended', limit=50):
        """
        Find and rank courts based on player preferences and smart algorithm
        
        Args:
            player_id: ID of the player requesting courts
            filters: Dict of filters (location, court_type, surface, max_price, date)
            sort_by: Sort criteria (recommended, price_low, price_high, distance, rating)
            limit: Maximum number of courts to return
            
        Returns:
            List of courts with recommendation scores and metadata
        """
        player = Player.query.get(player_id)
        if not player:
            return []
        
        # Ensure player has coordinates for distance calculations
        if not player.latitude or not player.longitude:
            player.update_coordinates()
            db.session.commit()
        
        # Build base query for active courts
        query = Court.query.options(joinedload(Court.bookings)).filter(
            Court.is_active == True
        )
        
        # Apply filters
        if filters:
            query = CourtRecommendationEngine._apply_filters(query, filters)
        
        # Get all potential courts
        potential_courts = query.all()
        
        # Score and rank courts
        scored_courts = []
        player_coords = player.get_coordinates()
        
        for court in potential_courts:
            # Calculate recommendation score
            score_data = CourtRecommendationEngine._calculate_court_score(
                player, court, player_coords, filters
            )
            
            # Skip courts with very low scores unless showing all
            if sort_by == 'recommended' and score_data['total_score'] < 30:
                continue
            
            scored_courts.append({
                'court': court,
                'score_data': score_data,
                'total_score': score_data['total_score'],
                'distance_km': score_data['distance_km'],
                'availability_score': score_data['availability_score'],
                'preference_score': score_data['preference_score'],
                'value_score': score_data['value_score']
            })
        
        # Sort courts based on criteria
        sorted_courts = CourtRecommendationEngine._sort_courts(scored_courts, sort_by)
        
        # Return limited results
        return sorted_courts[:limit]
    
    @staticmethod
    def get_all_courts_with_basic_sorting(filters=None, sort_by='name', limit=50):
        """
        Get all active courts with basic sorting - no recommendation scoring
        Used for "Show All Courts" functionality
        """
        # Build base query for active courts
        query = Court.query.filter(Court.is_active == True)
        
        # Apply filters
        if filters:
            query = CourtRecommendationEngine._apply_filters(query, filters)
        
        # Apply simple sorting
        if sort_by == 'price_low':
            query = query.order_by(Court.hourly_rate.asc())
        elif sort_by == 'price_high':
            query = query.order_by(Court.hourly_rate.desc())
        elif sort_by == 'name':
            query = query.order_by(Court.name.asc())
        elif sort_by == 'location':
            query = query.order_by(Court.location.asc())
        else:
            query = query.order_by(Court.name.asc())
        
        courts = query.limit(limit).all()
        
        # Return in same format as recommended courts for consistency
        return [{
            'court': court,
            'score_data': {'total_score': 0, 'distance_km': None},
            'total_score': 0,
            'distance_km': None,
            'availability_score': 0,
            'preference_score': 0,
            'value_score': 0
        } for court in courts]
    
    @staticmethod
    def _apply_filters(query, filters):
        """Apply search filters to court query"""
        if filters.get('location'):
            query = query.filter(Court.location.ilike(f"%{filters['location']}%"))
        
        if filters.get('court_type'):
            query = query.filter(Court.court_type == filters['court_type'])
        
        if filters.get('surface'):
            query = query.filter(Court.surface == filters['surface'])
        
        if filters.get('max_price'):
            try:
                max_price = float(filters['max_price'])
                query = query.filter(Court.hourly_rate <= max_price)
            except (ValueError, TypeError):
                pass
        
        return query
    
    @staticmethod
    def _calculate_court_score(player, court, player_coords, filters=None):
        """
        Calculate comprehensive recommendation score for a court
        Similar to MatchingEngine's compatibility scoring but for courts
        """
        scores = {
            'preference_score': 0,
            'distance_score': 0,
            'availability_score': 0,
            'value_score': 0,
            'amenity_score': 0,
            'distance_km': None
        }
        
        # 1. Player Preference Match (30 points max)
        scores['preference_score'] = CourtRecommendationEngine._calculate_preference_score(player, court)
        
        # 2. Distance Score (25 points max)
        if player_coords and court.latitude and court.longitude:
            court_coords = (court.latitude, court.longitude)
            distance_km = GeoService.calculate_distance_km(player_coords, court_coords)
            scores['distance_km'] = distance_km
            scores['distance_score'] = CourtRecommendationEngine._calculate_distance_score(
                distance_km, player.max_travel_distance or 25
            )
        else:
            # If no coordinates, use location string matching
            if player.preferred_location and court.location:
                if player.preferred_location.lower() in court.location.lower():
                    scores['distance_score'] = 20
                else:
                    scores['distance_score'] = 10
        
        # 3. Availability Score (20 points max)
        scores['availability_score'] = CourtRecommendationEngine._calculate_availability_score(
            court, filters
        )
        
        # 4. Value Score (15 points max)
        scores['value_score'] = CourtRecommendationEngine._calculate_value_score(court)
        
        # 5. Amenity Score (10 points max)
        scores['amenity_score'] = CourtRecommendationEngine._calculate_amenity_score(court, player)
        
        # Calculate total score
        total_score = (
            scores['preference_score'] +
            scores['distance_score'] +
            scores['availability_score'] +
            scores['value_score'] +
            scores['amenity_score']
        )
        
        scores['total_score'] = min(100, max(0, total_score))
        
        return scores
    
    @staticmethod
    def _calculate_preference_score(player, court):
        """Calculate score based on player's court preferences"""
        score = 0
        
        # Preferred court surface (20 points)
        if player.preferred_court_type:
            if player.preferred_court_type.lower() == court.surface.lower():
                score += 20
            elif player.preferred_court_type.lower() in court.surface.lower():
                score += 10
        else:
            score += 10  # Default bonus if no preference
        
        # Indoor vs outdoor preference based on player's playing style (10 points)
        if player.playing_style:
            if player.playing_style == 'aggressive' and court.court_type == 'outdoor':
                score += 5
            elif player.playing_style == 'defensive' and court.court_type == 'indoor':
                score += 5
            else:
                score += 3  # Neutral bonus
        
        return score
    
    @staticmethod
    def _calculate_distance_score(distance_km, max_travel_distance):
        """Calculate score based on distance from player"""
        if distance_km is None:
            return 10  # Default score if no coordinates
        
        if distance_km <= 5:
            return 25  # Very close
        elif distance_km <= 10:
            return 20  # Close
        elif distance_km <= max_travel_distance:
            # Linear decrease within max distance
            ratio = 1 - ((distance_km - 10) / (max_travel_distance - 10))
            return int(15 * ratio)
        else:
            return 5  # Too far but still reachable
    
    @staticmethod
    def _calculate_availability_score(court, filters):
        """Calculate score based on court availability"""
        score = 10  # Base availability score
        
        # If date filter is provided, check actual availability
        if filters and filters.get('date'):
            try:
                booking_date = datetime.strptime(filters['date'], '%Y-%m-%d').date()
                available_slots = court.get_available_slots(booking_date)
                
                if len(available_slots) >= 8:
                    score += 10  # Very available
                elif len(available_slots) >= 4:
                    score += 5   # Moderately available
                elif len(available_slots) >= 1:
                    score += 2   # Limited availability
                # No additional score if no availability
                
            except (ValueError, AttributeError):
                pass
        
        return score
    
    @staticmethod
    def _calculate_value_score(court):
        """Calculate value score based on price comparison"""
        # Get average price for comparison
        try:
            avg_price = db.session.query(func.avg(Court.hourly_rate)).filter(
                Court.is_active == True
            ).scalar() or 100
            
            price_ratio = court.hourly_rate / avg_price
            
            if price_ratio <= 0.8:
                return 15  # Great value
            elif price_ratio <= 1.0:
                return 10  # Good value
            elif price_ratio <= 1.2:
                return 5   # Fair value
            else:
                return 0   # Expensive
                
        except Exception:
            return 8  # Default if calculation fails
    
    @staticmethod
    def _calculate_amenity_score(court, player):
        """Calculate bonus score for desirable amenities"""
        score = 0
        
        # Essential amenities
        if court.has_parking:
            score += 2
        if court.has_changing_rooms:
            score += 2
        if court.has_lighting:
            score += 2
        if court.has_equipment_rental:
            score += 2
        
        # Bonus for beginners
        if player.skill_level == 'beginner':
            if court.has_equipment_rental:
                score += 2  # Extra bonus for equipment rental
        
        return min(10, score)
    
    @staticmethod
    def _sort_courts(scored_courts, sort_by):
        """Sort courts based on specified criteria"""
        if sort_by == 'recommended':
            return sorted(scored_courts, key=lambda x: x['total_score'], reverse=True)
        elif sort_by == 'price_low':
            return sorted(scored_courts, key=lambda x: x['court'].hourly_rate)
        elif sort_by == 'price_high':
            return sorted(scored_courts, key=lambda x: x['court'].hourly_rate, reverse=True)
        elif sort_by == 'distance':
            # Sort by distance, putting None values at the end
            return sorted(scored_courts, 
                         key=lambda x: x['distance_km'] if x['distance_km'] is not None else float('inf'))
        elif sort_by == 'name':
            return sorted(scored_courts, key=lambda x: x['court'].name)
        elif sort_by == 'location':
            return sorted(scored_courts, key=lambda x: x['court'].location)
        else:
            # Default to recommended
            return sorted(scored_courts, key=lambda x: x['total_score'], reverse=True)
    
    @staticmethod
    def get_sort_options():
        """Get available sorting options for frontend"""
        return [
            {'value': 'recommended', 'label': 'Recommended for You', 'icon': 'fas fa-star'},
            {'value': 'price_low', 'label': 'Price: Low to High', 'icon': 'fas fa-sort-amount-up'},
            {'value': 'price_high', 'label': 'Price: High to Low', 'icon': 'fas fa-sort-amount-down'},
            {'value': 'distance', 'label': 'Distance: Near to Far', 'icon': 'fas fa-map-marker-alt'},
            {'value': 'name', 'label': 'Name: A to Z', 'icon': 'fas fa-sort-alpha-up'},
            {'value': 'location', 'label': 'Location', 'icon': 'fas fa-map'}
        ]
    
    @staticmethod
    def get_recommendation_explanation(score_data):
        """Generate human-readable explanation of recommendation score"""
        explanations = []
        
        if score_data['preference_score'] >= 15:
            explanations.append("Matches your court preferences")
        
        if score_data['distance_km'] and score_data['distance_km'] <= 10:
            explanations.append(f"Only {score_data['distance_km']:.1f}km away")
        
        if score_data['availability_score'] >= 15:
            explanations.append("Great availability")
        
        if score_data['value_score'] >= 10:
            explanations.append("Good value for money")
        
        if score_data['amenity_score'] >= 8:
            explanations.append("Excellent amenities")
        
        if not explanations:
            explanations.append("Available court option")
        
        return explanations