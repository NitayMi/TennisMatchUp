"""
Calendar Service for TennisMatchUp
Handles calendar integration and scheduling functionality
"""
from datetime import datetime, timedelta, date
from models.database import db
from models.court import Court, Booking
from models.player import Player
import calendar

class CalendarService:
    """Calendar and scheduling service"""
    
    @staticmethod
    def get_monthly_calendar(year, month, court_id=None, player_id=None):
        """Generate calendar view for a specific month"""
        # Get the first day of the month and number of days
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get bookings for the month
        query = Booking.query.filter(
            Booking.booking_date >= first_day,
            Booking.booking_date <= last_day
        )
        
        if court_id:
            query = query.filter(Booking.court_id == court_id)
        if player_id:
            query = query.filter(Booking.player_id == player_id)
        
        bookings = query.all()
        
        # Organize bookings by date
        bookings_by_date = {}
        for booking in bookings:
            date_key = booking.booking_date.strftime('%Y-%m-%d')
            if date_key not in bookings_by_date:
                bookings_by_date[date_key] = []
            bookings_by_date[date_key].append(booking)
        
        # Generate calendar structure
        cal = calendar.monthcalendar(year, month)
        calendar_data = {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'weeks': [],
            'bookings_by_date': bookings_by_date
        }
        
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append({
                        'day': None,
                        'date': None,
                        'bookings': [],
                        'is_today': False,
                        'is_weekend': False
                    })
                else:
                    current_date = date(year, month, day)
                    date_str = current_date.strftime('%Y-%m-%d')
                    day_bookings = bookings_by_date.get(date_str, [])
                    
                    week_data.append({
                        'day': day,
                        'date': current_date,
                        'date_str': date_str,
                        'bookings': day_bookings,
                        'booking_count': len(day_bookings),
                        'is_today': current_date == date.today(),
                        'is_weekend': current_date.weekday() >= 5,
                        'is_past': current_date < date.today()
                    })
            calendar_data['weeks'].append(week_data)
        
        return calendar_data
    
    @staticmethod
    def get_daily_schedule(target_date, court_id=None, player_id=None):
        """Get detailed schedule for a specific day"""
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # Get bookings for the day
        query = Booking.query.filter(Booking.booking_date == target_date)
        
        if court_id:
            query = query.filter(Booking.court_id == court_id)
        if player_id:
            query = query.filter(Booking.player_id == player_id)
        
        bookings = query.order_by(Booking.start_time).all()
        
        # Generate hourly time slots
        time_slots = []
        for hour in range(6, 22):  # 6 AM to 9 PM
            slot_time = datetime.strptime(f'{hour}:00', '%H:%M').time()
            
            # Find bookings for this time slot
            slot_bookings = []
            for booking in bookings:
                if booking.start_time <= slot_time < booking.end_time:
                    slot_bookings.append(booking)
            
            time_slots.append({
                'time': slot_time.strftime('%H:%M'),
                'hour': hour,
                'bookings': slot_bookings,
                'is_available': len(slot_bookings) == 0,
                'is_peak_hour': 17 <= hour <= 20  # 5 PM to 8 PM
            })
        
        return {
            'date': target_date,
            'day_name': target_date.strftime('%A'),
            'time_slots': time_slots,
            'total_bookings': len(bookings),
            'is_today': target_date == date.today(),
            'is_weekend': target_date.weekday() >= 5
        }
    
    @staticmethod
    def get_availability_summary(court_id, start_date, end_date):
        """Get availability summary for a court over a date range"""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        court = Court.query.get(court_id)
        if not court:
            return None
        
        # Get all bookings in the date range
        bookings = Booking.query.filter(
            Booking.court_id == court_id,
            Booking.booking_date >= start_date,
            Booking.booking_date <= end_date,
            Booking.status.in_(['confirmed', 'pending'])
        ).all()
        
        # Calculate availability by day
        availability_data = {}
        current_date = start_date
        
        while current_date <= end_date:
            day_bookings = [b for b in bookings if b.booking_date == current_date]
            
            # Calculate total booked hours
            total_booked_hours = 0
            for booking in day_bookings:
                duration = (datetime.combine(date.today(), booking.end_time) - 
                          datetime.combine(date.today(), booking.start_time)).total_seconds() / 3600
                total_booked_hours += duration
            
            # Assume 14 hours available per day (8 AM to 10 PM)
            total_available_hours = 14
            availability_percentage = ((total_available_hours - total_booked_hours) / total_available_hours) * 100
            
            availability_data[current_date.strftime('%Y-%m-%d')] = {
                'date': current_date,
                'bookings': len(day_bookings),
                'booked_hours': total_booked_hours,
                'available_hours': max(0, total_available_hours - total_booked_hours),
                'availability_percentage': max(0, availability_percentage),
                'is_weekend': current_date.weekday() >= 5
            }
            
            current_date += timedelta(days=1)
        
        # Calculate overall statistics
        total_days = len(availability_data)
        avg_availability = sum(day['availability_percentage'] for day in availability_data.values()) / total_days
        total_bookings = sum(day['bookings'] for day in availability_data.values())
        
        return {
            'court': court,
            'start_date': start_date,
            'end_date': end_date,
            'daily_availability': availability_data,
            'summary': {
                'total_days': total_days,
                'average_availability': round(avg_availability, 1),
                'total_bookings': total_bookings,
                'busiest_day': max(availability_data.items(), key=lambda x: x[1]['bookings'])[0] if availability_data else None,
                'most_available_day': max(availability_data.items(), key=lambda x: x[1]['availability_percentage'])[0] if availability_data else None
            }
        }
    
    @staticmethod
    def find_common_availability(player1_id, player2_id, start_date, end_date):
        """Find common availability between two players"""
        # Get bookings for both players
        player1_bookings = Booking.query.filter(
            Booking.player_id == player1_id,
            Booking.booking_date >= start_date,
            Booking.booking_date <= end_date,
            Booking.status.in_(['confirmed', 'pending'])
        ).all()
        
        player2_bookings = Booking.query.filter(
            Booking.player_id == player2_id,
            Booking.booking_date >= start_date,
            Booking.booking_date <= end_date,
            Booking.status.in_(['confirmed', 'pending'])
        ).all()
        
        # Find free time slots
        common_slots = []
        current_date = start_date
        
        while current_date <= end_date:
            # Get bookings for current date
            p1_day_bookings = [b for b in player1_bookings if b.booking_date == current_date]
            p2_day_bookings = [b for b in player2_bookings if b.booking_date == current_date]
            
            # Find free slots (simplified - checking hourly slots)
            for hour in range(8, 21):  # 8 AM to 8 PM
                slot_start = datetime.strptime(f'{hour}:00', '%H:%M').time()
                slot_end = datetime.strptime(f'{hour + 1}:00', '%H:%M').time()
                
                # Check if both players are free
                p1_free = not any(b.start_time <= slot_start < b.end_time for b in p1_day_bookings)
                p2_free = not any(b.start_time <= slot_start < b.end_time for b in p2_day_bookings)
                
                if p1_free and p2_free:
                    common_slots.append({
                        'date': current_date,
                        'start_time': slot_start.strftime('%H:%M'),
                        'end_time': slot_end.strftime('%H:%M'),
                        'is_weekend': current_date.weekday() >= 5,
                        'is_peak_hour': 17 <= hour <= 20
                    })
            
            current_date += timedelta(days=1)
        
        return common_slots
    
    @staticmethod
    def get_booking_conflicts(new_booking_data):
        """Check for booking conflicts"""
        court_id = new_booking_data['court_id']
        booking_date = new_booking_data['booking_date']
        start_time = new_booking_data['start_time']
        end_time = new_booking_data['end_time']
        
        if isinstance(booking_date, str):
            booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, '%H:%M').time()
        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, '%H:%M').time()
        
        # Find conflicting bookings
        conflicts = Booking.query.filter(
            Booking.court_id == court_id,
            Booking.booking_date == booking_date,
            Booking.status.in_(['confirmed', 'pending']),
            db.or_(
                # New booking starts during existing booking
                db.and_(Booking.start_time <= start_time, Booking.end_time > start_time),
                # New booking ends during existing booking
                db.and_(Booking.start_time < end_time, Booking.end_time >= end_time),
                # New booking completely overlaps existing booking
                db.and_(Booking.start_time >= start_time, Booking.end_time <= end_time)
            )
        ).all()
        
        return {
            'has_conflicts': len(conflicts) > 0,
            'conflicts': conflicts,
            'suggested_alternatives': CalendarService._suggest_alternative_slots(
                court_id, booking_date, start_time, end_time
            ) if conflicts else []
        }
    
    @staticmethod
    def _suggest_alternative_slots(court_id, booking_date, preferred_start, preferred_end):
        """Suggest alternative time slots"""
        duration = (datetime.combine(date.today(), preferred_end) - 
                   datetime.combine(date.today(), preferred_start)).total_seconds() / 3600
        
        # Get existing bookings for the day
        existing_bookings = Booking.query.filter(
            Booking.court_id == court_id,
            Booking.booking_date == booking_date,
            Booking.status.in_(['confirmed', 'pending'])
        ).order_by(Booking.start_time).all()
        
        suggestions = []
        
        # Check slots before and after preferred time
        for hour_offset in [-2, -1, 1, 2, 3]:
            new_start_hour = preferred_start.hour + hour_offset
            
            if 6 <= new_start_hour <= 20:  # Within business hours
                new_start = datetime.strptime(f'{new_start_hour}:00', '%H:%M').time()
                new_end = (datetime.combine(date.today(), new_start) + 
                          timedelta(hours=duration)).time()
                
                # Check if this slot is free
                conflicts = any(
                    b.start_time <= new_start < b.end_time or
                    b.start_time < new_end <= b.end_time or
                    (new_start <= b.start_time and new_end >= b.end_time)
                    for b in existing_bookings
                )
                
                if not conflicts:
                    suggestions.append({
                        'start_time': new_start.strftime('%H:%M'),
                        'end_time': new_end.strftime('%H:%M'),
                        'time_difference': abs(hour_offset),
                        'is_peak_hour': 17 <= new_start_hour <= 20
                    })
        
        # Sort by time difference from preferred slot
        suggestions.sort(key=lambda x: x['time_difference'])
        
        return suggestions[:3]  # Return top 3 alternatives
    
    @staticmethod
    def generate_calendar_export_data(player_id, start_date, end_date, format='ical'):
        """Generate calendar export data (ICS format for calendar apps)"""
        player = Player.query.get(player_id)
        if not player:
            return None
        
        bookings = Booking.query.filter(
            Booking.player_id == player_id,
            Booking.booking_date >= start_date,
            Booking.booking_date <= end_date,
            Booking.status == 'confirmed'
        ).all()
        
        if format == 'ical':
            # Generate basic ICS format
            ical_data = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//TennisMatchUp//TennisMatchUp Calendar//EN",
                "CALSCALE:GREGORIAN",
                "METHOD:PUBLISH"
            ]
            
            for booking in bookings:
                start_datetime = datetime.combine(booking.booking_date, booking.start_time)
                end_datetime = datetime.combine(booking.booking_date, booking.end_time)
                
                ical_data.extend([
                    "BEGIN:VEVENT",
                    f"UID:{booking.id}@tennismatchup.com",
                    f"DTSTART:{start_datetime.strftime('%Y%m%dT%H%M%S')}",
                    f"DTEND:{end_datetime.strftime('%Y%m%dT%H%M%S')}",
                    f"SUMMARY:Tennis Court Booking - {booking.court.name}",
                    f"DESCRIPTION:Court: {booking.court.name}\\nLocation: {booking.court.location}\\nNotes: {booking.notes or 'No notes'}",
                    f"LOCATION:{booking.court.location}",
                    "STATUS:CONFIRMED",
                    "END:VEVENT"
                ])
            
            ical_data.append("END:VCALENDAR")
            return "\n".join(ical_data)
        
        return None
    
    @staticmethod
    def get_calendar_widget_data(player_id, days_ahead=7):
        """Get calendar widget data for dashboard"""
        player = Player.query.get(player_id)
        if not player:
            return None
        
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)
        
        upcoming_bookings = Booking.query.filter(
            Booking.player_id == player_id,
            Booking.booking_date >= start_date,
            Booking.booking_date <= end_date,
            Booking.status.in_(['confirmed', 'pending'])
        ).order_by(Booking.booking_date, Booking.start_time).all()
        
        # Group by date
        bookings_by_date = {}
        for booking in upcoming_bookings:
            date_str = booking.booking_date.strftime('%Y-%m-%d')
            if date_str not in bookings_by_date:
                bookings_by_date[date_str] = []
            bookings_by_date[date_str].append(booking)
        
        # Generate next 7 days
        widget_days = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            day_bookings = bookings_by_date.get(date_str, [])
            
            widget_days.append({
                'date': current_date,
                'day_name': current_date.strftime('%a'),
                'day_number': current_date.day,
                'bookings': day_bookings,
                'booking_count': len(day_bookings),
                'is_today': current_date == date.today(),
                'is_weekend': current_date.weekday() >= 5,
                'has_bookings': len(day_bookings) > 0
            })
            
            current_date += timedelta(days=1)
        
        return {
            'days': widget_days,
            'total_upcoming': len(upcoming_bookings),
            'next_booking': upcoming_bookings[0] if upcoming_bookings else None
        }