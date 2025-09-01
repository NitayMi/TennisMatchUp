# debug_detailed_proposal.py - בדיקה מפורטת עם המרות

from app import create_app

def test_detailed_proposal_creation():
    """Test proposal creation with detailed debugging"""
    app = create_app()
    
    with app.app_context():
        from models.player import Player
        from models.court import Court
        from models.shared_booking import SharedBooking
        from models.database import db
        from datetime import datetime, date, time
        
        print("🔧 Detailed Proposal Creation Test")
        print("=" * 60)
        
        # Get players
        john = Player.query.join(Player.user).filter(
            Player.user.has(full_name='John Player')
        ).first()
        maya = Player.query.join(Player.user).filter(
            Player.user.has(full_name='Maya Goldstein')  
        ).first()
        court = Court.query.filter_by(name='Sunshine Tennis Club').first()
        
        print(f"Players: John ID={john.id}, Maya ID={maya.id}")
        print(f"Court: {court.name} ID={court.id}")
        
        # Test conversion
        booking_date_str = "2025-09-02"
        start_time_str = "18:00"
        end_time_str = "19:00"
        
        print(f"\nConverting strings to objects:")
        try:
            booking_date_obj = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
            start_time_obj = datetime.strptime(start_time_str, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()
            
            print(f"✅ Date conversion: {booking_date_str} → {booking_date_obj}")
            print(f"✅ Start time: {start_time_str} → {start_time_obj}")  
            print(f"✅ End time: {end_time_str} → {end_time_obj}")
            
        except Exception as e:
            print(f"❌ Conversion error: {e}")
            return
        
        # Test SharedBooking creation directly
        print(f"\nTesting SharedBooking creation directly:")
        try:
            shared_booking = SharedBooking(
                player1_id=john.id,
                player2_id=maya.id,
                court_id=court.id,
                booking_date=booking_date_obj,  # Using converted objects
                start_time=start_time_obj,
                end_time=end_time_obj,
                initiator_notes="Test booking"
            )
            
            print(f"✅ SharedBooking object created")
            print(f"   Status: {shared_booking.status}")
            print(f"   Cost calculation...")
            
            # Test cost calculation
            shared_booking.calculate_cost()
            print(f"   Total cost: ₪{shared_booking.total_cost}")
            print(f"   Player shares: ₪{shared_booking.player1_share} each")
            
            # Test database save
            db.session.add(shared_booking)
            db.session.commit()
            
            print(f"✅ Successfully saved to database! ID: {shared_booking.id}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating SharedBooking: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_detailed_proposal_creation()