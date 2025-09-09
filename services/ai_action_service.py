"""
AI Action Service for TennisMatchUp
Fixed version with proper time handling
"""
import json
from datetime import datetime, timedelta, time
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court, Booking
from services.matching_engine import MatchingEngine
from services.rule_engine import RuleEngine
import re

class AIActionService:
    """Service for executing real platform actions via AI"""
    
    @staticmethod
    def find_available_players(location, date_str, time_str, skill_level, user_id):
        """Find players available for specific date/time/location"""
        try:
            # Parse date and time properly
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            target_time = datetime.strptime(time_str, '%H:%M').time()
            
            # Find players in location with similar skill level
            players = Player.query.join(User).filter(
                Player.preferred_location.ilike(f'%{location}%'),
                Player.skill_level == skill_level,
                User.id != user_id,
                User.is_active == True
            ).limit(10).all()
            
            available_players = []
            for player in players:
                # Check if player has conflicting bookings using proper time comparison
                conflicts = Booking.query.filter(
                    Booking.player_id == player.id,
                    Booking.booking_date == target_date,
                    Booking.start_time <= target_time,
                    Booking.end_time > target_time,
                    Booking.status.in_(['confirmed', 'pending'])
                ).count()
                
                if conflicts == 0:
                    # Calculate compatibility score
                    current_player = Player.query.filter_by(user_id=user_id).first()
                    compatibility = MatchingEngine.calculate_compatibility_score(
                        current_player, 
                        player
                    ) if current_player else 85
                    
                    available_players.append({
                        'player_id': player.id,
                        'name': player.user.full_name,
                        'skill_level': player.skill_level,
                        'location': player.preferred_location,
                        'compatibility': f"{compatibility}%",
                        'contact_available': True
                    })
            
            # Sort by compatibility score
            available_players.sort(key=lambda x: int(x['compatibility'].replace('%', '')), reverse=True)
            return available_players[:5]  # Top 5 matches
            
        except Exception as e:
            print(f"Error finding available players: {str(e)}")
            return []
    
    @staticmethod
    def find_available_courts(location, date_str, start_hour, duration_hours=2):
        """Find courts available for specific date/time/location"""
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = time(start_hour, 0)  # Convert hour to time object
            end_time = time(start_hour + duration_hours, 0)
            
            # Find courts in location
            courts = Court.query.filter(
                Court.location.ilike(f'%{location}%'),
                Court.is_active == True
            ).all()
            
            available_courts = []
            for court in courts:
                # Check for booking conflicts using proper time comparison
                conflicts = Booking.query.filter(
                    Booking.court_id == court.id,
                    Booking.booking_date == target_date,
                    ((Booking.start_time <= start_time) & (Booking.end_time > start_time)) |
                    ((Booking.start_time < end_time) & (Booking.end_time >= end_time)) |
                    ((Booking.start_time >= start_time) & (Booking.end_time <= end_time))
                ).filter(
                    Booking.status.in_(['confirmed', 'pending'])
                ).count()
                
                if conflicts == 0:
                    total_cost = court.hourly_rate * duration_hours
                    available_courts.append({
                        'court_id': court.id,
                        'name': court.name,
                        'location': court.location,
                        'surface': court.surface_type,
                        'hourly_rate': float(court.hourly_rate),
                        'total_cost': float(total_cost),
                        'duration': f"{duration_hours}h",
                        'time_slot': f"{start_hour:02d}:00-{(start_hour + duration_hours):02d}:00"
                    })
            
            # Sort by price
            available_courts.sort(key=lambda x: x['total_cost'])
            return available_courts[:5]  # Top 5 options
            
        except Exception as e:
            print(f"Error finding available courts: {str(e)}")
            return []
    
    @staticmethod
    def create_match_proposal(player_id, partner_candidates, court_options, date_str, time_str):
        """Create actionable match proposals combining players + courts"""
        proposals = []
        
        try:
            for i, player in enumerate(partner_candidates[:3]):  # Top 3 players
                for j, court in enumerate(court_options[:2]):  # Top 2 courts
                    proposal_id = f"proposal_{i}_{j}"
                    proposals.append({
                        'proposal_id': proposal_id,
                        'player': player,
                        'court': court,
                        'date': date_str,
                        'time': time_str,
                        'match_summary': f"{player['name']} at {court['name']}",
                        'total_cost': court['total_cost'],
                        'booking_action': {
                            'court_id': court['court_id'],
                            'partner_id': player['player_id'],
                            'datetime': f"{date_str} {time_str}"
                        }
                    })
            
            return proposals[:4]  # Max 4 proposals
            
        except Exception as e:
            print(f"Error creating match proposals: {str(e)}")
            return []
    
    @staticmethod
    def check_user_availability(user_id, date_str, start_hour, duration_hours=2):
        """Check if user has schedule conflicts - FIXED TIME HANDLING"""
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = time(start_hour, 0)  # Convert to time object
            end_time = time(start_hour + duration_hours, 0)
            
            player = Player.query.filter_by(user_id=user_id).first()
            if not player:
                return False
                
            # Fixed SQL query - compare time with time, not time with integer
            conflicts = Booking.query.filter(
                Booking.player_id == player.id,
                Booking.booking_date == target_date,
                ((Booking.start_time <= start_time) & (Booking.end_time > start_time)) |
                ((Booking.start_time < end_time) & (Booking.end_time >= end_time)),
                Booking.status.in_(['confirmed', 'pending'])
            ).count()
            
            return conflicts == 0
            
        except Exception as e:
            print(f"Error checking user availability: {str(e)}")
            return True  # Default to available if error
    
    @staticmethod
    def parse_user_intent(user_message):
        """Parse user message to determine what action they want"""
        message_lower = user_message.lower()
        
        # Intent detection patterns
        if any(word in message_lower for word in ['find partner', 'partner', 'someone', 'player']):
            return 'FIND_PARTNER'
        elif any(word in message_lower for word in ['court', 'book court', 'reserve']):
            return 'FIND_COURT'
        elif any(word in message_lower for word in ['complete match', 'setup match', 'court + partner', 'court and partner']):
            return 'COMPLETE_MATCH'
        elif any(word in message_lower for word in ['available', 'free', 'schedule']):
            return 'CHECK_AVAILABILITY'
        elif any(word in message_lower for word in ['weekend', 'saturday', 'sunday']):
            return 'WEEKEND_MATCHES'
        else:
            return 'GENERAL_CHAT'
    
    @staticmethod
    def extract_parameters(user_message):
        """Extract location, date, time from user message"""
        # Default parameters
        params = {
            'location': 'Tel Aviv',  # Default location
            'date': None,
            'time': None,
            'skill_level': 'beginner'
        }
        
        # Extract location patterns
        locations = ['tel aviv', 'rishon lezion', 'jerusalem', 'haifa', 'netanya', 'herzliya', 'ramat gan']
        for location in locations:
            if location in user_message.lower():
                params['location'] = location.title()
                break
        
        # Extract time patterns
        time_patterns = [r'(\d{1,2}):?(\d{0,2})\s*(am|pm)?', r'(\d{1,2})\s*(am|pm)']
        for pattern in time_patterns:
            match = re.search(pattern, user_message.lower())
            if match:
                hour = int(match.group(1))
                if 'pm' in user_message.lower() and hour != 12:
                    hour += 12
                elif 'am' in user_message.lower() and hour == 12:
                    hour = 0
                params['time'] = f"{hour:02d}:00"
                break
        
        # Extract date patterns
        date_patterns = ['saturday', 'sunday', 'weekend', 'tomorrow', 'today']
        for pattern in date_patterns:
            if pattern in user_message.lower():
                if pattern == 'saturday':
                    # Calculate next Saturday
                    today = datetime.now()
                    days_ahead = 5 - today.weekday()  # Saturday = 5
                    if days_ahead <= 0:
                        days_ahead += 7
                    target_date = today + timedelta(days=days_ahead)
                    params['date'] = target_date.strftime('%Y-%m-%d')
                elif pattern == 'sunday':
                    # Calculate next Sunday
                    today = datetime.now()
                    days_ahead = 6 - today.weekday()  # Sunday = 6
                    if days_ahead <= 0:
                        days_ahead += 7
                    target_date = today + timedelta(days=days_ahead)
                    params['date'] = target_date.strftime('%Y-%m-%d')
                elif pattern == 'tomorrow':
                    tomorrow = datetime.now() + timedelta(days=1)
                    params['date'] = tomorrow.strftime('%Y-%m-%d')
                elif pattern == 'today':
                    today = datetime.now()
                    params['date'] = today.strftime('%Y-%m-%d')
                elif pattern == 'weekend':
                    # Default to next Saturday
                    today = datetime.now()
                    days_ahead = 5 - today.weekday()  # Saturday = 5
                    if days_ahead <= 0:
                        days_ahead += 7
                    target_date = today + timedelta(days=days_ahead)
                    params['date'] = target_date.strftime('%Y-%m-%d')
                break
        
        # Default to next Saturday if no date found
        if not params['date']:
            today = datetime.now()
            days_ahead = 5 - today.weekday()  # Saturday = 5
            if days_ahead <= 0:
                days_ahead += 7
            target_date = today + timedelta(days=days_ahead)
            params['date'] = target_date.strftime('%Y-%m-%d')
        
        # Default to 3 PM if no time found
        if not params['time']:
            params['time'] = '15:00'
        
        return params