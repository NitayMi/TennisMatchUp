#!/usr/bin/env python3
"""
Fix Court Scoring Algorithm
Issue: Eilat (272km) appears before Jerusalem (48km) due to price weighting
Solution: Rebalance distance vs price scoring
"""

from app import create_app
from models.database import db
from models.player import Player
from models.court import Court
from services.matching_engine import MatchingEngine
from services.geo_service import GeoService

def analyze_current_scoring():
    """Analyze why Eilat appears before Jerusalem"""
    
    print("🔍 Analyzing Current Court Scoring Algorithm")
    print("="*60)
    
    app = create_app()
    
    with app.app_context():
        # Get a Tel Aviv player for testing
        tel_aviv_player = Player.query.filter(
            Player.preferred_location.ilike('%tel aviv%'),
            Player.latitude.isnot(None)
        ).first()
        
        if not tel_aviv_player:
            print("❌ No Tel Aviv player found for testing")
            return
        
        print(f"🎾 Testing with player: {tel_aviv_player.user.full_name}")
        print(f"   Location: {tel_aviv_player.preferred_location}")
        print(f"   Coordinates: {tel_aviv_player.latitude:.4f}, {tel_aviv_player.longitude:.4f}")
        
        # Get the problematic courts
        courts_to_analyze = [
            ("Daviko Tennis Court Eilat", "eilat"),
            ("Practice Court Jerusalem", "jerusalem"),
            ("Desert Tennis Academy", "beer sheva")
        ]
        
        print(f"\n📊 Court Scoring Analysis:")
        print("-" * 60)
        
        player_coords = (tel_aviv_player.latitude, tel_aviv_player.longitude)
        
        court_scores = []
        
        for court_name, location_filter in courts_to_analyze:
            court = Court.query.filter(
                Court.name.ilike(f'%{court_name}%')
            ).first()
            
            if not court:
                court = Court.query.filter(
                    Court.location.ilike(f'%{location_filter}%')
                ).first()
            
            if court and court.latitude and court.longitude:
                court_coords = (court.latitude, court.longitude)
                distance_km = GeoService.calculate_distance_km(player_coords, court_coords)
                
                # Calculate scoring components (based on MatchingEngine logic)
                base_score = 50
                
                # Distance scoring (seems to be the issue)
                if distance_km <= 5:
                    distance_score = 30
                elif distance_km <= 15:
                    distance_score = 25
                elif distance_km <= 25:
                    distance_score = 15
                elif distance_km <= 50:
                    distance_score = 10
                else:
                    distance_score = 0  # Should be 0 for very far distances!
                
                # Price scoring (this might be too high)
                hourly_rate = court.hourly_rate
                if hourly_rate <= 60:
                    price_score = 20      # Too high for cheap courts?
                elif hourly_rate <= 100:
                    price_score = 15
                elif hourly_rate <= 150:
                    price_score = 10
                else:
                    price_score = 5
                
                total_score = base_score + distance_score + price_score
                
                print(f"\n🏟️  {court.name}")
                print(f"   Location: {court.location}")
                print(f"   Distance: {distance_km:.1f} km")
                print(f"   Price: ₪{hourly_rate}/hr")
                print(f"   📈 Scoring Breakdown:")
                print(f"      Base score: {base_score}")
                print(f"      Distance score: {distance_score}")
                print(f"      Price score: {price_score}")
                print(f"      Total: {total_score}")
                
                court_scores.append({
                    'court': court,
                    'distance': distance_km,
                    'price': hourly_rate,
                    'total_score': total_score
                })
        
        # Sort by score to see the problem
        court_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        print(f"\n🏆 Current Ranking by Score:")
        print("-" * 40)
        for i, score_data in enumerate(court_scores, 1):
            court = score_data['court']
            distance = score_data['distance']
            price = score_data['price']
            score = score_data['total_score']
            
            print(f"   {i}. {court.name}")
            print(f"      {distance:.1f}km, ₪{price}/hr, Score: {score}")
            
            # Identify the issue
            if 'eilat' in court.location.lower() and i == 1:
                print(f"      🚨 PROBLEM: Eilat is ranked #1 despite being {distance:.1f}km away!")
        
        return court_scores

def create_improved_scoring_function():
    """Create a more logical scoring function"""
    
    print(f"\n🔧 Improved Scoring Algorithm")
    print("="*60)
    
    print("📋 New Logic:")
    print("1. Distance should have MUCH higher weight")
    print("2. Courts >100km should get severe distance penalty")
    print("3. Price should have lower impact")
    print("4. Add distance penalty multiplier")
    
    improved_scoring_code = '''
def calculate_court_recommendation_score_IMPROVED(court, player, distance_km=None):
    """Improved court scoring - prioritizes distance over price"""
    
    base_score = 50
    
    if distance_km is None:
        return base_score  # No distance data
    
    # IMPROVED DISTANCE SCORING - Much higher weight
    if distance_km <= 5:
        distance_score = 40      # Increased from 30
    elif distance_km <= 15:
        distance_score = 30      # Increased from 25  
    elif distance_km <= 25:
        distance_score = 20      # Increased from 15
    elif distance_km <= 50:
        distance_score = 10      # Same
    elif distance_km <= 100:
        distance_score = -20     # NEW: Penalty for far courts
    else:
        distance_score = -50     # SEVERE penalty for very far courts
    
    # REDUCED PRICE SCORING - Lower impact
    hourly_rate = court.hourly_rate
    if hourly_rate <= 60:
        price_score = 10         # Reduced from 20
    elif hourly_rate <= 100:
        price_score = 8          # Reduced from 15
    elif hourly_rate <= 150:
        price_score = 5          # Reduced from 10
    else:
        price_score = 0          # Reduced from 5
    
    total_score = base_score + distance_score + price_score
    
    # Additional distance penalty multiplier for very far courts
    if distance_km > 100:
        total_score = total_score * 0.3  # Reduce score by 70%
    
    return total_score
    '''
    
    print("💻 Improved Scoring Function:")
    print(improved_scoring_code)
    
    return improved_scoring_code

