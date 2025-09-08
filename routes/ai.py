"""
AI Routes for TennisMatchUp
"""
from flask import Blueprint, jsonify, request, session
from utils.decorators import login_required, player_required
from services.ai_service import AIService
from models.player import Player

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

@ai_bp.route('/recommendations')
@login_required
@player_required
def get_recommendations():
    """Get AI-powered recommendations for player"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Player not found'}), 404
    
    player = Player.query.filter_by(user_id=user_id).first()
    if not player:
        return jsonify({'error': 'Player profile not found'}), 404
    
    recommendations = AIService.get_personalized_recommendations(player.id)
    
    return jsonify({
        'success': True,
        'recommendations': recommendations
    })

@ai_bp.route('/court-advisor')
@login_required
@player_required  
def court_advisor():
    """Smart court recommendations"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Player not found'}), 404
    
    player = Player.query.filter_by(user_id=user_id).first()
    if not player:
        return jsonify({'error': 'Player profile not found'}), 404
    
    recommendations = AIService.get_smart_court_recommendations(player.id)
    
    return jsonify({
        'success': True,
        'advice': recommendations
    })

@ai_bp.route('/chat', methods=['POST'])
@login_required
def ai_chat():
    """General AI chat interface"""
    user_message = request.json.get('message', '')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    response = AIService.general_tennis_chat(user_message)
    
    return jsonify({
        'success': True,
        'response': response
    })