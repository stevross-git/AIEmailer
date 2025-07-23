"""
User model for AI Email Assistant
"""
from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """User model for authentication and profile data"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic user info
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=True)
    
    # Microsoft Azure AD info
    azure_id = db.Column(db.String(100), unique=True, nullable=True, index=True)
    azure_tenant_id = db.Column(db.String(100), nullable=True)
    
    # Authentication tokens (encrypted)
    access_token_hash = db.Column(db.Text, nullable=True)
    refresh_token_hash = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    
    # User preferences
    timezone = db.Column(db.String(50), nullable=True, default='UTC')
    language = db.Column(db.String(10), nullable=True, default='en')
    
    # Account status
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    last_sync = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, **kwargs):
        """Initialize user with default values"""
        super(User, self).__init__(**kwargs)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'display_name': self.display_name,
            'azure_id': self.azure_id,
            'timezone': self.timezone,
            'language': self.language,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None
        }
    
    @property
    def is_authenticated(self):
        """Check if user is authenticated"""
        return self.access_token_hash is not None
    
    @property 
    def has_valid_token(self):
        """Check if user has valid access token"""
        if not self.access_token_hash:
            return False
        if not self.token_expires_at:
            return True  # Assume valid if no expiry set
        return self.token_expires_at > datetime.utcnow()
