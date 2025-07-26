"""
Email model for AI Email Assistant
"""
from datetime import datetime
from app.models import db

class Email(db.Model):
    __tablename__ = 'emails'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Microsoft Graph email ID
    graph_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Email metadata
    subject = db.Column(db.Text, nullable=True)
    sender_email = db.Column(db.String(255), nullable=True, index=True)
    sender_name = db.Column(db.String(255), nullable=True)
    recipient_emails = db.Column(db.JSON, default=list)  # List of recipient emails
    cc_emails = db.Column(db.JSON, default=list)  # List of CC emails
    bcc_emails = db.Column(db.JSON, default=list)  # List of BCC emails
    
    # Email content
    body_text = db.Column(db.Text, nullable=True)
    body_html = db.Column(db.Text, nullable=True)
    body_preview = db.Column(db.Text, nullable=True)  # First 150 chars
    
    # Email properties
    importance = db.Column(db.String(20), default='normal')  # low, normal, high
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_draft = db.Column(db.Boolean, default=False, nullable=False)
    has_attachments = db.Column(db.Boolean, default=False, nullable=False)
    attachment_count = db.Column(db.Integer, default=0)
    
    # Conversation and threading
    conversation_id = db.Column(db.String(255), nullable=True, index=True)
    thread_id = db.Column(db.String(255), nullable=True, index=True)
    
    # Timestamps
    received_date = db.Column(db.DateTime, nullable=True, index=True)
    sent_date = db.Column(db.DateTime, nullable=True)
    created_date = db.Column(db.DateTime, nullable=True)
    last_modified = db.Column(db.DateTime, nullable=True)
    
    # AI Analysis fields
    ai_summary = db.Column(db.Text, nullable=True)
    ai_tags = db.Column(db.JSON, default=list)  # List of AI-generated tags
    ai_sentiment = db.Column(db.String(20), nullable=True)  # positive, negative, neutral
    ai_priority_score = db.Column(db.Integer, default=5)  # 1-10 scale
    ai_category = db.Column(db.String(50), nullable=True)
    ai_action_items = db.Column(db.JSON, default=list)  # List of detected action items
    ai_analyzed_at = db.Column(db.DateTime, nullable=True)
    
    # Sync and metadata
    sync_status = db.Column(db.String(20), default='synced')  # synced, pending, error
    sync_error = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Email {self.id}: {self.subject[:50] if self.subject else "No Subject"}>'
    
    def to_dict(self, include_body=False):
        """Convert email to dictionary"""
        data = {
            'id': self.id,
            'graph_id': self.graph_id,
            'subject': self.subject,
            'sender_email': self.sender_email,
            'sender_name': self.sender_name,
            'recipient_emails': self.recipient_emails or [],
            'cc_emails': self.cc_emails or [],
            'body_preview': self.body_preview,
            'importance': self.importance,
            'is_read': self.is_read,
            'is_draft': self.is_draft,
            'has_attachments': self.has_attachments,
            'attachment_count': self.attachment_count,
            'conversation_id': self.conversation_id,
            'thread_id': self.thread_id,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'ai_summary': self.ai_summary,
            'ai_tags': self.ai_tags or [],
            'ai_sentiment': self.ai_sentiment,
            'ai_priority_score': self.ai_priority_score,
            'ai_category': self.ai_category,
            'ai_action_items': self.ai_action_items or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_body:
            data.update({
                'body_text': self.body_text,
                'body_html': self.body_html
            })
        
        return data
    
    @classmethod
    def find_by_graph_id(cls, graph_id):
        """Find email by Microsoft Graph ID"""
        return cls.query.filter_by(graph_id=graph_id).first()
    
    @classmethod
    def get_user_emails(cls, user_id, limit=50, offset=0, unread_only=False):
        """Get emails for a user"""
        query = cls.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        return query.order_by(cls.received_date.desc()).offset(offset).limit(limit).all()
    
    @classmethod
    def get_by_sender(cls, user_id, sender_email, limit=10):
        """Get emails from specific sender"""
        return cls.query.filter_by(
            user_id=user_id,
            sender_email=sender_email
        ).order_by(cls.received_date.desc()).limit(limit).all()
    
    @classmethod
    def get_by_conversation(cls, conversation_id, limit=20):
        """Get emails in same conversation"""
        return cls.query.filter_by(
            conversation_id=conversation_id
        ).order_by(cls.received_date.asc()).limit(limit).all()
    
    def mark_as_read(self):
        """Mark email as read"""
        self.is_read = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_unread(self):
        """Mark email as unread"""
        self.is_read = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_ai_analysis(self, summary=None, tags=None, sentiment=None, 
                          priority_score=None, category=None, action_items=None):
        """Update AI analysis results"""
        if summary:
            self.ai_summary = summary
        if tags:
            self.ai_tags = tags
        if sentiment:
            self.ai_sentiment = sentiment
        if priority_score:
            self.ai_priority_score = priority_score
        if category:
            self.ai_category = category
        if action_items:
            self.ai_action_items = action_items
        
        self.ai_analyzed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def get_related_emails(self, limit=5):
        """Get related emails (same conversation or sender)"""
        related = []
        
        # Get emails from same conversation
        if self.conversation_id:
            conversation_emails = Email.get_by_conversation(self.conversation_id, limit)
            related.extend([e for e in conversation_emails if e.id != self.id])
        
        # Get recent emails from same sender
        if len(related) < limit and self.sender_email:
            sender_emails = Email.get_by_sender(self.user_id, self.sender_email, limit)
            for email in sender_emails:
                if email.id != self.id and email not in related:
                    related.append(email)
                if len(related) >= limit:
                    break
        
        return related[:limit]
    
    def get_user(self):
        """Get the user who owns this email"""
        # Import here to avoid circular imports
        from app.models.user import User
        return User.query.get(self.user_id)