# update_court_coordinates.py - עדכון קואורדינטות המגרשים

from app import create_app
from models.court import Court
from models.database import db
from services.geo_service import GeoService
import time

def update_all_court_coordinates():
    """Update GPS coordinates for all courts"""
    app = create_app()
    
    with app.app_context():
        print("🏟️ TennisMatchUp - Court Coordinates Update")
        print("=" * 60)
        
        # Get courts without coordinates
        courts_without_coords = Court.query.filter(
            Court.is_active == True,
            Court.latitude.is_(None)
        ).all()
        
        print(f"📍 Found {len(courts_without_coords)} courts needing coordinate updates")
        
        if not courts_without_coords:
            print("✅ All courts already have coordinates!")
            return True
        
        success_count = 0
        for i, court in enumerate(courts_without_coords, 1):
            print(f"Processing {i}/{len(courts_without_coords)}: {court.name} ({court.location})")
            
            coordinates = GeoService.get_coordinates(court.location)
            if coordinates:
                court.latitude = coordinates[0] 
                court.longitude = coordinates[1]
                
                try:
                    db.session.commit()
                    success_count += 1
                    print(f"  ✅ Updated: {coordinates[0]:.4f}, {coordinates[1]:.4f}")
                except Exception as e:
                    db.session.rollback()
                    print(f"  ❌ DB Error: {str(e)}")
            else:
                print(f"  ❌ Could not geocode: {court.location}")
            
            # Rate limiting for API
            if i < len(courts_without_coords):
                time.sleep(1.1)
        
        print(f"\n✅ Court coordinate update complete: {success_count}/{len(courts_without_coords)} successful")
        
        # Verification
        print("\n🔍 Verification - Courts with coordinates:")
        courts_with_coords = Court.query.filter(
            Court.latitude.isnot(None),
            Court.longitude.isnot(None)
        ).all()
        
        for court in courts_with_coords:
            print(f"  ✅ {court.name} - {court.location} ({court.latitude:.3f}, {court.longitude:.3f})")
        
        return success_count == len(courts_without_coords)

if __name__ == "__main__":
    success = update_all_court_coordinates()
    if success:
        print("\n🎯 Now the geographic algorithm should work perfectly!")
        print("Test again: Suggest Joint Booking → Should show court suggestions")
    else:
        print("\n❌ Some courts failed to update. Check API limits or network.")