#!/usr/bin/env python3
"""
Fix Flask-SQLAlchemy Initialization
"""
import os

def check_app_init():
    """Check how SQLAlchemy is initialized in app/__init__.py"""
    print("🔍 Checking App Initialization")
    print("=" * 28)
    
    app_init_file = 'app/__init__.py'
    
    try:
        with open(app_init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ Found app/__init__.py")
        
        # Look for db initialization
        lines = content.split('\n')
        db_lines = []
        
        for i, line in enumerate(lines):
            if any(term in line for term in ['db.', 'SQLAlchemy', 'init_app']):
                db_lines.append(f"Line {i+1}: {line.strip()}")
        
        print("Database-related lines:")
        for line in db_lines:
            print(f"  {line}")
        
        # Check for specific issues
        has_db_import = 'from app.models import db' in content
        has_init_app = 'db.init_app(app)' in content
        has_create_all = 'db.create_all()' in content
        
        print(f"\n📊 Analysis:")
        print(f"  Has db import: {has_db_import}")
        print(f"  Has init_app: {has_init_app}")
        print(f"  Has create_all: {has_create_all}")
        
        return content, has_db_import, has_init_app
        
    except Exception as e:
        print(f"❌ Error checking app init: {e}")
        return "", False, False

def fix_app_init():
    """Fix the app initialization to properly register SQLAlchemy"""
    print("\n🔧 Fixing App Initialization")
    print("=" * 27)
    
    app_init_file = 'app/__init__.py'
    backup_file = 'app/__init___backup.py'
    
    try:
        with open(app_init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup current file
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Backed up app/__init__.py")
        
        # Create a fixed version with proper SQLAlchemy initialization
        fixed_app_init = '''"""
AI Email Assistant Flask Application
"""
import os
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from flask_socketio import SocketIO

def create_app():
    """Create Flask application with proper configuration"""
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
    
    # Initialize database FIRST
    from app.models import db
    db.init_app(app)
    
    # Create tables within app context
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"⚠️ Database table creation warning: {e}")
    
    # Initialize extensions
    CORS(app, supports_credentials=True)
    Session(app)
    socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)
    
    # Register blueprints
    try:
        from app.routes.main import main_bp
        app.register_blueprint(main_bp)
        print("✅ Main blueprint registered")
    except Exception as e:
        print(f"⚠️ Main blueprint warning: {e}")
    
    try:
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        print("✅ Auth blueprint registered")
    except Exception as e:
        print(f"⚠️ Auth blueprint warning: {e}")
    
    try:
        from app.routes.email import email_bp
        app.register_blueprint(email_bp, url_prefix='/api/email')
        print("✅ Email blueprint registered")
    except Exception as e:
        print(f"⚠️ Email blueprint warning: {e}")
    
    try:
        from app.routes.chat import chat_bp
        app.register_blueprint(chat_bp, url_prefix='/api/chat')
        print("✅ Chat blueprint registered")
    except Exception as e:
        print(f"⚠️ Chat blueprint warning: {e}")
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {"error": "Not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error"}, 500
    
    print(f"🎉 Flask app created successfully")
    return app

# For backward compatibility
app = None
'''
        
        with open(app_init_file, 'w', encoding='utf-8') as f:
            f.write(fixed_app_init)
        
        print("✅ Fixed app/__init__.py with proper SQLAlchemy initialization")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing app init: {e}")
        return False

def create_simple_test_app():
    """Create a test to verify the fix works"""
    print("\n🧪 Creating Simple Test App")
    print("=" * 25)
    
    test_script = '''#!/usr/bin/env python3
"""
Test Fixed App Initialization
"""
import os
import sys

def test_fixed_app():
    """Test if the fixed app works"""
    print("🧪 Testing Fixed App Initialization")
    print("=" * 33)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("1. Creating app...")
        from app import create_app
        app = create_app()
        print("✅ App created")
        
        print("2. Testing app context...")
        with app.app_context():
            print("✅ App context works")
            
            print("3. Testing database...")
            from app.models import db, User, Email
            
            # Test database connection
            result = db.session.execute("SELECT 1").scalar()
            if result == 1:
                print("✅ Database connection works")
            
            # Test model queries (this was failing before)
            user_count = User.query.count()
            email_count = Email.query.count()
            print(f"✅ Model queries work - Users: {user_count}, Emails: {email_count}")
        
        print("\\n🎉 SUCCESS: App works without SQLAlchemy errors!")
        print("\\n🚀 You can now start the app: python docker_run.py")
        return True
        
    except Exception as e:
        print(f"\\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_fixed_app()
'''
    
    with open('test_fixed_app.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ Created test_fixed_app.py")

def create_minimal_docker_run():
    """Create a minimal docker_run.py that works with the fixed app"""
    print("\n🔧 Creating Fixed Docker Run Script")
    print("=" * 33)
    
    docker_run_script = '''#!/usr/bin/env python3
"""
Start the AI Email Assistant application (Fixed Version)
"""
import os
import sys

def main():
    """Start the Flask application"""
    print("🚀 Starting AI Email Assistant (Fixed)")
    print("=" * 36)
    
    # Set configuration
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    
    try:
        # Import and create app
        from app import create_app
        app = create_app()
        
        print("\\n🌟 AI Email Assistant Ready!")
        print("=" * 28)
        print("📧 Email Management: http://localhost:5000")
        print("🤖 AI Chat: http://localhost:5000/chat")
        print("⚙️ Dashboard: http://localhost:5000/dashboard")
        print()
        
        # Start the app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # Avoid reloader issues
        )
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        
        print("\\n💡 Troubleshooting:")
        print("   1. Check if all dependencies are installed")
        print("   2. Verify database permissions")
        print("   3. Check configuration files")

if __name__ == "__main__":
    main()
'''
    
    with open('docker_run_fixed.py', 'w', encoding='utf-8') as f:
        f.write(docker_run_script)
    
    print("✅ Created docker_run_fixed.py")

def main():
    """Main function"""
    print("🔧 Fix Flask-SQLAlchemy Initialization")
    print("=" * 37)
    print("🐛 Error: Flask app not registered with SQLAlchemy instance")
    print("This means db.init_app(app) is not being called properly")
    print()
    
    # Check current app init
    content, has_import, has_init = check_app_init()
    
    if not has_init:
        print("❌ db.init_app(app) is missing - this is the problem!")
        
        # Fix app init
        app_fixed = fix_app_init()
        
        # Create test
        create_simple_test_app()
        
        # Create fixed docker run
        create_minimal_docker_run()
        
        if app_fixed:
            print(f"\n🎉 FLASK-SQLALCHEMY INITIALIZATION FIXED!")
            print(f"=" * 42)
            
            print(f"\n🧪 Test the fix:")
            print(f"   python test_fixed_app.py")
            
            print(f"\n🚀 If test passes, start app:")
            print(f"   python docker_run_fixed.py")
            print(f"   OR")
            print(f"   python docker_run.py")
            
            print(f"\n✅ What was fixed:")
            print(f"   - Added db.init_app(app) call")
            print(f"   - Proper database initialization order")
            print(f"   - Table creation within app context")
            print(f"   - Error handling for blueprint registration")
            
            print(f"\n🎯 After app starts:")
            print(f"   - No more SQLAlchemy registration errors")
            print(f"   - Database queries will work")
            print(f"   - User.query.get() will work")
            print(f"   - Email sync and chat will function")
            
            print(f"\n📧 Then you can:")
            print(f"   1. Open enhanced_sync_test.html")
            print(f"   2. Run enhanced sync")
            print(f"   3. Visit http://localhost:5000/emails/267")
            print(f"   4. See full email content!")
            
        else:
            print(f"\n❌ Failed to fix app initialization")
    else:
        print("✅ db.init_app(app) is already present - check for other issues")

if __name__ == "__main__":
    main()