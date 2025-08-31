#!/usr/bin/env python3
"""
One-time script to update all player coordinates
Run this after installing the geo service
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.geo_service import GeoService
from services.matching_engine import MatchingEngine

def main():
    """Update coordinates for all players"""
    print("🌍 TennisMatchUp - Geographic Coordinate Update")
    print("=" * 60)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # First, validate API key
            print("🔑 Validating OpenCage API key...")
            is_valid, message = GeoService.validate_api_key()
            
            if not is_valid:
                print(f"❌ API validation failed: {message}")
                print("Please check your .env file and API key")
                return 1
            
            print(f"✅ API validation successful: {message}")
            print("-" * 40)
            
            # Update all player coordinates
            print("📍 Starting coordinate update process...")
            success = MatchingEngine.batch_update_all_player_coordinates()
            
            if success:
                print("\n🎯 Geographic system is now active!")
                print("Benefits:")
                print("• Real distance calculations")
                print("• Accurate proximity matching")
                print("• Better court recommendations")
                print("• Realistic compatibility scores")
                
                print("\n🚀 Next steps:")
                print("1. Restart your Flask server")
                print("2. Test the Find Matches page")
                print("3. Check if compatibility scores are more realistic")
                
            else:
                print("\n⚠️  Some coordinate updates failed")
                print("The system will still work but with reduced accuracy")
            
        except Exception as e:
            print(f"❌ Error during coordinate update: {str(e)}")
            print("You may need to run this script again")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())