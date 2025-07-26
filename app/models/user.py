"""
User model for AI Email Assistant
"""
from datetime import datetime
from app.models import db

class User(db.Model):
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # User information
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=True)
    
    # Azure/Microsoft Graph information
    azure_id = db.Column(db.String(100), unique=True, nullable=True, index=True)
    azure_tenant_id = db.Column(db.String(100), nullable=True)
    
    # Authentication tokens (hashed)
    access_token_hash = db.Column(db.Text, nullable=True)
    refresh_token_hash = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    
    # User preferences
    preferences = db.Column(db.JSON, default=dict)
    timezone = db.Column(db.String(50), default='UTC')
    
    # Status and metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    last_email_sync = db.Column(db.DateTime, nullable=True)
    email_sync_cursor = db.Column(db.String(255), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'display_name': self.display_name,
            'azure_id': self.azure_id,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_email_sync': self.last_email_sync.isoformat() if self.last_email_sync else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'preferences': self.preferences or {},
            'timezone': self.timezone
        }
    
    @classmethod
    def find_by_email(cls, email):
        """Find user by email address"""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def find_by_azure_id(cls, azure_id):
        """Find user by Azure ID"""
        return cls.query.filter_by(azure_id=azure_id).first()
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def update_sync_info(self, cursor=None):
        """Update email sync information"""
        self.last_email_sync = datetime.utcnow()
        if cursor:
            self.email_sync_cursor = cursor
        db.session.commit()
    
    def get_email_count(self):
        """Get count of user's emails"""
        # Import here to avoid circular imports
        from app.models.email import Email
        return Email.query.filter_by(user_id=self.id).count()
    
    def get_unread_email_count(self):
        """Get count of user's unread emails"""
        # Import here to avoid circular imports
        from app.models.email import Email
        return Email.query.filter_by(user_id=self.id, is_read=False).count()