# debug_email.py
"""
Debug email delivery - check SendGrid activity
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_sendgrid_activity():
    """Check recent email activity in SendGrid"""
    
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    
    print("🔍 Checking SendGrid Email Activity")
    print("=" * 50)
    
    # Get recent email events
    headers = {
        'Authorization': f'Bearer {SENDGRID_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Check email activity API
    url = "https://api.sendgrid.com/v3/messages"
    
    try:
        print("📡 Checking recent email activity...")
        
        response = requests.get(
            url,
            headers=headers,
            params={'limit': 10},  # Last 10 emails
            timeout=30
        )
        
        print(f"📊 Response Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'messages' in data and data['messages']:
                print(f"✅ Found {len(data['messages'])} recent emails:")
                
                for i, msg in enumerate(data['messages'][:3]):  # Show last 3
                    print(f"\n📧 Email #{i+1}:")
                    print(f"   To: {msg.get('to_email', 'N/A')}")
                    print(f"   Subject: {msg.get('subject', 'N/A')}")
                    print(f"   Status: {msg.get('status', 'N/A')}")
                    print(f"   Time: {msg.get('last_event_time', 'N/A')}")
                    
            else:
                print("📭 No recent emails found")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Error checking activity: {e}")

def send_simple_test():
    """Send a very simple test email"""
    
    YOUR_EMAIL = "nitay.michaeli@outlook.com"
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    
    print(f"\n📧 Sending simple test to {YOUR_EMAIL}...")
    
    headers = {
        'Authorization': f'Bearer {SENDGRID_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Very simple email
    data = {
        'personalizations': [{
            'to': [{'email': YOUR_EMAIL}]
        }],
        'from': {
            'email': YOUR_EMAIL,
            'name': 'TennisMatchUp'
        },
        'subject': '🏓 Simple Test Email',
        'content': [{
            'type': 'text/plain',
            'value': 'This is a simple test. If you get this, email is working!'
        }]
    }
    
    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"📡 Response: {response.status_code}")
        
        if response.status_code == 202:
            print("✅ Simple test sent!")
            print("📬 Check your email in 1-2 minutes")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Error: {e}")
        return False

def check_email_tips():
    """Provide tips for finding the email"""
    print("\n🔍 EMAIL TROUBLESHOOTING TIPS:")
    print("=" * 40)
    print("1. 📬 Check main inbox")
    print("2. 📂 Check Spam/Junk folder") 
    print("3. 🔍 Search for 'TennisMatchUp' in email")
    print("4. 🔍 Search for subject 'Email Service Test'")
    print("5. ⏰ Wait 2-3 minutes (SendGrid can be slow)")
    print("6. 📱 Check email on phone too")
    print("\n🌐 You can also check SendGrid dashboard:")
    print("   https://app.sendgrid.com/email_activity")

if __name__ == "__main__":
    print("🎾 TennisMatchUp - Email Debugging")
    print("=" * 50)
    
    # Check recent activity
    check_sendgrid_activity()
    
    # Send simple test
    print("\n" + "="*30)
    send_simple_test()
    
    # Show tips
    check_email_tips()