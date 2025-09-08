"""
Clean AI Service for TennisMatchUp
Pure business logic layer with proper separation of concerns
RAG implementation with external knowledge base and prompt templates
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
from services.ai_prompts import TennisPrompts

class AIService:
    """AI-powered services using Ollama with RAG capabilities - Clean Architecture"""
    
    # Ollama configuration
    OLLAMA_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "phi3:mini"
    KNOWLEDGE_BASE_PATH = "services/tennis_knowledge.json"
    
    @staticmethod
    def is_ollama_available():
        """Check if Ollama service is running and accessible"""
        try:
            response = requests.get(f"{AIService.OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def load_tennis_knowledge(category=None, subcategory=None):
        """Load tennis knowledge base for RAG - Data Layer Access"""
        try:
            with open(AIService.KNOWLEDGE_BASE_PATH, 'r', encoding='utf-8') as f:
                knowledge = json.load(f)
            
            if category is None:
                return knowledge
            
            category_data = knowledge.get(category, {})
            
            if subcategory and isinstance(category_data, dict):
                return category_data.get(subcategory, {})
            
            return category_data
            
        except FileNotFoundError:
            return {"error": "Tennis knowledge base not found"}
        except json.JSONDecodeError:
            return {"error": "Invalid knowledge base format"}
    
    @staticmethod
    def generate_response(prompt, model=None, temperature=0.7):
        """Generate AI response using Ollama with enhanced error handling"""
        if not model:
            model = AIService.DEFAULT_MODEL
        
        if not AIService.is_ollama_available():
            return "AI service is currently unavailable. Please ensure Ollama is running on localhost:11434."
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
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
                return f"AI service error: HTTP {response.status_code}"
                
        except Exception as e:
            return f"AI service error: {str(e)}"
    
    @staticmethod
    def get_personalized_recommendations(player_id):
        """RAG-Enhanced personalized recommendations for a player"""
        player = Player.query.get(player_id)
        if not player:
            return "Player not found"
        
        # Build player data context
        player_data = {
            'name': player.user.full_name,
            'skill_level': player.skill_level,
            'playing_style': getattr(player, 'playing_style', 'all-court'),
            'location': player.preferred_location
        }
        
        # Gather activity context
        context_data = AIService._build_player_context(player_id)
        
        # Load relevant knowledge from external file
        skill_knowledge = AIService.load_tennis_knowledge("skill_development", player.skill_level)
        style_knowledge = AIService.load_tennis_knowledge("playing_styles", player_data['playing_style'])
        booking_knowledge = AIService.load_tennis_knowledge("booking_strategies")
        
        # Combine knowledge for RAG context
        knowledge_base = json.dumps({
            "skill_guidelines": skill_knowledge,
            "playing_style_info": style_knowledge,
            "booking_strategies": booking_knowledge
        }, indent=2)
        
        # Generate prompt using template
        prompt = TennisPrompts.get_personalized_recommendation_prompt(
            player_data, context_data, knowledge_base
        )
        
        return AIService.generate_response(prompt, temperature=0.6)
    
    @staticmethod
    def get_smart_court_recommendations(player_id, requested_date=None, time_preference=None):
        """RAG-Enhanced smart court recommendations"""
        player = Player.query.get(player_id)
        if not player:
            return "Player not found"
        
        # Get available courts
        available_courts = Court.query.filter_by(is_active=True).limit(8).all()
        if not available_courts:
            return "No courts available at this time."
        
        # Build player data
        player_data = {
            'skill_level': player.skill_level,
            'playing_style': getattr(player, 'playing_style', 'all-court'),
            'location': player.preferred_location
        }
        
        # Build court information with RAG context
        court_knowledge = AIService.load_tennis_knowledge("court_types")
        court_info_list = []
        
        for court in available_courts:
            surface = court.surface.lower() if court.surface else 'hard'
            surface_info = court_knowledge.get(surface, court_knowledge.get('hard', {}))
            
            court_info_list.append(f"""
            Court: {court.name}
            - Location: {court.location}
            - Surface: {court.surface} ({surface_info.get('description', 'Standard court')})
            - Rate: ${court.hourly_rate}/hour
            - Ideal for: {', '.join(surface_info.get('recommended_for', ['all levels']))}
            - Pros: {surface_info.get('pros', 'Good playing surface')}
            - Best conditions: {surface_info.get('ideal_conditions', 'Any weather')}
            """)
        
        # Build weather context
        current_time = datetime.now()
        season = "summer" if current_time.month in [6, 7, 8] else "winter" if current_time.month in [12, 1, 2] else "spring/fall"
        
        weather_context = f"""
        - Season: {season}
        - Requested Date: {requested_date or 'Today'}
        - Time Preference: {time_preference or 'Flexible'}
        """
        
        # Load relevant knowledge
        skill_knowledge = AIService.load_tennis_knowledge("skill_development", player.skill_level)
        weather_knowledge = AIService.load_tennis_knowledge("booking_strategies", "weather_considerations")
        
        knowledge_base = json.dumps({
            "court_types": court_knowledge,
            "skill_requirements": skill_knowledge,
            "weather_considerations": weather_knowledge
        }, indent=2)
        
        # Generate prompt
        prompt = TennisPrompts.get_court_recommendation_prompt(
            player_data, '\n'.join(court_info_list), weather_context, knowledge_base
        )
        
        return AIService.generate_response(prompt, temperature=0.5)
    
    @staticmethod
    def analyze_playing_pattern(player_id):
        """RAG-Enhanced playing pattern analysis"""
        player = Player.query.get(player_id)
        if not player:
            return "Player not found"
        
        # Get booking history
        bookings = Booking.query.filter_by(player_id=player_id).order_by(
            Booking.booking_date.desc()
        ).limit(20).all()
        
        player_data = {
            'name': player.user.full_name,
            'skill_level': player.skill_level,
            'playing_style': getattr(player, 'playing_style', 'all-court')
        }
        
        if not bookings:
            # Handle new players with RAG guidance
            skill_knowledge = AIService.load_tennis_knowledge("skill_development", player.skill_level)
            knowledge_base = json.dumps(skill_knowledge, indent=2)
            
            prompt = TennisPrompts.get_beginner_guidance_prompt(player_data, knowledge_base)
            return AIService.generate_response(prompt)
        
        # Analyze patterns
        booking_patterns = AIService._analyze_booking_patterns(bookings)
        
        # Load relevant knowledge
        skill_knowledge = AIService.load_tennis_knowledge("skill_development", player.skill_level)
        injury_knowledge = AIService.load_tennis_knowledge("injury_prevention")
        booking_knowledge = AIService.load_tennis_knowledge("booking_strategies")
        
        knowledge_base = json.dumps({
            "skill_guidelines": skill_knowledge,
            "injury_prevention": injury_knowledge,
            "booking_optimization": booking_knowledge
        }, indent=2)
        
        # Generate analysis prompt
        prompt = TennisPrompts.get_playing_pattern_analysis_prompt(
            player_data, booking_patterns, knowledge_base
        )
        
        return AIService.generate_response(prompt, temperature=0.6)
    
    @staticmethod
    def get_injury_prevention_advice(player_id):
        """RAG-Enhanced injury prevention advice"""
        player = Player.query.get(player_id)
        if not player:
            return "Player not found"
        
        # Get activity level
        recent_bookings = Booking.query.filter_by(player_id=player_id).filter(
            Booking.booking_date >= datetime.now().date() - timedelta(days=30)
        ).count()
        
        # Build player data
        player_data = {
            'skill_level': player.skill_level,
            'playing_style': getattr(player, 'playing_style', 'all-court')
        }
        
        # Load injury prevention knowledge
        injury_knowledge = AIService.load_tennis_knowledge("injury_prevention")
        skill_knowledge = AIService.load_tennis_knowledge("skill_development", player.skill_level)
        
        knowledge_base = json.dumps({
            "injury_prevention": injury_knowledge,
            "skill_level_considerations": skill_knowledge
        }, indent=2)
        
        # Generate prompt
        prompt = TennisPrompts.get_injury_prevention_prompt(
            player_data, recent_bookings, knowledge_base
        )
        
        return AIService.generate_response(prompt, temperature=0.5)
    
    @staticmethod
    def analyze_player_compatibility(player1_id, player2_id):
        """RAG-Enhanced player compatibility analysis"""
        player1 = Player.query.get(player1_id)
        player2 = Player.query.get(player2_id)
        
        if not player1 or not player2:
            return "One or both players not found"
        
        # Build player data
        player1_data = {
            'name': player1.user.full_name,
            'skill_level': player1.skill_level,
            'playing_style': getattr(player1, 'playing_style', 'all-court')
        }
        
        player2_data = {
            'name': player2.user.full_name,
            'skill_level': player2.skill_level,
            'playing_style': getattr(player2, 'playing_style', 'all-court')
        }
        
        # Calculate compatibility using existing MatchingEngine
        compatibility_score = MatchingEngine.calculate_compatibility_score(player1, player2)
        
        # Load playing style knowledge
        style_knowledge = AIService.load_tennis_knowledge("playing_styles")
        skill_knowledge = AIService.load_tennis_knowledge("skill_development")
        
        knowledge_base = json.dumps({
            "playing_styles": style_knowledge,
            "skill_development": skill_knowledge
        }, indent=2)
        
        # Generate prompt
        prompt = TennisPrompts.get_compatibility_analysis_prompt(
            player1_data, player2_data, compatibility_score, knowledge_base
        )
        
        return AIService.generate_response(prompt, temperature=0.6)
    
    @staticmethod
    def analyze_system_trends():
        """RAG-Enhanced system trends analysis for admin dashboard"""
        if not AIService.is_ollama_available():
            return "AI analysis unavailable - Ollama not running"
        
        # Gather system statistics
        system_stats = AIService._gather_system_stats()
        
        # Load business knowledge
        booking_knowledge = AIService.load_tennis_knowledge("booking_strategies")
        
        knowledge_base = json.dumps({
            "booking_strategies": booking_knowledge,
            "business_intelligence": {
                "industry_standards": "Tennis facilities typically see 60-80% utilization",
                "peak