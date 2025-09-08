#!/usr/bin/env python3
"""
Quick debug test for matching algorithm
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models.database import db, init_db
from models.player import Player
from models.user import User
from services.matching_engine import MatchingEngine

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tennis.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def test_matching():
    print("🎾 Testing Find Matches Algorithm")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        # Get first player
        test_player = Player.query.first()
        if not test_player:
            print("❌ No players found")
            return
            
        print(f"Testing for: {test_player.user.full_name}")
        print(f"Skill: {test_player.skill_level}")
        print(f"Location: {test_player.preferred_location}")
        
        # Test the algorithm
        try:
            matches = MatchingEngine.find_matches(
                player_id=test_player.id,
                limit=5
            )
            
            print(f"\n🔍 Found {len(matches)} matches:")
            
            for i, match in enumerate(matches, 1):
                player = match.get('player')
                if player:
                    print(f"{i}. {player.user.full_name}")
                    print(f"   Skill: {player.skill_level}")
                    print(f"   Score: {match.get('compatibility_score', 'N/A')}%")
                    print(f"   Distance: {match.get('distance_km', 'N/A')} km")
                else:
                    print(f"{i}. Invalid match data: {match}")
                
        except Exception as e:
            print(f"❌ Error in matching: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_matching()