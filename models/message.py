from models.database import db, TimestampMixin
from datetime import datetime

class Message(db.Model, TimestampMixin):
    """Chat messages between users"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Message content
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.Enum('match_chat', 'booking_inquiry', 'general', 
                                    name='message_types'), default='general')
    
    # Related entities (optional)
    related_match_id = db.Column(db.Integer, db.ForeignKey('match_requests.id'))
    related_booking_id = db.Column(db.Integer, db.ForeignKey('booking_requests.id'))
    
    # Message status
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    related_match = db.relationship('MatchRequest', backref='messages')
    related_booking = db.relationship('BookingRequest', backref='messages')
    
    def __repr__(self):
        return f'<Message {self.sender.username} -> {self.receiver.username}>'
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            db.session.commit()
    
    def get_time_since_sent(self):
        """Get human-readable time since message was sent"""
        if not self.created_at:
            return "Unknown"
            
        now = datetime.utcnow()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    
    def get_conversation_partner(self, current_user_id):
        """Get the other user in this conversation"""
        if self.sender_id == current_user_id:
            return self.receiver
        else:
            return self.sender
    
    def is_sent_by(self, user_id):
        """Check if message was sent by specific user"""
        return self.sender_id == user_id
    
    def get_context_info(self):
        """Get context information about the message"""
        if self.related_match:
            return {
                'type': 'match',
                'context': f"Re: Match request with {self.related_match.target.user.username}"
            }
        elif self.related_booking:
            return {
                'type': 'booking',
                'context': f"Re: Booking at {self.related_booking.court.name}"
            }
        else:
            return {
                'type': 'general',
                'context': None
            }
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.get_display_name(),
            'receiver_id': self.receiver_id,
            'receiver_name': self.receiver.get_display_name(),
            'content': self.content,
            'message_type': self.message_type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'time_since_sent': self.get_time_since_sent(),
            'context': self.get_context_info()
        }

class Conversation:
    """Helper class to manage conversations between two users"""
    
    @staticmethod
    def get_messages_between(user1_id, user2_id, limit=50):
        """Get messages between two users"""
        return Message.query.filter(
            db.or_(
                db.and_(Message.sender_id == user1_id, Message.receiver_id == user2_id),
                db.and_(Message.sender_id == user2_id, Message.receiver_id == user1_id)
            )
        ).order_by(Message.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_user_conversations(user_id, limit=20):
        """Get all conversations for a user with the latest message"""
        # Get all users this user has exchanged messages with
        sent_to = db.session.query(Message.receiver_id).filter(Message.sender_id == user_id).distinct()
        received_from = db.session.query(Message.sender_id).filter(Message.receiver_id == user_id).distinct()
        
        conversation_user_ids = sent_to.union(received_from).all()
        conversations = []
        
        for (other_user_id,) in conversation_user_ids:
            # Get the latest message between these users
            latest_message = Message.query.filter(
                db.or_(
                    db.and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
                    db.and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
                )
            ).order_by(Message.created_at.desc()).first()
            
            if latest_message:
                # Count unread messages from the other user
                unread_count = Message.query.filter(
                    Message.sender_id == other_user_id,
                    Message.receiver_id == user_id,
                    Message.is_read == False
                ).count()
                
                from models.user import User
                other_user = User.query.get(other_user_id)
                
                conversations.append({
                    'other_user': other_user,
                    'latest_message': latest_message,
                    'unread_count': unread_count
                })
        
        # Sort by latest message timestamp
        conversations.sort(key=lambda x: x['latest_message'].created_at, reverse=True)
        return conversations[:limit]
    
    @staticmethod
    def mark_conversation_as_read(user_id, other_user_id):
        """Mark all messages from other_user to user as read"""
        unread_messages = Message.query.filter(
            Message.sender_id == other_user_id,
            Message.receiver_id == user_id,
            Message.is_read == False
        ).all()
        
        for message in unread_messages:
            message.mark_as_read()
    
    @staticmethod
    def send_message(sender_id, receiver_id, content, message_type='general', 
                    related_match_id=None, related_booking_id=None):
        """Send a new message"""
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type,
            related_match_id=related_match_id,
            related_booking_id=related_booking_id
        )
        
        db.session.add(message)
        db.session.commit()
        return message