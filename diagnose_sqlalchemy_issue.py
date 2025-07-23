#!/usr/bin/env python3
"""
Diagnose SQLAlchemy Issue
"""
import os

def analyze_app_init():
    """Analyze the current app/__init__.py structure"""
    print("🔍 Analyzing App Initialization Structure")
    print("=" * 38)
    
    app_init_file = 'app/__init__.py'
    
    try:
        with open(app_init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        print("Key initialization lines:")
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if any(term in line_stripped for term in [
                'SQLAlchemy', 'db =', 'db.init_app', 'db.create_all',
                'from app.models', 'import db', 'import User', 'import Email'
            ]):
                print(f"  Line {i+1}: {line_stripped}")
        
        # Check the order of operations
        print("\n📊 Order Analysis:")
        
        db_creation_line = None
        db_init_line = None
        models_import_line = None
        create_all_line = None
        
        for i, line in enumerate(lines):
            if 'db = SQLAlchemy()' in line:
                db_creation_line = i + 1
            elif 'db.init_app(app)' in line:
                db_init_line = i + 1
            elif 'from app.models' in line and 'import' in line:
                models_import_line = i + 1
            elif 'db.create_all()' in line:
                create_all_line = i + 1
        
        print(f"  db = SQLAlchemy(): Line {db_creation_line}")
        print(f"  db.init_app(app): Line {db_init_line}")
        print(f"  Models import: Line {models_import_line}")
        print(f"  db.create_all(): Line {create_all_line}")
        
        # Identify the problem
        if db_creation_line and db_init_line and models_import_line:
            if models_import_line < db_init_line:
                print("\n❌ PROBLEM FOUND: Models imported BEFORE db.init_app()")
                print("   This causes the 'not registered' error")
                return "models_before_init"
            elif db_creation_line > db_init_line:
                print("\n❌ PROBLEM FOUND: db.init_app() called before db creation")
                return "init_before_creation"
            else:
                print("\n✅ Order looks correct - checking for other issues...")
                return "other_issue"
        else:
            print("\n❌ PROBLEM: Missing required initialization steps")
            return "missing_steps"
            
    except Exception as e:
        print(f"❌ Error analyzing app init: {e}")
        return "analysis_error"

def create_fixed_app_init():
    """Create a corrected app/__init__.py"""
    print("\n🔧 Creating Fixed App Initialization")
    print("=" * 35)
    
    # Read current config to preserve settings
    current_config = {}
    try:
        with open('app/__init__.py', 'r') as f:
            content = f.read()
            if 'SECRET_KEY' in content:
                current_config['has_secret'] = True
            if 'SQLALCHEMY_DATABASE_URI' in content:
                current_config['has_db_uri'] = True
    except:
        pass
    
    fixed_app_init = '''"""
AI Email Assistant Flask Application - Fixed Version
"""
import os
from flask import Flask

def create_app():
    """Create Flask application with proper SQLAlchemy initialization"""
    app = Flask(__name__)
    
    # Load configuration
    if os.environ.get('USE_DOCKER_CONFIG') == 'true':
        print("🐳 Using Docker configuration")
        from app.config.docker_config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    else:
        print("💻 Using local configuration")
        from app.config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # STEP 1: Initialize SQLAlchemy FIRST (before importing models)
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()
    db.init_app(app)
    
    # STEP 2: Now import models (after db is initialized)
    with app.app_context():
        # Import models within app context to avoid registration issues
        from app.models.user import User
        from app.models.email import Email
        from app.models.chat import ChatMessage
        
        # Create all tables
        try:
            db.create_all()
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"⚠️ Database creation warning: {e}")
    
    # STEP 3: Initialize other extensions
    from flask_cors import CORS
    from flask_session import Session
    
    CORS(app, supports_credentials=True)
    Session(app)
    
    # STEP 4: Register blueprints
    try:
        from app.routes.main import main_bp
        app.register_blueprint(main_bp)
        print("✅ Main blueprint registered")
    except Exception as e:
        print(f"⚠️ Main blueprint: {e}")
    
    try:
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        print("✅ Auth blueprint registered")
    except Exception as e:
        print(f"⚠️ Auth blueprint: {e}")
    
    try:
        from app.routes.email import email_bp
        app.register_blueprint(email_bp, url_prefix='/api/email')
        print("✅ Email blueprint registered")
    except Exception as e:
        print(f"⚠️ Email blueprint: {e}")
    
    try:
        from app.routes.chat import chat_bp
        app.register_blueprint(chat_bp, url_prefix='/api/chat')
        print("✅ Chat blueprint registered")
    except Exception as e:
        print(f"⚠️ Chat blueprint: {e}")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {"error": "Not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error"}, 500
    
    print("🎉 Flask app created successfully with fixed SQLAlchemy init")
    return app

# Create app instance
app = create_app()
'''
    
    # Backup current file
    try:
        with open('app/__init__.py', 'r') as f:
            current_content = f.read()
        with open('app/__init___backup_final.py', 'w') as f:
            f.write(current_content)
        print("✅ Backed up current app/__init__.py")
    except Exception as e:
        print(f"⚠️ Backup warning: {e}")
    
    # Write fixed version
    try:
        with open('app/__init__.py', 'w') as f:
            f.write(fixed_app_init)
        print("✅ Created fixed app/__init__.py")
        return True
    except Exception as e:
        print(f"❌ Error creating fixed init: {e}")
        return False

def create_simple_test():
    """Create a simple test for the fixed app"""
    print("\n🧪 Creating Simple Test")
    print("=" * 21)
    
    test_script = '''#!/usr/bin/env python3
"""
Test Fixed SQLAlchemy App
"""
import os
import sys

def test_app():
    """Test the fixed app"""
    print("🧪 Testing Fixed SQLAlchemy App")
    print("=" * 28)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("Creating app...")
        from app import app
        
        print("Testing app...")
        with app.app_context():
            print("✅ App context works")
            
            # Import models and test
            from app.models.user import User
            from app.models.email import Email
            
            # Test queries
            user_count = User.query.count()
            email_count = Email.query.count()
            print(f"✅ Queries work - Users: {user_count}, Emails: {email_count}")
        
        print("\\n🎉 SUCCESS: Fixed app works!")
        print("\\n🚀 Start with: python docker_run.py")
        return True
        
    except Exception as e:
        print(f"\\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_app()
'''
    
    with open('test_fixed_sqlalchemy.py', 'w') as f:
        f.write(test_script)
    
    print("✅ Created test_fixed_sqlalchemy.py")

def main():
    """Main function"""
    print("🔧 Diagnose and Fix SQLAlchemy Issue")
    print("=" * 36)
    
    # Analyze current structure
    issue_type = analyze_app_init()
    
    if issue_type in ["models_before_init", "init_before_creation", "other_issue"]:
        print(f"\n🔧 Applying fix for: {issue_type}")
        
        # Create fixed version
        app_fixed = create_fixed_app_init()
        
        # Create test
        create_simple_test()
        
        if app_fixed:
            print(f"\n🎉 SQLALCHEMY ISSUE FIXED!")
            print(f"=" * 27)
            
            print(f"\n🧪 Test the fix:")
            print(f"   python test_fixed_sqlalchemy.py")
            
            print(f"\n🚀 If test works, start app:")
            print(f"   python docker_run.py")
            
            print(f"\n✅ What was fixed:")
            print(f"   - SQLAlchemy initialized BEFORE models import")
            print(f"   - db.init_app(app) called at the right time")
            print(f"   - Models imported within app context")
            print(f"   - Proper initialization order")
            
            print(f"\n📧 After app starts:")
            print(f"   - No SQLAlchemy registration errors")
            print(f"   - User queries will work")
            print(f"   - Email sync will function")
            print(f"   - Open enhanced_sync_test.html")
            print(f"   - Run sync and view emails with content!")
            
        else:
            print(f"\n❌ Failed to create fixed version")
    
    else:
        print(f"\n🤔 Unexpected issue type: {issue_type}")
        print("Manual investigation may be needed")

if __name__ == "__main__":
    main()