"""
Messaging Routes for TennisMatchUp
WhatsApp-like messaging system with full MVC separation
"""
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from utils.decorators import login_required
from services.messaging_service import MessagingService
from models.user import User
from models.message import Message
from sqlalchemy import or_
import logging

logger = logging.getLogger(__name__)

# Create blueprint
messaging_bp = Blueprint('messaging', __name__, url_prefix='/messaging')

# ========================= MAIN MESSAGING VIEWS =========================

@messaging_bp.route('/inbox')
@login_required
def inbox():
    """Show user's message conversations"""
    user_id = session['user_id']
    
    try:
        # Get all conversations using existing service
        conversations = MessagingService.get_user_conversations(user_id, limit=50)
        
        return render_template('messaging/inbox.html', 
                             conversations=conversations)
        
    except Exception as e:
        logger.error(f"Error loading inbox for user {user_id}: {str(e)}")
        flash('Error loading conversations', 'error')
        return render_template('messaging/inbox.html', conversations=[])

@messaging_bp.route('/conversation/<int:other_user_id>')
@login_required
def conversation(other_user_id):
    """Show conversation with specific user"""
    try:
        user_id = session['user_id']
        logger.debug(f"Current user: {user_id}, Other user: {other_user_id}")
        
        # Get the other user
        other_user = User.query.get_or_404(other_user_id)
        logger.debug(f"Other user found: {other_user.full_name}")
        
        # Get all messages between current user and other user
        messages = Message.get_conversation_messages(user_id, other_user_id)
        logger.debug(f"Found {len(messages)} messages")
        
        # Mark messages from other user as read
        Message.mark_conversation_as_read(user_id, other_user_id)
        
        # Add sender information to messages for template
        for message in messages:
            message.is_from_me = (message.sender_id == user_id)
        
        return render_template('messaging/conversation.html', 
                             messages=messages, 
                             other_user=other_user)
    except Exception as e:
        logger.error(f"ERROR in conversation: {str(e)}")
        flash(f'Error loading conversation: {str(e)}', 'error')
        return redirect(url_for('messaging.inbox'))
    """
    View full conversation with another user
    """
    user_id = session['user_id']
    
    try:
        # Validate other user exists
        other_user = User.query.get_or_404(other_user_id)
        
        if not other_user.is_active:
            flash('User not found', 'error')
            return redirect(url_for('messaging.inbox'))
        
        # Get conversation messages
        page = request.args.get('page', 1, type=int)
        conversation_data = MessagingService.get_conversation_messages(
            user_id=user_id,
            other_user_id=other_user_id,
            page=page,
            per_page=50
        )
        
        # Mark conversation as read
        MessagingService.mark_conversation_as_read(user_id, other_user_id)
        
        return render_template('messaging/conversation.html',
                             other_user=other_user,
                             messages=conversation_data['messages'],
                             has_next=conversation_data['has_next'],
                             has_prev=conversation_data['has_prev'],
                             current_page=page,
                             total_pages=conversation_data['pages'])
        
    except Exception as e:
        logger.error(f"Error loading conversation {user_id} -> {other_user_id}: {str(e)}")
        flash('Error loading conversation', 'error')
        return redirect(url_for('messaging.inbox'))

@messaging_bp.route('/compose')
@login_required
def compose():
    """
    Compose new message to a user
    """
    # Get recipient from query parameter
    recipient_id = request.args.get('to', type=int)
    recipient = None
    
    if recipient_id:
        recipient = User.query.get(recipient_id)
        if recipient and not recipient.is_active:
            recipient = None
    
    # Get all active users for recipient selection (excluding current user)
    user_id = session['user_id']
    potential_recipients = User.query.filter(
        User.id != user_id,
        User.is_active == True,
        User.user_type.in_(['player', 'owner'])  # Exclude admins from normal messaging
    ).order_by(User.full_name).all()
    
    return render_template('messaging/compose.html',
                         recipient=recipient,
                         potential_recipients=potential_recipients)

# ========================= MESSAGE ACTIONS =========================

@messaging_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """
    Send a new message
    """
    user_id = session['user_id']
    
    try:
        receiver_id = request.form.get('receiver_id', type=int)
        content = request.form.get('content', '').strip()
        message_type = request.form.get('message_type', 'text')
        
        if not receiver_id or not content:
            flash('Please provide recipient and message content', 'error')
            return redirect(url_for('messaging.inbox'))
        
        # Send message using service
        result = MessagingService.send_message(
            sender_id=user_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type
        )
        
        if result['success']:
            flash(result['message'], 'success')
            # Redirect to conversation with the recipient
            return redirect(url_for('messaging.conversation', other_user_id=receiver_id))
        else:
            flash(result['error'], 'error')
            return redirect(url_for('messaging.compose', to=receiver_id))
        
    except Exception as e:
        logger.error(f"Error sending message from user {user_id}: {str(e)}")
        flash('Error sending message', 'error')
        return redirect(url_for('messaging.compose'))

