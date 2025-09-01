# debug_proposal_creation.py - בדיקת יצירת הצעה מפורטת

from app import create_app

def test_proposal_creation():
    """Test creating a shared booking proposal step by step"""
    app = create_app()
    
    with app.app_context():
        from models.player import Player
        from models.court import Court
        from services.shared_booking_service import SharedBookingService
        
        print("🔧 Testing Proposal Creation Step by Step")
        print("=" * 60)
        
        # Get test players
        john = Player.query.join(Player.user).filter(
            Player.user.has(full_name='John Player')
        ).first()
        maya = Player.query.join(Player.user).filter(
            Player.user.has(full_name='Maya Goldstein')  
        ).first()
        
        # Get a test court
        court = Court.query.filter_by(name='Sunshine Tennis Club').first()
        
        print(f"👥 Players:")
        print(f"   John: ID={john.id}, User ID={john.user_id}")
        print(f"   Maya: ID={maya.id}, User ID={maya.user_id}")
        print(f"🏟️ Court:")
        print(f"   {court.name}: ID={court.id}, Active={court.is_active}")
        
        # Test data for proposal
        booking_date = "2025-09-02"  # Tomorrow
        start_time = "18:00"
        end_time = "19:00"
        notes = "Test booking"
        
        print(f"📅 Booking Data:")
        print(f"   Date: {booking_date}")
        print(f"   Time: {start_time} - {end_time}")
        
        # Test validation function directly
        print("\n🔍 Testing validation...")
        validation = SharedBookingService._validate_booking_proposal(
            john.id, maya.id, court.id, booking_date, start_time, end_time
        )
        
        print(f"Validation result: {validation}")
        
        if not validation['valid']:
            print(f"❌ Validation failed: {validation['reason']}")
            return
        
        # Test court availability method
        print("\n🔍 Testing court availability...")
        try:
            from datetime import datetime, time
            booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            
            # Check if court has is_available method
            if hasattr(court, 'is_available'):
                available = court.is_available(booking_date_obj, start_time_obj, end_time_obj)
                print(f"Court availability: {available}")
            else:
                print("❌ Court.is_available method not found!")
                
        except Exception as e:
            print(f"❌ Error checking availability: {str(e)}")
        
        # Test actual proposal creation
        print("\n🔍 Testing proposal creation...")
        try:
            result = SharedBookingService.create_booking_proposal(
                player1_id=john.id,
                player2_id=maya.id,
                court_id=court.id,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time,
                notes=notes
            )
            
            print(f"Creation result: {result}")
            
        except Exception as e:
            print(f"❌ Exception in creation: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_proposal_creation()