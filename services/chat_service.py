"""
ChatService - Production messaging with role-aware security
Handles Player ↔ Player, Player ↔ Owner, Admin oversight
"""
from models.database import db
from models.conversation import Conversation, ConversationParticipant, MessageReadStatus
from models.message import Message
from models.user import User
from services.rule_engine import RuleEngine
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ChatService:
    """Production chat service with role-based access control"""
    
    @staticmethod
    def create_conversation(creator_id, participant_ids, conversation_type='direct', title=None):
        """Create new conversation with participants"""
        try:
            # Validate participants
            if not ChatService.validate_conversation_creation(creator_id, participant_ids, conversation_type):
                return {'success': False, 'error': 'Invalid conversation setup'}
            
            # Create conversation
            conversation = Conversation(
                conversation_type=conversation_type,
                title=title
            )
            db.session.add(conversation)
            db.session.flush()  # Get ID
            
            # Add participants
            all_participant_ids = list(set([creator_id] + participant_ids))
            for user_id in all_participant_ids:
                participant = ConversationParticipant(
                    conversation_id=conversation.id,
                    user_id=user_id,
                    role='admin' if user_id == creator_id else 'participant'
                )
                db.session.add(participant)
            
            db.session.commit()
            logger.info(f"Conversation {conversation.id} created by user {creator_id}")
            
            return {
                'success': True,
                'conversation_id': conversation.id,
                'conversation': conversation
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating conversation: {str(e)}")
            return {'success': False, 'error': 'Failed to create conversation'}
    
    @staticmethod
    def get_or_create_direct_conversation(user1_id, user2_id):
        """Get existing direct conversation or create new one"""
        try:
            # Look for existing conversation between these users
            existing = db.session.query(Conversation).join(ConversationParticipant).filter(
                Conversation.conversation_type == 'direct',
                ConversationParticipant.user_id.in_([user1_id, user2_id])
            ).group_by(Conversation.id).having(
                db.func.count(ConversationParticipant.id) == 2
            ).first()
            
            if existing:
                # Verify both users are participants
                participant_ids = [p.user_id for p in existing.participants if p.is_active]
                if set(participant_ids) == {user1_id, user2_id}:
                    return {
                        'success': True,
                        'conversation_id': existing.id,
                        'conversation': existing,
                        'created': False
                    }
            
            # Create new conversation
            result = ChatService.create_conversation(user1_id, [user2_id], 'direct')
            if result['success']:
                result['created'] = True
            return result
            
        except Exception as e:
            logger.error(f"Error getting/creating direct conversation: {str(e)}")
            return {'success': False, 'error': 'Failed to setup conversation'}
    
    @staticmethod
    def send_message(sender_id, conversation_id, content, message_type='text', reply_to_message_id=None):
        """Send message with full validation"""
        try:
            # Security validation
            if not ChatService.can_access_conversation(sender_id, conversation_id):
                return {'success': False, 'error': 'Access denied'}
            
            # Business rules validation
            validation = RuleEngine.validate_message_sending(sender_id, None, content)
            if not validation['valid']:
                return {'success': False, 'error': validation['reason']}
            
            # Create message
            message = Message(
                sender_id=sender_id,
                receiver_id=None,  # Not used in conversation model
                content=content.strip(),
                message_type=message_type
            )
            
            # Add conversation fields if they exist
            if hasattr(message, 'conversation_id'):
                message.conversation_id = conversation_id
            if hasattr(message, 'reply_to_message_id') and reply_to_message_id:
                message.reply_to_message_id = reply_to_message_id
            
            db.session.add(message)
            
            # Update conversation timestamp
            conversation = Conversation.query.get(conversation_id)
            if conversation:
                conversation.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Message {message.id} sent by user {sender_id} to conversation {conversation_id}")
            
            return {
                'success': True,
                'message_id': message.id,
                'message': message.to_dict() if hasattr(message, 'to_dict') else None
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error sending message: {str(e)}")
            return {'success': False, 'error': 'Failed to send message'}
    
    @staticmethod
    def get_user_conversations(user_id, limit=50):
        """Get all conversations for user with role-aware filtering"""
        try:
            user = User.query.get(user_id)
            if not user:
                return []
            
            # Get conversations where user is participant
            query = db.session.query(Conversation).join(ConversationParticipant).filter(
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.is_active == True
            ).order_by(Conversation.updated_at.desc())
            
            # Admin can see all conversations
            if user.user_type == 'admin':
                query = db.session.query(Conversation).order_by(Conversation.updated_at.desc())
            
            conversations = query.limit(limit).all()
            
            result = []
            for conv in conversations:
                # Get other participant info for direct conversations
                other_participant = None
                if conv.conversation_type == 'direct':
                    other_participant = conv.get_other_participant(user_id)
                
                conv_data = {
                    'id': conv.id,
                    'type': conv.conversation_type,
                    'title': conv.title,
                    'created_at': conv.created_at.isoformat(),
                    'updated_at': conv.updated_at.isoformat(),
                    'unread_count': conv.get_unread_count(user_id),
                    'participant_count': len([p for p in conv.participants if p.is_active])
                }
                
                # Add other participant info for direct messages
                if other_participant and other_participant.user:
                    conv_data.update({
                        'other_participant': {
                            'id': other_participant.user.id,
                            'name': other_participant.user.full_name,
                            'user_type': other_participant.user.user_type
                        }
                    })
                
                # Get last message
                last_message = db.session.query(Message).filter(
                    Message.conversation_id == conv.id if hasattr(Message, 'conversation_id') else False
                ).order_by(Message.created_at.desc()).first()
                
                if not last_message and hasattr(Message, 'conversation_id'):
                    # Fallback: get any message related to participants
                    participant_ids = [p.user_id for p in conv.participants if p.is_active]
                    last_message = db.session.query(Message).filter(
                        Message.sender_id.in_(participant_ids),
                        Message.receiver_id.in_(participant_ids)
                    ).order_by(Message.created_at.desc()).first()
                
                if last_message:
                    conv_data['last_message'] = {
                        'id': last_message.id,
                        'content': last_message.get_preview(50) if hasattr(last_message, 'get_preview') else last_message.content[:50],
                        'sender_name': last_message.sender.full_name if last_message.sender else 'Unknown',
                        'created_at': last_message.created_at.isoformat(),
                        'message_type': last_message.message_type
                    }
                
                result.append(conv_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting conversations for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def get_conversation_messages(user_id, conversation_id, page=1, per_page=50, since_id=None):
        """Get messages with security and pagination"""
        try:
            # Security check
            if not ChatService.can_access_conversation(user_id, conversation_id):
                return {'messages': [], 'error': 'Access denied'}
            
            # Build query based on available fields
            if hasattr(Message, 'conversation_id'):
                query = db.session.query(Message).filter(
                    Message.conversation_id == conversation_id,
                    getattr(Message, 'is_deleted', False) == False
                ).order_by(Message.created_at.desc())
            else:
                # Fallback: use participant-based filtering
                conversation = Conversation.query.get(conversation_id)
                if not conversation:
                    return {'messages': [], 'error': 'Conversation not found'}
                
                participant_ids = [p.user_id for p in conversation.participants if p.is_active]
                query = db.session.query(Message).filter(
                    Message.sender_id.in_(participant_ids),
                    Message.receiver_id.in_(participant_ids)
                ).order_by(Message.created_at.desc())
            
            # Filter by since_id for real-time updates
            if since_id:
                query = query.filter(Message.id > since_id)
            
            paginated = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            messages = []
            for message in reversed(paginated.items):  # Oldest first for display
                msg_data = {
                    'id': message.id,
                    'content': message.content,
                    'sender_id': message.sender_id,
                    'sender_name': message.sender.full_name if message.sender else 'Unknown',
                    'is_from_me': message.sender_id == user_id,
                    'message_type': message.message_type,
                    'created_at': message.created_at.isoformat(),
                    'attachment_url': message.attachment_url
                }
                
                # Add enhanced fields if available
                if hasattr(message, 'reply_to_message_id'):
                    msg_data['reply_to_message_id'] = message.reply_to_message_id
                if hasattr(message, 'is_edited'):
                    msg_data['is_edited'] = message.is_edited
                if hasattr(message, 'attachment_type'):
                    msg_data['attachment_type'] = message.attachment_type
                
                # Add reply context if applicable
                if hasattr(message, 'reply_to_message_id') and message.reply_to_message_id:
                    reply_to = Message.query.get(message.reply_to_message_id)
                    if reply_to:
                        msg_data['reply_to'] = {
                            'id': reply_to.id,
                            'content': reply_to.content[:100],
                            'sender_name': reply_to.sender.full_name if reply_to.sender else 'Unknown'
                        }
                
                messages.append(msg_data)
            
            return {
                'messages': messages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev,
                'total': paginated.total
            }
            
        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {str(e)}")
            return {'messages': [], 'error': 'Failed to load messages'}
    
    @staticmethod
    def can_access_conversation(user_id, conversation_id):
        """Security check - can user access this conversation?"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Admin can access all conversations
            if user.user_type == 'admin':
                return True
            
            # Check if user is an active participant
            participant = db.session.query(ConversationParticipant).filter(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.is_active == True
            ).first()
            
            return participant is not None
            
        except Exception as e:
            logger.error(f"Error checking conversation access: {str(e)}")
            return False
    
    @staticmethod
    def mark_conversation_as_read(user_id, conversation_id):
        """Mark conversation as read for user"""
        try:
            participant = db.session.query(ConversationParticipant).filter(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.is_active == True
            ).first()
            
            if participant:
                participant.last_read_at = datetime.utcnow()
                db.session.commit()
                logger.info(f"Conversation {conversation_id} marked as read by user {user_id}")
                return {'success': True}
            
            return {'success': False, 'error': 'Participant not found'}
            
        except Exception as e:
            logger.error(f"Error marking conversation as read: {str(e)}")
            return {'success': False, 'error': 'Failed to mark as read'}
    
    @staticmethod
    def get_conversation_details(user_id, conversation_id):
        """Get conversation details with participant info"""
        try:
            conversation = Conversation.query.get(conversation_id)
            if not conversation:
                return None
            
            participants = []
            for p in conversation.participants:
                if p.is_active:
                    participants.append({
                        'user_id': p.user_id,
                        'name': p.user.full_name,
                        'user_type': p.user.user_type,
                        'role': p.role
                    })
            
            return {
                'id': conversation.id,
                'type': conversation.conversation_type,
                'title': conversation.title,
                'participants': participants,
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation details: {str(e)}")
            return None
    
    @staticmethod
    def validate_conversation_creation(creator_id, participant_ids, conversation_type):
        """Validate if conversation can be created"""
        try:
            creator = User.query.get(creator_id)
            if not creator or not creator.is_active:
                return False
            
            # Validate all participants exist and are active
            for participant_id in participant_ids:
                participant = User.query.get(participant_id)
                if not participant or not participant.is_active:
                    return False
            
            # Role-specific validation
            if conversation_type == 'support':
                # Support conversations: players can contact owners
                if creator.user_type != 'player':
                    return False
                # At least one participant should be owner
                owner_participants = [User.query.get(pid) for pid in participant_ids]
                if not any(p.user_type == 'owner' for p in owner_participants if p):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating conversation creation: {str(e)}")
            return False
    
    @staticmethod
    def get_all_conversations_admin():
        """Admin-only: Get all conversations"""
        try:
            conversations = Conversation.query.order_by(Conversation.updated_at.desc()).all()
            result = []
            
            for conv in conversations:
                participants = [
                    {
                        'user_id': p.user_id,
                        'name': p.user.full_name,
                        'user_type': p.user.user_type,
                        'is_active': p.is_active
                    } for p in conv.participants
                ]
                
                result.append({
                    'id': conv.id,
                    'type': conv.conversation_type,
                    'title': conv.title,
                    'participants': participants,
                    'message_count': len(conv.messages),
                    'created_at': conv.created_at.isoformat(),
                    'updated_at': conv.updated_at.isoformat()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all conversations for admin: {str(e)}")
            return []
    
    @staticmethod
    def get_conversation_details_admin(conversation_id):
        """Admin-only: Get conversation details"""
        return ChatService.get_conversation_details(None, conversation_id)  # Admin bypasses user check
    
    @staticmethod
    def get_conversation_messages_admin(conversation_id):
        """Admin-only: Get conversation messages"""
        try:
            if hasattr(Message, 'conversation_id'):
                messages = db.session.query(Message).filter(
                    Message.conversation_id == conversation_id
                ).order_by(Message.created_at.asc()).all()
            else:
                # Fallback for older schema
                conversation = Conversation.query.get(conversation_id)
                if not conversation:
                    return {'messages': []}
                
                participant_ids = [p.user_id for p in conversation.participants]
                messages = db.session.query(Message).filter(
                    Message.sender_id.in_(participant_ids),
                    Message.receiver_id.in_(participant_ids)
                ).order_by(Message.created_at.asc()).all()
            
            msg_list = []
            for msg in messages:
                msg_data = {
                    'id': msg.id,
                    'content': msg.content,
                    'sender_id': msg.sender_id,
                    'sender_name': msg.sender.full_name if msg.sender else 'Unknown',
                    'message_type': msg.message_type,
                    'created_at': msg.created_at.isoformat()
                }
                msg_list.append(msg_data)
            
            return {'messages': msg_list}
            
        except Exception as e:
            logger.error(f"Error getting admin conversation messages: {str(e)}")
            return {'messages': []}