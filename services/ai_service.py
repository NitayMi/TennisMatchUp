"""
Enhanced AI Service for TennisMatchUp
Combines existing functionality with RAG (Retrieval-Augmented Generation)
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
    
    # Ollama configuration - Updated for phi3:mini
    OLLAMA_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "phi3:mini"  # Updated to use your installed model
    
    # Tennis Knowledge Base for RAG
    TENNIS_KNOWLEDGE = {
        "court_types": {
            "hard": {
                "description": "Most common surface, medium pace",
                "pros": "Consistent bounce, all-weather play",
                "cons": "Can be tough on joints with extended play",
                "recommended_for": ["beginner", "intermediate", "advanced"],
                "ideal_conditions": "Year-round, any weather",
                "maintenance": "Low maintenance required",
                "ball_behavior": "Medium bounce, predictable trajectory"
            },
            "clay": {
                "description": "Slow surface, high bounce", 
                "pros": "Easier on joints, favors defensive play, teaches patience",
                "cons": "Weather dependent, requires regular maintenance",
                "recommended_for": ["intermediate", "advanced"],
                "ideal_conditions": "Dry weather, no wind",
                "maintenance": "Daily watering and brushing required",
                "ball_behavior": "High bounce, slower pace, more spin-friendly"
            },
            "grass": {
                "description": "Fast surface, low bounce",
                "pros": "Traditional surface, unique playing style, elegant game",
                "cons": "High maintenance, weather sensitive, limited availability", 
                "recommended_for": ["advanced", "professional"],
                "ideal_conditions": "Dry, mild weather",
                "maintenance": "Extensive daily care required",
                "ball_behavior": "Low bounce, fast pace, unpredictable bounces"
            },
            "indoor": {
                "description": "Controlled environment, consistent conditions",
                "pros": "Weather independent, consistent lighting, no wind",
                "cons": "Can feel confined, different air circulation",
                "recommended_for": ["all levels"],
                "ideal_conditions": "Any weather, year-round",
                "maintenance": "Climate control required",
                "ball_behavior": "Slightly slower due to air circulation"
            }
        },
        "skill_development": {
            "beginner": {
                "focus": ["basic strokes", "footwork", "court positioning", "serve technique"],
                "recommended_frequency": "2-3 times per week",
                "session_duration": "60-90 minutes",
                "practice_tips": [
                    "Focus on consistent contact point",
                    "Practice against a wall for repetition",
                    "Work on split step timing",
                    "Master the ready position",
                    "Start with slower balls"
                ],
                "common_mistakes": ["rushing shots", "poor grip", "wrong stance"],
                "progression_goals": "Develop muscle memory and basic consistency"
            },
            "intermediate": {
                "focus": ["spin techniques", "net play", "strategy", "shot variety"],
                "recommended_frequency": "3-4 times per week", 
                "session_duration": "90-120 minutes",
                "practice_tips": [
                    "Incorporate drills with movement",
                    "Practice different shot combinations",
                    "Work on mental toughness",
                    "Study opponent weaknesses",
                    "Develop signature shots"
                ],
                "common_mistakes": ["overplaying", "poor shot selection", "inconsistent serve"],
                "progression_goals": "Tactical awareness and shot consistency under pressure"
            },
            "advanced": {
                "focus": ["advanced tactics", "match play", "physical conditioning", "mental game"],
                "recommended_frequency": "4-5 times per week",
                "session_duration": "120+ minutes",
                "practice_tips": [
                    "Analyze match videos regularly",
                    "Practice under pressure situations",
                    "Focus on opponent's weaknesses",
                    "Develop multiple game styles",
                    "Work with coach on strategy"
                ],
                "common_mistakes": ["overconfidence", "neglecting basics", "poor fitness"],
                "progression_goals": "Tournament readiness and advanced match strategy"
            },
            "professional": {
                "focus": ["peak performance", "competition strategy", "injury prevention"],
                "recommended_frequency": "Daily training",
                "session_duration": "Multiple sessions per day",
                "practice_tips": [
                    "Periodized training cycles",
                    "Mental performance coaching",
                    "Advanced analytics review",
                    "Recovery and nutrition focus"
                ],
                "common_mistakes": ["overtraining", "neglecting recovery"],
                "progression_goals": "Peak competitive performance"
            }
        },
        "playing_styles": {
            "aggressive": {
                "description": "Offensive baseline player who seeks to control points",
                "strengths": ["powerful shots", "quick points", "intimidation factor"],
                "court_preference": ["hard", "grass"],
                "partner_compatibility": ["defensive", "all-court"],
                "recommended_strategy": "Take balls early, move forward when possible",
                "fitness_focus": "Power and explosive movements"
            },
            "defensive": {
                "description": "Patient, counter-attacking player with excellent court coverage",
                "strengths": ["consistency", "court coverage", "mental toughness"],
                "court_preference": ["clay", "hard"],
                "partner_compatibility": ["aggressive", "all-court"],
                "recommended_strategy": "Extend rallies, wait for opponent errors",
                "fitness_focus": "Endurance and lateral movement"
            },
            "all-court": {
                "description": "Versatile player comfortable anywhere on court",
                "strengths": ["adaptability", "variety", "tactical intelligence"],
                "court_preference": ["any"],
                "partner_compatibility": ["any"],
                "recommended_strategy": "Adapt to opponent and conditions",
                "fitness_focus": "Overall athleticism and flexibility"
            },
            "serve-volley": {
                "description": "Attacking player who follows serve to net",
                "strengths": ["quick points", "pressure on opponent", "net skills"],
                "court_preference": ["grass", "hard"],
                "partner_compatibility": ["baseline players"],
                "recommended_strategy": "Strong serve followed by aggressive net play",
                "fitness_focus": "Quick reactions and forward movement"
            }
        },
        "booking_strategies": {
            "peak_hours": {
                "times": ["17:00-20:00", "weekend_mornings", "7:00-9:00"],
                "pricing": "highest rates",
                "availability": "limited",
                "booking_tips": "Book 1-2 weeks in advance"
            },
            "off_peak_savings": {
                "description": "Book weekday mornings or afternoons for 20-40% savings",
                "best_times": ["10:00-15:00 weekdays", "late evening"],
                "savings": "20-40% off peak rates"
            },
            "weather_considerations": {
                "sunny": {
                    "advice": "Book early morning (7-9 AM) or late afternoon (5-7 PM)",
                    "avoid": "midday sessions in summer"
                },
                "cloudy": {
                    "advice": "Ideal conditions, book anytime",
                    "benefits": "consistent lighting, comfortable temperature"
                },
                "windy": {
                    "advice": "Indoor courts recommended, or sheltered outdoor courts",
                    "playing_tips": "adjust shot trajectory, use heavier balls"
                },
                "rainy": {
                    "advice": "Indoor courts only",
                    "alternatives": "practice serves and fitness training"
                }
            }
        },
        "injury_prevention": {
            "common_injuries": {
                "tennis_elbow": {
                    "prevention": "proper grip size, technique work, strength training",
                    "warning_signs": "elbow pain after playing"
                },
                "shoulder_issues": {
                    "prevention": "proper serve technique, rotator cuff strengthening",
                    "warning_signs": "shoulder pain during serve"
                },
                "knee_problems": {
                    "prevention": "proper footwork, court shoes, quadriceps strengthening",
                    "warning_signs": "knee pain during lateral movement"
                }
            },
            "warm_up": {
                "duration": "10-15 minutes",
                "components": ["light cardio", "dynamic stretching", "shadow swings"]
            },
            "cool_down": {
                "duration": "10 minutes",
                "components": ["static stretching", "hydration", "ice if needed"]
            }
        }
    }
    
    @staticmethod
    def is_ollama_available():
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{AIService.OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
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
    def get_tennis_knowledge(category=None, subcategory=None):
        """Retrieve specific tennis knowledge for RAG"""
        if category is None:
            return AIService.TENNIS_KNOWLEDGE
        
        knowledge = AIService.TENNIS_KNOWLEDGE.get(category, {})
        
        if subcategory and isinstance(knowledge, dict):
            return knowledge.get(subcategory, {})
        
        return knowledge
    
    @staticmethod
    def get_personalized_recommendations(player_id):
        """RAG-Enhanced personalized recommendations for a player"""
        player = Player.query.get(player_id)
        if not player:
            return "Player not found"
        
        # Gather player context
        context = AIService._build_player_context(player_id)
        
        # Get relevant knowledge from RAG
        skill_knowledge = AIService.get_tennis_knowledge("skill_development", player.skill_level)
        playing_style = getattr(player, 'playing_style', 'all-court')
        style_knowledge = AIService.get_tennis_knowledge("playing_styles", playing_style)
        booking_knowledge = AIService.get_tennis_knowledge("booking_strategies")
        
        # Enhanced RAG prompt with structured knowledge
        prompt = f"""
        You are TennisCoach AI, an expert tennis advisor with access to comprehensive tennis knowledge.
        
        PLAYER PROFILE:
        - Name: {player.user.full_name}
        - Skill Level: {player.skill_level}
        - Playing Style: {playing_style}
        - Preferred Location: {player.preferred_location or 'Not specified'}
        - Recent Activity: {context['recent_bookings']} bookings in last 30 days
        - Activity Level: {context['activity_summary']}
        
        TENNIS KNOWLEDGE BASE (for your reference):
        
        Skill Development Guidelines for {player.skill_level}:
        - Focus Areas: {', '.join(skill_knowledge.get('focus', []))}
        - Recommended Frequency: {skill_knowledge.get('recommended_frequency', 'Not specified')}
        - Session Duration: {skill_knowledge.get('session_duration', 'Not specified')}
        - Practice Tips: {'; '.join(skill_knowledge.get('practice_tips', []))}
        
        Playing Style Analysis for {playing_style}:
        - Description: {style_knowledge.get('description', 'Versatile player')}
        - Strengths: {', '.join(style_knowledge.get('strengths', []))}
        - Recommended Strategy: {style_knowledge.get('recommended_strategy', 'Adapt to situation')}
        
        Booking Strategy Insights:
        - Peak Hours: {', '.join(booking_knowledge.get('peak_hours', {}).get('times', []))}
        - Off-Peak Savings: {booking_knowledge.get('off_peak_savings', {}).get('description', 'Book during less popular times')}
        
        TASK: Based on this player profile and tennis knowledge, provide 4 specific, actionable recommendations:
        1. Playing technique improvement based on their skill level
        2. Strategic booking advice for better court access
        3. Training routine optimization
        4. Partner matching strategy
        
        Make each recommendation specific, practical, and tailored to their profile and activity level.
        """
        
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
        
        # Get court knowledge from RAG
        court_knowledge = AIService.get_tennis_knowledge("court_types")
        weather_knowledge = AIService.get_tennis_knowledge("booking_strategies", "weather_considerations")
        skill_knowledge = AIService.get_tennis_knowledge("skill_development", player.skill_level)
        
        # Build court information with RAG context
        court_info = []
        for court in available_courts:
            surface = court.surface.lower() if court.surface else 'hard'
            surface_info = court_knowledge.get(surface, court_knowledge.get('hard', {}))
            
            court_info.append(f"""
            Court: {court.name}
            - Location: {court.location}
            - Surface: {court.surface} ({surface_info.get('description', 'Standard court')})
            - Rate: ${court.hourly_rate}/hour
            - Ideal for: {', '.join(surface_info.get('recommended_for', ['all levels']))}
            - Pros: {surface_info.get('pros', 'Good playing surface')}
            - Best conditions: {surface_info.get('ideal_conditions', 'Any weather')}
            """)
        
        # Enhanced prompt with weather and timing considerations
        current_time = datetime.now()
        season = "summer" if current_time.month in [6, 7, 8] else "winter" if current_time.month in [12, 1, 2] else "spring/fall"
        
        prompt = f"""
        You are TennisCoach AI helping select the perfect court for a tennis player.
        
        PLAYER PROFILE:
        - Skill Level: {player.skill_level}
        - Playing Style: {getattr(player, 'playing_style', 'versatile')}
        - Location Preference: {player.preferred_location or 'No preference'}
        
        AVAILABLE COURTS:
        {chr(10).join(court_info)}
        
        CURRENT CONDITIONS:
        - Season: {season}
        - Requested Date: {requested_date or 'Today'}
        - Time Preference: {time_preference or 'Flexible'}
        
        TENNIS KNOWLEDGE FOR RECOMMENDATIONS:
        
        Player Skill Requirements:
        - Focus Areas: {', '.join(skill_knowledge.get('focus', []))}
        - Session Goals: {skill_knowledge.get('progression_goals', 'Skill development')}
        
        Weather Considerations:
        - Sunny conditions: {weather_knowledge.get('sunny', {}).get('advice', 'Avoid peak sun hours')}
        - Indoor benefits: {court_knowledge.get('indoor', {}).get('pros', 'Weather independent')}
        
        TASK: Recommend the top 2-3 courts that best match this player's needs. For each recommendation:
        1. Explain why this court suits their skill level and style
        2. Mention any surface-specific advantages
        3. Suggest optimal playing times
        4. Include any cost-saving tips
        
        Prioritize courts that align with their skill development needs and location preferences.
        """
        
        return AIService.generate_response(prompt, temperature=0.5)
    
    @staticmethod
    def analyze_playing_pattern(player_id):
        """RAG-Enhanced playing pattern analysis"""
        player = Player.query.get(player_id)
        if not player:
            return "Player not found"
        
        # Get booking history with more detail
        bookings = Booking.query.filter_by(player_id=player_id).order_by(
            Booking.booking_date.desc()
        ).limit(20).all()
        
        if not bookings:
            # Use RAG to provide guidance for new players
            skill_knowledge = AIService.get_tennis_knowledge("skill_development", player.skill_level)
            prompt = f"""
            This is a new {player.skill_level} tennis player who hasn't made any bookings yet.
            
            Based on tennis knowledge for {player.skill_level} players:
            - Recommended frequency: {skill_knowledge.get('recommended_frequency', '2-3 times per week')}
            - Session duration: {skill_knowledge.get('session_duration', '60-90 minutes')}
            - Focus areas: {', '.join(skill_knowledge.get('focus', []))}
            
            Provide specific advice for getting started with regular tennis play.
            """
            return AIService.generate_response(prompt)
        
        # Analyze patterns with RAG context
        booking_patterns = AIService._analyze_booking_patterns(bookings)
        skill_knowledge = AIService.get_tennis_knowledge("skill_development", player.skill_level)
        injury_knowledge = AIService.get_tennis_knowledge("injury_prevention")
        
        prompt = f"""
        Analyze this tennis player's playing patterns using expert knowledge:
        
        PLAYER: {player.user.full_name} ({player.skill_level} level)
        
        BOOKING ANALYSIS:
        - Total bookings analyzed: {len(bookings)}
        - Preferred day: {booking_patterns.get('preferred_day', 'Varies')}
        - Preferred time: {booking_patterns.get('preferred_time', 'Varies')}
        - Booking frequency: {booking_patterns.get('frequency', 'Irregular')}
        - Favorite courts: {', '.join(booking_patterns.get('favorite_courts', ['None yet']))}
        - Average session cost: ${booking_patterns.get('avg_cost', 0):.0f}
        
        SKILL LEVEL GUIDELINES:
        - Recommended frequency for {player.skill_level}: {skill_knowledge.get('recommended_frequency', '2-3 times per week')}
        - Optimal session duration: {skill_knowledge.get('session_duration', '60-90 minutes')}
        - Development focus: {', '.join(skill_knowledge.get('focus', []))}
        
        INJURY PREVENTION INSIGHTS:
        - Warm-up importance: {injury_knowledge.get('warm_up', {}).get('duration', '10-15 minutes')} recommended
        - Recovery considerations: {injury_knowledge.get('cool_down', {}).get('duration', '10 minutes')} cool-down
        
        TASK: Provide insights on:
        1. How their current pattern aligns with their skill level needs
        2. Optimization suggestions for frequency and timing
        3. Cost-effectiveness of their booking choices
        4. Health and injury prevention recommendations
        5. Progression suggestions based on their activity level
        """
        
        return AIService.generate_response(prompt, temperature=0.6)
    
    @staticmethod
    def get_injury_prevention_advice(player_id):
        """RAG-Enhanced injury prevention advice"""
        player = Player.query.get(player_id)
        if not player:
            return "Player not found"
        
        # Get playing frequency
        recent_bookings = Booking.query.filter_by(player_id=player_id).filter(
            Booking.booking_date >= datetime.now().date() - timedelta(days=30)
        ).count()
        
        # Get injury prevention knowledge from RAG
        injury_knowledge = AIService.get_tennis_knowledge("injury_prevention")
        skill_knowledge = AIService.get_tennis_knowledge("skill_development", player.skill_level)
        
        prompt = f"""
        Provide injury prevention advice for a tennis player using expert knowledge:
        
        PLAYER PROFILE:
        - Skill Level: {player.skill_level}
        - Monthly Playing Frequency: {recent_bookings} sessions
        - Age Group: {getattr(player, 'age_group', 'Adult')}
        
        INJURY PREVENTION KNOWLEDGE:
        
        Common Tennis Injuries:
        {json.dumps(injury_knowledge.get('common_injuries', {}), indent=2)}
        
        Warm-up Protocol:
        - Duration: {injury_knowledge.get('warm_up', {}).get('duration', '10-15 minutes')}
        - Components: {', '.join(injury_knowledge.get('warm_up', {}).get('components', []))}
        
        Cool-down Protocol:
        - Duration: {injury_knowledge.get('cool_down', {}).get('duration', '10 minutes')}
        - Components: {', '.join(injury_knowledge.get('cool_down', {}).get('components', []))}
        
        Skill Level Considerations:
        - Common mistakes for {player.skill_level}: {', '.join(skill_knowledge.get('common_mistakes', []))}
        - Focus areas: {', '.join(skill_knowledge.get('focus', []))}
        
        TASK: Provide personalized advice covering:
        1. Specific injury risks for their playing frequency and skill level
        2. Customized warm-up routine (5-7 exercises)
        3. Post-play recovery recommendations
        4. Technique adjustments to prevent common injuries
        5. Warning signs to watch for
        
        Make recommendations specific to their activity level and skill progression.
        """
        
        return AIService.generate_response(prompt, temperature=0.5)
    
    @staticmethod
    def analyze_player_compatibility(player1_id, player2_id):
        """RAG-Enhanced player compatibility analysis"""
        player1 = Player.query.get(player1_id)
        player2 = Player.query.get(player2_id)
        
        if not player1 or not player2:
            return "One or both players not found"
        
        # Get playing style knowledge from RAG
        style1 = getattr(player1, 'playing_style', 'all-court')
        style2 = getattr(player2, 'playing_style', 'all-court')
        
        style1_knowledge = AIService.get_tennis_knowledge("playing_styles", style1)
        style2_knowledge = AIService.get_tennis_knowledge("playing_styles", style2)
        
        skill1_knowledge = AIService.get_tennis_knowledge("skill_development", player1.skill_level)
        skill2_knowledge = AIService.get_tennis_knowledge("skill_development", player2.skill_level)
        
        # Calculate compatibility using existing MatchingEngine
        compatibility_score = MatchingEngine.calculate_compatibility_score(player1, player2)
        
        prompt = f"""
        Analyze compatibility between two tennis players using expert knowledge:
        
        PLAYER 1: {player1.user.full_name}
        - Skill Level: {player1.skill_level}
        - Playing Style: {style1}
        - Style Strengths: {', '.join(style1_knowledge.get('strengths', []))}
        - Compatible With: {', '.join(style1_knowledge.get('partner_compatibility', []))}
        - Focus Areas: {', '.join(skill1_knowledge.get('focus', []))}
        
        PLAYER 2: {player2.user.full_name}
        - Skill Level: {player2.skill_level}
        - Playing Style: {style2}
        - Style Strengths: {', '.join(style2_knowledge.get('strengths', []))}
        - Compatible With: {', '.join(style2_knowledge.get('partner_compatibility', []))}
        - Focus Areas: {', '.join(skill2_knowledge.get('focus', []))}
        
        CALCULATED COMPATIBILITY: {compatibility_score}%
        
        TASK: Provide detailed compatibility analysis including:
        1. Playing style compatibility explanation
        2. Skill level match assessment
        3. Mutual learning opportunities
        4. Recommended playing format (singles/doubles)
        5. Potential challenges and how to address them
        6. Court surface recommendations for their combined styles
        
        Give specific advice for maximizing their playing experience together.
        """
        
        return AIService.generate_response(prompt, temperature=0.6)
    
    @staticmethod
    def analyze_system_trends():
        """RAG-Enhanced system trends analysis for admin dashboard"""
        if not AIService.is_ollama_available():
            return "AI analysis unavailable - Ollama not running"
        
        # Gather enhanced system statistics
        stats = AIService._gather_system_stats()
        
        # Get booking strategy knowledge for insights
        booking_knowledge = AIService.get_tennis_knowledge("booking_strategies")
        
        prompt = f"""
        Analyze tennis platform trends using business intelligence and tennis industry knowledge:
        
        SYSTEM STATISTICS (Last 30 Days):
        - New users: {stats['new_users']}
        - Total bookings: {stats['total_bookings']}
        - Revenue: ${stats['revenue']}
        - Most popular locations: {', '.join(stats['popular_locations'])}
        - Peak booking times: {', '.join(stats['peak_times'])}
        - Average booking duration: {stats['avg_duration']} hours
        - User retention rate: {stats['retention_rate']}%
        - Court utilization: {stats.get('court_utilization', 'N/A')}%
        
        TENNIS INDUSTRY KNOWLEDGE:
        - Peak Hours Typically: {', '.join(booking_knowledge.get('peak_hours', {}).get('times', []))}
        - Off-Peak Savings Potential: {booking_knowledge.get('off_peak_savings', {}).get('savings', '20-40%')}
        
        TASK: Provide executive-level insights:
        1. Key performance trends and what they indicate
        2. Revenue optimization opportunities
        3. User engagement patterns and retention strategies
        4. Seasonal trends and predictions
        5. Competitive positioning recommendations
        6. Platform improvement priorities
        
        Focus on actionable business intelligence for tennis facility management.
        """
        
        return AIService.generate_response(prompt, temperature=0.7)
    
    @staticmethod
    def general_tennis_chat(user_message, user_context=None):
        """RAG-Enhanced general tennis chat with knowledge base"""
        # Get relevant knowledge based on message content
        knowledge_context = ""
        
        # Determine what knowledge to include based on user message
        if any(word in user_message.lower() for word in ['court', 'surface', 'clay', 'hard', 'grass']):
            court_knowledge = AIService.get_tennis_knowledge("court_types")
            knowledge_context += f"Court Types Knowledge: {json.dumps(court_knowledge, indent=2)}\n\n"
        
        if any(word in user_message.lower() for word in ['beginner', 'advanced', 'skill', 'improve', 'learn']):
            skill_knowledge = AIService.get_tennis_knowledge("skill_development")
            knowledge_context += f"Skill Development Knowledge: {json.dumps(skill_knowledge, indent=2)}\n\n"
        
        if any(word in user_message.lower() for word in ['book', 'booking', 'schedule', 'time', 'cost']):
            booking_knowledge = AIService.get_tennis_knowledge("booking_strategies")
            knowledge_context += f"Booking Strategies Knowledge: {json.dumps(booking_knowledge, indent=2)}\n\n"
        
        if any(word in user_message.lower() for word in ['injury', 'pain', 'hurt', 'prevention', 'warm']):
            injury_knowledge = AIService.get_tennis_knowledge("injury_prevention")
            knowledge_context += f"Injury Prevention Knowledge: {json.dumps(injury_knowledge, indent=2)}\n\n"
        
        if any(word in user_message.lower() for word in ['style', 'aggressive', 'defensive', 'strategy']):
            style_knowledge = AIService.get_tennis_knowledge("playing_styles")
            knowledge_context += f"Playing Styles Knowledge: {json.dumps(style_knowledge, indent=2)}\n\n"
        
        # If no specific knowledge matched, provide general tennis knowledge
        if not knowledge_context:
            knowledge_context = "General Tennis Knowledge: I have comprehensive information about court types, skill development, playing styles, booking strategies, and injury prevention."
        
        prompt = f"""
        You are TennisCoach AI, an expert tennis advisor with access to comprehensive tennis knowledge.
        
        USER QUESTION: {user_message}
        
        {f"USER CONTEXT: {user_context}" if user_context else ""}
        
        RELEVANT KNOWLEDGE BASE:
        {knowledge_context}
        
        INSTRUCTIONS:
        - Provide helpful, accurate tennis advice based on the knowledge base
        - Be encouraging and supportive
        - Give specific, actionable recommendations when possible
        - If the question isn't tennis-related, politely redirect to tennis topics
        - Use the knowledge base to provide detailed, expert-level answers
        - Keep responses conversational but informative
        
        Respond as a knowledgeable tennis coach would, using the provided knowledge to give the best possible advice.
        """
        
        return AIService.generate_response(prompt, temperature=0.7)
    
    # Helper methods (keeping existing functionality)
    @staticmethod
    def _build_player_context(player_id):
        """Build comprehensive context about a player for AI analysis"""
        player = Player.query.get(player_id)
        
        # Get recent bookings
        recent_bookings = Booking.query.filter_by(player_id=player_id).filter(
            Booking.created_at >= datetime.now() - timedelta(days=30)
        ).count()
        
        # Get match statistics
        try:
            match_stats = MatchingEngine.get_match_statistics(player_id)
        except:
            match_stats = {'compatibility_rate': 75}  # Default fallback
        
        # Build activity summary
        if recent_bookings == 0:
            activity_summary = "No recent activity (inactive player)"
        elif recent_bookings > 8:
            activity_summary = f"Very active player with {recent_bookings} bookings this month"
        elif recent_bookings > 4:
            activity_summary = f"Active player with {recent_bookings} bookings this month"
        else:
            activity_summary = f"Moderately active with {recent_bookings} bookings this month"
        
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
        preferred_day = max(set(days), key=days.count) if days else 'Varies'
        
        # Time analysis
        times = [b.start_time.strftime('%H:00') for b in bookings]
        preferred_time = max(set(times), key=times.count) if times else 'Varies'
        
        # Cost analysis
        costs = [float(b.total_cost or b.court.hourly_rate) for b in bookings if hasattr(b, 'total_cost')]
        avg_cost = sum(costs) / len(costs) if costs else 0
        
        # Court preferences
        court_names = [b.court.name for b in bookings if b.court]
        favorite_courts = list(set(court_names))[:3]  # Top 3
        
        # Frequency calculation
        if len(bookings) >= 4:
            frequency = "Regular player"
        elif len(bookings) >= 2:
            frequency = "Occasional player"
        else:
            frequency = "New player"
        
        return {
            'preferred_day': preferred_day,
            'preferred_time': preferred_time,
            'avg_cost': avg_cost,
            'favorite_courts': favorite_courts,
            'frequency': frequency,
            'total_sessions': len(bookings)
        }
    
    @staticmethod
    def _gather_system_stats():
        """Gather comprehensive system statistics for analysis"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # User statistics
        new_users = User.query.filter(User.created_at >= start_date).count()
        total_users = User.query.count()
        
        # Booking statistics
        recent_bookings = Booking.query.filter(Booking.created_at >= start_date).all()
        total_bookings = len(recent_bookings)
        
        # Revenue calculation
        revenue = sum(float(b.total_cost or b.court.hourly_rate) for b in recent_bookings)
        
        # Popular locations
        locations = [b.court.location for b in recent_bookings if b.court and b.court.location]
        popular_locations = []
        if locations:
            location_counts = {}
            for loc in locations:
                location_counts[loc] = location_counts.get(loc, 0) + 1
            popular_locations = sorted(location_counts.keys(), key=lambda x: location_counts[x], reverse=True)[:3]
        
        # Peak times
        peak_times = []
        if recent_bookings:
            time_counts = {}
            for booking in recent_bookings:
                hour = booking.start_time.strftime('%H:00')
                time_counts[hour] = time_counts.get(hour, 0) + 1
            peak_times = sorted(time_counts.keys(), key=lambda x: time_counts[x], reverse=True)[:3]
        
        # Average duration
        durations = []
        for booking in recent_bookings:
            try:
                start = datetime.combine(booking.booking_date, booking.start_time)
                end = datetime.combine(booking.booking_date, booking.end_time)
                duration = (end - start).total_seconds() / 3600
                durations.append(duration)
            except:
                continue
        
        avg_duration = sum(durations) / len(durations) if durations else 1.5
        
        # Retention rate (simplified)
        if total_users > 0:
            active_users = User.query.join(Booking).filter(Booking.created_at >= start_date).distinct().count()
            retention_rate = (active_users / total_users) * 100
        else:
            retention_rate = 0
        
        # Court utilization
        total_courts = Court.query.filter_by(is_active=True).count()
        if total_courts > 0:
            court_utilization = min(100, (total_bookings / (total_courts * 30)) * 100)
        else:
            court_utilization = 0
        
        return {
            'new_users': new_users,
            'total_bookings': total_bookings,
            'revenue': revenue,
            'popular_locations': popular_locations,
            'peak_times': peak_times,
            'avg_duration': round(avg_duration, 1),
            'retention_rate': round(retention_rate, 1),
            'court_utilization': round(court_utilization, 1)
        }