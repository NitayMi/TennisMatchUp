from models.database import db
from datetime import datetime
from sqlalchemy.orm import relationship

class Conversation(db.Model):
    """Production conversation model with enhanced features"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_type = db.Column(db.String(20), nullable=False, default='direct')  # direct, support
    title = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    participants = relationship('ConversationParticipant', back_populates='conversation', cascade='all, delete-orphan')
    messages = relationship('Message', back_populates='conversation', cascade='all, delete-orphan')
    
    def get_other_participant(self, current_user_id):
        """Get the other participant in a direct conversation"""
        for participant in self.participants:
            if participant.user_id != current_user_id and participant.is_active:
                return participant
        return None
    
    def get_unread_count(self, user_id):
        """Get unread message count for a specific user"""
        participant = self.get_participant(user_id)
        if not participant:
            return 0
        
        from models.message import Message
        return db.session.query(db.func.count(Message.id)).filter(
            Message.conversation_id == self.id,
            Message.sender_id != user_id,
            Message.created_at > (participant.last_read_at or participant.joined_at)
        ).scalar() or 0
    
    def get_participant(self, user_id):
        """Get specific participant by user ID"""
        return next((p for p in self.participants if p.user_id == user_id and p.is_active), None)
    
    def mark_as_read(self, user_id):
        """Mark conversation as read for specific user"""
        participant = self.get_participant(user_id)
        if participant:
            participant.last_read_at = datetime.utcnow()
            db.session.commit()

class ConversationParticipant(db.Model):
    """Conversation participants with roles and read tracking"""
    __tablename__ = 'conversation_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='participant')  # participant, admin, observer
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_read_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    conversation = relationship('Conversation', back_populates='participants')
    user = relationship('User', backref='conversation_participations')
    
    __table_args__ = (
        db.UniqueConstraint('conversation_id', 'user_id'),
    )

class MessageReadStatus(db.Model):
    """Track message read status per user"""
    __tablename__ = 'message_read_status'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('message_id', 'user_id'),
    )

class MessageReaction(db.Model):
    """Message reactions (like, love, etc.)"""
    __tablename__ = 'message_reactions'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)  # like, love, laugh, angry
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('message_id', 'user_id', 'reaction_type'),
    )