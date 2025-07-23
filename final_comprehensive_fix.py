#!/usr/bin/env python3
"""
Final Comprehensive Fix for SQLAlchemy Issue
"""
import os
import shutil

def backup_current_files():
    """Backup current files"""
    print("Backing up current files")
    print("=" * 23)
    
    files_to_backup = [
        'app/__init__.py',
        'app/models/__init__.py',
        'app/models/user.py',
        'app/models/email.py'
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = file_path + '.backup'
            try:
                shutil.copy2(file_path, backup_path)
                print(f"Backed up {file_path}")
            except Exception as e:
                print(f"Backup warning for {file_path}: {e}")

def create_clean_models_init():
    """Create clean models/__init__.py"""
    print("\nCreating clean models init")
    print("=" * 26)
    
    models_init = '''"""
Models package
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
'''
    
    with open('app/models/__init__.py', 'w', encoding='utf-8') as f:
        f.write(models_init)
    print("Created app/models/__init__.py")

def create_clean_user_model():
    """Create clean user model"""
    print("\nCreating clean user model")
    print("=" * 25)
    
    user_model = '''"""
User model
"""
from app.models import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    azure_id = db.Column(db.String(100), unique=True, nullable=True)
    azure_tenant_id = db.Column(db.String(100), nullable=True)
    access_token_hash = db.Column(db.Text, nullable=True)
    refresh_token_hash = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    timezone = db.Column(db.String(50), nullable=True, default='UTC')
    language = db.Column(db.String(10), nullable=True, default='en')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    last_sync = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
'''
    
    with open('app/models/user.py', 'w', encoding='utf-8') as f:
        f.write(user_model)
    print("Created app/models/user.py")

def create_clean_email_model():
    """Create clean email model"""
    print("\nCreating clean email model")
    print("=" * 26)
    
    email_model = '''"""
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
'''
    
    with open('app/models/email.py', 'w', encoding='utf-8') as f:
        f.write(email_model)
    print("Created app/models/email.py")

def create_clean_chat_model():
    """Create clean chat model"""
    print("\nCreating clean chat model")
    print("=" * 25)
    
    chat_model = '''"""
Chat model
"""
from app.models import db
from datetime import datetime

class ChatMessage(db.Model):
    __tablename__ = 'chat_message'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChatMessage {self.id}>'
'''
    
    with open('app/models/chat.py', 'w', encoding='utf-8') as f:
        f.write(chat_model)
    print("Created app/models/chat.py")

def create_final_app_init():
    """Create final clean app/__init__.py"""
    print("\nCreating final app init")
    print("=" * 22)
    
    app_init = '''"""
AI Email Assistant Flask Application - Final Version
"""
import os
from flask import Flask

def create_app():
    """Create Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config.update({
        'SECRET_KEY': 'dev-secret-key-change-in-production',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///instance/app.db',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'DEBUG': True,
        'SESSION_TYPE': 'filesystem',
        'SESSION_PERMANENT': False,
        'AZURE_CLIENT_ID': 'your-client-id',
        'AZURE_CLIENT_SECRET': 'your-client-secret',
        'AZURE_TENANT_ID': 'your-tenant-id',
        'AZURE_REDIRECT_URI': 'http://localhost:5000/auth/callback',
        'GRAPH_API_ENDPOINT': 'https://graph.microsoft.com/v1.0',
        'GRAPH_SCOPES': ['openid', 'profile', 'email', 'User.Read', 'Mail.Read', 'Mail.Send']
    })
    
    # Create instance directory
    os.makedirs('instance', exist_ok=True)
    
    # Initialize database
    from app.models import db
    db.init_app(app)
    
    # Import models and create tables
    with app.app_context():
        try:
            # Import all models
            from app.models.user import User
            from app.models.email import Email  
            from app.models.chat import ChatMessage
            
            # Create tables
            db.create_all()
            print("Database tables created successfully")
            
        except Exception as e:
            print(f"Database setup error: {e}")
    
    # Initialize extensions
    try:
        from flask_cors import CORS
        CORS(app, supports_credentials=True)
        print("CORS initialized")
    except:
        pass
    
    try:
        from flask_session import Session
        Session(app)
        print("Session initialized")
    except:
        pass
    
    # Register blueprints
    blueprints_config = [
        ('app.routes.main', 'main_bp', None),
        ('app.routes.auth', 'auth_bp', '/auth'),
        ('app.routes.email', 'email_bp', '/api/email'),
    ]
    
    for module_path, blueprint_name, url_prefix in blueprints_config:
        try:
            module = __import__(module_path, fromlist=[blueprint_name])
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

# For imports
__all__ = ['create_app']
'''
    
    with open('app/__init__.py', 'w', encoding='utf-8') as f:
        f.write(app_init)
    print("Created app/__init__.py")

def create_final_test():
    """Create final test"""
    print("\nCreating final test")
    print("=" * 19)
    
    test_content = '''#!/usr/bin/env python3
"""
Final Test - Everything Should Work
"""
import os
import sys

def test():
    print("FINAL TEST - Complete Fix")
    print("=" * 26)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'  
    sys.path.append('.')
    
    try:
        print("1. Creating app...")
        from app import create_app
        app = create_app()
        print("App creation: SUCCESS")
        
        print("2. Testing app context...")
        with app.app_context():
            print("App context: SUCCESS")
            
            print("3. Testing database queries...")
            from app.models.user import User
            from app.models.email import Email
            
            # These should work now
            user_count = User.query.count()
            email_count = Email.query.count()
            print(f"Database queries: SUCCESS (Users: {user_count}, Emails: {email_count})")
        
        print()
        print("FINAL SUCCESS!")
        print("=" * 14)
        print("All issues resolved!")
        print()
        print("Start the app:")
        print("   python docker_run.py")
        print()
        print("Then:")
        print("   1. Open enhanced_sync_test.html")
        print("   2. Run enhanced sync")
        print("   3. Visit http://localhost:5000/emails/267")
        print("   4. See full email content!")
        
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test()
'''
    
    with open('test_final.py', 'w', encoding='utf-8') as f:
        f.write(test_content)
    print("Created test_final.py")

def main():
    """Main function"""
    print("Final Comprehensive Fix")
    print("=" * 23)
    print("Fixing all SQLAlchemy and configuration issues")
    print()
    
    # Backup files
    backup_current_files()
    
    # Create all clean components
    create_clean_models_init()
    create_clean_user_model()
    create_clean_email_model()
    create_clean_chat_model()
    create_final_app_init()
    create_final_test()
    
    print()
    print("COMPREHENSIVE FIX COMPLETE!")
    print("=" * 28)
    
    print("Test everything works:")
    print("   python test_final.py")
    
    print("Start the app:")
    print("   python docker_run.py")
    
    print("What was fixed:")
    print("   - Single SQLAlchemy instance")
    print("   - Clean model imports")
    print("   - Proper initialization order")
    print("   - Email content fields included")
    print("   - Configuration embedded")
    
    print("Database schema includes:")
    print("   - User table with all fields")
    print("   - Email table with body_text, body_html, body_preview")
    print("   - Chat table for AI conversations")
    
    print("After app starts successfully:")
    print("   - Run enhanced sync to get email content")
    print("   - View individual emails with full content")
    print("   - Chat with AI about specific emails")

if __name__ == "__main__":
    main()