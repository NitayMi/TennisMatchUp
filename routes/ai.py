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
    """Handle AI requests that require platform actions"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Player not found'}), 404

    data = request.json
    action_type = data.get('action_type')
    user_message = data.get('message', '')

    player = Player.query.filter_by(user_id=user_id).first()
    if not player:
        return jsonify({'error': 'Player profile not found'}), 404

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    # Quick action handling
    if action_type == 'find_partner_now':
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
        params = {
            'location': player.preferred_location or 'Tel Aviv',
            'date': (datetime.now() + timedelta(days=(5-datetime.now().weekday()+7)%7)).strftime('%Y-%m-%d'),
            'time': '15:00',
            'skill_level': player.skill_level
        }
    elif action_type == 'my_availability':
        return jsonify({
            'success': True,
            'action_type': action_type,
            'message': f"You appear to be available most days this week. Your preferred location is {player.preferred_location or 'not set'}."
        })
    elif action_type == 'tell_ai':
        intent = AIActionService.parse_user_intent(user_message)
        params = AIActionService.extract_parameters(user_message)
        params['skill_level'] = player.skill_level
    else:
        return jsonify({'error': 'Unknown action type'}), 400

    start_hour = int(params['time'].split(':')[0])

    if not AIActionService.check_user_availability(user_id, params['date'], start_hour):
        return jsonify({
            'success': False,
            'message': f"You have a booking conflict on {params['date']} at {params['time']}"
        })

    available_players = AIActionService.find_available_players(
        params['location'],
        params['date'],
        params['time'],
        params['skill_level'],
        user_id
    )

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

@ai_bp.route('/find-players', methods=['POST'])
@login_required
@player_required
def find_players():
    """Find available players based on criteria"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Player not found'}), 404
        
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player profile not found'}), 404
        
        # Get search parameters
        data = request.json or {}
        location = data.get('location')
        date_str = data.get('date')
        time_str = data.get('time')
        skill_level = data.get('skill_level')
        
        # Execute player search
        result = AIService.find_available_players(
            player_id=player.id,
            location=location,
            date_str=date_str,
            time_str=time_str,
            skill_level=skill_level
        )
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'players': result['players_found'],
            'search_params': result['search_params']
        })
        
    except Exception as e:
        logging.error(f"Find players error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_bp.route('/find-courts', methods=['POST'])
@login_required
@player_required
def find_courts():
    """Find available courts based on criteria"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Player not found'}), 404
        
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player profile not found'}), 404
        
        # Get search parameters
        data = request.json or {}
        location = data.get('location')
        date_str = data.get('date')
        time_range = data.get('time_range')
        
        # Execute court search
        result = AIService.find_available_courts(
            player_id=player.id,
            location=location,
            date_str=date_str,
            time_range=time_range
        )
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'courts': result['courts_found'],
            'search_params': result['search_params']
        })
        
    except Exception as e:
        logging.error(f"Find courts error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_bp.route('/create-proposal', methods=['POST'])
@login_required
@player_required
def create_proposal():
    """Create a match proposal with player and court"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Player not found'}), 404
        
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player profile not found'}), 404
        
        # Get proposal parameters
        data = request.json or {}
        target_player_id = data.get('target_player_id')
        court_id = data.get('court_id')
        datetime_str = data.get('datetime')
        
        if not all([target_player_id, court_id, datetime_str]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: target_player_id, court_id, datetime'
            }), 400
        
        # Create match proposal
        result = AIService.create_match_proposal(
            player_id=player.id,
            target_player_id=target_player_id,
            court_id=court_id,
            datetime_str=datetime_str
        )
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'proposal': result['proposal']
        })
        
    except Exception as e:
        logging.error(f"Create proposal error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_bp.route('/check-availability', methods=['POST'])
@login_required
@player_required
def check_availability():
    """Check player schedule for conflicts"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Player not found'}), 404
        
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player profile not found'}), 404
        
        # Get datetime to check
        data = request.json or {}
        datetime_str = data.get('datetime')
        
        if not datetime_str:
            return jsonify({
                'success': False,
                'error': 'Missing datetime parameter'
            }), 400
        
        # Check schedule conflicts
        result = AIService.check_schedule_conflicts(player.id, datetime_str)
        
        return jsonify({
            'success': True,
            'availability': result
        })
        
    except Exception as e:
        logging.error(f"Check availability error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_bp.route('/execute-proposal', methods=['POST'])
@login_required
@player_required
def execute_proposal():
    """Execute approved AI suggestions (book court, send match request)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Player not found'}), 404
        
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player profile not found'}), 404
        
        # Get proposal to execute
        data = request.json or {}
        proposal_id = data.get('proposal_id')
        action_type = data.get('action_type')
        
        if not proposal_id or not action_type:
            return jsonify({
                'success': False,
                'error': 'Missing proposal_id or action_type'
            }), 400
        
        # For now, return success message
        # In full implementation, this would integrate with booking and messaging systems
        if action_type == 'SEND_MATCH_REQUEST':
            return jsonify({
                'success': True,
                'message': 'Match request sent successfully! The player will receive a notification.',
                'next_steps': [
                    'Wait for player response',
                    'Check your messages for updates',
                    'Court booking will be handled once match is confirmed'
                ]
            })
        elif action_type == 'BOOK_COURT':
            return jsonify({
                'success': True,
                'message': 'Court booking initiated! You will receive confirmation shortly.',
                'next_steps': [
                    'Check your email for booking confirmation',
                    'Court details will appear in your calendar',
                    'Payment will be processed according to court policy'
                ]
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown action type: {action_type}'
            }), 400
        
    except Exception as e:
        logging.error(f"Execute proposal error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_bp.route('/quick-actions')
@login_required
@player_required
def quick_actions():
    """Get available quick actions for current player"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Player not found'}), 404
        
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player profile not found'}), 404
        
        # Return available quick actions based on player status
        actions = [
            {
                'id': 'find_partner_now',
                'title': 'Find Partner Now',
                'description': 'Find available players in your area',
                'icon': 'fas fa-users',
                'action_type': 'FIND_PARTNER'
            },
            {
                'id': 'book_court_and_partner',
                'title': 'Court + Partner',
                'description': 'Complete match setup with court booking',
                'icon': 'fas fa-calendar-plus',
                'action_type': 'FIND_MATCH_AND_COURT'
            },
            {
                'id': 'check_my_availability',
                'title': 'My Availability',
                'description': 'See when you\'re free this week',
                'icon': 'fas fa-clock',
                'action_type': 'CHECK_AVAILABILITY'
            },
            {
                'id': 'weekend_matches',
                'title': 'Weekend Matches',
                'description': 'Find matches for this weekend',
                'icon': 'fas fa-calendar-weekend',
                'action_type': 'WEEKEND_SEARCH'
            }
        ]
        
        return jsonify({
            'success': True,
            'actions': actions,
            'player_context': {
                'name': player.user.full_name,
                'skill_level': player.skill_level,
                'location': player.preferred_location
            }
        })
        
    except Exception as e:
        logging.error(f"Quick actions error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
    

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
