"""
AI Routes for TennisMatchUp
"""
from flask import Blueprint, jsonify, render_template, session
from utils.decorators import login_required, player_required
from services.ai_service import AIService

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

@ai_bp.route('/recommendations')
@login_required
@player_required
def get_recommendations():
    """Get AI-powered recommendations for player"""
    player_id = session.get('player_id')
    if not player_id:
        return jsonify({'error': 'Player not found'}), 404
    
    recommendations = AIService.get_personalized_recommendations(player_id)
    
    return jsonify({
        'success': True,
        'recommendations': recommendations
    })

@ai_bp.route('/court-advisor')
@login_required
@player_required  
def court_advisor():
    """Smart court recommendations"""
    player_id = session.get('player_id')
    recommendations = AIService.get_smart_court_recommendations(player_id)
    
    return jsonify({
        'success': True,
        'advice': recommendations
    })

@ai_bp.route('/chat', methods=['POST'])
@login_required
def ai_chat():
    """General AI chat interface"""
    from flask import request
    
    user_message = request.json.get('message', '')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Create tennis-focused prompt
    tennis_prompt = f"""
    You are TennisCoach AI, an expert tennis advisor. 
    User question: {user_message}
    
    Provide helpful tennis-related advice. If the question is not about tennis,
    politely redirect to tennis topics.
    """
    
    response = AIService.generate_response(tennis_prompt)
    
    return jsonify({
        'success': True,
        'response': response
    })