"""
Email and EmailThread Models for AI Email Assistant
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from app import db

class Email(db.Model):
    """Email model for storing email information"""
    
    __tablename__ = 'emails'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String(255), unique=True, nullable=False, index=True)  # Outlook message ID
    conversation_id = Column(String(255), index=True)  # For threading
    
    # User relationship
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Email metadata
    subject = Column(String(255), nullable=False)
    sender_email = Column(String(255), nullable=False, index=True)
    sender_name = Column(String(255))
    
    # Recipients
    to_recipients = Column(JSON)  # List of recipient objects
    cc_recipients = Column(JSON)  # List of CC recipient objects
    bcc_recipients = Column(JSON)  # List of BCC recipient objects
    
    # Email content
    body_preview = Column(Text)  # Short preview text
    body_content = Column(Text)  # Full email body (HTML or plain text)
    body_content_type = Column(String(20), default='html')  # 'html' or 'text'
    
    # Timestamps
    received_date = Column(DateTime, nullable=False, index=True)
    sent_date = Column(DateTime, index=True)
    
    # Email properties
    importance = Column(String(20), default='normal')  # low, normal, high
    is_read = Column(Boolean, default=False, index=True)
    is_draft = Column(Boolean, default=False)
    is_sent_item = Column(Boolean, default=False, index=True)
    has_attachments = Column(Boolean, default=False)
    
    # Categories and tags
    categories = Column(JSON)  # Outlook categories
    ai_tags = Column(JSON)  # AI-generated tags
    ai_summary = Column(Text)  # AI-generated summary
    ai_sentiment = Column(String(20))  # positive, negative, neutral
    ai_priority_score = Column(Integer)  # 1-10 AI-determined priority
    
    # Vector embeddings reference
    embedding_id = Column(String(255))  # Reference to vector DB
    
    # Folder information
    folder_id = Column(String(255))
    folder_name = Column(String(255))
    
    # Thread relationship
    thread_id = Column(Integer, ForeignKey('email_threads.id'), index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    thread = relationship('EmailThread', back_populates='emails')
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self, include_body=False):
        """Convert email object to dictionary"""
        data = {
            'id': self.id,
            'message_id': self.message_id,
            'conversation_id': self.conversation_id,
            'subject': self.subject,
            'sender_email': self.sender_email,
            'sender_name': self.sender_name,
            'to_recipients': self.to_recipients or [],
            'cc_recipients': self.cc_recipients or [],
            'bcc_recipients': self.bcc_recipients or [],
            'body_preview': self.body_preview,
            'body_content_type': self.body_content_type,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'importance': self.importance,
            'is_read': self.is_read,
            'is_draft': self.is_draft,
            'is_sent_item': self.is_sent_item,
            'has_attachments': self.has_attachments,
            'categories': self.categories or [],
            'ai_tags': self.ai_tags or [],
            'ai_summary': self.ai_summary,
            'ai_sentiment': self.ai_sentiment,
            'ai_priority_score': self.ai_priority_score,
            'folder_name': self.folder_name,
            'thread_id': self.thread_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_body:
            data['body_content'] = self.body_content
        
        return data
    
    def get_recipients_list(self):
        """Get all recipients as a flat list"""
        recipients = []
        if self.to_recipients:
            recipients.extend([r.get('emailAddress', {}).get('address', '') for r in self.to_recipients])
        if self.cc_recipients:
            recipients.extend([r.get('emailAddress', {}).get('address', '') for r in self.cc_recipients])
        return list(set(recipients))  # Remove duplicates
    
    def update_ai_analysis(self, summary=None, tags=None, sentiment=None, priority_score=None):
        """Update AI analysis results"""
        if summary:
            self.ai_summary = summary
        if tags:
            self.ai_tags = tags if isinstance(tags, list) else [tags]
        if sentiment:
            self.ai_sentiment = sentiment
        if priority_score:
            self.ai_priority_score = priority_score
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def find_by_message_id(message_id):
        """Find email by message ID"""
        return Email.query.filter_by(message_id=message_id).first()
    
    @staticmethod
    def get_user_emails(user_id, folder=None, is_read=None, limit=50, offset=0):
        """Get emails for a specific user with filters"""
        query = Email.query.filter_by(user_id=user_id)
        
        if folder:
            query = query.filter_by(folder_name=folder)
        if is_read is not None:
            query = query.filter_by(is_read=is_read)
        
        return query.order_by(db.desc(Email.received_date)).offset(offset).limit(limit).all()
    
    @staticmethod
    def search_emails(user_id, search_term, limit=50):
        """Search emails by content"""
        return Email.query.filter(
            Email.user_id == user_id,
            db.or_(
                Email.subject.contains(search_term),
                Email.body_preview.contains(search_term),
                Email.sender_name.contains(search_term),
                Email.sender_email.contains(search_term)
            )
        ).order_by(db.desc(Email.received_date)).limit(limit).all()
    
    def __repr__(self):
        return f'<Email {self.subject[:50]}... from {self.sender_email}>'


class EmailThread(db.Model):
    """Email thread model for grouping related emails"""
    
    __tablename__ = 'email_threads'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Thread metadata
    subject = Column(String(255), nullable=False)
    participants = Column(JSON)  # List of all participants in the thread
    
    # Thread statistics
    message_count = Column(Integer, default=0)
    unread_count = Column(Integer, default=0)
    
    # Timestamps
    first_message_date = Column(DateTime, index=True)
    last_message_date = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # AI analysis
    ai_thread_summary = Column(Text)
    ai_thread_sentiment = Column(String(20))
    ai_action_required = Column(Boolean, default=False)
    
    # Relationships
    emails = relationship('Email', back_populates='thread', order_by='Email.received_date')
    
    def to_dict(self):
        """Convert thread object to dictionary"""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'subject': self.subject,
            'participants': self.participants or [],
            'message_count': self.message_count,
            'unread_count': self.unread_count,
            'first_message_date': self.first_message_date.isoformat() if self.first_message_date else None,
            'last_message_date': self.last_message_date.isoformat() if self.last_message_date else None,
            'ai_thread_summary': self.ai_thread_summary,
            'ai_thread_sentiment': self.ai_thread_sentiment,
            'ai_action_required': self.ai_action_required,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def update_thread_stats(self):
        """Update thread statistics based on emails"""
        emails = self.emails
        self.message_count = len(emails)
        self.unread_count = sum(1 for email in emails if not email.is_read)
        
        if emails:
            self.first_message_date = min(email.received_date for email in emails)
            self.last_message_date = max(email.received_date for email in emails)
            
            # Update participants
            participants = set()
            for email in emails:
                participants.add(email.sender_email)
                participants.update(email.get_recipients_list())
            self.participants = list(participants)
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def find_by_conversation_id(conversation_id):
        """Find thread by conversation ID"""
        return EmailThread.query.filter_by(conversation_id=conversation_id).first()
    
    def __repr__(self):
        return f'<EmailThread {self.subject[:50]}... ({self.message_count} messages)>'


# Create indexes for better query performance
Index('idx_emails_user_received', Email.user_id, Email.received_date.desc())
Index('idx_emails_user_read_received', Email.user_id, Email.is_read, Email.received_date.desc())
Index('idx_emails_user_sent_received', Email.user_id, Email.is_sent_item, Email.received_date.desc())