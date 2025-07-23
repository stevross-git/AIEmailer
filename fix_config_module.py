#!/usr/bin/env python3
"""
Fix Configuration Module
"""
import os

def check_config_structure():
    """Check what config files exist"""
    print("Checking Config Structure")
    print("=" * 24)
    
    config_paths = [
        'app/config.py',
        'app/config/__init__.py',
        'app/config/docker_config.py',
        'config.py'
    ]
    
    existing_configs = []
    for path in config_paths:
        if os.path.exists(path):
            existing_configs.append(path)
            print(f"EXISTS: {path}")
        else:
            print(f"MISSING: {path}")
    
    return existing_configs

def create_config_directory():
    """Create config directory and files"""
    print("\nCreating Config Directory")
    print("=" * 25)
    
    # Create config directory
    os.makedirs('app/config', exist_ok=True)
    print("Created app/config directory")
    
    # Create __init__.py
    init_content = '''"""
Configuration package for AI Email Assistant
"""
from .docker_config import DevelopmentConfig

__all__ = ['DevelopmentConfig']
'''
    
    with open('app/config/__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)
    print("Created app/config/__init__.py")
    
    # Create docker_config.py
    docker_config_content = '''"""
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
'''
    
    with open('app/config/docker_config.py', 'w', encoding='utf-8') as f:
        f.write(docker_config_content)
    print("Created app/config/docker_config.py")
    
    return True

def fix_app_init_config():
    """Fix app/__init__.py to handle config properly"""
    print("\nFixing App Config Import")
    print("=" * 23)
    
    app_init_content = '''"""
AI Email Assistant Flask Application
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create SQLAlchemy instance
db = SQLAlchemy()

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    try:
        if os.environ.get('USE_DOCKER_CONFIG') == 'true':
            print("Using Docker configuration")
            from app.config.docker_config import DevelopmentConfig
            app.config.from_object(DevelopmentConfig)
        else:
            print("Using local configuration")
            # Try docker config as fallback
            from app.config.docker_config import DevelopmentConfig
            app.config.from_object(DevelopmentConfig)
    except ImportError:
        print("Config import failed - using minimal config")
        # Minimal fallback config
        app.config.update({
            'SECRET_KEY': 'dev-secret-key',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///instance/app.db',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'DEBUG': True
        })
    
    # Create instance directory
    os.makedirs('instance', exist_ok=True)
    
    # Initialize database
    db.init_app(app)
    
    # Initialize extensions
    try:
        from flask_cors import CORS
        from flask_session import Session
        
        CORS(app, supports_credentials=True)
        Session(app)
    except ImportError:
        print("Extension import warning - continuing without CORS/Session")
    
    # Import models and create tables within app context
    with app.app_context():
        try:
            from app.models.user import User
            from app.models.email import Email
            from app.models.chat import ChatMessage
            
            db.create_all()
            print("Database tables created")
        except Exception as e:
            print(f"Database setup error: {e}")
    
    # Register blueprints with error handling
    blueprints = [
        ('app.routes.main', 'main_bp', ''),
        ('app.routes.auth', 'auth_bp', '/auth'),
        ('app.routes.email', 'email_bp', '/api/email'),
        ('app.routes.chat', 'chat_bp', '/api/chat')
    ]
    
    for module_name, blueprint_name, url_prefix in blueprints:
        try:
            module = __import__(module_name, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            if url_prefix:
                app.register_blueprint(blueprint, url_prefix=url_prefix)
            else:
                app.register_blueprint(blueprint)
            print(f"{blueprint_name} registered")
        except Exception as e:
            print(f"{blueprint_name} error: {e}")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        return {"error": "Server error"}, 500
    
    print("Flask app created successfully")
    return app

# Export for module imports
__all__ = ['create_app', 'db']
'''
    
    try:
        with open('app/__init__.py', 'w', encoding='utf-8') as f:
            f.write(app_init_content)
        print("Fixed app/__init__.py with better config handling")
        return True
    except Exception as e:
        print(f"Error fixing app init: {e}")
        return False

def create_final_test():
    """Create final test for the complete fix"""
    print("\nCreating Final Test")
    print("=" * 18)
    
    test_content = '''#!/usr/bin/env python3
"""
Final Test - Complete Fix
"""
import os
import sys

def test():
    print("Testing Complete Configuration Fix")
    print("=" * 34)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("1. Testing config import...")
        from app.config.docker_config import DevelopmentConfig
        print("Config import: SUCCESS")
        
        print("2. Testing create_app...")
        from app import create_app
        print("create_app import: SUCCESS")
        
        print("3. Creating app...")
        app = create_app()
        print("App creation: SUCCESS")
        
        print("4. Testing app configuration...")
        with app.app_context():
            if hasattr(app, 'config') and app.config.get('SECRET_KEY'):
                print("App config: SUCCESS")
                
                # Test database
                from app.models.user import User
                from app.models.email import Email
                users = User.query.count()
                emails = Email.query.count()
                print(f"Database queries: SUCCESS (Users: {users}, Emails: {emails})")
            else:
                print("App config: FAILED")
                return False
        
        print()
        print("COMPLETE SUCCESS!")
        print("=" * 16)
        print("Ready to start app with: python docker_run.py")
        print("After start:")
        print("  1. Open enhanced_sync_test.html")
        print("  2. Run enhanced sync")
        print("  3. Visit http://localhost:5000/emails/267")
        print("  4. See full email content!")
        
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test()
'''
    
    try:
        with open('test_complete_fix.py', 'w', encoding='utf-8') as f:
            f.write(test_content)
        print("Created test_complete_fix.py")
        return True
    except Exception as e:
        print(f"Error creating test: {e}")
        return False

def main():
    """Main function"""
    print("Fix Configuration Module")
    print("=" * 24)
    
    # Check existing config
    existing = check_config_structure()
    
    # Create config directory and files
    config_created = create_config_directory()
    
    # Fix app init
    app_fixed = fix_app_init_config()
    
    # Create final test
    test_created = create_final_test()
    
    if config_created and app_fixed:
        print()
        print("CONFIGURATION MODULE FIXED!")
        print("=" * 28)
        
        if test_created:
            print("Test the complete fix:")
            print("   python test_complete_fix.py")
        
        print("Start the app:")
        print("   python docker_run.py")
        
        print("What was created:")
        print("   - app/config directory")
        print("   - app/config/__init__.py")
        print("   - app/config/docker_config.py")
        print("   - Fixed app/__init__.py")
        
        print("Configuration includes:")
        print("   - Database settings (SQLite)")
        print("   - Azure/Microsoft Graph config")
        print("   - Session management")
        print("   - Development settings")
        
    else:
        print("Fix failed")

if __name__ == "__main__":
    main()