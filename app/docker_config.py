"""
Docker-based Configuration
"""
import os
from datetime import timedelta

class DockerConfig:
    """Docker-based configuration for development"""
    
    # Flask Core Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # PostgreSQL Database Configuration (Docker)
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'ai_email_assistant')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'ai_email_user')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'ai_email_password123')
    
    SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
    
    # Redis Configuration (Docker)
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    
    # Session Configuration (using Redis)
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'ai_email_'
    SESSION_REDIS_HOST = REDIS_HOST
    SESSION_REDIS_PORT = REDIS_PORT
    SESSION_REDIS_DB = REDIS_DB
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Cookie Configuration
    SESSION_COOKIE_NAME = 'ai_email_session'
    SESSION_COOKIE_DOMAIN = None
    SESSION_COOKIE_PATH = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Microsoft Azure AD Configuration
    AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
    AZURE_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
    AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID')
    AZURE_REDIRECT_URI = os.getenv('AZURE_REDIRECT_URI', 'http://localhost:5000/auth/callback')
    
    # Microsoft Graph API
    GRAPH_API_ENDPOINT = os.getenv('GRAPH_API_ENDPOINT', 'https://graph.microsoft.com/v1.0')
    GRAPH_SCOPES = os.getenv('GRAPH_SCOPES', 'User.Read,Mail.Read,Mail.Send,Mail.ReadWrite,Calendars.Read').split(',')
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'deepseek-r1:7b')
    OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '120'))
    OLLAMA_STREAM = os.getenv('OLLAMA_STREAM', 'true').lower() == 'true'
    
    # ChromaDB Configuration (Docker)
    CHROMADB_HOST = os.getenv('CHROMADB_HOST', 'localhost')
    CHROMADB_PORT = int(os.getenv('CHROMADB_PORT', '8000'))
    CHROMADB_URL = f'http://{CHROMADB_HOST}:{CHROMADB_PORT}'
    
    # Vector Database Configuration
    VECTOR_DB_TYPE = os.getenv('VECTOR_DB_TYPE', 'chromadb')
    VECTOR_DB_PATH = CHROMADB_URL  # Use HTTP endpoint for Docker ChromaDB
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    VECTOR_COLLECTION_NAME = os.getenv('VECTOR_COLLECTION_NAME', 'email_embeddings')
    
    # Email Processing Configuration
    MAX_EMAILS_PER_SYNC = int(os.getenv('MAX_EMAILS_PER_SYNC', '500'))
    EMAIL_SYNC_INTERVAL_MINUTES = int(os.getenv('EMAIL_SYNC_INTERVAL_MINUTES', '30'))
    INDEX_SENT_ITEMS = os.getenv('INDEX_SENT_ITEMS', 'true').lower() == 'true'
    INDEX_INBOX = os.getenv('INDEX_INBOX', 'true').lower() == 'true'
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/app.log')
    
    # Windows-specific Configuration
    USE_WINDOWS_CREDENTIAL_MANAGER = os.getenv('USE_WINDOWS_CREDENTIAL_MANAGER', 'true').lower() == 'true'
    WINDOWS_SERVICE_NAME = os.getenv('WINDOWS_SERVICE_NAME', 'AIEmailAssistant')
    
    # SocketIO Configuration
    SOCKETIO_ASYNC_MODE = 'threading'
    
    @staticmethod
    def init_app(app):
        """Initialize configuration-specific setup"""
        # Create necessary directories
        os.makedirs('./logs', exist_ok=True)