"""
Chat model for AI Email Assistant
"""
from datetime import datetime
from app.models import db

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Message content
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    
    # Message type and context
    message_type = db.Column(db.String(50), default='general')  # general, email_specific, action
    context_type = db.Column(db.String(50), nullable=True)  # email, summary, compose
    context_id = db.Column(db.Integer, nullable=True)  # email_id or other context reference
    
    # AI processing information
    ai_model = db.Column(db.String(100), nullable=True)
    processing_time = db.Column(db.Float, nullable=True)  # Seconds
    confidence_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    
    # Message metadata
    extra_data = db.Column(db.JSON, default=dict)  # Additional context data
    intent = db.Column(db.String(100), nullable=True)  # Detected user intent
    entities = db.Column(db.JSON, default=list)  # Extracted entities
    
    # Status
    is_processed = db.Column(db.Boolean, default=False, nullable=False)
    processing_error = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<ChatMessage {self.id}: {self.message[:50]}...>'
    
    def to_dict(self):
        """Convert chat message to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'response': self.response,
            'message_type': self.message_type,
            'context_type': self.context_type,
            'context_id': self.context_id,
            'ai_model': self.ai_model,
            'processing_time': self.processing_time,
            'confidence_score': self.confidence_score,
            'extra_data': self.extra_data or {},
            'intent': self.intent,
            'entities': self.entities or [],
            'is_processed': self.is_processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
    
    @classmethod
    def get_user_chat_history(cls, user_id, limit=50, offset=0):
        """Get chat history for a user"""
        return cls.query.filter_by(user_id=user_id)\
                       .order_by(cls.created_at.desc())\
                       .offset(offset).limit(limit).all()
    
    @classmethod
    def get_email_specific_chat(cls, user_id, email_id, limit=20):
        """Get chat messages specific to an email"""
        return cls.query.filter_by(
            user_id=user_id,
            context_type='email',
            context_id=email_id
        ).order_by(cls.created_at.asc()).limit(limit).all()
    
    @classmethod
    def create_message(cls, user_id, message, context_type=None, context_id=None, message_type='general'):
        """Create a new chat message"""
        chat_message = cls(
            user_id=user_id,
            message=message,
            message_type=message_type,
            context_type=context_type,
            context_id=context_id
        )
        db.session.add(chat_message)
        db.session.commit()
        return chat_message
    
    def update_response(self, response, ai_model=None, processing_time=None, 
                       confidence_score=None, intent=None, entities=None):
        """Update the AI response for this message"""
        self.response = response
        self.is_processed = True
        self.processed_at = datetime.utcnow()
        
        if ai_model:
            self.ai_model = ai_model
        if processing_time:
            self.processing_time = processing_time
        if confidence_score:
            self.confidence_score = confidence_score
        if intent:
            self.intent = intent
        if entities:
            self.entities = entities
        
        db.session.commit()
    
    def mark_error(self, error_message):
        """Mark message as having a processing error"""
        self.processing_error = error_message
        self.is_processed = False
        self.processed_at = datetime.utcnow()
        db.session.commit()
    
    def get_context_email(self):
        """Get the email associated with this chat message if context_type is 'email'"""
        if self.context_type == 'email' and self.context_id:
            # Import here to avoid circular imports
            from app.models.email import Email
            return Email.query.get(self.context_id)
        return None
    
    def get_user(self):
        """Get the user who sent this message"""
        # Import here to avoid circular imports
        from app.models.user import User
        return User.query.get(self.user_id)