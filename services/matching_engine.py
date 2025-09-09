"""
Perfect Matching Engine for TennisMatchUp
Real geographic calculations with intelligent compatibility scoring
"""
from datetime import datetime, timedelta
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court, Booking
from services.rule_engine import RuleEngine
from services.geo_service import GeoService
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload
import random
import time

class MatchingEngine:
    """Intelligent matching system with real geographic precision"""
    
    @staticmethod
    def find_matches(player_id, skill_level=None, location=None, availability=None, limit=10):
        """Find compatible players with geographic precision"""
        current_player = Player.query.get(player_id)
        if not current_player:
            return []
        
        # Ensure current player has coordinates
        if not current_player.latitude or not current_player.longitude:
            current_player.update_coordinates()
            db.session.commit()
        
        # Build base query
        query = Player.query.options(joinedload(Player.user)).join(User).filter(
            Player.id != player_id,  # Exclude self
            User.is_active == True
        )
        
        # Apply filters
        if skill_level:
            skill_levels = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'professional': 4}
            target_level = skill_levels.get(skill_level, 2)
            compatible_levels = []
            
            for level_name, level_num in skill_levels.items():
                if abs(level_num - target_level) <= 1:  # Allow ±1 level difference
                    compatible_levels.append(level_name)
            
            query = query.filter(Player.skill_level.in_(compatible_levels))
        
        if location:
            query = query.filter(Player.preferred_location.ilike(f'%{location}%'))
        
        if availability:
            # More flexible availability matching
            if availability == 'flexible':
                # Flexible matches with everyone
                pass
            else:
                query = query.filter(
                    or_(
                        Player.availability == availability,
                        Player.availability == 'flexible'
                    )
                )
        
        # Get potential matches
        potential_matches = query.limit(100).all()  # Get more for better scoring
        
        # Score and rank matches
        scored_matches = []
        current_coords = current_player.get_coordinates()
        
        for match_player in potential_matches:
            # Validate basic compatibility
            validation_result = RuleEngine.validate_player_matching(current_player.id, match_player.id)
            if not validation_result['valid']:
                continue
            
            # Ensure match player has coordinates
            if not match_player.latitude or not match_player.longitude:
                match_player.update_coordinates()
                db.session.commit()
            
            # Calculate real distance
            match_coords = match_player.get_coordinates()
            real_distance = None
            if current_coords and match_coords:
                real_distance = GeoService.calculate_distance_km(current_coords, match_coords)
            
            # Skip if too far (more than 50km)
            if real_distance and real_distance > 50:
                continue
            
            # Calculate comprehensive compatibility score
            compatibility_score = MatchingEngine._calculate_perfect_compatibility(
                current_player, match_player, real_distance
            )
            
            # Skip low compatibility scores
            if compatibility_score < 25:
                continue
            
            scored_matches.append({
                'player': match_player,
                'user': match_player.user,
                'compatibility_score': compatibility_score,
                'distance_km': real_distance,
                'common_interests': MatchingEngine._find_smart_common_interests(current_player, match_player),
                'recent_activity': MatchingEngine._get_activity_summary(match_player.id),
                'match_quality': MatchingEngine._determine_match_quality(compatibility_score),
                'geographic_zone': MatchingEngine._get_geographic_zone(real_distance)
            })
        
        # Sort by compatibility score
        scored_matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        return scored_matches[:limit]
    
    @staticmethod
    def _calculate_perfect_compatibility(player1, player2, real_distance=None):
        """Calculate realistic compatibility score (25-85 range)"""
        
        # Start with base score
        total_points = 0
        max_possible_points = 100
        
        # 1. Skill Level Compatibility (35 points max)
        skill_points = MatchingEngine._calculate_skill_compatibility(
            player1.skill_level, player2.skill_level
        )
        total_points += skill_points
        
        # 2. Geographic Compatibility (25 points max)
        if real_distance is not None:
            geo_points = MatchingEngine._calculate_geographic_compatibility(real_distance)
        else:
            # Fallback to text-based location matching
            geo_points = MatchingEngine._calculate_location_text_compatibility(
                player1.preferred_location, player2.preferred_location
            )
        total_points += geo_points
        
        # 3. Availability Compatibility (20 points max)
        availability_points = MatchingEngine._calculate_availability_compatibility(
            player1.availability, player2.availability
        )
        total_points += availability_points
        
        # 4. Activity Level Compatibility (10 points max)
        activity_points = MatchingEngine._calculate_activity_compatibility(player1, player2)
        total_points += activity_points
        
        # 5. Bio/Personality Compatibility (10 points max)
        personality_points = MatchingEngine._calculate_personality_compatibility(
            player1.bio, player2.bio
        )
        total_points += personality_points
        
        # Calculate final percentage
        percentage = (total_points / max_possible_points) * 100
        
        # Apply realistic constraints
        if percentage > 85:
            percentage = 85  # Cap at 85% - no one is perfect
        elif percentage < 25:
            percentage = 25  # Minimum viable match
        
        return round(percentage)
    
    @staticmethod
    def _calculate_skill_compatibility(skill1, skill2):
        """Calculate skill level compatibility (0-35 points)"""
        skill_map = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'professional': 4}
        
        level1 = skill_map.get(skill1, 2)
        level2 = skill_map.get(skill2, 2)
        skill_diff = abs(level1 - level2)
        
        if skill_diff == 0:
            return 35  # Perfect skill match
        elif skill_diff == 1:
            return 28  # Close skill match
        elif skill_diff == 2:
            return 15  # Manageable difference
        else:
            return 5   # Too big difference
    
    @staticmethod
    def _calculate_geographic_compatibility(distance_km):
        """Calculate geographic compatibility based on real distance (0-25 points)"""
        if distance_km <= 2:
            return 25       # Same neighborhood
        elif distance_km <= 5:
            return 23       # Same city center
        elif distance_km <= 10:
            return 20       # Across city
        elif distance_km <= 15:
            return 16       # Neighboring areas
        elif distance_km <= 25:
            return 12       # Same metropolitan area
        elif distance_km <= 35:
            return 8        # Different cities but doable
        elif distance_km <= 50:
            return 4        # Far but possible
        else:
            return 0        # Too far
    
    @staticmethod
    def _calculate_location_text_compatibility(loc1, loc2):
        """Fallback text-based location matching (0-25 points)"""
        if not loc1 or not loc2:
            return 12  # Neutral
        
        loc1_clean = loc1.lower().strip()
        loc2_clean = loc2.lower().strip()
        
        # Exact match
        if loc1_clean == loc2_clean:
            return 25
        
        # Metropolitan area matching
        tel_aviv_metro = ['tel aviv', 'tel-aviv', 'ramat gan', 'herzliya', 'givatayim', 'holon']
        jerusalem_metro = ['jerusalem', 'yerushalayim', 'beit shemesh']
        haifa_metro = ['haifa', 'netanya', 'hadera']
        
        def get_metro_area(location):
            for metro_list, name in [(tel_aviv_metro, 'tel_aviv'), 
                                   (jerusalem_metro, 'jerusalem'), 
                                   (haifa_metro, 'haifa')]:
                if any(city in location for city in metro_list):
                    return name
            return location
        
        metro1 = get_metro_area(loc1_clean)
        metro2 = get_metro_area(loc2_clean)
        
        if metro1 == metro2:
            return 20  # Same metropolitan area
        else:
            return 8   # Different areas
    
    @staticmethod
    def _calculate_availability_compatibility(avail1, avail2):
        """Calculate availability compatibility (0-20 points)"""
        if not avail1 or not avail2:
            return 10  # Neutral
        
        avail1_clean = avail1.lower()
        avail2_clean = avail2.lower()
        
        # Exact match
        if avail1_clean == avail2_clean:
            return 20
        
        # Flexible is compatible with everything
        if 'flexible' in [avail1_clean, avail2_clean]:
            return 18
        
        # Compatibility matrix
        compatibility_scores = {
            ('weekdays', 'evenings'): 15,
            ('weekends', 'evenings'): 12,
            ('weekdays', 'weekends'): 8
        }
        
        # Check both directions
        score = compatibility_scores.get((avail1_clean, avail2_clean)) or \
                compatibility_scores.get((avail2_clean, avail1_clean)) or 6
        
        return score
    
    @staticmethod
    def _calculate_activity_compatibility(player1, player2):
        """Calculate activity level compatibility (0-10 points)"""
        try:
            # Get recent activity for both players
            recent_cutoff = datetime.now() - timedelta(days=30)
            
            p1_bookings = Booking.query.filter(
                Booking.player_id == player1.id,
                Booking.created_at >= recent_cutoff
            ).count()
            
            p2_bookings = Booking.query.filter(
                Booking.player_id == player2.id,
                Booking.created_at >= recent_cutoff
            ).count()
            
            # Both active
            if p1_bookings >= 3 and p2_bookings >= 3:
                return 10
            # One very active, one moderately active
            elif (p1_bookings >= 3 and p2_bookings >= 1) or (p2_bookings >= 3 and p1_bookings >= 1):
                return 8
            # Both moderately active
            elif p1_bookings >= 1 and p2_bookings >= 1:
                return 7
            # One active, one new
            elif p1_bookings >= 1 or p2_bookings >= 1:
                return 5
            else:
                # Both new players
                return 6
        except:
            return 6  # Default if query fails
    
    @staticmethod
    def _calculate_personality_compatibility(bio1, bio2):
        """Calculate personality compatibility from bio text (0-10 points)"""
        if not bio1 or not bio2:
            return 6  # Neutral
        
        bio1_lower = bio1.lower()
        bio2_lower = bio2.lower()
        
        # Personality indicators
        competitive_words = ['competitive', 'tournament', 'serious', 'advanced', 'professional']
        social_words = ['fun', 'social', 'friendly', 'casual', 'enjoy', 'love']
        learning_words = ['learning', 'improving', 'practice', 'beginner', 'new']
        
        def get_personality_profile(bio):
            competitive_count = sum(1 for word in competitive_words if word in bio)
            social_count = sum(1 for word in social_words if word in bio)
            learning_count = sum(1 for word in learning_words if word in bio)
            
            return {
                'competitive': competitive_count,
                'social': social_count,
                'learning': learning_count
            }
        
        profile1 = get_personality_profile(bio1_lower)
        profile2 = get_personality_profile(bio2_lower)
        
        # Calculate compatibility
        total_compatibility = 0
        
        # Similar competitive level
        comp_diff = abs(profile1['competitive'] - profile2['competitive'])
        if comp_diff <= 1:
            total_compatibility += 4
        
        # Both social or both serious
        if profile1['social'] > 0 and profile2['social'] > 0:
            total_compatibility += 3
        elif profile1['competitive'] > 0 and profile2['competitive'] > 0:
            total_compatibility += 3
        
        # Learning compatibility
        if profile1['learning'] > 0 and profile2['learning'] > 0:
            total_compatibility += 3
        
        return min(10, total_compatibility)
    
    @staticmethod
    def _find_smart_common_interests(player1, player2):
        """Find detailed common interests with proper UX formatting"""
        interests = []
        
        # Skill level compatibility
        if player1.skill_level == player2.skill_level:
            interests.append(f"Both {player1.skill_level} players")
        elif abs(MatchingEngine._skill_level_to_num(player1.skill_level) - 
                MatchingEngine._skill_level_to_num(player2.skill_level)) == 1:
            interests.append("Compatible skill levels")
        
        # Geographic proximity
        coords1 = player1.get_coordinates()
        coords2 = player2.get_coordinates()
        if coords1 and coords2:
            distance = GeoService.calculate_distance_km(coords1, coords2)
            if distance <= 5:
                interests.append("Very close location")
            elif distance <= 15:
                interests.append("Same area")
        
        # Availability - FIX THE CORE PROBLEM
        if (player1.availability and player2.availability and 
            player1.availability.lower() not in ['none', 'null', ''] and
            player2.availability.lower() not in ['none', 'null', '']):
            
            if player1.availability == player2.availability:
                interests.append(f"Both prefer {player1.availability} sessions")
            elif 'flexible' in [player1.availability.lower(), player2.availability.lower()]:
                interests.append("Flexible scheduling available")
        
        # Bio analysis with better filtering
        if player1.bio and player2.bio:
            bio1_words = set(player1.bio.lower().split())
            bio2_words = set(player2.bio.lower().split())
            
            tennis_keywords = {'competitive', 'social', 'fun', 'doubles', 'singles', 'tournament', 'practice'}
            common_tennis_words = bio1_words.intersection(bio2_words).intersection(tennis_keywords)
            
            for word in list(common_tennis_words)[:2]:
                interests.append(f"Both enjoy {word} tennis")
        
        # Return clean, user-friendly list
        return interests[:3] if interests else ["Similar playing style"]
    
    @staticmethod
    def _skill_level_to_num(skill_level):
        """Convert skill level to number"""
        return {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'professional': 4}.get(skill_level, 2)
    
    @staticmethod
    def _is_valid_availability(availability):
        """Validate availability value for display"""
        if not availability:
            return False
        if isinstance(availability, str):
            return availability.lower() not in ['none', 'null', '', 'undefined']
        return True
    
    @staticmethod
    def _get_activity_summary(player_id):
        """Get comprehensive activity summary"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        recent_bookings = Booking.query.filter(
            Booking.player_id == player_id,
            Booking.created_at >= thirty_days_ago
        ).count()
        
        # Determine activity level
        if recent_bookings >= 8:
            activity_level = 'Very High'
        elif recent_bookings >= 4:
            activity_level = 'High'
        elif recent_bookings >= 2:
            activity_level = 'Medium'
        elif recent_bookings >= 1:
            activity_level = 'Low'
        else:
            activity_level = 'New Player'
        
        return {
            'recent_bookings': recent_bookings,
            'activity_level': activity_level,
            'days_since_last_booking': MatchingEngine._get_days_since_last_booking(player_id)
        }
    
    @staticmethod
    def _get_days_since_last_booking(player_id):
        """Get days since last booking"""
        try:
            last_booking = Booking.query.filter_by(player_id=player_id).order_by(
                Booking.created_at.desc()
            ).first()
            
            if last_booking:
                days_diff = (datetime.now() - last_booking.created_at).days
                return days_diff
            else:
                return 999  # Never booked
        except:
            return 999
    
    @staticmethod
    def _determine_match_quality(compatibility_score):
        """Determine match quality description"""
        if compatibility_score >= 75:
            return "Excellent Match"
        elif compatibility_score >= 65:
            return "Very Good Match"
        elif compatibility_score >= 50:
            return "Good Match"
        elif compatibility_score >= 35:
            return "Fair Match"
        else:
            return "Poor Match"
    
    @staticmethod
    def _get_geographic_zone(distance_km):
        """Get geographic zone description"""
        if distance_km is None:
            return "Unknown Distance"
        elif distance_km <= 5:
            return "Very Close"
        elif distance_km <= 15:
            return "Nearby"
        elif distance_km <= 30:
            return "Same Region"
        else:
            return "Different Region"
    
    @staticmethod
    def recommend_courts_for_pair(player1_id, player2_id, max_courts=5):
        """Recommend optimal courts for two matched players"""
        player1 = Player.query.get(player1_id)
        player2 = Player.query.get(player2_id)
        
        if not player1 or not player2:
            return []
        
        coords1 = player1.get_coordinates()
        coords2 = player2.get_coordinates()
        
        if not coords1 or not coords2:
            # Fallback to text-based location
            return MatchingEngine._recommend_courts_by_location_text(player1, player2, max_courts)
        
        # Use geographic service to find optimal meeting points
        court_suggestions = GeoService.suggest_meeting_points(coords1, coords2, max_courts * 2)
        
        # Add business logic scoring
        enhanced_suggestions = []
        for suggestion in court_suggestions:
            court = suggestion['court']
            
            # Apply business rules
            business_score = RuleEngine.calculate_court_recommendation_score(court, player1)
            business_score += RuleEngine.calculate_court_recommendation_score(court, player2)
            business_score = business_score / 2  # Average
            
            # Combine geographic and business scores
            total_score = (suggestion['total_score'] * 0.6) + (business_score * 0.4)
            
            enhanced_suggestions.append({
                'court': court,
                'geographic_data': suggestion,
                'business_score': business_score,
                'total_score': total_score,
                'recommendation_reason': MatchingEngine._generate_court_recommendation_reason(suggestion)
            })
        
        # Sort by total score
        enhanced_suggestions.sort(key=lambda x: x['total_score'], reverse=True)
        
        return enhanced_suggestions[:max_courts]
    
    @staticmethod
    def _recommend_courts_by_location_text(player1, player2, max_courts=5):
        """Fallback court recommendation without coordinates"""
        # Simple text-based court recommendation
        location_priority = [player1.preferred_location, player2.preferred_location]
        
        courts = Court.query.filter(Court.is_active == True).all()
        court_scores = []
        
        for court in courts:
            score = 50  # Base score
            
            # Location matching
            for player_location in location_priority:
                if player_location.lower() in court.location.lower():
                    score += 25
                    break
            
            # Business factors
            business_score = RuleEngine.calculate_court_recommendation_score(court, player1)
            score += business_score * 0.3
            
            court_scores.append({
                'court': court,
                'score': score,
                'recommendation_reason': f"Good option in {court.location}"
            })
        
        court_scores.sort(key=lambda x: x['score'], reverse=True)
        return court_scores[:max_courts]
    
    @staticmethod
    def _generate_court_recommendation_reason(suggestion):
        """Generate human-readable recommendation reason"""
        reasons = []
        
        avg_dist = suggestion.get('average_distance', 0)
        fairness = suggestion.get('fairness_score', 0)
        
        if avg_dist <= 10:
            reasons.append("close to both players")
        elif avg_dist <= 20:
            reasons.append("reasonable distance")
        
        if fairness >= 80:
            reasons.append("equally convenient")
        elif fairness >= 60:
            reasons.append("fairly balanced location")
        
        return ", ".join(reasons) if reasons else "available option"
    
    @staticmethod
    def batch_update_all_player_coordinates():
        """Update coordinates for all players - run once after API setup"""
        print("🔄 Starting batch coordinate update...")
        
        players_without_coords = Player.query.filter(
            Player.preferred_location.isnot(None),
            Player.latitude.is_(None)
        ).all()
        
        if not players_without_coords:
            print("✅ All players already have coordinates!")
            return True
        
        print(f"📍 Found {len(players_without_coords)} players needing coordinate updates")
        
        success_count = 0
        for i, player in enumerate(players_without_coords, 1):
            print(f"Processing {i}/{len(players_without_coords)}: {player.user.full_name} ({player.preferred_location})")
            
            coordinates = GeoService.get_coordinates(player.preferred_location)
            if coordinates:
                player.latitude = coordinates[0]
                player.longitude = coordinates[1]
                player.location_updated_at = datetime.now()
                
                try:
                    db.session.commit()
                    success_count += 1
                    print(f"  ✅ Updated: {coordinates[0]:.4f}, {coordinates[1]:.4f}")
                except Exception as e:
                    db.session.rollback()
                    print(f"  ❌ DB Error: {str(e)}")
            else:
                print(f"  ❌ Could not geocode: {player.preferred_location}")
            
            # Rate limiting - 1 request per second for free tier
            if i < len(players_without_coords):
                time.sleep(1.1)
        
        print(f"✅ Coordinate update complete: {success_count}/{len(players_without_coords)} successful")
        return success_count == len(players_without_coords)
    
    @staticmethod
    def get_recent_matches(player_id, limit=5):
        """Get recent match recommendations for a player"""
        return MatchingEngine.find_matches(player_id, limit=limit)
    
    @staticmethod
    def get_match_insights(player_id):
        """Generate insights about player's matching potential"""
        player = Player.query.get(player_id)
        if not player:
            return {}
        
        # Get all possible matches
        all_matches = MatchingEngine.find_matches(player_id, limit=50)
        
        if not all_matches:
            return {
                'total_potential_matches': 0,
                'avg_compatibility': 0,
                'insights': ["No potential matches found - try updating your profile"],
                'recommendations': ["Expand your search criteria", "Update your location", "Add more details to your bio"]
            }
        
        # Calculate statistics
        compatibility_scores = [match['compatibility_score'] for match in all_matches]
        avg_compatibility = sum(compatibility_scores) / len(compatibility_scores)
        
        high_quality_matches = len([score for score in compatibility_scores if score >= 65])
        
        insights = []
        recommendations = []
        
        # Analyze compatibility distribution
        if avg_compatibility >= 60:
            insights.append(f"You have excellent compatibility with other players (avg: {avg_compatibility:.0f}%)")
        elif avg_compatibility >= 45:
            insights.append(f"You have good compatibility potential (avg: {avg_compatibility:.0f}%)")
        else:
            insights.append(f"Your compatibility could be improved (avg: {avg_compatibility:.0f}%)")
            recommendations.append("Consider updating your skill level or location preferences")
        
        # High quality match analysis
        if high_quality_matches >= 5:
            insights.append(f"You have {high_quality_matches} high-quality potential matches")
        elif high_quality_matches >= 2:
            insights.append(f"You have {high_quality_matches} high-quality matches available")
        else:
            insights.append("Limited high-quality matches found")
            recommendations.append("Try being more flexible with your availability")
        
        # Geographic analysis
        if player.latitude and player.longitude:
            close_matches = len([m for m in all_matches if m['distance'] and m['distance'] <= 10])
            if close_matches >= 3:
                insights.append(f"{close_matches} players are within 10km of you")
            else:
                recommendations.append("Consider expanding your location radius")
        
        return {
            'total_potential_matches': len(all_matches),
            'avg_compatibility': round(avg_compatibility, 1),
            'high_quality_matches': high_quality_matches,
            'insights': insights,
            'recommendations': recommendations[:3]  # Max 3 recommendations
        }
    
    # Legacy methods to maintain compatibility with existing code
    @staticmethod
    def _calculate_distance(location1, location2):
        """Legacy distance calculation - now uses real coordinates when available"""
        # Try to get players by location name and calculate real distance
        players1 = Player.query.filter(Player.preferred_location.ilike(f'%{location1}%')).first()
        players2 = Player.query.filter(Player.preferred_location.ilike(f'%{location2}%')).first()
        
        if players1 and players2:
            coords1 = players1.get_coordinates()
            coords2 = players2.get_coordinates()
            
            if coords1 and coords2:
                return GeoService.calculate_distance_km(coords1, coords2)
        
        # Fallback to old text-based estimation
        if location1.lower() == location2.lower():
            return random.uniform(0, 5)
        else:
            return random.uniform(10, 50)
    
    @staticmethod
    def _get_recent_activity(player_id):
        """Legacy method - maintained for compatibility"""
        activity_summary = MatchingEngine._get_activity_summary(player_id)
        
        return {
            'recent_bookings': activity_summary['recent_bookings'],
            'activity_level': activity_summary['activity_level']
        }
    
    @staticmethod
    def recommend_courts(player_id, location=None, max_price=None, court_type=None, limit=10):
        """Recommend courts for a player based on preferences and location"""
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
        player_coords = player.get_coordinates()
        
        for court in potential_courts:
            # Calculate distance if coordinates available
            distance_km = None
            if player_coords and court.latitude and court.longitude:
                court_coords = (court.latitude, court.longitude)
                distance_km = GeoService.calculate_distance_km(player_coords, court_coords)
            
            # Calculate recommendation score
            recommendation_score = MatchingEngine._calculate_court_recommendation_score(
                court, player, distance_km
            )
            
            # Get additional information
            availability_score = MatchingEngine._calculate_court_availability(court.id)
            owner_rating = MatchingEngine._get_court_owner_rating(court.owner_id)
            
            scored_courts.append({
                'court': court,
                'owner': court.owner,
                'recommendation_score': recommendation_score,
                'availability_score': availability_score,
                'owner_rating': owner_rating,
                'distance': distance_km,
                'recent_bookings': MatchingEngine._get_court_recent_bookings(court.id)
            })
        
        # Sort by recommendation score
        scored_courts.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        return scored_courts[:limit]
    
    @staticmethod
    def _calculate_court_recommendation_score(court, player, distance_km=None):
        """Calculate court recommendation score for a player"""
        score = 50  # Base score
        
        # Distance factor (30 points max)
        if distance_km is not None:
            if distance_km <= 5:
                score += 30
            elif distance_km <= 10:
                score += 25
            elif distance_km <= 20:
                score += 15
            elif distance_km <= 35:
                score += 8
            else:
                score += 2
        else:
            # Text-based location matching
            if player.preferred_location.lower() in court.location.lower():
                score += 25
            else:
                score += 10
        
        # Price factor (20 points max)
        if court.hourly_rate <= 50:
            score += 20  # Very affordable
        elif court.hourly_rate <= 100:
            score += 15  # Affordable
        elif court.hourly_rate <= 150:
            score += 10  # Moderate
        elif court.hourly_rate <= 200:
            score += 5   # Expensive
        else:
            score += 1   # Very expensive
        
        return min(100, score)
    
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
        
        if match_data.get('distance') and match_data['distance'] <= 10:
            reasons.append("nearby location")
        
        if match_data.get('recent_activity', {}).get('activity_level') == 'High':
            reasons.append("active player")
        
        if match_data.get('common_interests'):
            reasons.append(f"shares {len(match_data['common_interests'])} common interests")
        
        return ", ".join(reasons[:3])  # Limit to top 3 reasons
    
    @staticmethod
    def _suggest_next_action(match_data):
        """Suggest what action the player should take"""
        activity_level = match_data.get('recent_activity', {}).get('activity_level', 'Unknown')
        
        if activity_level == 'High':
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
        
        # Generate all possible slots (business hours: 6 AM to 10 PM)
        available_slots = []
        start_hour = 6
        end_hour = 22
        
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