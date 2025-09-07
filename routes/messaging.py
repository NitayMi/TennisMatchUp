"""
Messaging Routes for TennisMatchUp
Simple messaging system implementation
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from models.user import User
from models.player import Player
from models.message import Message
from models.database import db
from utils.decorators import login_required
from services.rule_engine import RuleEngine
from datetime import datetime
from sqlalchemy import or_, and_

messaging_bp = Blueprint('messaging', __name__, url_prefix='/messages')

@messaging_bp.route('/inbox')
@login_required
def inbox():
    """Display user's message inbox - simple version"""
    user_id = session['user_id']
    
    # Get all messages received by current user
    messages_received = Message.query.filter_by(receiver_id=user_id).order_by(
        Message.created_at.desc()
    ).limit(50).all()
    
    # Get all messages sent by current user  
    messages_sent = Message.query.filter_by(sender_id=user_id).order_by(
        Message.created_at.desc()
    ).limit(50).all()
    
    # Count unread messages
    unread_count = Message.count_unread_messages(user_id)
    
    return render_template('messages/inbox.html',
                         messages_received=messages_received,
                         messages_sent=messages_sent,
                         unread_count=unread_count)

@messaging_bp.route('/compose')
@login_required
def compose():
    """Compose new message - simple version"""
    user_id = session['user_id']
    
    # Get all users except current user
    available_users = User.query.filter(
        and_(User.id != user_id, User.is_active == True)
    ).order_by(User.full_name).all()
    
    return render_template('messages/compose.html',
                         available_users=available_users)

@messaging_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """Send a new message - simple version"""
    user_id = session['user_id']
    
    recipient_id = request.form.get('recipient_id', type=int)
    content = request.form.get('content', '').strip()
    
    if not recipient_id or not content:
        flash('Please select a recipient and enter a message', 'error')
        return redirect(url_for('messaging.compose'))
    
    # Validate message using RuleEngine
    validation_result = RuleEngine.validate_message_sending(user_id, recipient_id, content)
    
    if not validation_result['valid']:
        flash(validation_result['reason'], 'error')
        return redirect(url_for('messaging.compose'))
    
    # Create and save message
    try:
        message = Message(
            sender_id=user_id,
            receiver_id=recipient_id,
            content=content,
            message_type='text'
        )
        
        db.session.add(message)
        db.session.commit()
        
        recipient = User.query.get(recipient_id)
        flash(f'Message sent to {recipient.full_name}!', 'success')
        return redirect(url_for('messaging.inbox'))
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to send message. Please try again.', 'error')
        return redirect(url_for('messaging.compose'))