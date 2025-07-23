"""
Email model
"""
from app.models import db
from datetime import datetime

class Email(db.Model):
    __tablename__ = 'email'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_id = db.Column(db.String(255), nullable=False, index=True)
    subject = db.Column(db.String(500), nullable=True)
    sender_email = db.Column(db.String(255), nullable=True)
    sender_name = db.Column(db.String(255), nullable=True)
    
    # Content fields
    body_text = db.Column(db.Text, nullable=True)
    body_html = db.Column(db.Text, nullable=True)
    body_preview = db.Column(db.String(500), nullable=True)
    
    received_date = db.Column(db.DateTime, nullable=True)
    sent_date = db.Column(db.DateTime, nullable=True)
    importance = db.Column(db.String(20), nullable=True, default='normal')
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    is_draft = db.Column(db.Boolean, nullable=False, default=False)
    has_attachments = db.Column(db.Boolean, nullable=False, default=False)
    folder = db.Column(db.String(100), nullable=True, default='inbox')
    conversation_id = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    priority_score = db.Column(db.Float, nullable=True)
    sentiment = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Email {self.id}: {self.subject}>'
