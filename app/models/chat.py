"""
Chat models for AI Email Assistant - Fixed Relationships
"""
from datetime import datetime
from app import db

class ChatSession(db.Model):
    """Chat session model"""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Direct relationship to User (no backref to avoid conflicts)
    user = db.relationship('User', foreign_keys=[user_id])
    
    # Relationship to messages
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ChatSession {self.id}: {self.title[:30]}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'message_count': len(self.messages)
        }

class ChatMessage(db.Model):
    """Chat message model"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Optional extra data (renamed from metadata to avoid SQLAlchemy conflict)
    extra_data = db.Column(db.JSON, nullable=True)
    
    def __repr__(self):
        return f'<ChatMessage {self.id}: {self.role} - {self.content[:50]}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'extra_data': self.extra_data
        }
    
    @property
    def user_id(self):
        """Get user_id through session relationship"""
        return self.session.user_id if self.session else None
