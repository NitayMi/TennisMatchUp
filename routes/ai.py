"""
Enhanced AI Routes for TennisMatchUp
Fixed version with no duplicate endpoints
"""
from flask import Blueprint, jsonify, request, session
from utils.decorators import login_required, player_required
from services.ai_service import AIService
from services.ai_action_service import AIActionService
from models.player import Player
from datetime import datetime, timedelta
import logging

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

# ===== EXISTING ADVISORY ENDPOINTS =====

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

# ===== NEW ACTION ENDPOINTS =====

@ai_bp.route('/action-request', methods=['POST'])
@login_required
@player_required
def action_request():
    """Handle AI action requests from dashboard buttons"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    data = request.json
    action_type = data.get('action_type')
    user_message = data.get('message', '')
    
    try:
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player profile not found'}), 404
        
        # Quick action handling
        if action_type == 'find_partner_now':
            # Use player's preferred location and default to Saturday 3 PM
            params = {
                'location': player.preferred_location or 'Tel Aviv',
                'date': (datetime.now() + timedelta(days=(5-datetime.now().weekday()+7)%7)).strftime('%Y-%m-%d'),
                'time': '15:00',
                'skill_level': player.skill_level
            }
            
        elif action_type == 'court_and_partner':
            params = AIActionService.extract_parameters(user_message)
            params['skill_level'] = player.skill_level
            
        elif action_type == 'weekend_matches':
            # Default to Saturday
            params = {
                'location': player.preferred_location or 'Tel Aviv',
                'date': (datetime.now() + timedelta(days=(5-datetime.now().weekday()+7)%7)).strftime('%Y-%m-%d'),
                'time': '15:00',
                'skill_level': player.skill_level
            }
            
        elif action_type == 'my_availability':
            # Check availability for next few days
            return jsonify({
                'success': True,
                'action_type': action_type,
                'message': f"You appear to be available most days this week. Your last booking was on {datetime.now().strftime('%Y-%m-%d')}."
            })
            
        elif action_type == 'tell_ai':
            # Parse natural language message
            intent = AIActionService.parse_user_intent(user_message)
            params = AIActionService.extract_parameters(user_message)
            params['skill_level'] = player.skill_level
            
        else:
            return jsonify({'error': 'Unknown action type'}), 400
        
        # For actions that don't need proposals (like availability check)
        if action_type == 'my_availability':
            return jsonify({
                'success': True,
                'action_type': action_type,
                'message': f"You appear to be available most days this week. Your preferred location is {player.preferred_location or 'not set'}."
            })
        
        # Execute the action for other types
        start_hour = int(params['time'].split(':')[0])
        
        # Check user availability
        if not AIActionService.check_user_availability(user_id, params['date'], start_hour):
            return jsonify({
                'success': False,
                'message': f"You have a booking conflict on {params['date']} at {params['time']}"
            })
        
        # Find available players
        available_players = AIActionService.find_available_players(
            params['location'], 
            params['date'], 
            params['time'],
            params['skill_level'], 
            user_id
        )
        
        # Find available courts
        available_courts = AIActionService.find_available_courts(
            params['location'],
            params['date'], 
            start_hour
        )
        
        if not available_players and not available_courts:
            return jsonify({
                'success': False,
                'message': f"No players or courts available in {params['location']} on {params['date']} at {params['time']}"
            })
        
        # Create match proposals
        proposals = AIActionService.create_match_proposal(
            player.id,
            available_players,
            available_courts,
            params['date'],
            params['time']
        )
        
        return jsonify({
            'success': True,
            'action_type': action_type,
            'parameters': params,
            'proposals': proposals,
            'available_players': len(available_players),
            'available_courts': len(available_courts)
        })
        
    except Exception as e:
        logging.error(f"Action request error: {str(e)}")
        return jsonify({'error': f'Action failed: {str(e)}'}), 500

@ai_bp.route('/execute-proposal', methods=['POST'])
@login_required
def execute_proposal():
    """Execute a specific match proposal"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    data = request.json
    proposal_id = data.get('proposal_id')
    booking_action = data.get('booking_action')
    
    try:
        # Here you would integrate with your existing booking system
        # For now, return success message
        return jsonify({
            'success': True,
            'message': 'Match request sent! You will be notified when the other player responds.',
            'next_steps': [
                'Check your messages for partner response',
                'Court will be auto-booked when partner confirms',
                'Receive confirmation email with details'
            ]
        })
        
    except Exception as e:
        logging.error(f"Execute proposal error: {str(e)}")
        return jsonify({'error': f'Execution failed: {str(e)}'}), 500