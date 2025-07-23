"""
Email model for AI Email Assistant
"""
from . import db
from datetime import datetime

class Email(db.Model):
    """Email model to store email data"""
    __tablename__ = 'email'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.String(255), nullable=False, index=True)
    
    # Email metadata
    subject = db.Column(db.String(500), nullable=True)
    sender_email = db.Column(db.String(255), nullable=True, index=True)
    sender_name = db.Column(db.String(255), nullable=True)
    
    # Email content fields
    body_text = db.Column(db.Text, nullable=True)
    body_html = db.Column(db.Text, nullable=True)
    body_preview = db.Column(db.String(500), nullable=True)
    
    # Email properties
    received_date = db.Column(db.DateTime, nullable=True, index=True)
    sent_date = db.Column(db.DateTime, nullable=True)
    importance = db.Column(db.String(20), nullable=True, default='normal')
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    is_draft = db.Column(db.Boolean, nullable=False, default=False)
    has_attachments = db.Column(db.Boolean, nullable=False, default=False)
    
    # Organization
    folder = db.Column(db.String(100), nullable=True, default='inbox', index=True)
    conversation_id = db.Column(db.String(255), nullable=True, index=True)
    
    # AI analysis
    category = db.Column(db.String(100), nullable=True, index=True)
    priority_score = db.Column(db.Float, nullable=True)
    sentiment = db.Column(db.String(20), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    
    def __init__(self, **kwargs):
        """Initialize email with default values"""
        super(Email, self).__init__(**kwargs)
        if not self.received_date:
            self.received_date = datetime.utcnow()
    
    def __repr__(self):
        return f'<Email {self.id}: {self.subject}>'
    
    def to_dict(self):
        """Convert email to dictionary"""
        return {
            'id': self.id,
            'message_id': self.message_id,
            'subject': self.subject,
            'sender_email': self.sender_email,
            'sender_name': self.sender_name,
            'body_text': self.body_text,
            'body_html': self.body_html,
            'body_preview': self.body_preview,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'importance': self.importance,
            'is_read': self.is_read,
            'is_draft': self.is_draft,
            'has_attachments': self.has_attachments,
            'folder': self.folder,
            'conversation_id': self.conversation_id,
            'category': self.category,
            'priority_score': self.priority_score,
            'sentiment': self.sentiment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def display_date(self):
        """Get formatted display date"""
        if self.received_date:
            return self.received_date.strftime('%B %d, %Y at %I:%M %p')
        return 'Unknown'
    
    @property
    def short_preview(self):
        """Get short preview of email content"""
        if self.body_preview:
            return self.body_preview[:100] + '...' if len(self.body_preview) > 100 else self.body_preview
        elif self.body_text:
            preview = self.body_text.strip()[:100]
            return preview + '...' if len(self.body_text) > 100 else preview
        return 'No preview available'
    
    @property
    def has_content(self):
        """Check if email has any content"""
        return any([
            self.body_text and len(self.body_text.strip()) > 0,
            self.body_html and len(self.body_html.strip()) > 0,
            self.body_preview and len(self.body_preview.strip()) > 0
        ])
