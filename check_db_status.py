# check_db_status.py - בדיקת מצב מסד הנתונים

from app import create_app

def check_database_status():
    """Check what's actually in the database"""
    app = create_app()
    
    with app.app_context():
        from models.user import User
        from models.player import Player
        from models.court import Court
        from models.shared_booking import SharedBooking
        
        print("🗄️ TennisMatchUp - Database Status Check")
        print("=" * 50)
        
        # Check Users
        print("👥 USERS:")
        users = User.query.all()
        for user in users:
            print(f"  • {user.full_name} ({user.email}) - {user.user_type}")
        print(f"Total users: {len(users)}")
        
        print("\n🎾 PLAYERS:")
        players = Player.query.all()
        for player in players:
            coords = player.get_coordinates()
            coord_str = f"({coords[0]:.3f}, {coords[1]:.3f})" if coords else "No coordinates"
            print(f"  • {player.user.full_name} - {player.skill_level} - {player.preferred_location} {coord_str}")
        print(f"Total players: {len(players)}")
        
        print("\n🏟️ COURTS:")
        courts = Court.query.all()
        for court in courts:
            active_status = "✅" if court.is_active else "❌"
            print(f"  • {active_status} {court.name} - {court.location} - ₪{court.hourly_rate}/hr (Owner: {court.owner.full_name})")
        print(f"Total courts: {len(courts)}")
        
        print("\n📋 SHARED BOOKINGS:")
        shared_bookings = SharedBooking.query.all()
        for booking in shared_bookings:
            print(f"  • {booking.player1.user.full_name} → {booking.player2.user.full_name} - {booking.status}")
        print(f"Total shared bookings: {len(shared_bookings)}")
        
        if len(courts) == 0:
            print("\n🚨 PROBLEM: No courts found in database!")
            print("Run: python add_demo_players.py")
            return False
        elif all(not court.is_active for court in courts):
            print("\n🚨 PROBLEM: All courts are inactive!")
            return False
        else:
            print("\n✅ Database looks good!")
            return True

if __name__ == "__main__":
    check_database_status()