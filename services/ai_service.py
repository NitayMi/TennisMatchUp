"""
Enhanced AI Service for TennisMatchUp - Action Agent Implementation
Combines existing advisory functions with real platform action execution
Integrates with MatchingEngine and RuleEngine for actionable proposals
"""
import requests
import json
import os
from datetime import datetime, timedelta
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court, Booking
from services.matching_engine import MatchingEngine
from services.rule_engine import RuleEngine

class AIService:
    """AI-powered services using Ollama with RAG capabilities"""
    
    # Ollama configuration
    OLLAMA_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "phi3:mini"
    
    @staticmethod
    def is_ollama_available():
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{AIService.OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def load_tennis_knowledge():
        """Load tennis knowledge base for RAG"""
        return {
            "court_types": {
                "hard": {
                    "description": "Most common surface, medium pace",
                    "pros": "Consistent bounce, all-weather play",
                    "cons": "Can be tough on joints",
                    "recommended_for": ["beginner", "intermediate", "advanced"]
                },
                "clay": {
                    "description": "Slow surface, high bounce", 
                    "pros": "Easier on joints, favors defensive play",
                    "cons": "Weather dependent, requires maintenance",
                    "recommended_for": ["intermediate", "advanced"]
                },
                "grass": {
                    "description": "Fast surface, low bounce",
                    "pros": "Traditional tennis, favors serve-and-volley",
                    "cons": "High maintenance, weather sensitive", 
                    "recommended_for": ["advanced", "professional"]
                }
            },
            "skill_levels": {
                "beginner": {
                    "characteristics": ["Learning basic strokes", "Developing consistency"],
                    "focus_areas": ["Footwork", "Basic technique", "Court positioning"],
                    "recommendations": [
                        "Practice wall hitting for consistency",
                        "Focus on proper grip and stance",
                        "Take lessons to build foundation"
                    ]
                },
                "intermediate": {
                    "characteristics": ["Consistent basic strokes", "Understanding strategy"],
                    "focus_areas": ["Shot placement", "Mental game", "Fitness"],
                    "recommendations": [
                        "Work on shot variety and spin",
                        "Develop tactical awareness",
                        "Practice under pressure situations"
                    ]
                }
            },
            "playing_styles": {
                "aggressive": {
                    "description": "Offensive baseline player",
                    "strengths": ["powerful shots", "quick points"],
                    "partner_compatibility": ["defensive", "all-court"]
                },
                "defensive": {
                    "description": "Patient, counter-attacking player",
                    "strengths": ["consistency", "court coverage"],
                    "partner_compatibility": ["aggressive", "all-court"]
                },
                "all-court": {
                    "description": "Versatile player comfortable anywhere",
                    "strengths": ["adaptability", "variety"],
                    "partner_compatibility": ["any"]
                }
            },
            "booking_strategies": {
                "peak_hours": ["17:00-20:00", "weekend_mornings"],
                "off_peak_savings": "Book weekday mornings for 20-30% savings",
                "weather_considerations": {
                    "sunny": "Book early morning or late afternoon",
                    "cloudy": "Ideal conditions, book anytime",
                    "windy": "Indoor courts recommended"
                }
            }
        }
    
    @staticmethod
    def generate_response(prompt, model=None, temperature=0.7):
        """Generate AI response using Ollama"""
        if model is None:
            model = AIService.DEFAULT_MODEL
            
        if not AIService.is_ollama_available():
            return "AI service unavailable. Please ensure Ollama is running on localhost:11434."
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "max_tokens": 100
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
                return f"AI service error: HTTP {response.status_code}"
                
        except Exception as e:
            return f"AI service error: {str(e)}"
    
    @staticmethod  
    def _build_player_context(player_id):
        """Build context for player-specific recommendations"""
        player = Player.query.get(player_id)
        if not player:
            return {}
            
        recent_bookings = Booking.query.filter_by(player_id=player_id).filter(
            Booking.booking_date >= datetime.now().date() - timedelta(days=30)
        ).count()
        
        return {
            'recent_bookings': recent_bookings,
            'activity_summary': f'Active player with {recent_bookings} bookings this month'
        }
    
    # ===== EXISTING ADVISORY FUNCTIONS (KEEP UNCHANGED) =====
    
    @staticmethod
    def get_personalized_recommendations(player_id):
        """RAG-Enhanced personalized recommendations for a player"""
        player = Player.query.get(player_id)
        if not player:
            return "Player not found"
        
        context = AIService._build_player_context(player_id) 
        knowledge = AIService.load_tennis_knowledge()
        
        prompt = f"""
        You are TennisCoach AI, an expert tennis advisor.
        
        PLAYER PROFILE:
        - Name: {player.user.full_name}
        - Skill Level: {player.skill_level}
        - Recent Activity: {context.get('recent_bookings', 0)} bookings in last 30 days
        
        TENNIS KNOWLEDGE: {json.dumps(knowledge, indent=2)}
        
        TASK: Provide 3 personalized tennis recommendations:
        1. Skill improvement suggestion
        2. Booking strategy advice  
        3. Playing partner recommendation
        
        Keep advice practical and encouraging.
        """
        
        return AIService.generate_response(prompt)
    
    @staticmethod
    def get_smart_court_recommendations(player_id):
        """Smart court selection advice"""
        player = Player.query.get(player_id)
        if not player:
            return "Player not found"
        
        context = AIService._build_player_context(player_id)
        knowledge = AIService.load_tennis_knowledge()
        
        prompt = f"""
        You are TennisCoach AI, an expert court advisor.
        
        PLAYER PROFILE:
        - Skill Level: {player.skill_level}
        - Location: {player.preferred_location}
        - Activity: {context.get('recent_bookings', 0)} bookings this month
        
        COURT KNOWLEDGE: {json.dumps(knowledge['court_types'], indent=2)}
        
        TASK: Recommend the best court types and booking strategies for this player.
        Include specific advice on timing, surface selection, and cost optimization.
        """
        
        return AIService.generate_response(prompt)
    
    @staticmethod
    def general_tennis_chat(user_message):
        """General tennis chat with knowledge"""
        knowledge = AIService.load_tennis_knowledge()
        
        prompt = f"""
        You are TennisCoach AI, a helpful tennis expert.
        
        USER QUESTION: {user_message}
        
        TENNIS KNOWLEDGE: {json.dumps(knowledge, indent=2)}
        
        TASK: Answer the user's tennis question using the knowledge base.
        Be conversational, helpful, and encouraging.
        """
        
        return AIService.generate_response(prompt)
    
    # ===== NEW ACTION FUNCTIONS =====
    
    @staticmethod
    def find_available_players(player_id, location=None, date_str=None, time_str=None, skill_level=None):
        """Execute real player search with availability check"""
        try:
            current_player = Player.query.get(player_id)
            if not current_player:
                return {'error': 'Player not found'}
            
            # Use existing MatchingEngine for robust search
            search_location = location or current_player.preferred_location
            search_skill = skill_level or current_player.skill_level
            
            matches = MatchingEngine.find_matches(
                player_id=player_id,
                skill_level=search_skill,
                location=search_location,
                limit=5
            )
            
            # Format results for AI presentation
            player_results = []
            for match in matches[:3]:  # Top 3 matches
                player_results.append({
                    'name': match['player'].user.full_name,
                    'skill_level': match['player'].skill_level,
                    'location': match['player'].preferred_location,
                    'compatibility_score': match['compatibility_score'],
                    'distance': f"{match['distance']:.1f}km" if match['distance'] else "Location match",
                    'player_id': match['player'].id
                })
            
            return {
                'success': True,
                'players_found': player_results,
                'search_params': {
                    'location': search_location,
                    'skill_level': search_skill,
                    'date': date_str,
                    'time': time_str
                }
            }
            
        except Exception as e:
            return {'error': f'Player search failed: {str(e)}'}
    
    @staticmethod
    def find_available_courts(player_id, location=None, date_str=None, time_range=None):
        """Execute real court availability search"""
        try:
            current_player = Player.query.get(player_id)
            if not current_player:
                return {'error': 'Player not found'}
            
            # Use existing MatchingEngine court recommendations
            search_location = location or current_player.preferred_location
            
            courts = MatchingEngine.recommend_courts(
                player_id=player_id,
                location=search_location,
                limit=5
            )
            
            # Format results for AI presentation
            court_results = []
            for court in courts[:3]:  # Top 3 courts
                court_results.append({
                    'name': court.name,
                    'location': court.location,
                    'surface_type': court.surface_type,
                    'hourly_rate': float(court.hourly_rate),
                    'court_id': court.id,
                    'availability_note': f"Available {time_range}" if time_range else "Check availability"
                })
            
            return {
                'success': True,
                'courts_found': court_results,
                'search_params': {
                    'location': search_location,
                    'date': date_str,
                    'time_range': time_range
                }
            }
            
        except Exception as e:
            return {'error': f'Court search failed: {str(e)}'}
    
    @staticmethod
    def create_match_proposal(player_id, target_player_id, court_id, datetime_str):
        """Generate actionable match proposal"""
        try:
            current_player = Player.query.get(player_id)
            target_player = Player.query.get(target_player_id)
            court = Court.query.get(court_id)
            
            if not all([current_player, target_player, court]):
                return {'error': 'Invalid player or court ID'}
            
            # Validate using RuleEngine
            validation = RuleEngine.validate_player_matching(player_id, target_player_id)
            if not validation['valid']:
                return {'error': f'Match not allowed: {validation["reason"]}'}
            
            proposal = {
                'proposal_id': f"match_{player_id}_{target_player_id}_{court_id}",
                'current_player': {
                    'name': current_player.user.full_name,
                    'skill': current_player.skill_level
                },
                'target_player': {
                    'name': target_player.user.full_name,
                    'skill': target_player.skill_level,
                    'id': target_player_id
                },
                'court': {
                    'name': court.name,
                    'location': court.location,
                    'surface': court.surface_type,
                    'rate': float(court.hourly_rate),
                    'id': court_id
                },
                'datetime': datetime_str,
                'estimated_cost': float(court.hourly_rate * 2),  # Assume 2-hour booking
                'action_type': 'SEND_MATCH_REQUEST'
            }
            
            return {
                'success': True,
                'proposal': proposal
            }
            
        except Exception as e:
            return {'error': f'Proposal creation failed: {str(e)}'}
    
    @staticmethod
    def process_action_request(user_message, player_id):
        """Parse user intent and execute appropriate actions"""
        try:
            player = Player.query.get(player_id)
            if not player:
                return {'error': 'Player not found'}
            
            # Simple intent detection (can be enhanced with more sophisticated NLP)
            message_lower = user_message.lower()
            
            if any(word in message_lower for word in ['find', 'partner', 'player', 'match']):
                # Extract location if mentioned
                location = None
                for word in message_lower.split():
                    if word in ['rishon', 'tel', 'aviv', 'jerusalem', 'haifa']:
                        location = word.title()
                        break
                
                # Extract skill preference
                skill_level = None
                if 'beginner' in message_lower:
                    skill_level = 'beginner'
                elif 'intermediate' in message_lower:
                    skill_level = 'intermediate'
                elif 'advanced' in message_lower:
                    skill_level = 'advanced'
                
                return AIService.find_available_players(
                    player_id=player_id,
                    location=location,
                    skill_level=skill_level
                )
            
            elif any(word in message_lower for word in ['court', 'book', 'reserve']):
                location = None
                for word in message_lower.split():
                    if word in ['rishon', 'tel', 'aviv', 'jerusalem', 'haifa']:
                        location = word.title()
                        break
                
                return AIService.find_available_courts(
                    player_id=player_id,
                    location=location
                )
            
            else:
                # Default to general chat
                return {
                    'action_type': 'GENERAL_CHAT',
                    'response': AIService.general_tennis_chat(user_message)
                }
                
        except Exception as e:
            return {'error': f'Action processing failed: {str(e)}'}
    
    @staticmethod
    def check_schedule_conflicts(player_id, proposed_datetime):
        """Verify user availability for proposed time"""
        try:
            # Parse datetime string to datetime object
            proposed_dt = datetime.fromisoformat(proposed_datetime.replace('Z', '+00:00'))
            proposed_date = proposed_dt.date()
            proposed_hour = proposed_dt.hour
            
            # Check for existing bookings
            existing_bookings = Booking.query.filter(
                Booking.player_id == player_id,
                Booking.booking_date == proposed_date,
                Booking.start_time <= proposed_hour + 2,  # 2-hour buffer
                Booking.end_time >= proposed_hour
            ).all()
            
            if existing_bookings:
                return {
                    'conflict': True,
                    'message': f'You have {len(existing_bookings)} booking(s) around that time'
                }
            
            return {
                'conflict': False,
                'message': 'Time slot appears available'
            }
            
        except Exception as e:
            return {
                'conflict': True,
                'message': f'Could not check schedule: {str(e)}'
            }