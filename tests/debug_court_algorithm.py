# debug_court_algorithm.py - בדיקת אלגוריתם המלצת מגרשים

from app import create_app

def debug_court_suggestions():
    """Debug why court suggestions don't work"""
    app = create_app()
    
    with app.app_context():
        from models.player import Player
        from models.court import Court
        from services.matching_engine import MatchingEngine
        
        print("🔧 Debugging Court Suggestion Algorithm")
        print("=" * 60)
        
        # Get two players from Tel Aviv (John Player and Maya Goldstein)
        john = Player.query.join(Player.user).filter(
            Player.user.has(full_name='John Player')
        ).first()
        maya = Player.query.join(Player.user).filter(
            Player.user.has(full_name='Maya Goldstein')  
        ).first()
        
        if not john or not maya:
            print("❌ Test players not found")
            return
        
        print(f"🎾 Testing court suggestions for:")
        print(f"   Player 1: {john.user.full_name} - {john.preferred_location}")
        print(f"   Player 2: {maya.user.full_name} - {maya.preferred_location}")
        
        # Check their coordinates
        john_coords = john.get_coordinates()
        maya_coords = maya.get_coordinates()
        
        print(f"📍 Coordinates:")
        print(f"   John: {john_coords}")
        print(f"   Maya: {maya_coords}")
        
        if not john_coords or not maya_coords:
            print("❌ One of the players missing coordinates")
            return
        
        # Test court suggestions
        print(f"\n🏟️ Testing MatchingEngine.recommend_courts_for_pair({john.id}, {maya.id})")
        
        try:
            court_suggestions = MatchingEngine.recommend_courts_for_pair(
                john.id, maya.id, 5
            )
            
            print(f"📊 Results: {len(court_suggestions)} suggestions returned")
            
            if court_suggestions:
                for i, suggestion in enumerate(court_suggestions, 1):
                    court = suggestion.get('court')
                    score = suggestion.get('total_score', 'No score')
                    reason = suggestion.get('recommendation_reason', 'No reason')
                    
                    print(f"   {i}. {court.name} - {court.location}")
                    print(f"      Score: {score}, Reason: {reason}")
            else:
                print("❌ No suggestions returned")
                
                # Debug deeper - check what courts are available
                all_courts = Court.query.filter_by(is_active=True).all()
                print(f"\n🔍 All active courts in system: {len(all_courts)}")
                for court in all_courts:
                    print(f"   • {court.name} - {court.location} - ₪{court.hourly_rate}")
                
                # Test if the problem is in GeoService or MatchingEngine
                print(f"\n🔍 Testing fallback method...")
                fallback_suggestions = MatchingEngine._recommend_courts_by_location_text(
                    john, maya, 5
                )
                print(f"Fallback suggestions: {len(fallback_suggestions)}")
                
        except Exception as e:
            print(f"❌ Error in algorithm: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_court_suggestions()