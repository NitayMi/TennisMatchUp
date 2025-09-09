# services/email_service.py
"""
Email Service for TennisMatchUp
Handles all email communications using SendGrid
Pure email service - no other responsibilities
"""
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmailService:
    """Email service using SendGrid API"""
    
    # SendGrid configuration
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
    SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
    FROM_EMAIL = os.getenv('EMAIL_ADDRESS', 'noreply@tennismatchup.com')
    FROM_NAME = "TennisMatchUp"
    
    @staticmethod
    def send_email(to_email, subject, body, html_body=None):
        """Send email via SendGrid API"""
        try:
            print(f"📧 Sending email to: {to_email}")
            print(f"📧 Subject: {subject}")
            
            if not EmailService.SENDGRID_API_KEY or not EmailService.SENDGRID_API_KEY.startswith('SG.'):
                print("❌ SendGrid API key not configured or invalid")
                return False
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {EmailService.SENDGRID_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            # Prepare email content
            content = [{'type': 'text/plain', 'value': body}]
            if html_body:
                content.append({'type': 'text/html', 'value': html_body})
            
            # Prepare email data
            data = {
                'personalizations': [{
                    'to': [{'email': to_email}],
                    'subject': subject
                }],
                'from': {
                    'email': EmailService.FROM_EMAIL,
                    'name': EmailService.FROM_NAME
                },
                'content': content
            }
            
            # Send to SendGrid
            response = requests.post(
                EmailService.SENDGRID_API_URL,
                headers=headers,
                json=data,
                timeout=30
            )
            
            print(f"📡 SendGrid Response: {response.status_code}")
            
            if response.status_code == 202:
                print("✅ Email sent successfully!")
                return True
            else:
                print(f"❌ SendGrid Error: {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"💥 Email sending failed: {str(e)}")
            return False
    
    @staticmethod
    def send_booking_confirmation(booking):
        """Send beautiful booking confirmation email"""
        try:
            # Calculate duration and cost
            start_datetime = datetime.combine(booking.booking_date, booking.start_time)
            end_datetime = datetime.combine(booking.booking_date, booking.end_time)
            duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
            total_cost = booking.court.hourly_rate * duration_hours
            
            subject = f"🎾 Booking Confirmed - {booking.court.name}"
            
            # Text body
            body = f"""
Dear {booking.player.user.full_name},

🎉 Your tennis court booking has been CONFIRMED!

📋 BOOKING DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏟️  Court: {booking.court.name}
📍 Location: {booking.court.location}
📅 Date: {booking.booking_date.strftime('%A, %B %d, %Y')}
🕐 Time: {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}
⏱️  Duration: {duration_hours:.1f} hours
💰 Total Cost: ${total_cost:.2f}

👤 Court Owner: {booking.court.owner.full_name}
📞 Contact: {booking.court.owner.phone_number or booking.court.owner.email}

📝 Notes: {booking.notes or 'No special notes'}

🎾 IMPORTANT REMINDERS:
• Please arrive 10 minutes early
• Bring your own tennis equipment
• Check weather conditions before arrival
• Contact the court owner for any changes

Thank you for using TennisMatchUp! 🎾

Best regards,
The TennisMatchUp Team
            """
            
            # HTML body
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Booking Confirmation</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
                <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #2c5530, #4a7c59); color: white; padding: 30px 20px; text-align: center;">
                        <h1 style="margin: 0; font-size: 28px; font-weight: bold;">🎾 TennisMatchUp</h1>
                        <p style="margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;">Booking Confirmed!</p>
                    </div>
                    
                    <!-- Main Content -->
                    <div style="padding: 30px 25px;">
                        <p style="font-size: 18px; margin-bottom: 25px;">
                            Dear <strong>{booking.player.user.full_name}</strong>,
                        </p>
                        
                        <div style="background: #f8f9fa; border-left: 5px solid #2c5530; padding: 25px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                            <h3 style="color: #2c5530; margin: 0 0 20px 0; font-size: 20px;">🎉 Your booking is confirmed!</h3>
                            
                            <table style="width: 100%; border-collapse: collapse; font-size: 16px;">
                                <tr style="border-bottom: 1px solid #dee2e6;">
                                    <td style="padding: 12px 0; font-weight: bold; color: #495057;">🏟️ Court:</td>
                                    <td style="padding: 12px 0; color: #2c5530; font-weight: bold;">{booking.court.name}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #dee2e6;">
                                    <td style="padding: 12px 0; font-weight: bold; color: #495057;">📍 Location:</td>
                                    <td style="padding: 12px 0;">{booking.court.location}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #dee2e6;">
                                    <td style="padding: 12px 0; font-weight: bold; color: #495057;">📅 Date:</td>
                                    <td style="padding: 12px 0; color: #2c5530; font-weight: bold;">{booking.booking_date.strftime('%A, %B %d, %Y')}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #dee2e6;">
                                    <td style="padding: 12px 0; font-weight: bold; color: #495057;">🕐 Time:</td>
                                    <td style="padding: 12px 0; color: #2c5530; font-weight: bold;">{booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #dee2e6;">
                                    <td style="padding: 12px 0; font-weight: bold; color: #495057;">⏱️ Duration:</td>
                                    <td style="padding: 12px 0;">{duration_hours:.1f} hours</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; font-weight: bold; color: #495057;">💰 Total Cost:</td>
                                    <td style="padding: 12px 0; color: #2c5530; font-weight: bold; font-size: 18px;">${total_cost:.2f}</td>
                                </tr>
                            </table>
                            
                            <div style="margin-top: 25px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                                <p style="margin: 5px 0;"><strong>👤 Court Owner:</strong> {booking.court.owner.full_name}</p>
                                <p style="margin: 5px 0;"><strong>📞 Contact:</strong> {booking.court.owner.phone_number or booking.court.owner.email}</p>
                            </div>
                        </div>
                        
                        <!-- Important Reminders -->
                        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 25px 0;">
                            <h4 style="color: #856404; margin: 0 0 15px 0; font-size: 18px;">🎾 Important Reminders:</h4>
                            <ul style="margin: 0; color: #856404; padding-left: 20px;">
                                <li style="margin: 8px 0;">Please arrive 10 minutes early</li>
                                <li style="margin: 8px 0;">Bring your own tennis equipment</li>
                                <li style="margin: 8px 0;">Check weather conditions before arrival</li>
                                <li style="margin: 8px 0;">Contact the court owner for any changes</li>
                            </ul>
                        </div>
                        
                        <!-- CTA Button -->
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="mailto:{booking.court.owner.email}" 
                               style="background: #2c5530; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; font-size: 16px;">
                                Contact Court Owner
                            </a>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background: #f8f9fa; padding: 25px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #dee2e6;">
                        <p style="margin: 0 0 10px 0;"><strong>Thank you for using TennisMatchUp! 🎾</strong></p>
                        <p style="margin: 0;">Have a great game!</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Send the email
            return EmailService.send_email(
                to_email=booking.player.user.email,
                subject=subject,
                body=body,
                html_body=html_body
            )
            
        except Exception as e:
            print(f"❌ Error sending booking confirmation: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new users"""
        subject = "🎾 Welcome to TennisMatchUp!"
        
        body = f"""
Dear {user.full_name},

Welcome to TennisMatchUp - your premier tennis court booking platform!

We're excited to have you join our tennis community.

{'As a Player:' if user.user_type == 'player' else 'As a Court Owner:'}
{'''- Find and book tennis courts in your area
- Connect with other tennis players  
- Manage your bookings and schedule
- Get personalized court recommendations''' if user.user_type == 'player' else '''- List your tennis courts
- Manage booking requests
- Set your own rates and availability  
- Connect with tennis players in your area'''}

Getting Started:
1. Complete your profile
2. {'Browse available courts' if user.user_type == 'player' else 'Add your first court'}
3. {'Book your first court' if user.user_type == 'player' else 'Start receiving bookings'}

Game on!
The TennisMatchUp Team
        """
        
        return EmailService.send_email(user.email, subject, body)
    
    @staticmethod
    def send_booking_request_notification(booking):
        """Notify court owner of new booking request"""
        subject = f"🎾 New Booking Request - {booking.court.name}"
        
        body = f"""
Dear {booking.court.owner.full_name},

You have a new booking request for your court!

Booking Request Details:
- Court: {booking.court.name}
- Player: {booking.player.user.full_name}
- Date: {booking.booking_date.strftime('%A, %B %d, %Y')}
- Time: {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}
- Player Contact: {booking.player.user.email}

Notes: {booking.notes or 'No notes provided'}

Please log in to approve or decline this request.

Best regards,
The TennisMatchUp Team
        """
        
        return EmailService.send_email(booking.court.owner.email, subject, body)
    
    @staticmethod
    def send_test_email(to_email):
        """Send test email for setup verification"""
        subject = "🎾 TennisMatchUp - Email Service Test"
        
        body = """
🎉 Congratulations!

Your EmailService is working perfectly.
SendGrid integration is successful.

This is a test email from your TennisMatchUp application.

Best regards,
The TennisMatchUp Team
        """
        
        html_body = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 500px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5530;">🎾 TennisMatchUp</h2>
                <div style="background: #d1eddb; padding: 20px; border-radius: 8px; border-left: 4px solid #2c5530;">
                    <h3 style="color: #2c5530; margin: 0 0 10px 0;">🎉 Congratulations!</h3>
                    <p>Your <strong>EmailService</strong> is working perfectly.</p>
                    <p>SendGrid integration is successful.</p>
                </div>
                <p style="margin-top: 20px;">This is a test email from your TennisMatchUp application.</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="color: #666; font-size: 14px;">Best regards,<br>The TennisMatchUp Team</p>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(to_email, subject, body, html_body)
    

@staticmethod
def send_booking_approval_notification(booking):
    """Notify court owner of new booking request"""
    subject = f"New Booking Request - {booking.court.name}"
    
    body = f"""
Dear {booking.court.owner.full_name},

You have received a new booking request for your court.

Booking Request Details:
- Court: {booking.court.name}
- Player: {booking.player.user.full_name}
- Date: {booking.booking_date.strftime('%A, %B %d, %Y')}
- Time: {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}
- Player Contact: {booking.player.user.email}

Please log in to your TennisMatchUp account to approve or decline this request.

Best regards,
The TennisMatchUp Team
    """
    
    return EmailService.send_email(booking.court.owner.email, subject, body)

@staticmethod  
def send_password_reset(user, reset_token):
    """Send password reset email"""
    subject = "Password Reset - TennisMatchUp"
    
    reset_url = f"http://localhost:5000/auth/reset-password?token={reset_token}"
    
    body = f"""
Dear {user.full_name},

You requested a password reset for your TennisMatchUp account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

Best regards,
The TennisMatchUp Team
    """
    
    return EmailService.send_email(user.email, subject, body)

@staticmethod
def send_welcome_email(user):
    """Send welcome email to new users"""
    subject = "Welcome to TennisMatchUp!"
    
    body = f"""
Dear {user.full_name},

Welcome to TennisMatchUp - your premier tennis court booking platform!

We're excited to have you join our tennis community.

Getting Started:
1. Complete your profile
2. {'Browse available courts' if user.user_type == 'player' else 'Add your first court'}
3. {'Book your first court' if user.user_type == 'player' else 'Start receiving booking requests'}

Game on!

The TennisMatchUp Team
    """
    
    return EmailService.send_email(user.email, subject, body)