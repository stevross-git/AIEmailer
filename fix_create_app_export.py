#!/usr/bin/env python3
"""
Fix create_app Export Issue
"""
import os

def fix_app_init():
    """Fix the app/__init__.py to properly export create_app"""
    print("Fixing create_app Export")
    print("=" * 22)
    
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
    if os.environ.get('USE_DOCKER_CONFIG') == 'true':
        print("Using Docker configuration")
        from app.config.docker_config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    else:
        print("Using local configuration") 
        from app.config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # Initialize database
    db.init_app(app)
    
    # Initialize extensions
    from flask_cors import CORS
    from flask_session import Session
    
    CORS(app, supports_credentials=True)
    Session(app)
    
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
    
    # Register blueprints
    try:
        from app.routes.main import main_bp
        app.register_blueprint(main_bp)
    except Exception as e:
        print(f"Main routes error: {e}")
    
    try:
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
    except Exception as e:
        print(f"Auth routes error: {e}")
    
    try:
        from app.routes.email import email_bp
        app.register_blueprint(email_bp, url_prefix='/api/email')
    except Exception as e:
        print(f"Email routes error: {e}")
    
    try:
        from app.routes.chat import chat_bp
        app.register_blueprint(chat_bp, url_prefix='/api/chat')
    except Exception as e:
        print(f"Chat routes error: {e}")
    
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
        # Write the fixed version
        with open('app/__init__.py', 'w', encoding='utf-8') as f:
            f.write(app_init_content)
        
        print("Fixed app/__init__.py")
        return True
        
    except Exception as e:
        print(f"Error fixing app init: {e}")
        return False

def create_quick_test():
    """Create a quick test to verify create_app works"""
    print("Creating quick test")
    print("=" * 18)
    
    test_content = '''#!/usr/bin/env python3
"""
Quick Test for create_app
"""
import os
import sys

def test():
    print("Testing create_app import")
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("1. Importing create_app...")
        from app import create_app
        print("SUCCESS: create_app imported")
        
        print("2. Creating app...")
        app = create_app()
        print("SUCCESS: App created")
        
        print("3. Testing app...")
        if app and hasattr(app, 'config'):
            print("SUCCESS: App is valid")
            print("Ready to start with: python docker_run.py")
            return True
        else:
            print("ERROR: App is invalid")
            return False
            
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test()
'''
    
    try:
        with open('test_create_app.py', 'w', encoding='utf-8') as f:
            f.write(test_content)
        print("Created test_create_app.py")
        return True
    except Exception as e:
        print(f"Error creating test: {e}")
        return False

def main():
    """Main function"""
    print("Fix create_app Export Issue")
    print("=" * 27)
    print("The app module can't export create_app function")
    print()
    
    # Fix app init
    app_fixed = fix_app_init()
    
    # Create test
    test_created = create_quick_test()
    
    if app_fixed:
        print()
        print("CREATE_APP EXPORT FIXED!")
        print("=" * 24)
        
        if test_created:
            print("Test the fix:")
            print("   python test_create_app.py")
        
        print("Start the app:")
        print("   python docker_run.py")
        
        print("What was fixed:")
        print("   - Proper create_app function definition")
        print("   - __all__ export list added")
        print("   - Clean module structure")
        
    else:
        print("Fix failed")

if __name__ == "__main__":
    main()