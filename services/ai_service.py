"""
AI Service for TennisMatchUp
Integrates with Ollama for intelligent recommendations and chat assistance
"""
import requests
import json
from datetime import datetime, timedelta
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court, Booking
from services.matching_engine import MatchingEngine
from services.rule_engine import RuleEngine

class AIService:
    """AI-powered services using Ollama"""
    
    # Ollama configuration
    OLLAMA_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.2"  # or "phi3" for lighter model
    
    @staticmethod
    def is_ollama_available():
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{AIService.OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def generate_response(prompt, model=None):
        """Generate AI response using Ollama"""
        if not model:
            model = AIService.DEFAULT_MODEL
        
        if not AIService.is_ollama_available():
            return "AI service is currently unavailable. Please try again later."
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            response = requests.post(
                f"{AIService.OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated')
            else:
                return "Error generating AI response"
                
        except Exception as e:
            return f"AI service error: {str(e)}"
    
    @staticmethod
    def get_personalized_recommendations(player_id):
        """Get AI-powered personalized recommendations for a player"""
        player = Player.query.get(player_id)
        if not player:
            return "Player not found"
        
        # Gather player context
        context = AIService._build_player_context(player_id)
        
        prompt = f"""
        As a tennis coaching AI, provide personalized recommendations for a tennis player with the following profile:
        
        Player Profile:
        - Name: {player.user.full_name}
        - Skill Level: {player.skill_level}
        - Preferred Location: {player.preferred_location}
        - Availability: {player.availability}
        - Recent Activity: {context['recent_bookings']} bookings in last 30 days
        - Match Compatibility: {context['match_stats']['compatibility_rate']}% with other players
        
        Recent Activity Summary:
        {context['activity_summary']}
        
        Please provide 3-4 specific, actionable recommendations to help this player:
        1. Find better playing partners
        2. Improve their booking strategy
        3. Enhance their tennis experience
        4. Grow their skills
        
        Keep recommendations practical and specific to their profile.
        """
        
        return AIService.generate_response(prompt)
    
    @staticmethod
    def analyze_playing_pattern(player_id):
        """Analyze player's booking and playing patterns"""
        player = Player.query.get(player_id)
        if not player:
            return "Player not found"
        
        # Get booking history
        bookings = Booking.query.filter_by(player_id=player_id).order_by(
            Booking.booking_date.desc()
        ).limit(20).all()
        
        if not bookings:
            return "Not enough data to analyze playing patterns. Book a few courts first!"
        
        # Analyze patterns
        patterns = AIService._analyze_booking_patterns(bookings)
        
        prompt = f"""
        As a tennis analytics AI, analyze this player's playing patterns and provide insights:
        
        Player: {player.user.full_name} ({player.skill_level} level)
        
        Booking Patterns Analysis:
        - Total bookings: {len(bookings)}
        - Most common booking day: {patterns['preferred_day']}
        - Most common time slot: {patterns['preferred_time']}
        - Average booking duration: {patterns['avg_duration']} hours
        - Preferred court types: {', '.join(patterns['court_types'])}
        - Average cost per booking: ${patterns['avg_cost']}
        - Cancellation rate: {patterns['cancellation_rate']}%
        
        Based on this data, provide:
        1. Key insights about their playing habits
        2. Suggestions for optimizing their booking strategy
        3. Recommendations for trying new things
        4. Tips for saving money or getting better value
        
        Keep the analysis encouraging and actionable.
        """
        
        return AIService.generate_response(prompt)
    
    @staticmethod
    def suggest_court_improvements(court_id):
        """AI suggestions for court owners to improve their courts"""
        court = Court.query.get(court_id)
        if not court:
            return "Court not found"
        
        # Gather court performance data
        context = AIService._build_court_context(court_id)
        
        prompt = f"""
        As a tennis facility management AI, provide improvement suggestions for this court:
        
        Court Information:
        - Name: {court.name}
        - Location: {court.location}
        - Type: {court.court_type}
        - Surface: {court.surface}
        - Hourly Rate: ${court.hourly_rate}
        
        Performance Metrics:
        - Total bookings: {context['total_bookings']}
        - Booking confirmation rate: {context['confirmation_rate']}%
        - Average rating: {context['avg_rating']}/5.0
        - Recent activity: {context['recent_bookings']} bookings last 30 days
        - Utilization rate: {context['utilization_rate']}%
        - Competition: {context['nearby_courts']} similar courts in area
        
        Provide specific recommendations to:
        1. Increase booking rates
        2. Improve customer satisfaction
        3. Optimize pricing strategy
        4. Enhance court appeal
        
        Consider market conditions and competition.
        """
        
        return AIService.generate_response(prompt)
    
    @staticmethod
    def generate_smart_match_description(player1_id, player2_id):
        """Generate AI description for why two players are a good match"""
        player1 = Player.query.get(player1_id)
        player2 = Player.query.get(player2_id)
        
        if not player1 or not player2:
            return "Player not found"
        
        # Get compatibility analysis
        validation = RuleEngine.validate_player_matching(player1_id, player2_id)
        if not validation['valid']:
            return f"Not a compatible match: {validation['reason']}"
        
        prompt = f"""
        As a tennis matchmaking AI, explain why these two players would be great playing partners:
        
        Player 1: {player1.user.full_name}
        - Skill: {player1.skill_level}
        - Location: {player1.preferred_location}
        - Availability: {player1.availability}
        
        Player 2: {player2.user.full_name}
        - Skill: {player2.skill_level}
        - Location: {player2.preferred_location}
        - Availability: {player2.availability}
        
        Compatibility Score: {validation['compatibility_score']}/100
        
        Write a friendly, encouraging message (2-3 sentences) explaining why they should play together.
        Focus on what they have in common and how they could enjoy playing together.
        """
        
        response = AIService.generate_response(prompt)
        return response if response else "You two seem like a great match - similar skill levels and compatible schedules!"
    
    @staticmethod
    def generate_booking_confirmation_message(booking_id):
        """Generate personalized booking confirmation message"""
        booking = Booking.query.get(booking_id)
        if not booking:
            return "Booking not found"
        
        prompt = f"""
        Generate a friendly, enthusiastic booking confirmation message for:
        
        Player: {booking.player.user.full_name}
        Court: {booking.court.name}
        Date: {booking.booking_date}
        Time: {booking.start_time} - {booking.end_time}
        Location: {booking.court.location}
        
        Include:
        - Confirmation details
        - A positive, encouraging tone
        - Brief playing tip or motivation
        - Reminder about court policies
        
        Keep it concise but warm and professional.
        """
        
        return AIService.generate_response(prompt)
    
    @staticmethod
    def analyze_system_trends():
        """Analyze overall system trends for admin dashboard"""
        if not AIService.is_ollama_available():
            return "AI analysis unavailable - Ollama not running"
        
        # Gather system statistics
        stats = AIService._gather_system_stats()
        
        prompt = f"""
        As a tennis platform analytics AI, analyze these system trends and provide insights:
        
        System Statistics (Last 30 Days):
        - New users: {stats['new_users']}
        - Total bookings: {stats['total_bookings']}
        - Revenue: ${stats['revenue']}
        - Most popular locations: {', '.join(stats['popular_locations'])}
        - Peak booking times: {', '.join(stats['peak_times'])}
        - Average booking duration: {stats['avg_duration']} hours
        - User retention rate: {stats['retention_rate']}%
        
        Provide:
        1. Key trends and insights
        2. Areas of concern or opportunity
        3. Recommendations for platform improvements
        4. Predictions for next month
        
        Focus on actionable business insights.
        """
        
        return AIService.generate_response(prompt)
    
    @staticmethod
    def _build_player_context(player_id):
        """Build comprehensive context about a player for AI analysis"""
        player = Player.query.get(player_id)
        
        # Get recent bookings
        recent_bookings = Booking.query.filter_by(player_id=player_id).filter(
            Booking.created_at >= datetime.now() - timedelta(days=30)
        ).count()
        
        # Get match statistics
        match_stats = MatchingEngine.get_match_statistics(player_id)
        
        # Build activity summary
        activity_summary = f"Player has made {recent_bookings} bookings in the last 30 days"
        if recent_bookings == 0:
            activity_summary += " (inactive)"
        elif recent_bookings > 8:
            activity_summary += " (very active)"
        elif recent_bookings > 4:
            activity_summary += " (active)"
        
        return {
            'recent_bookings': recent_bookings,
            'match_stats': match_stats,
            'activity_summary': activity_summary
        }
    
    @staticmethod
    def _analyze_booking_patterns(bookings):
        """Analyze booking patterns for AI insights"""
        if not bookings:
            return {}
        
        # Day of week analysis
        days = [b.booking_date.strftime('%A') for b in bookings]
        preferred_day = max(set(days), key=days.count) if days else 'N/A'
        
        # Time analysis
        times = [b.start_time.strftime('%H:00') for b in bookings]
        preferred_time = max(set(times), key=times.count) if times else 'N/A'
        
        # Duration analysis
        durations = [(b.end_time.hour - b.start_time.hour) for b in bookings]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Court type analysis
        court_types = [b.court.court_type for b in bookings if b.court]
        unique_court_types = list(set(court_types)) if court_types else []
        
        # Cost analysis
        costs = [b.court.hourly_rate * (b.end_time.hour - b.start_time.hour) for b in bookings if b.court]
        avg_cost = sum(costs) / len(costs) if costs else 0
        
        # Cancellation analysis
        cancelled = len([b for b in bookings if b.status == 'cancelled'])
        cancellation_rate = (cancelled / len(bookings) * 100) if bookings else 0
        
        return {
            'preferred_day': preferred_day,
            'preferred_time': preferred_time,
            'avg_duration': round(avg_duration, 1),
            'court_types': unique_court_types,
            'avg_cost': round(avg_cost, 2),
            'cancellation_rate': round(cancellation_rate, 1)
        }
    
    @staticmethod
    def _build_court_context(court_id):
        """Build comprehensive context about a court for AI analysis"""
        # Get court performance metrics
        total_bookings = Booking.query.filter_by(court_id=court_id).count()
        confirmed_bookings = Booking.query.filter_by(court_id=court_id, status='confirmed').count()
        recent_bookings = Booking.query.filter(
            Booking.court_id == court_id,
            Booking.created_at >= datetime.now() - timedelta(days=30)
        ).count()
        
        confirmation_rate = (confirmed_bookings / max(1, total_bookings)) * 100
        utilization_rate = min(100, (recent_bookings / 30) * 100)  # Simplified calculation
        
        # Get nearby competition
        court = Court.query.get(court_id)
        nearby_courts = Court.query.filter(
            Court.location.ilike(f'%{court.location}%'),
            Court.id != court_id
        ).count() if court else 0
        
        return {
            'total_bookings': total_bookings,
            'confirmation_rate': round(confirmation_rate, 1),
            'recent_bookings': recent_bookings,
            'utilization_rate': round(utilization_rate, 1),
            'nearby_courts': nearby_courts,
            'avg_rating': 4.2  # Would calculate from real reviews
        }
    
    @staticmethod
    def _gather_system_stats():
        """Gather system-wide statistics for trend analysis"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        new_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        total_bookings = Booking.query.filter(Booking.created_at >= thirty_days_ago).count()
        
        # Revenue calculation (simplified)
        from sqlalchemy import func
        revenue_query = db.session.query(
            func.sum(Court.hourly_rate * func.extract('hour', Booking.end_time - Booking.start_time))
        ).join(Booking).filter(
            Booking.status == 'confirmed',
            Booking.created_at >= thirty_days_ago
        ).scalar()
        revenue = revenue_query or 0
        
        # Popular locations
        location_stats = db.session.query(
            Court.location,
            func.count(Booking.id).label('booking_count')
        ).join(Booking).filter(
            Booking.created_at >= thirty_days_ago
        ).group_by(Court.location).order_by(
            func.count(Booking.id).desc()
        ).limit(3).all()
        
        popular_locations = [loc.location for loc in location_stats]
        
        # Peak times
        time_stats = db.session.query(
            func.extract('hour', Booking.start_time).label('hour'),
            func.count(Booking.id).label('booking_count')
        ).filter(
            Booking.created_at >= thirty_days_ago
        ).group_by(func.extract('hour', Booking.start_time)).order_by(
            func.count(Booking.id).desc()
        ).limit(3).all()
        
        peak_times = [f"{int(time.hour)}:00" for time in time_stats]
        
        return {
            'new_users': new_users,
            'total_bookings': total_bookings,
            'revenue': round(revenue, 2),
            'popular_locations': popular_locations or ['N/A'],
            'peak_times': peak_times or ['N/A'],
            'avg_duration': 1.5,  # Would calculate from real data
            'retention_rate': 75  # Would calculate from real user activity
        }