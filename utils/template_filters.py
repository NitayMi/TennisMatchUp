"""
Template Filters for TennisMatchUp
Custom Jinja2 filters to clean up templates from business logic
"""
from datetime import datetime, date, time , timedelta
import json


def register_filters(app):
    """Register all custom filters with the Flask app"""
    
    @app.template_filter('currency')
    def currency_filter(amount):
        """Format amount as currency"""
        if amount is None:
            return "$0.00"
        return f"${amount:.2f}"
    
    @app.template_filter('currency_no_decimals') 
    def currency_no_decimals_filter(amount):
        """Format amount as currency without decimals"""
        if amount is None:
            return "$0"
        return f"${amount:.0f}"
    
    @app.template_filter('percentage')
    def percentage_filter(value, precision=1):
        """Format value as percentage"""
        if value is None:
            return "0%"
        return f"{value:.{precision}f}%"
    
    @app.template_filter('format_date')
    def format_date_filter(date_obj, format_string='%B %d, %Y'):
        """Format date object"""
        if date_obj is None:
            return ""
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
            except ValueError:
                return date_obj
        return date_obj.strftime(format_string)
    
    @app.template_filter('format_time')
    def format_time_filter(time_obj, format_string='%H:%M'):
        """Format time object"""
        if time_obj is None:
            return ""
        if isinstance(time_obj, str):
            try:
                time_obj = datetime.strptime(time_obj, '%H:%M').time()
            except ValueError:
                return time_obj
        return time_obj.strftime(format_string)
    
    @app.template_filter('format_datetime')
    def format_datetime_filter(datetime_obj, format_string='%B %d, %Y at %H:%M'):
        """Format datetime object"""
        if datetime_obj is None:
            return ""
        return datetime_obj.strftime(format_string)
    
    @app.template_filter('time_ago')
    def time_ago_filter(datetime_obj):
        """Show time ago format (e.g., '2 hours ago')"""
        if datetime_obj is None:
            return ""
        
        # Handle string dates (ISO format)
        if isinstance(datetime_obj, str):
            try:
                # Try parsing ISO format first
                if 'T' in datetime_obj:
                    datetime_obj = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
                else:
                    # Try other common formats
                    datetime_obj = datetime.strptime(datetime_obj, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return datetime_obj  # Return original string if can't parse
        
        now = datetime.now()
        if hasattr(datetime_obj, 'tzinfo') and datetime_obj.tzinfo:
            now = now.replace(tzinfo=datetime_obj.tzinfo)
        
        diff = now - datetime_obj
        
        if diff.days > 0:
            if diff.days == 1:
                return "1 day ago"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            else:
                months = diff.days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
        
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        
        return "Just now"
    
    @app.template_filter('status_color')
    def status_color_filter(status):
        """Get Bootstrap color class for status"""
        status_colors = {
            'pending': 'warning',
            'confirmed': 'success', 
            'cancelled': 'danger',
            'rejected': 'secondary',
            'completed': 'info',
            'active': 'success',
            'inactive': 'secondary'
        }
        return status_colors.get(status.lower() if status else '', 'secondary')
    
    @app.template_filter('status_icon')
    def status_icon_filter(status):
        """Get icon for status"""
        status_icons = {
            'pending': 'fas fa-clock',
            'confirmed': 'fas fa-check-circle',
            'cancelled': 'fas fa-times-circle',
            'rejected': 'fas fa-ban',
            'completed': 'fas fa-check',
            'active': 'fas fa-check-circle',
            'inactive': 'fas fa-pause-circle'
        }
        return status_icons.get(status.lower() if status else '', 'fas fa-question-circle')
    
    @app.template_filter('status_display')
    def status_display_filter(status):
        """Get display text for status"""
        status_display = {
            'pending': 'Pending Approval',
            'confirmed': 'Confirmed',
            'cancelled': 'Cancelled',
            'rejected': 'Rejected', 
            'completed': 'Completed',
            'active': 'Active',
            'inactive': 'Inactive'
        }
        return status_display.get(status.lower() if status else '', status.title() if status else '')
    
    @app.template_filter('skill_level_color')
    def skill_level_color_filter(skill_level):
        """Get color for skill level"""
        colors = {
            'beginner': 'success',
            'intermediate': 'warning', 
            'advanced': 'danger',
            'professional': 'primary'
        }
        return colors.get(skill_level.lower() if skill_level else '', 'secondary')
    
    @app.template_filter('skill_level_icon')
    def skill_level_icon_filter(skill_level):
        """Get icon for skill level"""
        icons = {
            'beginner': 'fas fa-seedling',
            'intermediate': 'fas fa-chart-line',
            'advanced': 'fas fa-fire',
            'professional': 'fas fa-crown'
        }
        return icons.get(skill_level.lower() if skill_level else '', 'fas fa-user')
    
    @app.template_filter('truncate_words')
    def truncate_words_filter(text, max_words=20):
        """Truncate text to maximum number of words"""
        if not text:
            return ""
        
        words = text.split()
        if len(words) <= max_words:
            return text
        
        return " ".join(words[:max_words]) + "..."
    
    @app.template_filter('capitalize_each')
    def capitalize_each_filter(text):
        """Capitalize each word"""
        if not text:
            return ""
        return " ".join(word.capitalize() for word in text.split())
    
    @app.template_filter('phone_format')
    def phone_format_filter(phone):
        """Format phone number"""
        if not phone:
            return ""
        
        # Remove all non-digit characters
        digits = ''.join(c for c in phone if c.isdigit())
        
        # Format as (XXX) XXX-XXXX if 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        
        return phone
    
    @app.template_filter('duration_display')
    def duration_display_filter(start_time, end_time):
        """Display duration between two times"""
        if not start_time or not end_time:
            return ""
        
        # Handle string inputs
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, '%H:%M').time()
        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, '%H:%M').time()
        
        # Convert to datetime for calculation
        today = date.today()
        start_datetime = datetime.combine(today, start_time)
        end_datetime = datetime.combine(today, end_time)
        
        # Handle overnight bookings
        if end_datetime <= start_datetime:
            end_datetime = datetime.combine(today, end_time) + timedelta(days=1)
        
        duration = end_datetime - start_datetime
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"
    
    @app.template_filter('booking_cost')
    def booking_cost_filter(hourly_rate, start_time, end_time):
        """Calculate booking cost"""
        if not hourly_rate or not start_time or not end_time:
            return "$0.00"
        
        try:
            # Handle string inputs
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, '%H:%M').time()
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, '%H:%M').time()
            
            # Convert to datetime for calculation
            today = date.today()
            start_datetime = datetime.combine(today, start_time)
            end_datetime = datetime.combine(today, end_time)
            
            # Handle overnight bookings
            if end_datetime <= start_datetime:
                end_datetime = datetime.combine(today, end_time) + timedelta(days=1)
            
            duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
            total_cost = hourly_rate * duration_hours
            
            return f"${total_cost:.2f}"
        except:
            return "$0.00"
    
    @app.template_filter('compatibility_percentage')
    def compatibility_percentage_filter(score):
        """Convert compatibility score to percentage"""
        if score is None:
            return "0%"
        
        # Assuming score is out of 100
        percentage = max(0, min(100, score))
        return f"{percentage:.0f}%"
    
    @app.template_filter('distance_format')
    def distance_format_filter(distance_km):
        """Format distance in appropriate units"""
        if distance_km is None:
            return "Unknown"
        
        if distance_km < 1:
            meters = distance_km * 1000
            return f"{meters:.0f}m"
        elif distance_km < 10:
            return f"{distance_km:.1f}km"
        else:
            return f"{distance_km:.0f}km"
    
    @app.template_filter('json_safe')
    def json_safe_filter(data):
        """Convert data to JSON safely for JavaScript"""
        if data is None:
            return 'null'
        
        # Handle datetime objects
        def default_serializer(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            elif isinstance(obj, time):
                return obj.strftime('%H:%M:%S')
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(data, default=default_serializer)
    
    @app.template_filter('rating_stars')
    def rating_stars_filter(rating, max_rating=5):
        """Convert numeric rating to star display"""
        if rating is None:
            return "No rating"
        
        full_stars = int(rating)
        half_star = (rating - full_stars) >= 0.5
        empty_stars = max_rating - full_stars - (1 if half_star else 0)
        
        stars = []
        stars.extend(['★'] * full_stars)
        if half_star:
            stars.append('☆')
        stars.extend(['☆'] * empty_stars)
        
        return ''.join(stars)
    
    @app.template_filter('initials')
    def initials_filter(full_name):
        """Get initials from full name"""
        if not full_name:
            return "?"
        
        words = full_name.split()
        initials = ''.join(word[0].upper() for word in words if word)
        return initials[:2]  # Limit to 2 initials
    
    @app.template_filter('booking_status_badge')
    def booking_status_badge_filter(status):
        """Generate complete status badge HTML"""
        color = status_color_filter(status)
        icon = status_icon_filter(status)
        display = status_display_filter(status)
        
        return f'<span class="badge bg-{color}"><i class="{icon}"></i> {display}</span>'
    
    @app.template_filter('court_type_icon')
    def court_type_icon_filter(court_type):
        """Get icon for court type"""
        icons = {
            'outdoor': 'fas fa-sun',
            'indoor': 'fas fa-home',
            'covered': 'fas fa-umbrella',
            'hard': 'fas fa-square',
            'clay': 'fas fa-mountain',
            'grass': 'fas fa-seedling'
        }
        return icons.get(court_type.lower() if court_type else '', 'fas fa-tennis-ball')
    
    @app.template_filter('availability_color')
    def availability_color_filter(available_slots, total_slots):
        """Get color based on availability percentage"""
        if total_slots == 0:
            return 'secondary'
        
        percentage = (available_slots / total_slots) * 100
        
        if percentage >= 70:
            return 'success'
        elif percentage >= 30:
            return 'warning'
        else:
            return 'danger'
    
    @app.template_filter('month_name')
    def month_name_filter(month_num):
        """Convert month number to name"""
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        try:
            return month_names[int(month_num) - 1]
        except (ValueError, IndexError):
            return str(month_num)
    
    @app.template_filter('day_of_week')
    def day_of_week_filter(date_obj):
        """Get day of week name"""
        if date_obj is None:
            return ""
        
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
            except ValueError:
                return date_obj
        
        return date_obj.strftime('%A')
    
    @app.template_filter('time_slot_class')
    def time_slot_class_filter(hour, bookings):
        """Get CSS class for time slot based on bookings"""
        if not bookings:
            return 'available'
        
        for booking in bookings:
            if hasattr(booking, 'start_time') and hasattr(booking, 'end_time'):
                start_hour = booking.start_time.hour
                end_hour = booking.end_time.hour
                
                if start_hour <= hour < end_hour:
                    return f'booked {booking.status}'
        
        return 'available'
    
    @app.template_filter('format_list')
    def format_list_filter(items, conjunction='and'):
        """Format a list with proper conjunctions"""
        if not items:
            return ""
        
        if len(items) == 1:
            return str(items[0])
        elif len(items) == 2:
            return f"{items[0]} {conjunction} {items[1]}"
        else:
            return f"{', '.join(str(item) for item in items[:-1])}, {conjunction} {items[-1]}"
    
    @app.template_filter('humanize_number')
    def humanize_number_filter(num):
        """Convert large numbers to human readable format"""
        if num is None:
            return "0"
        
        num = float(num)
        
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return f"{num:.0f}"