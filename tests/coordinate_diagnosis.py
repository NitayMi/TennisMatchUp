#!/usr/bin/env python3
"""
Simple Coordinate Diagnosis - Compatible with existing setup
"""

import os
from dotenv import load_dotenv
from app import create_app
from models.database import db
from models.player import Player
from models.court import Court
from services.geo_service import GeoService

load_dotenv()

def simple_diagnosis():
    """Simple diagnosis using ORM only"""
    print("🏥 TennisMatchUp - Simple Coordinate Diagnosis")
    print("=" * 60)
    
    os.environ['FLASK_ENV'] = 'production'
    
    try:
        app = create_app()
        
        with app.app_context():
            
            # 1. Basic Data Count
            print("📊 Database Overview:")
            total_players = Player.query.count()
            total_courts = Court.query.filter(Court.is_active == True).count()
            
            print(f"  Total Players: {total_players}")
            print(f"  Active Courts: {total_courts}")
            
            # 2. Coordinate Analysis
            print("\n🌍 Coordinate Analysis:")
            
            # Check players with coordinates
            players_with_coords = Player.query.filter(
                Player.latitude.isnot(None),
                Player.longitude.isnot(None)
            ).count()
            
            players_without_coords = total_players - players_with_coords
            
            print(f"  Players WITH coordinates: {players_with_coords}")
            print(f"  Players WITHOUT coordinates: {players_without_coords}")
            
            if total_players > 0:
                coord_percentage = (players_with_coords / total_players) * 100
                print(f"  Player coordinate coverage: {coord_percentage:.1f}%")
            
            # Check courts with coordinates
            courts_with_coords = Court.query.filter(
                Court.is_active == True,
                Court.latitude.isnot(None),
                Court.longitude.isnot(None)
            ).count()
            
            courts_without_coords = total_courts - courts_with_coords
            
            print(f"  Courts WITH coordinates: {courts_with_coords}")
            print(f"  Courts WITHOUT coordinates: {courts_without_coords}")
            
            if total_courts > 0:
                court_coord_percentage = (courts_with_coords / total_courts) * 100
                print(f"  Court coordinate coverage: {court_coord_percentage:.1f}%")
            
            # 3. Sample Data
            print("\n🔍 Sample Data:")
            
            # Show some players without coordinates
            missing_coord_players = Player.query.filter(
                Player.latitude.is_(None)
            ).limit(3).all()
            
            if missing_coord_players:
                print("  Players missing coordinates:")
                for player in missing_coord_players:
                    print(f"    • {player.user.full_name} - '{player.preferred_location}'")
            
            # Show some courts without coordinates
            missing_coord_courts = Court.query.filter(
                Court.is_active == True,
                Court.latitude.is_(None)
            ).limit(3).all()
            
            if missing_coord_courts:
                print("  Courts missing coordinates:")
                for court in missing_coord_courts:
                    print(f"    • {court.name} - '{court.location}'")
            
            # 4. API Test
            print("\n🌐 GeoService API Test:")
            try:
                test_coords = GeoService.get_coordinates("Tel Aviv, Israel")
                if test_coords:
                    print(f"  ✅ API working: Tel Aviv → {test_coords}")
                else:
                    print("  ❌ API not responding or invalid key")
                    return "API_ISSUE"
            except Exception as e:
                print(f"  ❌ API error: {str(e)}")
                return "API_ISSUE"
            
            # 5. Algorithm Test
            print("\n🧠 Algorithm Test:")
            
            # Get two players for testing
            test_players = Player.query.limit(2).all()
            if len(test_players) >= 2:
                p1, p2 = test_players[0], test_players[1]
                
                print(f"  Testing: {p1.user.full_name} + {p2.user.full_name}")
                
                coords1 = p1.get_coordinates()
                coords2 = p2.get_coordinates()
                
                print(f"  {p1.user.full_name} coordinates: {coords1}")
                print(f"  {p2.user.full_name} coordinates: {coords2}")
                
                if not coords1 or not coords2:
                    print("  ❌ Missing coordinates - this causes court suggestion failure")
                else:
                    print("  ✅ Both have coordinates - should work")
            
            # 6. Diagnosis
            print("\n💊 Diagnosis:")
            
            if players_with_coords == 0:
                print("  🚨 CRITICAL: No players have coordinates")
                print("  📋 Action: Run player coordinate update")
                return "NO_PLAYER_COORDS"
            elif courts_with_coords == 0:
                print("  🚨 CRITICAL: No courts have coordinates")
                print("  📋 Action: Run court coordinate update")
                return "NO_COURT_COORDS"
            elif players_with_coords < total_players * 0.8:
                print("  ⚠️  WARNING: Most players missing coordinates")
                print("  📋 Action: Update missing player coordinates")
                return "PARTIAL_PLAYER_COORDS"
            elif courts_with_coords < total_courts * 0.8:
                print("  ⚠️  WARNING: Most courts missing coordinates")
                print("  📋 Action: Update missing court coordinates")
                return "PARTIAL_COURT_COORDS"
            else:
                print("  ✅ GOOD: Most entities have coordinates")
                print("  📋 Investigation: Check algorithm logic")
                return "COORDS_OK"
            
    except Exception as e:
        print(f"❌ Diagnosis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return "ERROR"

if __name__ == "__main__":
    result = simple_diagnosis()
    print(f"\n🎯 Result: {result}")
    
    if result in ["NO_PLAYER_COORDS", "PARTIAL_PLAYER_COORDS"]:
        print("\n🔧 Next: Update player coordinates")
        print("   Run: python update_player_coordinates.py")
    elif result in ["NO_COURT_COORDS", "PARTIAL_COURT_COORDS"]:
        print("\n🔧 Next: Update court coordinates")
        print("   Run: python update_court_coordinates.py")
    elif result == "API_ISSUE":
        print("\n🔧 Next: Fix GeoService API configuration")
        print("   Check: OPENCAGE_API_KEY in .env file")
    elif result == "COORDS_OK":
        print("\n🔧 Next: Debug algorithm logic")
        print("   Issue: Coordinates exist but algorithm fails")