@messaging_bp.route('/send_match_request', methods=['POST'])
@login_required
def send_match_request():
    """
    Send a tennis match request to another player
    """
    user_id = session['user_id']
    
    try:
        receiver_id = request.form.get('receiver_id', type=int)
        custom_message = request.form.get('custom_message', '').strip()
        
        if not receiver_id:
            flash('Please select a player', 'error')
            return redirect(request.referrer or url_for('messaging.compose'))
        
        # Send match request using service
        result = MessagingService.send_match_request(
            sender_id=user_id,
            receiver_id=receiver_id,
            message_content=custom_message if custom_message else None
        )
        
        if result['success']:
            flash('Match request sent successfully!', 'success')
            return redirect(url_for('messaging.conversation', other_user_id=receiver_id))
        else:
            flash(result['error'], 'error')
            return redirect(request.referrer or url_for('messaging.compose'))
        
    except Exception as e:
        logger.error(f"Error sending match request from user {user_id}: {str(e)}")
        flash('Error sending match request', 'error')
        return redirect(url_for('messaging.compose'))

# ========================= SEARCH AND UTILITIES =========================

@messaging_bp.route('/search')
@login_required
def search():
    """
    Search messages
    """
    user_id = session['user_id']
    query = request.args.get('q', '').strip()
    
    results = []
    if query and len(query) >= 2:
        results = MessagingService.search_messages(user_id, query, limit=30)
    
    return render_template('messaging/search_results.html',
                         query=query,
                         results=results)

@messaging_bp.route('/mark_read/<int:other_user_id>', methods=['POST'])
@login_required
def mark_conversation_read(other_user_id):
    """
    Mark all messages from another user as read
    """
    user_id = session['user_id']
    
    try:
        result = MessagingService.mark_conversation_as_read(user_id, other_user_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'marked_count': result['marked_count'],
                'message': f"Marked {result['marked_count']} messages as read"
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to mark as read'}), 500
            
    except Exception as e:
        logger.error(f"Error marking conversation as read: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

# ========================= API ENDPOINTS FOR JAVASCRIPT =========================

@messaging_bp.route('/api/conversations')
@login_required
def api_conversations():
    """
    API endpoint to get conversations (for AJAX updates)
    """
    user_id = session['user_id']
    
    try:
        conversations = MessagingService.get_user_conversations(user_id, limit=50)
        return jsonify({
            'success': True,
            'conversations': conversations
        })
    except Exception as e:
        logger.error(f"Error getting conversations API: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to load conversations'}), 500

@messaging_bp.route('/api/conversation/<int:other_user_id>/messages')
@login_required
def api_conversation_messages(other_user_id):
    """
    API endpoint to get messages in a conversation (for AJAX/polling)
    """
    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    since_id = request.args.get('since_id', type=int)  # For getting new messages only
    
    try:
        conversation_data = MessagingService.get_conversation_messages(
            user_id=user_id,
            other_user_id=other_user_id,
            page=page,
            per_page=50
        )
        
        # If since_id provided, filter for newer messages only
        if since_id:
            conversation_data['messages'] = [
                msg for msg in conversation_data['messages'] 
                if msg['id'] > since_id
            ]
        
        return jsonify({
            'success': True,
            'messages': conversation_data['messages'],
            'has_next': conversation_data['has_next'],
            'has_prev': conversation_data['has_prev'],
            'total': conversation_data['total']
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation messages API: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to load messages'}), 500

@messaging_bp.route('/api/send', methods=['POST'])
@login_required
def api_send_message():
    """
    API endpoint to send message (for AJAX)
    """
    user_id = session['user_id']
    
    try:
        data = request.get_json()
        receiver_id = data.get('receiver_id')
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        
        if not receiver_id or not content:
            return jsonify({
                'success': False, 
                'error': 'Receiver and content are required'
            }), 400
        
        result = MessagingService.send_message(
            sender_id=user_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error sending message API: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to send message'}), 500

@messaging_bp.route('/api/unread_count')
@login_required
def api_unread_count():
    """
    API endpoint to get unread message count (for notifications)
    """
    user_id = session['user_id']
    
    try:
        count = MessagingService.get_unread_message_count(user_id)
        return jsonify({
            'success': True,
            'unread_count': count
        })
    except Exception as e:
        logger.error(f"Error getting unread count API: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get count'}), 500

# ========================= ADMIN/UTILITY ROUTES =========================

@messaging_bp.route('/stats')
@login_required
def messaging_stats():
    """
    Messaging statistics for user (optional feature)
    """
    user_id = session['user_id']
    
    try:
        stats = MessagingService.get_conversation_stats(user_id)
        return render_template('messaging/stats.html', stats=stats)
    except Exception as e:
        logger.error(f"Error getting messaging stats: {str(e)}")
        flash('Error loading statistics', 'error')
        return redirect(url_for('messaging.inbox'))

# ========================= ERROR HANDLERS =========================

@messaging_bp.errorhandler(404)
def messaging_not_found(error):
    """Custom 404 handler for messaging routes"""
    return render_template('messaging/error.html', 
                         error_title="Conversation Not Found",
                         error_message="The conversation you're looking for doesn't exist."), 404

@messaging_bp.errorhandler(500)
def messaging_server_error(error):
    """Custom 500 handler for messaging routes"""
    return render_template('messaging/error.html',
                         error_title="Messaging Error", 
                         error_message="Something went wrong with the messaging system."), 500