"""
Cloud Service for TennisMatchUp
Handles email notifications, SMS, and other cloud integrations
"""
import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

class CloudService:
    """Cloud integration services"""
    
    # Email configuration (would use environment variables)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', 'noreply@tennismatchup.com')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    
    # SendGrid configuration (alternative to SMTP)
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
    SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
    
    # SMS configuration (using a service like Twilio)
    TWILIO_SID = os.getenv('TWILIO_SID', '')
    TWILIO_TOKEN = os.getenv('TWILIO_TOKEN', '')
    TWILIO_PHONE = os.getenv('TWILIO_PHONE', '')
    
    @staticmethod
    def send_email(to_email, subject, body, html_body=None):
        """Send email notification"""
        try:
            if CloudService.SENDGRID_API_KEY:
                return CloudService._send_email_sendgrid(to_email, subject, body, html_body)
            else:
                return CloudService._send_email_smtp(to_email, subject, body, html_body)
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return False
    
    @staticmethod
    def _send_email_smtp(to_email, subject, body, html_body=None):
        """Send email using SMTP"""
        if not CloudService.EMAIL_PASSWORD:
            print("Email password not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = CloudService.EMAIL_ADDRESS
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(CloudService.SMTP_SERVER, CloudService.SMTP_PORT)
            server.starttls()
            server.login(CloudService.EMAIL_ADDRESS, CloudService.EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"SMTP email failed: {str(e)}")
            return False
    
    @staticmethod
    def _send_email_sendgrid(to_email, subject, body, html_body=None):
        """Send email using SendGrid API"""
        if not CloudService.SENDGRID_API_KEY:
            print("SendGrid API key not configured")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {CloudService.SENDGRID_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'personalizations': [{
                    'to': [{'email': to_email}]
                }],
                'from': {'email': CloudService.EMAIL_ADDRESS, 'name': 'TennisMatchUp'},
                'subject': subject,
                'content': [
                    {'type': 'text/plain', 'value': body}
                ]
            }
            
            if html_body:
                data['content'].append({'type': 'text/html', 'value': html_body})
            
            response = requests.post(
                CloudService.SENDGRID_API_URL,
                headers=headers,
                json=data,
                timeout=10
            )
            
            return response.status_code == 202
        except Exception as e:
            print(f"SendGrid email failed: {str(e)}")
            return False
    
    @staticmethod
    def send_booking_confirmation(booking):
        """Send booking confirmation email"""
        subject = f"Booking Confirmation - {booking.court.name}"
        
        body = f"""
Dear {booking.player.user.full_name},

Your tennis court booking has been confirmed!

Booking Details:
- Court: {booking.court.name}
- Location: {booking.court.location}
- Date: {booking.booking_date.strftime('%A, %B %d, %Y')}
- Time: {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}
- Duration: {(datetime.combine(booking.booking_date, booking.end_time) - datetime.combine(booking.booking_date, booking.start_time)).total_seconds() / 3600} hours
- Cost: ${booking.court.hourly_rate * ((datetime.combine(booking.booking_date, booking.end_time) - datetime.combine(booking.booking_date, booking.start_time)).total_seconds() / 3600)}

Court Owner: {booking.court.owner.full_name}
Contact: {booking.court.owner.phone_number or booking.court.owner.email}

Notes: {booking.notes or 'No special notes'}

Important Reminders:
- Please arrive 10 minutes early
- Bring your own tennis equipment
- Check weather conditions before arrival
- Contact the court owner if you need to cancel or reschedule

Thank you for using TennisMatchUp!

Best regards,
The TennisMatchUp Team
        """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5530;">Booking Confirmation</h2>
                
                <p>Dear {booking.player.user.full_name},</p>
                
                <p style="font-size: 18px; color: #2c5530;"><strong>Your tennis court booking has been confirmed! 🎾</strong></p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #2c5530;">Booking Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px 0; font-weight: bold;">Court:</td><td style="padding: 8px 0;">{booking.court.name}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Location:</td><td style="padding: 8px 0;">{booking.court.location}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Date:</td><td style="padding: 8px 0;">{booking.booking_date.strftime('%A, %B %d, %Y')}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Time:</td><td style="padding: 8px 0;">{booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Cost:</td><td style="padding: 8px 0;">${booking.court.hourly_rate}</td></tr>
                    </table>
                </div>
                
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #2c5530;">Important Reminders</h4>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>Please arrive 10 minutes early</li>
                        <li>Bring your own tennis equipment</li>
                        <li>Check weather conditions before arrival</li>
                        <li>Contact the court owner if you need to cancel or reschedule</li>
                    </ul>
                </div>
                
                <p>Thank you for using TennisMatchUp!</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666;">
                    <p>Best regards,<br>The TennisMatchUp Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return CloudService.send_email(booking.player.user.email, subject, body, html_body)
    
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
- Player Phone: {booking.player.user.phone_number or 'Not provided'}

Notes from player: {booking.notes or 'No notes provided'}

Please log in to your TennisMatchUp account to approve or decline this request.
The player will be notified of your decision.

Best regards,
The TennisMatchUp Team
        """
        
        return CloudService.send_email(booking.court.owner.email, subject, body)
    
    @staticmethod
    def send_booking_reminder(booking, hours_before=24):
        """Send booking reminder email"""
        subject = f"Reminder: Tennis Court Booking Tomorrow - {booking.court.name}"
        
        body = f"""
Dear {booking.player.user.full_name},

This is a friendly reminder about your upcoming tennis court booking.

Tomorrow's Booking:
- Court: {booking.court.name}
- Location: {booking.court.location}
- Date: {booking.booking_date.strftime('%A, %B %d, %Y')}
- Time: {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}

Weather reminder: Please check the weather forecast and dress appropriately.

Have a great game!

The TennisMatchUp Team
        """
        
        return CloudService.send_email(booking.player.user.email, subject, body)
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new users"""
        subject = "Welcome to TennisMatchUp!"
        
        body = f"""
Dear {user.full_name},

Welcome to TennisMatchUp - your premier tennis court booking platform!

We're excited to have you join our tennis community. Here's what you can do:

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
3. {'Book your first court or find playing partners' if user.user_type == 'player' else 'Start receiving booking requests'}

If you have any questions, feel free to contact our support team.

Game on!

The TennisMatchUp Team
        """
        
        return CloudService.send_email(user.email, subject, body)
    
    @staticmethod
    def send_password_reset(user, reset_token):
        """Send password reset email"""
        subject = "Password Reset - TennisMatchUp"
        
        # In production, this would be a proper URL
        reset_url = f"http://localhost:5000/auth/reset-password?token={reset_token}"
        
        body = f"""
Dear {user.full_name},

You requested a password reset for your TennisMatchUp account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you didn't request this reset, please ignore this email.

Best regards,
The TennisMatchUp Team
        """
        
        return CloudService.send_email(user.email, subject, body)
    
    @staticmethod
    def send_sms(phone_number, message):
        """Send SMS notification (using Twilio or similar service)"""
        if not CloudService.TWILIO_SID or not CloudService.TWILIO_TOKEN:
            print("SMS service not configured")
            return False
        
        try:
            # This would use Twilio's API in production
            # For now, just log the message
            print(f"SMS to {phone_number}: {message}")
            return True
        except Exception as e:
            print(f"SMS sending failed: {str(e)}")
            return False
    
    @staticmethod
    def get_weather_info(location):
        """Get weather information for a location"""
        # This would integrate with a weather API like OpenWeatherMap
        # For now, return mock data
        return {
            'location': location,
            'temperature': 22,
            'condition': 'Sunny',
            'humidity': 45,
            'wind_speed': 8,
            'is_good_for_tennis': True,
            'forecast': 'Perfect weather for tennis!'
        }
    
    @staticmethod
    def send_bulk_notification(user_list, subject, body):
        """Send bulk email notifications"""
        successful_sends = 0
        failed_sends = 0
        
        for user in user_list:
            try:
                if CloudService.send_email(user.email, subject, body):
                    successful_sends += 1
                else:
                    failed_sends += 1
            except:
                failed_sends += 1
        
        return {
            'total_users': len(user_list),
            'successful_sends': successful_sends,
            'failed_sends': failed_sends,
            'success_rate': (successful_sends / len(user_list)) * 100 if user_list else 0
        }
    
    @staticmethod
    def log_notification(user_id, notification_type, content, status):
        """Log notification for tracking and analytics"""
        # In production, this would save to a notifications table
        log_entry = {
            'timestamp': datetime.now(),
            'user_id': user_id,
            'type': notification_type,
            'content': content[:100] + '...' if len(content) > 100 else content,
            'status': status,
            'delivery_method': 'email'
        }
        
        print(f"Notification Log: {log_entry}")
        return True
    
    @staticmethod
    def get_notification_preferences(user_id):
        """Get user notification preferences"""
        # In production, this would read from user preferences table
        return {
            'email_booking_confirmations': True,
            'email_booking_reminders': True,
            'email_match_suggestions': True,
            'email_promotional': False,
            'sms_urgent_updates': True,
            'sms_booking_reminders': False,
            'push_notifications': True
        }
    
    @staticmethod
    def update_notification_preferences(user_id, preferences):
        """Update user notification preferences"""
        # In production, this would save to user preferences table
        print(f"Updated notification preferences for user {user_id}: {preferences}")
        return True
    
    @staticmethod
    def get_system_health_status():
        """Get status of external services"""
        status = {
            'email_service': 'operational',
            'sms_service': 'operational',
            'weather_api': 'operational',
            'maps_api': 'operational',
            'overall_health': 'healthy'
        }
        
        # Test email service
        try:
            if CloudService.SENDGRID_API_KEY or CloudService.EMAIL_PASSWORD:
                status['email_service'] = 'operational'
            else:
                status['email_service'] = 'not_configured'
        except:
            status['email_service'] = 'error'
        
        # Test SMS service
        if CloudService.TWILIO_SID and CloudService.TWILIO_TOKEN:
            status['sms_service'] = 'operational'
        else:
            status['sms_service'] = 'not_configured'
        
        # Determine overall health
        services_down = sum(1 for service in ['email_service', 'sms_service', 'weather_api', 'maps_api'] 
                          if status[service] == 'error')
        
        if services_down == 0:
            status['overall_health'] = 'healthy'
        elif services_down <= 2:
            status['overall_health'] = 'degraded'
        else:
            status['overall_health'] = 'critical'
        
        return status