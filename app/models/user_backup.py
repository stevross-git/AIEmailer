from . import db
"""
User Model for AI Email Assistant
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from app import db

class User(db.Model):
    """User model for storing authenticated user information"""
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    azure_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    given_name = Column(String(255))
    surname = Column(String(255))
    job_title = Column(String(255))
    office_location = Column(String(255))
    preferred_language = Column(String(10))
    
    # Authentication tokens (encrypted)
    access_token_hash = Column(Text)  # Encrypted access token
    refresh_token_hash = Column(Text)  # Encrypted refresh token
    token_expires_at = Column(DateTime)
    
    # User preferences
    preferences = Column(JSON, default=dict)
    timezone = Column(String(50), default='UTC')
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime)
    last_sync = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    emails = db.relationship('Email', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, azure_id, email, display_name, **kwargs):
        self.azure_id = azure_id
        self.email = email
        self.display_name = display_name
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'azure_id': self.azure_id,
            'email': self.email,
            'display_name': self.display_name,
            'given_name': self.given_name,
            'surname': self.surname,
            'job_title': self.job_title,
            'office_location': self.office_location,
            'preferred_language': self.preferred_language,
            'preferences': self.preferences or {},
            'timezone': self.timezone,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def update_login_time(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def update_sync_time(self):
        """Update last sync timestamp"""
        self.last_sync = datetime.utcnow()
        db.session.commit()
    
    def update_preferences(self, preferences):
        """Update user preferences"""
        if self.preferences is None:
            self.preferences = {}
        self.preferences.update(preferences)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def get_preference(self, key, default=None):
        """Get a specific preference value"""
        if self.preferences is None:
            return default
        return self.preferences.get(key, default)
    
    def has_valid_token(self):
        """Check if user has a valid access token"""
        if not self.access_token_hash or not self.token_expires_at:
            return False
        return datetime.utcnow() < self.token_expires_at
    
    def get_email_count(self):
        """Get total number of emails for this user"""
        return self.emails.count()
    
    def get_recent_emails(self, limit=10):
        """Get recent emails for this user"""
        return self.emails.order_by(db.desc('received_date')).limit(limit).all()
    
    @staticmethod
    def find_by_azure_id(azure_id):
        """Find user by Azure ID"""
        return User.query.filter_by(azure_id=azure_id).first()
    
    @staticmethod
    def find_by_email(email):
        """Find user by email address"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def get_active_users():
        """Get all active users"""
        return User.query.filter_by(is_active=True).all()
    
    def __repr__(self):
        return f'<User {self.email}>'