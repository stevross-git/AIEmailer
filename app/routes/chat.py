"""
Chat Message Model for AI Email Assistant
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Index
from app import db

class ChatMessage(db.Model):
    """Chat message model for storing conversation history"""
    
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    
    # User relationship
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Message content
    message = Column(Text, nullable=False)
    response = Column(Text)
    
    # Message metadata
    message_type = Column(String(20), default='query')  # query, command, system
    context_type = Column(String(50))  # email, thread, general, search
    context_data = Column(JSON)  # Additional context information
    
    # AI model information
    model_used = Column(String(100))  # Which AI model was used
    response_time_ms = Column(Integer)  # Response time in milliseconds
    token_count = Column(Integer)  # Number of tokens used
    
    # Message status
    is_processed = Column(Boolean, default=False)
    has_error = Column(Boolean, default=False)
    error_message = Column(Text)
    
    # Ratings and feedback
    user_rating = Column(Integer)  # 1-5 rating from user
    user_feedback = Column(Text)
    
    # Related entities
    related_email_ids = Column(JSON)  # List of email IDs referenced
    related_thread_ids = Column(JSON)  # List of thread IDs referenced
    
    # Session information
    session_id = Column(String(255), index=True)
    conversation_turn = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed_at = Column(DateTime)
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self, include_context=False):
        """Convert chat message object to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'response': self.response,
            'message_type': self.message_type,
            'context_type': self.context_type,
            'model_used': self.model_used,
            'response_time_ms': self.response_time_ms,
            'token_count': self.token_count,
            'is_processed': self.is_processed,
            'has_error': self.has_error,
            'error_message': self.error_message,
            'user_rating': self.user_rating,
            'user_feedback': self.user_feedback,
            'session_id': self.session_id,
            'conversation_turn': self.conversation_turn,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
        
        if include_context:
            data['context_data'] = self.context_data or {}
            data['related_email_ids'] = self.related_email_ids or []
            data['related_thread_ids'] = self.related_thread_ids or []
        
        return data
    
    def update_response(self, response, model_used=None, response_time_ms=None, token_count=None):
        """Update message with AI response"""
        self.response = response
        self.is_processed = True
        self.processed_at = datetime.utcnow()
        
        if model_used:
            self.model_used = model_used
        if response_time_ms:
            self.response_time_ms = response_time_ms
        if token_count:
            self.token_count = token_count
        
        db.session.commit()
    
    def set_error(self, error_message):
        """Set error state for message"""
        self.has_error = True
        self.error_message = error_message
        self.is_processed = True
        self.processed_at = datetime.utcnow()
        db.session.commit()
    
    def add_rating(self, rating, feedback=None):
        """Add user rating and feedback"""
        self.user_rating = rating
        if feedback:
            self.user_feedback = feedback
        db.session.commit()
    
    def add_related_emails(self, email_ids):
        """Add related email IDs"""
        if not isinstance(email_ids, list):
            email_ids = [email_ids]
        
        current_ids = self.related_email_ids or []
        self.related_email_ids = list(set(current_ids + email_ids))
        db.session.commit()
    
    def add_related_threads(self, thread_ids):
        """Add related thread IDs"""
        if not isinstance(thread_ids, list):
            thread_ids = [thread_ids]
        
        current_ids = self.related_thread_ids or []
        self.related_thread_ids = list(set(current_ids + thread_ids))
        db.session.commit()
    
    @staticmethod
    def get_user_conversation(user_id, session_id=None, limit=50):
        """Get conversation history for a user"""
        query = ChatMessage.query.filter_by(user_id=user_id)
        
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        return query.order_by(db.desc(ChatMessage.created_at)).limit(limit).all()
    
    @staticmethod
    def get_recent_messages(user_id, limit=10):
        """Get recent messages for a user"""
        return ChatMessage.query.filter_by(
            user_id=user_id,
            is_processed=True,
            has_error=False
        ).order_by(db.desc(ChatMessage.created_at)).limit(limit).all()
    
    @staticmethod
    def get_session_messages(session_id):
        """Get all messages for a specific session"""
        return ChatMessage.query.filter_by(session_id=session_id).order_by(
            ChatMessage.conversation_turn
        ).all()
    
    @staticmethod
    def get_unprocessed_messages(limit=100):
        """Get unprocessed messages for background processing"""
        return ChatMessage.query.filter_by(
            is_processed=False,
            has_error=False
        ).order_by(ChatMessage.created_at).limit(limit).all()
    
    @staticmethod
    def get_user_stats(user_id):
        """Get chat statistics for a user"""
        total_messages = ChatMessage.query.filter_by(user_id=user_id).count()
        processed_messages = ChatMessage.query.filter_by(
            user_id=user_id, 
            is_processed=True
        ).count()
        error_messages = ChatMessage.query.filter_by(
            user_id=user_id, 
            has_error=True
        ).count()
        
        # Average response time
        avg_response_time = db.session.query(
            db.func.avg(ChatMessage.response_time_ms)
        ).filter_by(
            user_id=user_id,
            is_processed=True,
            has_error=False
        ).scalar()
        
        # Average rating
        avg_rating = db.session.query(
            db.func.avg(ChatMessage.user_rating)
        ).filter_by(user_id=user_id).filter(
            ChatMessage.user_rating.isnot(None)
        ).scalar()
        
        return {
            'total_messages': total_messages,
            'processed_messages': processed_messages,
            'error_messages': error_messages,
            'success_rate': (processed_messages - error_messages) / max(processed_messages, 1) * 100,
            'avg_response_time_ms': int(avg_response_time) if avg_response_time else 0,
            'avg_rating': round(avg_rating, 2) if avg_rating else None
        }
    
    def __repr__(self):
        return f'<ChatMessage {self.id}: {self.message[:50]}...>'


# Create indexes for better query performance
Index('idx_chat_messages_user_session', ChatMessage.user_id, ChatMessage.session_id)
Index('idx_chat_messages_user_created', ChatMessage.user_id, ChatMessage.created_at.desc())
Index('idx_chat_messages_processed', ChatMessage.is_processed, ChatMessage.has_error)