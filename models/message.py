from models.database import db
from datetime import datetime

class Message(db.Model):
    """Message model for user communications"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    is_broadcast = db.Column(db.Boolean, default=False, nullable=False)
    message_type = db.Column(db.String(20), default='text', nullable=False)  # text, system, notification
    related_booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)
    attachment_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Enhanced fields for production chat
    reply_to_message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)
    is_edited = db.Column(db.Boolean, default=False, nullable=False)
    edited_at = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    attachment_type = db.Column(db.String(50), nullable=True)
    attachment_size = db.Column(db.Integer, nullable=True)
    
    # Relationships
    related_booking = db.relationship('Booking', backref='messages')
    reply_to = db.relationship('Message', remote_side='Message.id', backref='replies')
    
    def __init__(self, sender_id, receiver_id, content, message_type='text', is_broadcast=False):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.message_type = message_type
        self.is_broadcast = is_broadcast
        self.is_read = False
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            db.session.commit()
    
    def get_preview(self, max_length=100):
        """Get message preview"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."
    
    def get_message_type_display(self):
        """Get formatted message type"""
        type_mapping = {
            'text': 'Message',
            'system': 'System Message',
            'notification': 'Notification'
        }
        return type_mapping.get(self.message_type, self.message_type.title())
    
    def get_time_display(self):
        """Get formatted time display"""
        now = datetime.utcnow()
        diff = now - self.created_at
        
        if diff.days > 7:
            return self.created_at.strftime('%b %d, %Y')
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    def is_from_sender(self, user_id):
        """Check if message is from specific user"""
        return self.sender_id == user_id
    
    def is_to_receiver(self, user_id):
        """Check if message is to specific user"""
        return self.receiver_id == user_id
    
    def involves_user(self, user_id):
        """Check if message involves specific user"""
        return self.sender_id == user_id or self.receiver_id == user_id
    
    def to_dict(self):
        """Convert message to dictionary"""
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'content': self.content,
            'preview': self.get_preview(),
            'is_read': self.is_read,
            'is_broadcast': self.is_broadcast,
            'message_type': self.message_type,
            'message_type_display': self.get_message_type_display(),
            'related_booking_id': self.related_booking_id,
            'attachment_url': self.attachment_url,
            'time_display': self.get_time_display(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
    
    @staticmethod
    def get_conversation_messages(user1_id, user2_id):
        """Get all messages between two users"""
        return Message.query.filter(
            db.or_(
                db.and_(Message.sender_id == user1_id, Message.receiver_id == user2_id),
                db.and_(Message.sender_id == user2_id, Message.receiver_id == user1_id)
            )
        ).order_by(Message.created_at.asc()).all()
    
    @staticmethod
    def get_user_conversations(user_id):
        """Get all conversations for a user"""
        # Get all messages involving the user
        messages = Message.query.filter(
            db.or_(Message.sender_id == user_id, Message.receiver_id == user_id)
        ).order_by(Message.created_at.desc()).all()
        
        # Extract unique conversation partners
        partners = {}
        for msg in messages:
            partner_id = msg.receiver_id if msg.sender_id == user_id else msg.sender_id
            if partner_id not in partners:
                partners[partner_id] = {
                    'partner_id': partner_id,
                    'last_message_time': msg.created_at,
                    'last_message': msg
                }
        
        # Convert to list and sort by last message time
        conversations = list(partners.values())
        conversations.sort(key=lambda x: x['last_message_time'], reverse=True)
        
        return conversations
    
    @staticmethod
    def count_unread_messages(user_id):
        """Count unread messages for a user"""
        return Message.query.filter(
            Message.receiver_id == user_id,
            Message.is_read == False
        ).count()
    
    @staticmethod
    def mark_conversation_as_read(user_id, other_user_id):
        """Mark all messages in a conversation as read"""
        Message.query.filter(
            Message.sender_id == other_user_id,
            Message.receiver_id == user_id,
            Message.is_read == False
        ).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })
        db.session.commit()
    
    def __repr__(self):
        sender_name = self.sender.full_name if self.sender else "Unknown"
        receiver_name = self.receiver.full_name if self.receiver else "Unknown"
        return f'<Message from {sender_name} to {receiver_name}: {self.get_preview(50)}>'