"""
Docker Configuration for AI Email Assistant
"""
import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'ai_email_assistant:'
    
    # Azure/Microsoft Graph
    AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID') or 'your-client-id'
    AZURE_CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET') or 'your-client-secret'
    AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID') or 'your-tenant-id'
    AZURE_REDIRECT_URI = os.environ.get('AZURE_REDIRECT_URI') or 'http://localhost:5000/auth/callback'
    
    # Microsoft Graph API
    GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    GRAPH_SCOPES = [
        'openid',
        'profile', 
        'email',
        'User.Read',
        'Mail.Read',
        'Mail.Send',
        'Mail.ReadWrite'
    ]
    
    # Email settings
    MAX_EMAILS_PER_SYNC = 50
    EMAIL_SYNC_BATCH_SIZE = 20
    
    # AI/Chat settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or ''
    CHAT_MAX_HISTORY = 10
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Use SQLite for development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/app.db'
    
    # Relaxed CORS for development
    CORS_ORIGINS = ['http://localhost', 'http://localhost:5000', 'http://127.0.0.1:5000']
    
    # Development logging
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production database (PostgreSQL recommended)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:pass@localhost/aiemaildb'
    
    # Strict CORS for production
    CORS_ORIGINS = []  # Configure for your domain
    
    # Production logging
    LOG_LEVEL = 'INFO'

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    
    # In-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
