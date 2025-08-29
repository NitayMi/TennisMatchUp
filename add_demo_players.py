#!/usr/bin/env python3
"""
Script to add demo players to TennisMatchUp
Run this script to populate the database with diverse demo players
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.demo_data import DemoDataService

def main():
    """Main function to add demo data"""
    print("🎾 TennisMatchUp - Adding Demo Players")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            print("Adding comprehensive demo data...")
            
            # Add demo data
            results = DemoDataService.populate_all_demo_data()
            
            print("\n✅ Demo data added successfully!")
            print("-" * 30)
            
            if 'players' in results:
                print(f"👥 Players created: {results['players']}")
            
            if 'courts' in results:
                print(f"🏟️  Courts created: {results['courts']}")
                
            if 'messages' in results:
                print(f"💬 Messages created: {results['messages']}")
            
            if 'error' in results:
                print(f"❌ Error occurred: {results['error']}")
            
            print("\n🚀 Demo data is ready!")
            print("You can now:")
            print("• Login as any demo player (password123)")
            print("• Test the matching system")
            print("• Explore court bookings")
            print("• Try the messaging system")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())