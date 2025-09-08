"""
AI Service for TennisMatchUp - Clean MVC Architecture
Integrates with Ollama for intelligent recommendations and chat assistance
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
                    "pros": "Traditional surface, unique playing style",
                    "cons": "High maintenance, weather sensitive", 
                    "recommended_for": ["advanced"]
                }
            },
            "skill_development": {
                "beginner": {
                    "focus": ["basic strokes", "footwork", "court positioning"],
                    "recommended_frequency": "2-3 times per week",
                    "session_duration": "60-90 minutes",
                    "practice_tips": [
                        "Focus on consistent contact point",
                        "Practice against a wall for repetition",
                        "Work on split step timing"
                    ]
                },
                "intermediate": {
                    "focus": ["spin techniques", "net play", "strategy"],
                    "recommended_frequency": "3-4 times per week", 
                    "session_duration": "90-120 minutes",
                    "practice_tips": [
                        "Incorporate drills with movement",
                        "Practice different shot combinations",
                        "Work on mental toughness"
                    ]
                },
                "advanced": {
                    "focus": ["advanced tactics", "match play", "physical conditioning"],
                    "recommended_frequency": "4-5 times per week",
                    "session_duration": "120+ minutes",
                    "practice_tips": [
                        "Analyze match videos",
                        "Practice under pressure situations",
                        "Focus on opponent weaknesses"
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
        
        return AIService.generate_response(prompt, temperature=0.6)
    
    @staticmethod
    def get_smart_court_recommendations(player_id):
        """RAG-Enhanced smart court recommendations"""
        player = Player.query.get(player_id)
        if not player:
            return "Player not found"
        
        # Get available courts
        available_courts = Court.query.filter_by(is_active=True).limit(5).all()
        if not available_courts:
            return "No courts available at this time."
        
        knowledge = AIService.load_tennis_knowledge()
        
        court_info = []
        for court in available_courts:
            court_info.append(f"Court: {court.name} - {court.surface} surface, ${court.hourly_rate}/hour, Location: {court.location}")
        
        prompt = f"""
        You are TennisCoach AI helping select the perfect court for a tennis player.
        
        PLAYER PROFILE:
        - Skill Level: {player.skill_level}
        - Location Preference: {getattr(player, 'preferred_location', 'Any')}
        
        AVAILABLE COURTS:
        {chr(10).join(court_info)}
        
        TENNIS KNOWLEDGE: {json.dumps(knowledge['court_types'], indent=2)}
        
        TASK: Recommend the top 2-3 courts that best match this player's needs. For each recommendation:
        1. Explain why this court suits their skill level
        2. Mention any surface-specific advantages
        3. Include cost considerations
        
        Keep recommendations practical and helpful.
        """
        
        return AIService.generate_response(prompt, temperature=0.6)
    
    @staticmethod
    def general_tennis_chat(user_message):
        """RAG-Enhanced general tennis chat"""
        knowledge = AIService.load_tennis_knowledge()
        
        prompt = f"""
        You are TennisCoach AI, an expert tennis advisor with access to comprehensive tennis knowledge.
        
        TENNIS KNOWLEDGE AVAILABLE:
        {json.dumps(knowledge, indent=2)}
        
        USER QUESTION: {user_message}
        
        TASK: Provide helpful tennis-related advice. If the question is not about tennis,
        politely redirect to tennis topics. Use the knowledge base to give accurate,
        helpful responses.
        
        Keep responses conversational and encouraging.
        """
        
        return AIService.generate_response(prompt, temperature=0.7)