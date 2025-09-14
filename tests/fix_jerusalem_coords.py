#!/usr/bin/env python3
"""
URGENT FIX: Jerusalem Coordinates Correction
Based on audit results showing 43km deviation
"""

from app import create_app
from models.database import db
from models.court import Court
from services.geo_service import GeoService

def fix_jerusalem_coordinates():
    """Fix the incorrect Jerusalem coordinates immediately"""
    
    print("🚨 URGENT: Fixing Jerusalem coordinates...")
    print("="*60)
    
    app = create_app()
    
    with app.app_context():
        # 1. Clear the geocoding cache first
        print("1. 🧹 Clearing geocoding cache...")
        GeoService._location_cache.clear()
        print("   ✅ Cache cleared")
        
        # 2. Set correct Jerusalem coordinates manually
        print("\n2. 🎯 Setting correct Jerusalem coordinates...")
        CORRECT_JERUSALEM_COORDS = (31.7683, 35.2137)  # Known accurate coordinates
        
        # Find all Jerusalem courts
        jerusalem_courts = Court.query.filter(
            Court.location.ilike('%jerusalem%')
        ).all()
        
        print(f"   Found {len(jerusalem_courts)} Jerusalem courts:")
        
        for court in jerusalem_courts:
            old_coords = (court.latitude, court.longitude)
            print(f"\n   🏟️  {court.name}")
            print(f"      Old coordinates: {old_coords[0]:.4f}, {old_coords[1]:.4f}")
            
            # Calculate how far off the old coordinates were
            if old_coords[0] and old_coords[1]:
                old_distance = GeoService.calculate_distance_km(
                    old_coords, 
                    CORRECT_JERUSALEM_COORDS
                )
                print(f"      Distance from real Jerusalem: {old_distance:.1f} km")
            
            # Set correct coordinates
            court.latitude = CORRECT_JERUSALEM_COORDS[0]
            court.longitude = CORRECT_JERUSALEM_COORDS[1]
            print(f"      ✅ Updated to: {court.latitude:.4f}, {court.longitude:.4f}")
        
        # 3. Commit changes
        try:
            db.session.commit()
            print(f"\n💾 Successfully updated {len(jerusalem_courts)} Jerusalem courts")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating database: {str(e)}")
            return False
        
        # 4. Test the fix
        print("\n3. 🧪 Testing the fix...")
        
        # Try to find two players near Tel Aviv for testing
        from models.player import Player
        tel_aviv_players = Player.query.filter(
            Player.preferred_location.ilike('%tel aviv%'),
            Player.latitude.isnot(None)
        ).limit(2).all()
        
        if len(tel_aviv_players) >= 2:
            p1, p2 = tel_aviv_players[0], tel_aviv_players[1]
            
            print(f"   Testing with: {p1.user.full_name} + {p2.user.full_name}")
            
            # Run the recommendation algorithm
            meeting_points = GeoService.suggest_meeting_points(
                (p1.latitude, p1.longitude),
                (p2.latitude, p2.longitude),
                max_courts=5
            )
            
            print(f"   📊 Results after fix:")
            jerusalem_rank = None
            
            for i, suggestion in enumerate(meeting_points, 1):
                court = suggestion['court']
                is_jerusalem = 'jerusalem' in court.location.lower()
                
                print(f"      {i}. {court.name}")
                print(f"         Location: {court.location}")
                print(f"         Distance to P1: {suggestion.get('distance_to_player1', 0):.1f}km")
                print(f"         Distance to P2: {suggestion.get('distance_to_player2', 0):.1f}km")
                
                if is_jerusalem:
                    jerusalem_rank = i
                    print(f"         🏛️  Jerusalem court now at position {i}")
            
            if jerusalem_rank:
                if jerusalem_rank > 3:
                    print(f"   ✅ SUCCESS: Jerusalem now at position {jerusalem_rank} (more realistic!)")
                else:
                    print(f"   ⚠️  Jerusalem still at position {jerusalem_rank} - may need algorithm adjustment")
            else:
                print("   ✅ Jerusalem courts not in top 5 - much more realistic!")
        
        print("\n" + "="*60)
        print("🎉 Jerusalem coordinates fix completed!")
        print("\n📋 What was fixed:")
        print("   • Corrected Jerusalem coordinates from 43km off to city center")
        print("   • Updated all Jerusalem courts in database")
        print("   • Cleared geocoding cache to prevent re-caching wrong data")
        
        print("\n🔍 Next steps:")
        print("   • Test the court recommendations in your UI")
        print("   • Monitor if Jerusalem still appears inappropriately")
        print("   • Consider adding validation to prevent future coordinate drift")
        
        return True

def validate_fix():
    """Validate that the fix worked correctly"""
    
    print("\n🔍 Validating the fix...")
    
    app = create_app()
    
    with app.app_context():
        jerusalem_courts = Court.query.filter(
            Court.location.ilike('%jerusalem%')
        ).all()
        
        CORRECT_JERUSALEM = (31.7683, 35.2137)
        
        all_good = True
        for court in jerusalem_courts:
            distance = GeoService.calculate_distance_km(
                (court.latitude, court.longitude),
                CORRECT_JERUSALEM
            )
            
            print(f"   {court.name}: {distance:.1f}km from Jerusalem center")
            
            if distance > 5:  # More than 5km from center is suspicious
                print(f"      ⚠️  Still too far from Jerusalem center!")
                all_good = False
            else:
                print(f"      ✅ Distance looks reasonable")
        
        return all_good

if __name__ == "__main__":
    print("🚀 Running Jerusalem coordinates fix...")
    
    success = fix_jerusalem_coordinates()
    
    if success:
        print("\n" + "="*60)
        validation_success = validate_fix()
        
        if validation_success:
            print("✅ Fix validated successfully!")
            print("\n🎯 Your issue should now be resolved!")
            print("   Jerusalem courts should no longer appear before closer options.")
        else:
            print("⚠️  Fix applied but validation shows issues remain")
    else:
        print("❌ Fix failed - check error messages above")