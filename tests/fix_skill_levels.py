#!/usr/bin/env python3
"""
Fix skill levels to match system expectations
"""

import os
from dotenv import load_dotenv
from app import create_app
from models.database import db
from models.player import Player

load_dotenv()

def fix_skill_levels():
    print("Fixing Skill Levels")
    print("=" * 30)
    
    os.environ['FLASK_ENV'] = 'production'
    
    try:
        app = create_app()
        
        with app.app_context():
            # Map numeric skill levels to text
            skill_mapping = {
                '2.0': 'beginner',
                '2.5': 'beginner', 
                '3.0': 'intermediate',
                '3.5': 'intermediate',
                '4.0': 'advanced',
                '4.5': 'advanced',
                '5.0': 'professional'
            }
            
            # Get all players with numeric skill levels
            players = Player.query.all()
            fixed = 0
            
            for player in players:
                if player.skill_level in skill_mapping:
                    old_skill = player.skill_level
                    new_skill = skill_mapping[old_skill]
                    player.skill_level = new_skill
                    print(f"Fixed {player.user.full_name}: {old_skill} → {new_skill}")
                    fixed += 1
            
            db.session.commit()
            
            print(f"Fixed {fixed} players")
            
            # Verify no numeric skills remain
            remaining = Player.query.filter(
                Player.skill_level.in_(['2.0', '2.5', '3.0', '3.5', '4.0', '4.5', '5.0'])
            ).count()
            
            if remaining == 0:
                print("All skill levels fixed!")
                return True
            else:
                print(f"Warning: {remaining} players still have numeric skills")
                return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    fix_skill_levels()