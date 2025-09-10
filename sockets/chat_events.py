"""
Real-time chat events using Socket.IO
Handles typing indicators, live messages, presence
"""
from flask import session
from flask_socketio import emit, join_room, leave_room, disconnect
from utils.decorators import login_required
from services.chat_service import ChatService
import logging

logger = logging.getLogger(__name__)

def register_chat_events(socketio):
    """Register all chat-related socket events"""
    
    @socketio.on('connect')
    def on_connect():
        user_id = session.get('user_id')
        if not user_id:
            disconnect()
            return False
        
        logger.info(f"User {user_id} connected to chat socket")
        emit('connected', {'status': 'Connected to chat'})
    
    @socketio.on('disconnect')
    def on_disconnect():
        user_id = session.get('user_id')
        if user_id:
            logger.info(f"User {user_id} disconnected from chat socket")
    
    @socketio.on('join_conversation')
    def on_join_conversation(data):
        user_id = session.get('user_id')
        if not user_id:
            emit('error', {'message': 'Not authenticated'})
            return
        
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            emit('error', {'message': 'Conversation ID required'})
            return
        
        # Security check
        if not ChatService.can_access_conversation(user_id, conversation_id):
            emit('error', {'message': 'Access denied'})
            return
        
        room_name = f"conversation_{conversation_id}"
        join_room(room_name)
        emit('joined_conversation', {'conversation_id': conversation_id})
        logger.info(f"User {user_id} joined conversation {conversation_id}")
    
    @socketio.on('leave_conversation')
    def on_leave_conversation(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        
        conversation_id = data.get('conversation_id')
        
        if conversation_id:
            room_name = f"conversation_{conversation_id}"
            leave_room(room_name)
            emit('left_conversation', {'conversation_id': conversation_id})
            logger.info(f"User {user_id} left conversation {conversation_id}")
    
    @socketio.on('typing_start')
    def on_typing_start(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        
        conversation_id = data.get('conversation_id')
        
        if not ChatService.can_access_conversation(user_id, conversation_id):
            return
        
        room_name = f"conversation_{conversation_id}"
        emit('user_typing', {'user_id': user_id, 'typing': True}, room=room_name, include_self=False)
    
    @socketio.on('typing_stop')
    def on_typing_stop(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        
        conversation_id = data.get('conversation_id')
        
        if not ChatService.can_access_conversation(user_id, conversation_id):
            return
        
        room_name = f"conversation_{conversation_id}"
        emit('user_typing', {'user_id': user_id, 'typing': False}, room=room_name, include_self=False)
    
    @socketio.on('send_message')
    def on_send_message(data):
        user_id = session.get('user_id')
        if not user_id:
            emit('error', {'message': 'Not authenticated'})
            return
        
        conversation_id = data.get('conversation_id')
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        
        if not content:
            emit('error', {'message': 'Message content required'})
            return
        
        # Send message via service
        result = ChatService.send_message(user_id, conversation_id, content, message_type)
        
        if result['success']:
            # Broadcast to conversation room
            room_name = f"conversation_{conversation_id}"
            message_data = result.get('message', {})
            message_data['sender_id'] = user_id
            
            emit('new_message', message_data, room=room_name)
            emit('message_sent', {'message_id': result['message_id']})
        else:
            emit('error', {'message': result.get('error', 'Failed to send message')})
    
    return socketio