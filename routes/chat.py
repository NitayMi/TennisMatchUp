"""
Production Chat System for TennisMatchUp
Role-aware messaging: Player ↔ Player, Player ↔ Owner, Admin oversight
"""
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from utils.decorators import login_required, admin_required
from services.chat_service import ChatService
from models.user import User
from models.conversation import Conversation
import logging

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# ========================= MAIN CHAT VIEWS =========================

@chat_bp.route('/conversations')
@login_required
def conversations():
    """Show user's conversation list - role-aware"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    try:
        conversations = ChatService.get_user_conversations(user_id)
        unread_total = sum(conv.get('unread_count', 0) for conv in conversations)
        
        return render_template('chat/conversations.html', 
                             conversations=conversations,
                             unread_total=unread_total,
                             user_type=user.user_type)
    except Exception as e:
        logger.error(f"Error loading conversations for user {user_id}: {str(e)}")
        flash('Error loading conversations', 'error')
        return render_template('chat/conversations.html', conversations=[])

@chat_bp.route('/conversation/<int:conversation_id>')
@login_required
def conversation(conversation_id):
    """View specific conversation with security checks"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    try:
        # Security: Verify user can access this conversation
        if not ChatService.can_access_conversation(user_id, conversation_id):
            flash('Access denied', 'error')
            return redirect(url_for('chat.conversations'))
        
        conversation_data = ChatService.get_conversation_details(user_id, conversation_id)
        messages = ChatService.get_conversation_messages(user_id, conversation_id)
        
        # Mark as read
        ChatService.mark_conversation_as_read(user_id, conversation_id)
        
        return render_template('chat/conversation.html',
                             conversation=conversation_data,
                             messages=messages,
                             user_type=user.user_type,
                             can_moderate=user.user_type == 'admin')
    except Exception as e:
        logger.error(f"Error loading conversation {conversation_id} for user {user_id}: {str(e)}")
        flash('Error loading conversation', 'error')
        return redirect(url_for('chat.conversations'))

@chat_bp.route('/support')
@login_required
def support():
    """Create support conversation with court owner"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if user.user_type not in ['player']:
        flash('Support is available for players only', 'info')
        return redirect(url_for('chat.conversations'))
    
    # Get available court owners for support
    owners = User.query.filter(
        User.user_type == 'owner',
        User.is_active == True
    ).all()
    
    return render_template('chat/support.html', owners=owners)

# ========================= API ENDPOINTS =========================

@chat_bp.route('/api/send', methods=['POST'])
@login_required
def api_send_message():
    """Send message via AJAX with enhanced features"""
    user_id = session['user_id']
    
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        reply_to_id = data.get('reply_to_message_id')
        
        if not conversation_id or not content:
            return jsonify({
                'success': False, 
                'error': 'Conversation and content are required'
            }), 400
        
        # Security check
        if not ChatService.can_access_conversation(user_id, conversation_id):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        result = ChatService.send_message(
            sender_id=user_id,
            conversation_id=conversation_id,
            content=content,
            message_type=message_type,
            reply_to_message_id=reply_to_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error sending message API: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to send message'}), 500

@chat_bp.route('/api/conversations')
@login_required
def api_conversations():
    """Get conversations via AJAX"""
    user_id = session['user_id']
    
    try:
        conversations = ChatService.get_user_conversations(user_id, limit=50)
        return jsonify({
            'success': True,
            'conversations': conversations
        })
    except Exception as e:
        logger.error(f"Error getting conversations API: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to load conversations'}), 500

@chat_bp.route('/api/messages/<int:conversation_id>')
@login_required  
def api_messages(conversation_id):
    """Get messages for conversation via AJAX"""
    user_id = session['user_id']
    
    try:
        # Security check
        if not ChatService.can_access_conversation(user_id, conversation_id):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        since_id = request.args.get('since_id', type=int)
        
        messages = ChatService.get_conversation_messages(
            user_id, conversation_id, page=page, since_id=since_id
        )
        
        return jsonify({
            'success': True,
            'messages': messages
        })
        
    except Exception as e:
        logger.error(f"Error getting messages API: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to load messages'}), 500

@chat_bp.route('/api/create-conversation', methods=['POST'])
@login_required
def api_create_conversation():
    """Create new direct conversation"""
    user_id = session['user_id']
    
    try:
        data = request.get_json()
        recipient_id = data.get('recipient_id')
        first_message = data.get('first_message', '').strip()
        
        if not recipient_id or not first_message:
            return jsonify({
                'success': False,
                'error': 'Recipient and first message are required'
            }), 400
        
        # Get or create conversation
        conv_result = ChatService.get_or_create_direct_conversation(user_id, recipient_id)
        if not conv_result['success']:
            return jsonify(conv_result), 400
        
        # Send first message
        msg_result = ChatService.send_message(
            sender_id=user_id,
            conversation_id=conv_result['conversation_id'],
            content=first_message,
            message_type='text'
        )
        
        if msg_result['success']:
            return jsonify({
                'success': True,
                'conversation_id': conv_result['conversation_id'],
                'created': conv_result.get('created', False)
            })
        else:
            return jsonify(msg_result), 400
        
    except Exception as e:
        logger.error(f"Error creating conversation API: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create conversation'}), 500

# ========================= ADMIN OVERSIGHT =========================

@chat_bp.route('/admin/conversations')
@admin_required
def admin_conversations():
    """Admin view of all conversations"""
    try:
        conversations = ChatService.get_all_conversations_admin()
        return render_template('chat/admin_conversations.html', conversations=conversations)
    except Exception as e:
        logger.error(f"Error in admin conversations: {str(e)}")
        flash('Error loading admin conversations', 'error')
        return redirect(url_for('admin.dashboard'))

@chat_bp.route('/admin/conversation/<int:conversation_id>')
@admin_required
def admin_conversation_view(conversation_id):
    """Admin view specific conversation (impersonation for debugging)"""
    admin_user_id = session['user_id']
    
    try:
        conversation_data = ChatService.get_conversation_details_admin(conversation_id)
        messages = ChatService.get_conversation_messages_admin(conversation_id)
        
        return render_template('chat/admin_conversation.html',
                             conversation=conversation_data,
                             messages=messages,
                             admin_user_id=admin_user_id)
    except Exception as e:
        logger.error(f"Error in admin conversation view: {str(e)}")
        flash('Error loading conversation for admin', 'error')
        return redirect(url_for('chat.admin_conversations'))