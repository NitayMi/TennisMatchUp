# test_email_service.py
"""
Test script for EmailService
Run this to verify your SendGrid integration works
"""
import os
from dotenv import load_dotenv
from services.email_service import EmailService

# Load environment variables
load_dotenv()

def test_email_service():
    """Test EmailService functionality"""
    print("📧 Testing EmailService...")
    print("=" * 50)
    
    # Check configuration
    api_key = os.getenv('SENDGRID_API_KEY')
    email_address = os.getenv('EMAIL_ADDRESS')
    
    print("⚙️  Configuration Check:")
    print(f"✅ SENDGRID_API_KEY: {api_key[:20]}..." if api_key else "❌ SENDGRID_API_KEY: Not found")
    print(f"✅ EMAIL_ADDRESS: {email_address}" if email_address else "❌ EMAIL_ADDRESS: Not found")
    
    if not api_key or not api_key.startswith('SG.'):
        print("\n❌ SendGrid API key missing or invalid!")
        print("Make sure your .env file has:")
        print("SENDGRID_API_KEY=SG.your_api_key_here")
        return False
    
    # Test email sending
    print(f"\n🧪 Testing email sending...")
    
    # 🔴 CHANGE THIS TO YOUR EMAIL
    test_email = "nitay.boostapp@gmail.com"  # PUT YOUR EMAIL HERE!
    
    try:
        result = EmailService.send_test_email(test_email)
        
        if result:
            print("✅ Test email sent successfully!")
            print(f"📬 Check your inbox at: {test_email}")
            print("📂 Don't forget to check spam folder")
            return True
        else:
            print("❌ Failed to send test email")
            return False
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return False

def simulate_booking_email():
    """Test booking confirmation email with mock data"""
    print("\n📋 Testing booking confirmation email...")
    
    # Create mock booking object
    class MockUser:
        def __init__(self, full_name, email):
            self.full_name = full_name
            self.email = email
    
    class MockPlayer:
        def __init__(self):
            self.user = MockUser("John Doe", "john@example.com")
    
    class MockOwner:
        def __init__(self):
            self.full_name = "Court Owner"
            self.email = "owner@example.com"
            self.phone_number = "+1-555-0123"
    
    class MockCourt:
        def __init__(self):
            self.name = "Center Court"
            self.location = "123 Tennis St, Tel Aviv"
            self.hourly_rate = 50.0
            self.owner = MockOwner()
    
    class MockBooking:
        def __init__(self):
            self.player = MockPlayer()
            self.court = MockCourt()
            self.booking_date = datetime(2025, 1, 15).date()
            self.start_time = datetime(2025, 1, 15, 14, 0).time()
            self.end_time = datetime(2025, 1, 15, 16, 0).time()
            self.notes = "Looking forward to playing!"
    
    # Test booking confirmation
    from datetime import datetime
    mock_booking = MockBooking()
    
    try:
        result = EmailService.send_booking_confirmation(mock_booking)
        
        if result:
            print("✅ Booking confirmation email sent!")
            print(f"📬 Check inbox at: {mock_booking.player.user.email}")
        else:
            print("❌ Failed to send booking confirmation")
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")

if __name__ == "__main__":
    print("🎾 TennisMatchUp - EmailService Test")
    print("=" * 50)
    
    # Test basic email
    if test_email_service():
        print("\n🎉 SUCCESS! EmailService is working!")
        
        # Test booking email with mock data
        simulate_booking_email()
        
        print("\n✅ EmailService is ready for production!")
        print("\nNext steps:")
        print("1. Integrate with booking routes")
        print("2. Add to user registration")
        print("3. Test with real bookings")
        
    else:
        print("\n💥 TEST FAILED")
        print("Fix configuration and try again")
    
    print("\n" + "=" * 50)