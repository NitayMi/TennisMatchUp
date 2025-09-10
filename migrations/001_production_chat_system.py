"""Production chat system with conversations and enhanced messaging

Revision ID: 001_chat_system
Revises: base
Create Date: 2025-01-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001_chat_system'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create conversations table
    op.create_table('conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_type', sa.String(20), nullable=False, server_default='direct'),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create conversation_participants table
    op.create_table('conversation_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='participant'),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_read_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('conversation_id', 'user_id')
    )
    
    # Enhance existing messages table
    op.add_column('messages', sa.Column('conversation_id', sa.Integer(), nullable=True))
    op.add_column('messages', sa.Column('reply_to_message_id', sa.Integer(), nullable=True))
    op.add_column('messages', sa.Column('is_edited', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('messages', sa.Column('edited_at', sa.DateTime(), nullable=True))
    op.add_column('messages', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('messages', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('messages', sa.Column('attachment_type', sa.String(50), nullable=True))
    op.add_column('messages', sa.Column('attachment_size', sa.Integer(), nullable=True))
    
    # Add foreign key constraints
    op.create_foreign_key('fk_messages_conversation', 'messages', 'conversations', ['conversation_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_messages_reply', 'messages', 'messages', ['reply_to_message_id'], ['id'], ondelete='SET NULL')
    
    # Create message_read_status table
    op.create_table('message_read_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('message_id', 'user_id')
    )
    
    # Create message_reactions table
    op.create_table('message_reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('reaction_type', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('message_id', 'user_id', 'reaction_type')
    )
    
    # Create indexes for performance
    op.create_index('idx_conversations_type', 'conversations', ['conversation_type'])
    op.create_index('idx_participants_user', 'conversation_participants', ['user_id', 'is_active'])
    op.create_index('idx_messages_conversation_created', 'messages', ['conversation_id', 'created_at'])
    op.create_index('idx_messages_sender_created', 'messages', ['sender_id', 'created_at'])
    op.create_index('idx_read_status_user', 'message_read_status', ['user_id', 'read_at'])

def downgrade():
    # Drop new tables in reverse order
    op.drop_table('message_reactions')
    op.drop_table('message_read_status')
    
    # Remove foreign keys and columns from messages
    op.drop_constraint('fk_messages_reply', 'messages')
    op.drop_constraint('fk_messages_conversation', 'messages')
    op.drop_column('messages', 'attachment_size')
    op.drop_column('messages', 'attachment_type')
    op.drop_column('messages', 'deleted_at')
    op.drop_column('messages', 'is_deleted')
    op.drop_column('messages', 'edited_at')
    op.drop_column('messages', 'is_edited')
    op.drop_column('messages', 'reply_to_message_id')
    op.drop_column('messages', 'conversation_id')
    
    op.drop_table('conversation_participants')
    op.drop_table('conversations')