def test_improved_scoring():
    """Test the improved scoring with same courts"""
    
    print(f"\n🧪 Testing Improved Scoring")
    print("="*60)
    
    app = create_app()
    
    with app.app_context():
        tel_aviv_player = Player.query.filter(
            Player.preferred_location.ilike('%tel aviv%'),
            Player.latitude.isnot(None)
        ).first()
        
        if not tel_aviv_player:
            return
        
        player_coords = (tel_aviv_player.latitude, tel_aviv_player.longitude)
        
        # Test courts
        test_courts = [
            "Daviko Tennis Court Eilat",
            "Practice Court Jerusalem", 
            "Desert Tennis Academy",
            "Center Court Tel Aviv",
            "Test Court Auto Geocoding"
        ]
        
        improved_scores = []
        
        for court_name in test_courts:
            court = Court.query.filter(
                Court.name.ilike(f'%{court_name}%')
            ).first()
            
            if court and court.latitude:
                distance = GeoService.calculate_distance_km(
                    player_coords, 
                    (court.latitude, court.longitude)
                )
                
                # Apply improved scoring
                base_score = 50
                
                # Improved distance scoring
                if distance <= 5:
                    distance_score = 40
                elif distance <= 15:
                    distance_score = 30
                elif distance <= 25:
                    distance_score = 20
                elif distance <= 50:
                    distance_score = 10
                elif distance <= 100:
                    distance_score = -20
                else:
                    distance_score = -50
                
                # Reduced price scoring
                if court.hourly_rate <= 60:
                    price_score = 10
                elif court.hourly_rate <= 100:
                    price_score = 8
                elif court.hourly_rate <= 150:
                    price_score = 5
                else:
                    price_score = 0
                
                total_score = base_score + distance_score + price_score
                
                # Distance penalty for very far courts
                if distance > 100:
                    total_score = total_score * 0.3
                
                improved_scores.append({
                    'name': court.name,
                    'distance': distance,
                    'price': court.hourly_rate,
                    'score': total_score
                })
        
        # Sort by improved score
        improved_scores.sort(key=lambda x: x['score'], reverse=True)
        
        print("🏆 NEW Ranking with Improved Scoring:")
        print("-" * 50)
        
        for i, court_data in enumerate(improved_scores, 1):
            name = court_data['name']
            distance = court_data['distance'] 
            price = court_data['price']
            score = court_data['score']
            
            print(f"   {i}. {name}")
            print(f"      {distance:.1f}km, ₪{price}/hr, Score: {score:.1f}")
            
            if 'eilat' in name.lower() and i > 3:
                print(f"      ✅ Eilat now properly ranked low due to distance!")
            elif 'jerusalem' in name.lower() and 'eilat' in [s['name'].lower() for s in improved_scores[:i]]:
                print(f"      ✅ Jerusalem now ranks higher than Eilat!")

def generate_fix_script():
    """Generate script to implement the fix"""
    
    print(f"\n📝 Implementation Script")
    print("="*60)
    
    implementation_script = '''
# Add this to services/matching_engine.py or services/court_recommendation_engine.py

@staticmethod
def calculate_court_recommendation_score(court, player, distance_km=None):
    """FIXED: Improved court scoring - prioritizes distance over price"""
    
    base_score = 50
    
    if distance_km is None:
        return base_score
    
    # DISTANCE SCORING - Higher weight, penalties for far courts
    if distance_km <= 5:
        distance_score = 40      # Very close - excellent
    elif distance_km <= 15:
        distance_score = 30      # Close - very good
    elif distance_km <= 25:
        distance_score = 20      # Moderate - good
    elif distance_km <= 50:
        distance_score = 10      # Far - acceptable
    elif distance_km <= 100:
        distance_score = -20     # Very far - penalty
    else:
        distance_score = -50     # Extremely far - severe penalty
    
    # PRICE SCORING - Lower impact
    hourly_rate = court.hourly_rate
    if hourly_rate <= 60:
        price_score = 10         # Good value
    elif hourly_rate <= 100:
        price_score = 8          # Decent value
    elif hourly_rate <= 150:
        price_score = 5          # Acceptable
    else:
        price_score = 0          # Expensive
    
    total_score = base_score + distance_score + price_score
    
    # Additional penalty for extremely distant courts
    if distance_km > 100:
        total_score = total_score * 0.3  # 70% penalty
    
    return max(0, total_score)  # Don't go negative
    '''
    
    print("🔧 Copy this code to fix your scoring algorithm:")
    print(implementation_script)

if __name__ == "__main__":
    print("🚀 Analyzing Court Scoring Issue...")
    
    # Analyze current problem
    current_scores = analyze_current_scoring()
    
    # Show improved algorithm
    create_improved_scoring_function()
    
    # Test the improvement
    test_improved_scoring()
    
    # Generate implementation
    generate_fix_script()
    
    print(f"\n🎯 SOLUTION SUMMARY:")
    print("1. Distance weight increased significantly")
    print("2. Price weight reduced") 
    print("3. Added penalties for courts >50km away")
    print("4. Severe penalties for courts >100km away")
    print("5. This should fix Eilat appearing before Jerusalem!")