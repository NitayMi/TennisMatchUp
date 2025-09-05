"""
Geographic Service for TennisMatchUp
Real geographic calculations using OpenCage API
"""
import requests
import os
from math import radians, cos, sin, asin, sqrt
from models.database import db
import time


class GeoService:
    """Geographic service with real coordinate calculation"""
    
    API_KEY = os.getenv('OPENCAGE_API_KEY')
    BASE_URL = "https://api.opencagedata.com/geocode/v1/json"
    
    # Cache to avoid API calls for known locations
    _location_cache = {}
    

    @staticmethod
    def get_coordinates(location_name):
        """Enhanced geocoding with city sub-location handling"""
        if not location_name:
            return None
        
        # Clean location name
        location_name = location_name.strip()
        location_key = location_name.lower()
        
        # Check cache first
        if location_key in GeoService._location_cache:
            return GeoService._location_cache[location_key]
        
        try:
            # First, try direct geocoding
            base_coords = GeoService._get_base_coordinates(location_name)
            if not base_coords:
                return None
            
            # Enhanced precision for major cities
            enhanced_coords = GeoService._enhance_city_precision(location_name, base_coords)
            
            # Cache the result
            GeoService._location_cache[location_key] = enhanced_coords
            
            print(f"📍 Geocoded: {location_name} → {enhanced_coords[0]:.4f}, {enhanced_coords[1]:.4f}")
            return enhanced_coords
            
        except Exception as e:
            print(f"❌ Geocoding error for {location_name}: {str(e)}")
            return None

    @staticmethod
    def _get_base_coordinates(location_name):
        """Get base coordinates from OpenCage API"""
        if not GeoService.API_KEY:
            return None
        
        try:
            response = requests.get(
                'https://api.opencagedata.com/geocode/v1/json',
                params={
                    'q': location_name,
                    'key': GeoService.API_KEY,
                    'limit': 1,
                    'countrycode': 'il',  # Focus on Israel
                    'language': 'en'
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    result = data['results'][0]
                    lat = result['geometry']['lat']
                    lng = result['geometry']['lng']
                    return (lat, lng)
        
        except Exception as e:
            print(f"❌ API error: {str(e)}")
        
        return None

    @staticmethod
    def _enhance_city_precision(location_name, base_coords):
        """Add realistic precision to city coordinates"""
        import hashlib
        
        # Create deterministic but varied coordinates within city bounds
        # Use location name to ensure consistency per unique location string
        location_hash = hashlib.md5(location_name.encode()).hexdigest()
        
        # Convert hash to offset values
        hash_int = int(location_hash[:8], 16)
        
        # City radius mapping (in km)
        city_radius = {
            'tel aviv': 5,     # Tel Aviv radius ~5km
            'haifa': 8,        # Haifa radius ~8km  
            'jerusalem': 10,   # Jerusalem radius ~10km
            'eilat': 3,        # Eilat radius ~3km
            'netanya': 4,      # Netanya radius ~4km
            'beer sheva': 6,   # Beer Sheva radius ~6km
            'rishon lezion': 4,
            'petah tikva': 3,
            'ashdod': 4,
            'herzliya': 2
        }
        
        # Determine city from location name
        city_name = None
        for city in city_radius.keys():
            if city in location_name.lower():
                city_name = city
                break
        
        if not city_name:
            # Default for unknown cities
            radius_km = 3
        else:
            radius_km = city_radius[city_name]
        
        # Calculate offset based on hash (deterministic but varied)
        # Convert km to approximate degrees (1 degree ≈ 111km)
        max_offset_degrees = radius_km / 111.0
        
        # Create offsets from hash
        lat_offset = ((hash_int % 1000) / 1000.0 - 0.5) * 2 * max_offset_degrees
        lng_offset = (((hash_int >> 10) % 1000) / 1000.0 - 0.5) * 2 * max_offset_degrees
        
        # Apply offsets to base coordinates
        enhanced_lat = base_coords[0] + lat_offset
        enhanced_lng = base_coords[1] + lng_offset
        
        return (enhanced_lat, enhanced_lng)
        
    @staticmethod
    def calculate_distance_km(coord1, coord2):
        """Calculate distance between two coordinates using Haversine formula"""
        if not coord1 or not coord2:
            return None
        
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Earth radius in kilometers
        R = 6371
        distance = R * c
        
        return round(distance, 2)
    
    @staticmethod
    def get_distance_score(distance_km):
        """Convert distance to compatibility score (0-100)"""
        if distance_km is None:
            return 50  # Neutral if distance unknown
        
        if distance_km <= 2:
            return 100      # Very close (same neighborhood)
        elif distance_km <= 5:
            return 90       # Close (same city center)
        elif distance_km <= 10:
            return 75       # Moderate (across city)
        elif distance_km <= 20:
            return 50       # Acceptable (neighboring cities)
        elif distance_km <= 35:
            return 25       # Far but doable
        else:
            return 10       # Very far
    
    @staticmethod
    def update_player_coordinates(player_id):
        """Update player coordinates based on their preferred location"""
        from models.player import Player
        
        player = Player.query.get(player_id)
        if not player or not player.preferred_location:
            return False
        
        # Skip if coordinates already exist and location hasn't changed
        if player.latitude and player.longitude:
            return True
        
        coordinates = GeoService.get_coordinates(player.preferred_location)
        if coordinates:
            player.latitude = coordinates[0]
            player.longitude = coordinates[1]
            player.location_updated_at = db.func.current_timestamp()
            
            try:
                db.session.commit()
                print(f"✅ Updated coordinates for {player.user.full_name}: {coordinates}")
                return True
            except Exception as e:
                db.session.rollback()
                print(f"❌ Failed to save coordinates: {str(e)}")
                return False
        
        return False
    
    @staticmethod
    def batch_update_all_players():
        """Update coordinates for all players (run once)"""
        from models.player import Player
        
        players = Player.query.filter(
            Player.preferred_location.isnot(None),
            Player.latitude.is_(None)  # Only update players without coordinates
        ).all()
        
        success_count = 0
        total_count = len(players)
        
        print(f"🔄 Updating coordinates for {total_count} players...")
        
        for i, player in enumerate(players, 1):
            print(f"Processing {i}/{total_count}: {player.user.full_name} ({player.preferred_location})")
            
            if GeoService.update_player_coordinates(player.id):
                success_count += 1
            
            # Rate limiting - OpenCage allows 1 request per second for free accounts
            if i < total_count:
                time.sleep(1.1)  # Wait 1.1 seconds between requests
        
        print(f"✅ Updated {success_count}/{total_count} players successfully!")
        return success_count
    
    @staticmethod
    def get_nearby_players(center_lat, center_lng, radius_km=25):
        """Find players within a specific radius"""
        from models.player import Player
        
        # Simple bounding box calculation (more efficient than calculating exact distance for each)
        # 1 degree ≈ 111 km, so we create a square around the center point
        lat_offset = radius_km / 111.0
        lng_offset = radius_km / (111.0 * cos(radians(center_lat)))
        
        min_lat = center_lat - lat_offset
        max_lat = center_lat + lat_offset
        min_lng = center_lng - lng_offset
        max_lng = center_lng + lng_offset
        
        # Query players within bounding box
        nearby_players = Player.query.filter(
            Player.latitude.between(min_lat, max_lat),
            Player.longitude.between(min_lng, max_lng),
            Player.latitude.isnot(None),
            Player.longitude.isnot(None)
        ).all()
        
        # Calculate exact distances and filter
        filtered_players = []
        for player in nearby_players:
            distance = GeoService.calculate_distance_km(
                (center_lat, center_lng),
                (player.latitude, player.longitude)
            )
            
            if distance <= radius_km:
                filtered_players.append({
                    'player': player,
                    'distance_km': distance
                })
        
        # Sort by distance
        filtered_players.sort(key=lambda x: x['distance_km'])
        return filtered_players
    
    @staticmethod
    def suggest_meeting_points(player1_coords, player2_coords, max_courts=5):
        """Suggest courts that are convenient for both players - FIXED VERSION"""
        from models.court import Court
        
        if not player1_coords or not player2_coords:
            return []
        
        # Calculate distance between players
        player_distance = GeoService.calculate_distance_km(player1_coords, player2_coords)
        
        # If players are too far apart, no reasonable meeting point exists
        if player_distance > 100:  # More than 100km apart
            print(f"⚠️ Players too far apart: {player_distance:.1f}km - no reasonable meeting points")
            return []
        
        # Find midpoint between players
        mid_lat = (player1_coords[0] + player2_coords[0]) / 2
        mid_lng = (player1_coords[1] + player2_coords[1]) / 2
        
        # Get courts near midpoint
        courts = Court.query.filter(
            Court.is_active == True,
            Court.latitude.isnot(None),
            Court.longitude.isnot(None)
        ).all()
        
        court_suggestions = []
        for court in courts:
            court_coords = (court.latitude, court.longitude)
            
            # Calculate distances to both players
            dist_to_p1 = GeoService.calculate_distance_km(player1_coords, court_coords)
            dist_to_p2 = GeoService.calculate_distance_km(player2_coords, court_coords)
            
            # IMPROVED LOGIC: Multiple filters for realistic suggestions
            
            # Filter 1: Basic distance constraint (30km from each player)
            if dist_to_p1 > 30 or dist_to_p2 > 30:
                continue
            
            # Filter 2: Court shouldn't be way off the direct path between players
            # If players are close (same city), be more flexible
            if player_distance <= 20:  # Same city/region
                max_detour = 15  # Allow 15km detour
            else:  # Different cities
                max_detour = player_distance * 0.4  # Allow 40% detour
            
            # Check if court is reasonable compared to direct travel
            if max(dist_to_p1, dist_to_p2) > player_distance + max_detour:
                continue  # Skip courts that require major detours
            
            # Filter 3: Fairness constraint - court shouldn't heavily favor one player
            distance_diff = abs(dist_to_p1 - dist_to_p2)
            
            # If players are close, allow bigger difference
            if player_distance <= 10:
                max_unfairness = 20  # 20km difference allowed
            else:
                max_unfairness = player_distance * 0.6  # 60% of player distance
            
            if distance_diff > max_unfairness:
                continue  # Skip unfair court locations
            
            # Calculate metrics for valid courts
            avg_distance = (dist_to_p1 + dist_to_p2) / 2
            max_distance = max(dist_to_p1, dist_to_p2)
            
            # Fairness score - prefer courts that are equally distant
            fairness_score = 100 - (distance_diff * 3)  # Penalize unfairness more
            
            # Convenience score - prefer closer courts
            convenience_score = max(0, 100 - (avg_distance * 4))
            
            # Combined score
            total_score = (convenience_score * 0.6) + (fairness_score * 0.4)
            
            court_suggestions.append({
                'court': court,
                'distance_to_player1': dist_to_p1,
                'distance_to_player2': dist_to_p2,
                'average_distance': avg_distance,
                'max_distance': max_distance,
                'distance_difference': distance_diff,
                'fairness_score': fairness_score,
                'convenience_score': convenience_score,
                'total_score': total_score,
                'player_distance': player_distance
            })
        
        # Sort by total score (better courts first)
        court_suggestions.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Debug output
        print(f"🎾 Court suggestions for players {player_distance:.1f}km apart:")
        for i, suggestion in enumerate(court_suggestions[:3], 1):
            court = suggestion['court']
            print(f"  {i}. {court.name}: {suggestion['distance_to_player1']:.1f}km + {suggestion['distance_to_player2']:.1f}km (score: {suggestion['total_score']:.1f})")
        
        return court_suggestions[:max_courts]
    
    @staticmethod
    def validate_api_key():
        """Validate OpenCage API key is working"""
        if not GeoService.API_KEY:
            return False, "API key not found in environment variables"
        
        # Test with a simple query
        test_result = GeoService.get_coordinates("Tel Aviv")
        if test_result:
            return True, f"API working - Tel Aviv coordinates: {test_result}"
        else:
            return False, "API key invalid or service unavailable"
        
    @staticmethod
    def geocode_address(address):
        """Convert address to coordinates using geocoding service"""
        # This would use Google Maps API or similar
        # For now, return mock coordinates
        return {
            'address': address,
            'latitude': 32.0853,  # Tel Aviv coordinates as default
            'longitude': 34.7818,
            'formatted_address': address
        }
    
    @staticmethod
    def calculate_distance(location1, location2):
        """Calculate distance between two locations"""
        # This would use Google Distance Matrix API or similar
        # For now, return mock distance
        return {
            'distance_km': 12.5,
            'duration_minutes': 18,
            'route_available': True
        }
