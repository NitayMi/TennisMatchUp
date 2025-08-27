"""
Matching Engine for TennisMatchUp
Handles player-to-player matching and court recommendations
"""
from datetime import datetime, timedelta
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court, Booking
from services.rule_engine import RuleEngine
from sqlalchemy import func, and_, or_
import random

class MatchingEngine:
    """Intelligent matching system for players and courts"""
    
    @staticmethod
    def find_matches(player_id, skill_level=None, location=None, availability=None, limit=10):
        """Find compatible players for matching"""
        current_player = Player.query.get(player_id)
        if not current_player:
            return []
        
        # Build base query
        query = Player.query.join(User).filter(
            Player.id != player_id,  # Exclude self
            User.is_active == True
        )
        
        # Apply filters
        if skill_level:
            # Find players with compatible skill levels
            skill_levels = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'professional': 4}
            target_level = skill_levels.get(skill_level, 2)
            compatible_levels = []
            
            for level_name, level_num in skill_levels.items():
                if abs(level_num - target_level) <= RuleEngine.MAX_SKILL_LEVEL_DIFFERENCE:
                    compatible_levels.append(level_name)
            
            query = query.filter(Player.skill_level.in_(compatible_levels))
        
        if location:
            # Simple location matching - in production would use geospatial queries
            query = query.filter(Player.preferred_location.ilike(f'%{location}%'))
        
        if availability:
            query = query.filter(Player.availability == availability)
        
        # Get potential matches
        potential_matches = query.limit(50).all()  # Get more than needed for scoring
        
        # Score and rank matches
        scored_matches = []
        for match_player in potential_matches:
            validation_result = RuleEngine.validate_player_matching(player_id, match_player.id)
            if validation_result['valid']:
                # Calculate detailed compatibility score
                compatibility_score = MatchingEngine._calculate_player_compatibility(
                    current_player, match_player
                )
                
                scored_matches.append({
                    'player': match_player,
                    'user': match_player.user,
                    'compatibility_score': compatibility_score,
                    'common_interests': MatchingEngine._find_common_interests(current_player, match_player),
                    'distance': MatchingEngine._calculate_distance(current_player.preferred_location, match_player.preferred_location),
                    'recent_activity': MatchingEngine._get_recent_activity(match_player.id)
                })
        
        # Sort by compatibility score
        scored_matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        return scored_matches[:limit]
    
    @staticmethod
    def _calculate_player_compatibility(player1, player2):
        """Calculate detailed compatibility score between two players"""
        score = 100
        
        # Skill level compatibility (40% weight)
        skill_levels = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'professional': 4}
        skill_diff = abs(skill_levels[player1.skill_level] - skill_levels[player2.skill_level])
        skill_score = max(0, 100 - (skill_diff * 30))
        score = score * 0.6 + skill_score * 0.4
        
        # Location compatibility (30% weight)
        location_score = 100 if player1.preferred_location.lower() == player2.preferred_location.lower() else 50
        score = score * 0.7 + location_score * 0.3
        
        # Availability compatibility (20% weight)
        availability_score = 100 if player1.availability == player2.availability else 60
        score = score * 0.8 + availability_score * 0.2
        
        # Activity level (10% weight) - players who are more active get higher scores
        player1_bookings = Booking.query.filter_by(player_id=player1.id).count()
        player2_bookings = Booking.query.filter_by(player_id=player2.id).count()
        activity_score = min(100, (player2_bookings / max(1, player1_bookings)) * 50 + 50)
        score = score * 0.9 + activity_score * 0.1
        
        return round(score, 1)
    
    @staticmethod
    def _find_common_interests(player1, player2):
        """Find common interests between players"""
        # In a real implementation, this would check shared preferences, playing styles, etc.
        common_interests = []
        
        if player1.skill_level == player2.skill_level:
            common_interests.append('Same skill level')
        
        if player1.preferred_location.lower() == player2.preferred_location.lower():
            common_interests.append('Same preferred location')
        
        if player1.availability == player2.availability:
            common_interests.append('Similar availability')
        
        return common_interests
    
    @staticmethod
    def _calculate_distance(location1, location2):
        """Calculate distance between locations (simplified)"""
        # In production, would use actual geocoding and distance calculation
        if location1.lower() == location2.lower():
            return random.uniform(0, 5)  # Same city, small distance
        else:
            return random.uniform(10, 50)  # Different locations
    
    @staticmethod
    def _get_recent_activity(player_id):
        """Get recent activity summary for a player"""
        # Get bookings from last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_bookings = Booking.query.filter(
            Booking.player_id == player_id,
            Booking.created_at >= thirty_days_ago
        ).count()
        
        return {
            'recent_bookings': recent_bookings,
            'activity_level': 'High' if recent_bookings > 4 else 'Medium' if recent_bookings > 1 else 'Low'
        }
    
    @staticmethod
    def get_recent_matches(player_id, limit=5):
        """Get recent match recommendations for a player"""
        # In a real system, this would store match history and recommendations
        # For now, return recent compatible players
        return MatchingEngine.find_matches(player_id, limit=limit)
    
    @staticmethod
    def recommend_courts(player_id, location=None, max_price=None, court_type=None, limit=10):
        """Recommend courts for a player based on preferences"""
        player = Player.query.get(player_id)
        if not player:
            return []
        
        # Build base query
        query = Court.query.filter(Court.is_active == True)
        
        # Apply filters
        if location:
            query = query.filter(Court.location.ilike(f'%{location}%'))
        elif player.preferred_location:
            # Use player's preferred location if none specified
            query = query.filter(Court.location.ilike(f'%{player.preferred_location}%'))
        
        if max_price:
            query = query.filter(Court.hourly_rate <= max_price)
        
        if court_type:
            query = query.filter(Court.court_type == court_type)
        
        # Get potential courts
        potential_courts = query.all()
        
        # Score and rank courts
        scored_courts = []
        for court in potential_courts:
            recommendation_score = RuleEngine.calculate_court_recommendation_score(court, player)
            
            # Get additional information
            availability_score = MatchingEngine._calculate_court_availability(court.id)
            owner_rating = MatchingEngine._get_court_owner_rating(court.owner_id)
            
            scored_courts.append({
                'court': court,
                'owner': court.owner,
                'recommendation_score': recommendation_score,
                'availability_score': availability_score,
                'owner_rating': owner_rating,
                'distance': MatchingEngine._calculate_distance(player.preferred_location, court.location),
                'recent_bookings': MatchingEngine._get_court_recent_bookings(court.id)
            })
        
        # Sort by recommendation score
        scored_courts.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        return scored_courts[:limit]
    
    @staticmethod
    def _calculate_court_availability(court_id, days_ahead=7):
        """Calculate court availability score"""
        # Check how many slots are available in the next week
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=days_ahead)
        
        # Get existing bookings
        existing_bookings = Booking.query.filter(
            Booking.court_id == court_id,
            Booking.booking_date.between(start_date, end_date),
            Booking.status.in_(['confirmed', 'pending'])
        ).count()
        
        # Calculate total possible slots (simplified: 14 hours per day * days)
        total_possible_slots = 14 * days_ahead
        availability_percentage = ((total_possible_slots - existing_bookings) / total_possible_slots) * 100
        
        return round(max(0, availability_percentage), 1)
    
    @staticmethod
    def _get_court_owner_rating(owner_id):
        """Get owner rating based on booking history"""
        # Calculate based on booking confirmations, cancellations, etc.
        total_bookings = Booking.query.join(Court).filter(Court.owner_id == owner_id).count()
        
        if total_bookings == 0:
            return 5.0  # New owners get benefit of the doubt
        
        confirmed_bookings = Booking.query.join(Court).filter(
            Court.owner_id == owner_id,
            Booking.status == 'confirmed'
        ).count()
        
        cancelled_by_owner = Booking.query.join(Court).filter(
            Court.owner_id == owner_id,
            Booking.status == 'cancelled',
            Booking.cancellation_reason.like('%owner%')
        ).count()
        
        # Calculate rating (simplified formula)
        confirmation_rate = confirmed_bookings / total_bookings if total_bookings > 0 else 1
        cancellation_penalty = (cancelled_by_owner / total_bookings) * 2 if total_bookings > 0 else 0
        
        rating = (confirmation_rate * 5) - cancellation_penalty
        return round(max(1.0, min(5.0, rating)), 1)
    
    @staticmethod
    def _get_court_recent_bookings(court_id, days=30):
        """Get recent booking count for a court"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return Booking.query.filter(
            Booking.court_id == court_id,
            Booking.created_at >= cutoff_date
        ).count()
    
    @staticmethod
    def suggest_playing_partners(player_id, limit=5):
        """Suggest specific playing partners based on compatibility and activity"""
        matches = MatchingEngine.find_matches(player_id, limit=limit * 2)  # Get more for filtering
        
        # Filter for most active and compatible players
        suggestions = []
        for match in matches:
            if match['compatibility_score'] >= 70:  # High compatibility threshold
                suggestions.append({
                    'player': match['player'],
                    'user': match['user'],
                    'compatibility_score': match['compatibility_score'],
                    'reason': MatchingEngine._generate_match_reason(match),
                    'suggested_action': MatchingEngine._suggest_next_action(match)
                })
        
        return suggestions[:limit]
    
    @staticmethod
    def _generate_match_reason(match_data):
        """Generate human-readable reason for the match suggestion"""
        reasons = []
        
        if match_data['compatibility_score'] >= 90:
            reasons.append("Excellent compatibility")
        elif match_data['compatibility_score'] >= 80:
            reasons.append("Very good match")
        else:
            reasons.append("Good potential match")
        
        if match_data['distance'] <= 10:
            reasons.append("nearby location")
        
        if match_data['recent_activity']['activity_level'] == 'High':
            reasons.append("active player")
        
        if match_data['common_interests']:
            reasons.append(f"shares {len(match_data['common_interests'])} common interests")
        
        return ", ".join(reasons[:3])  # Limit to top 3 reasons
    
    @staticmethod
    def _suggest_next_action(match_data):
        """Suggest what action the player should take"""
        if match_data['recent_activity']['activity_level'] == 'High':
            return "Send a message to arrange a game"
        elif match_data['compatibility_score'] >= 85:
            return "View their profile and send an introduction"
        else:
            return "Check out their playing schedule"
    
    @staticmethod
    def find_available_time_slots(court_id, date, duration_hours=1):
        """Find available time slots for a specific court and date"""
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get existing bookings for the date
        existing_bookings = Booking.query.filter(
            Booking.court_id == court_id,
            Booking.booking_date == date,
            Booking.status.in_(['confirmed', 'pending'])
        ).order_by(Booking.start_time).all()
        
        # Generate all possible slots (business hours)
        business_hours = RuleEngine.get_business_hours()
        start_hour = int(business_hours['open_time'].split(':')[0])
        end_hour = int(business_hours['close_time'].split(':')[0])
        
        available_slots = []
        current_hour = start_hour
        
        while current_hour + duration_hours <= end_hour:
            slot_start = datetime.strptime(f'{current_hour:02d}:00', '%H:%M').time()
            slot_end = datetime.strptime(f'{current_hour + duration_hours:02d}:00', '%H:%M').time()
            
            # Check if this slot conflicts with any existing booking
            conflicts = False
            for booking in existing_bookings:
                if (slot_start < booking.end_time and slot_end > booking.start_time):
                    conflicts = True
                    break
            
            if not conflicts:
                available_slots.append({
                    'start_time': slot_start.strftime('%H:%M'),
                    'end_time': slot_end.strftime('%H:%M'),
                    'duration': duration_hours
                })
            
            current_hour += 1
        
        return available_slots
    
    @staticmethod
    def get_popular_courts(location=None, limit=10):
        """Get most popular courts based on booking activity"""
        # Build query
        query = db.session.query(
            Court.id,
            Court.name,
            Court.location,
            Court.hourly_rate,
            Court.court_type,
            func.count(Booking.id).label('booking_count'),
            func.avg(Court.hourly_rate).label('avg_rate')
        ).outerjoin(Booking).filter(Court.is_active == True)
        
        if location:
            query = query.filter(Court.location.ilike(f'%{location}%'))
        
        # Group and order
        popular_courts = query.group_by(
            Court.id, Court.name, Court.location, Court.hourly_rate, Court.court_type
        ).order_by(
            func.count(Booking.id).desc()
        ).limit(limit).all()
        
        return popular_courts
    
    @staticmethod
    def get_match_statistics(player_id):
        """Get matching statistics for a player"""
        player = Player.query.get(player_id)
        if not player:
            return None
        
        # Calculate various stats
        total_possible_matches = Player.query.join(User).filter(
            Player.id != player_id,
            User.is_active == True
        ).count()
        
        compatible_matches = len(MatchingEngine.find_matches(player_id, limit=total_possible_matches))
        
        # Recent activity
        recent_bookings = Booking.query.filter(
            Booking.player_id == player_id,
            Booking.created_at >= datetime.now() - timedelta(days=30)
        ).count()
        
        return {
            'total_possible_matches': total_possible_matches,
            'compatible_matches': compatible_matches,
            'compatibility_rate': round((compatible_matches / max(1, total_possible_matches)) * 100, 1),
            'recent_activity': {
                'bookings_last_30_days': recent_bookings,
                'activity_level': 'High' if recent_bookings > 4 else 'Medium' if recent_bookings > 1 else 'Low'
            },
            'recommendations': {
                'improve_profile': compatible_matches < total_possible_matches * 0.3,
                'be_more_flexible': compatible_matches < 5,
                'expand_location': player.preferred_location and compatible_matches < 10
            }
        }
    
    @staticmethod
    def get_trending_locations():
        """Get trending locations based on recent booking activity"""
        # Get locations with most bookings in last 7 days
        week_ago = datetime.now() - timedelta(days=7)
        
        trending = db.session.query(
            Court.location,
            func.count(Booking.id).label('recent_bookings'),
            func.count(func.distinct(Court.id)).label('court_count'),
            func.avg(Court.hourly_rate).label('avg_rate')
        ).join(Booking).filter(
            Booking.created_at >= week_ago,
            Court.is_active == True
        ).group_by(Court.location).order_by(
            func.count(Booking.id).desc()
        ).limit(10).all()
        
        return [{
            'location': item.location,
            'recent_bookings': item.recent_bookings,
            'court_count': item.court_count,
            'avg_rate': round(float(item.avg_rate), 2) if item.avg_rate else 0,
            'trend_score': item.recent_bookings * 10 + item.court_count * 5
        } for item in trending]
    
    @staticmethod
    def smart_scheduling_suggestions(player_id, preferred_date=None, duration=1):
        """Suggest optimal booking times based on player history and court availability"""
        player = Player.query.get(player_id)
        if not player:
            return []
        
        # If no preferred date, suggest next 7 days
        if not preferred_date:
            dates_to_check = [(datetime.now().date() + timedelta(days=i)) for i in range(1, 8)]
        else:
            if isinstance(preferred_date, str):
                preferred_date = datetime.strptime(preferred_date, '%Y-%m-%d').date()
            dates_to_check = [preferred_date]
        
        suggestions = []
        
        for check_date in dates_to_check:
            # Get recommended courts for player
            recommended_courts = MatchingEngine.recommend_courts(
                player_id, 
                location=player.preferred_location,
                limit=5
            )
            
            for court_info in recommended_courts:
                court = court_info['court']
                
                # Find available slots
                available_slots = MatchingEngine.find_available_time_slots(
                    court.id, check_date, duration
                )
                
                for slot in available_slots:
                    # Calculate dynamic pricing
                    dynamic_rate = RuleEngine.apply_dynamic_pricing(
                        court.hourly_rate,
                        check_date,
                        slot['start_time']
                    )
                    
                    suggestions.append({
                        'court': court,
                        'date': check_date.strftime('%Y-%m-%d'),
                        'start_time': slot['start_time'],
                        'end_time': slot['end_time'],
                        'base_rate': court.hourly_rate,
                        'dynamic_rate': dynamic_rate,
                        'savings': court.hourly_rate - dynamic_rate if dynamic_rate < court.hourly_rate else 0,
                        'recommendation_score': court_info['recommendation_score'],
                        'optimal_factors': MatchingEngine._analyze_booking_factors(check_date, slot['start_time'])
                    })
        
        # Sort suggestions by overall score
        suggestions.sort(key=lambda x: (
            x['recommendation_score'] * 0.4 + 
            (100 - x['dynamic_rate']) * 0.3 +
            sum(x['optimal_factors'].values()) * 0.3
        ), reverse=True)
        
        return suggestions[:20]  # Return top 20 suggestions
    
    @staticmethod
    def _analyze_booking_factors(date, time):
        """Analyze factors that make a booking time optimal"""
        factors = {
            'off_peak': 0,
            'weekday': 0,
            'good_weather': 0,  # Would integrate with weather API
            'low_demand': 0
        }
        
        # Off-peak hours (before 5 PM or after 8 PM)
        hour = int(time.split(':')[0])
        if hour < 17 or hour >= 20:
            factors['off_peak'] = 20
        
        # Weekday vs weekend
        if date.weekday() < 5:  # Monday = 0, Sunday = 6
            factors['weekday'] = 15
        
        # Simulate weather factor (would use real weather API)
        factors['good_weather'] = random.randint(10, 30)
        
        # Simulate demand factor (would use real booking data)
        factors['low_demand'] = random.randint(0, 25)
        
        return factors
    
    @staticmethod
    def generate_match_insights(player_id):
        """Generate insights and tips for better matching"""
        player = Player.query.get(player_id)
        if not player:
            return {}
        
        stats = MatchingEngine.get_match_statistics(player_id)
        insights = []
        tips = []
        
        # Analyze compatibility rate
        if stats['compatibility_rate'] < 30:
            insights.append("Your match compatibility rate is below average")
            tips.append("Consider updating your skill level or expanding your location preferences")
        elif stats['compatibility_rate'] > 70:
            insights.append("You have excellent compatibility with other players")
            tips.append("You're in great shape for finding matches - keep being active!")
        
        # Analyze activity level
        activity_level = stats['recent_activity']['activity_level']
        if activity_level == 'Low':
            insights.append("Your recent activity is low")
            tips.append("Try booking more courts to increase your visibility to other players")
        elif activity_level == 'High':
            insights.append("You're very active - great job!")
            tips.append("Your high activity makes you more attractive to potential playing partners")
        
        # Location-based insights
        trending_locations = MatchingEngine.get_trending_locations()
        player_location = player.preferred_location.lower()
        
        is_in_trending = any(loc['location'].lower() == player_location for loc in trending_locations[:3])
        if not is_in_trending:
            insights.append("Your preferred location has moderate activity")
            tips.append(f"Consider trying courts in {trending_locations[0]['location']} - it's trending this week!")
        
        # Skill level insights
        skill_distribution = db.session.query(
            Player.skill_level,
            func.count(Player.id).label('count')
        ).group_by(Player.skill_level).all()
        
        player_skill_count = next((s.count for s in skill_distribution if s.skill_level == player.skill_level), 0)
        total_players = sum(s.count for s in skill_distribution)
        
        if player_skill_count / total_players > 0.4:
            insights.append(f"Your skill level ({player.skill_level}) is very common")
            tips.append("With many players at your level, you should find matches easily")
        elif player_skill_count / total_players < 0.1:
            insights.append(f"Your skill level ({player.skill_level}) is rare")
            tips.append("Consider being flexible with skill level matching to find more players")
        
        return {
            'insights': insights,
            'tips': tips,
            'stats': stats,
            'next_steps': [
                "Update your profile with more details",
                "Try booking during off-peak hours for better rates",
                "Send messages to highly compatible players",
                "Check out trending courts in popular locations"
            ][:3]  # Limit to top 3 next steps
        }