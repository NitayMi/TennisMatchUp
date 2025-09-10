"""
MessagingService - Centralized messaging business logic for TennisMatchUp
Follows MVC pattern with complete separation of concerns
"""
from models.database import db
from models.message import Message
from models.user import User
from services.rule_engine import RuleEngine
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MessagingService:
    """Professional messaging service following TennisMatchUp architecture"""
    
    @staticmethod
    def send_message(sender_id, receiver_id, content, message_type='text', related_booking_id=None):
        """
        Send a message with full validation and business logic
        
        Args:
            sender_id (int): ID of the message sender
            receiver_id (int): ID of the message receiver  
            content (str): Message content
            message_type (str): Type of message (text, system, notification, match_request, booking_request)
            related_booking_id (int, optional): Related booking ID for context
            
        Returns:
            dict: {'success': bool, 'message_id': int, 'error': str}
        """
        try:
            # Validate using RuleEngine (existing validation)
            validation = RuleEngine.validate_message_sending(sender_id, receiver_id, content)
            if not validation['valid']:
                return {'success': False, 'error': validation['reason']}
            
            # Create message object
            message = Message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content.strip(),
                message_type=message_type
            )
            
            if related_booking_id:
                message.related_booking_id = related_booking_id
            
            # Save to database
            db.session.add(message)
            db.session.commit()
            
            logger.info(f"Message sent: {sender_id} -> {receiver_id}, type: {message_type}")
            
            return {
                'success': True,
                'message_id': message.id,
                'message': 'Message sent successfully!'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error sending message: {str(e)}")
            return {'success': False, 'error': 'Failed to send message'}
    
    @staticmethod
    def get_user_conversations(user_id, limit=50):
        """
        Get all conversations for a user with last message preview
        
        Args:
            user_id (int): User ID to get conversations for
            limit (int): Maximum number of conversations to return
            
        Returns:
            list: List of conversation dictionaries with participant info and last message
        """
        try:
            # Use the existing static method but enhance the data
            raw_conversations = Message.get_user_conversations(user_id)
            
            conversations = []
            for conv in raw_conversations[:limit]:
                # Get the other participant ID from the conversation data
                other_user_id = conv['partner_id']
                other_user = User.query.get(other_user_id)
                
                if not other_user:
                    continue
                
                # Use last message from conversation data
                last_message = conv['last_message']
                
                # Count unread messages from this user
                unread_count = Message.query.filter(
                    Message.sender_id == other_user_id,
                    Message.receiver_id == user_id,
                    Message.is_read == False
                ).count()
                
                # Create simple objects that the template expects
                class ConversationData:
                    def __init__(self):
                        self.other_user = other_user
                        self.last_message = last_message
                        self.unread_count = unread_count
                        self.has_unread = unread_count > 0
                
                conversation_data = ConversationData()
                conversations.append(conversation_data)
            
            # Sort by last message time
            conversations.sort(key=lambda x: x.last_message.created_at if x.last_message else datetime.min, reverse=True)
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversations for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def get_conversation_messages(user_id, other_user_id, page=1, per_page=50):
        """
        Get messages in a conversation between two users with pagination
        
        Args:
            user_id (int): Current user ID
            other_user_id (int): Other participant ID
            page (int): Page number for pagination
            per_page (int): Messages per page
            
        Returns:
            dict: {'messages': list, 'has_next': bool, 'has_prev': bool, 'total': int}
        """
        try:
            # Validate users exist and are active
            user = User.query.get(user_id)
            other_user = User.query.get(other_user_id)
            
            if not user or not other_user or not user.is_active or not other_user.is_active:
                return {'messages': [], 'has_next': False, 'has_prev': False, 'total': 0}
            
            # Get paginated messages using existing static method but with pagination
            query = Message.query.filter(
                db.or_(
                    db.and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
                    db.and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
                )
            ).order_by(Message.created_at.desc())
            
            paginated = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            messages = []
            for message in reversed(paginated.items):  # Reverse to show oldest first
                message_data = {
                    'id': message.id,
                    'content': message.content,
                    'sender_id': message.sender_id,
                    'sender_name': message.sender.full_name,
                    'is_from_me': message.sender_id == user_id,
                    'message_type': message.message_type,
                    'message_type_display': message.get_message_type_display(),
                    'is_read': message.is_read,
                    'read_at': message.read_at.isoformat() if message.read_at else None,
                    'created_at': message.created_at.isoformat(),
                    'time_display': message.get_time_display(),
                    'related_booking_id': message.related_booking_id,
                    'attachment_url': message.attachment_url
                }
                messages.append(message_data)
            
            return {
                'messages': messages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev,
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation messages: {str(e)}")
            return {'messages': [], 'has_next': False, 'has_prev': False, 'total': 0}
    
    @staticmethod
    def mark_conversation_as_read(user_id, other_user_id):
        """
        Mark all messages from other_user as read
        
        Args:
            user_id (int): Current user ID (receiver)
            other_user_id (int): Sender whose messages to mark as read
            
        Returns:
            dict: {'success': bool, 'marked_count': int}
        """
        try:
            # Use existing static method from Message model
            marked_count = Message.query.filter(
                Message.sender_id == other_user_id,
                Message.receiver_id == user_id,
                Message.is_read == False
            ).count()
            
            Message.mark_conversation_as_read(user_id, other_user_id)
            
            logger.info(f"Marked {marked_count} messages as read for user {user_id} from {other_user_id}")
            
            return {'success': True, 'marked_count': marked_count}
            
        except Exception as e:
            logger.error(f"Error marking conversation as read: {str(e)}")
            return {'success': False, 'marked_count': 0}
    
    @staticmethod
    def get_unread_message_count(user_id):
        """
        Get total count of unread messages for a user
        
        Args:
            user_id (int): User ID to count unread messages for
            
        Returns:
            int: Number of unread messages
        """
        try:
            return Message.count_unread_messages(user_id)
        except Exception as e:
            logger.error(f"Error counting unread messages for user {user_id}: {str(e)}")
            return 0
    
    @staticmethod
    def search_messages(user_id, query, limit=50):
        """
        Search messages for a user
        
        Args:
            user_id (int): User ID to search messages for
            query (str): Search query
            limit (int): Maximum results to return
            
        Returns:
            list: List of matching messages with context
        """
        try:
            if not query or len(query.strip()) < 2:
                return []
            
            search_term = f"%{query.strip()}%"
            
            messages = Message.query.filter(
                db.or_(Message.sender_id == user_id, Message.receiver_id == user_id),
                Message.content.ilike(search_term)
            ).order_by(Message.created_at.desc()).limit(limit).all()
            
            results = []
            for message in messages:
                # Determine other participant
                other_user_id = message.receiver_id if message.sender_id == user_id else message.sender_id
                other_user = User.query.get(other_user_id)
                
                result = {
                    'message_id': message.id,
                    'content': message.content,
                    'preview': message.get_preview(100),
                    'other_user_name': other_user.full_name if other_user else 'Unknown',
                    'other_user_id': other_user_id,
                    'is_from_me': message.sender_id == user_id,
                    'created_at': message.created_at.isoformat(),
                    'time_display': message.get_time_display(),
                    'message_type': message.message_type
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching messages for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def send_match_request(sender_id, receiver_id, message_content=None):
        """
        Send a tennis match request message
        
        Args:
            sender_id (int): Player sending the request
            receiver_id (int): Player receiving the request
            message_content (str, optional): Custom message
            
        Returns:
            dict: {'success': bool, 'message_id': int, 'error': str}
        """
        try:
            sender = User.query.get(sender_id)
            if not sender:
                return {'success': False, 'error': 'Sender not found'}
            
            if not message_content:
                message_content = f"Hi! I'm {sender.full_name} and I'd like to play tennis with you. Are you available for a match?"
            
            return MessagingService.send_message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=message_content,
                message_type='match_request'
            )
            
        except Exception as e:
            logger.error(f"Error sending match request: {str(e)}")
            return {'success': False, 'error': 'Failed to send match request'}
        