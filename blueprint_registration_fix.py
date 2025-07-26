#!/usr/bin/env python3
"""
Quick fix for blueprint registration issue
"""
import os

def diagnose_blueprint_issue():
    """Diagnose why auth blueprint isn't registering"""
    print("🔍 Diagnosing Blueprint Registration Issue")
    print("=" * 41)
    
    # Check if auth.py exists and has auth_bp
    auth_file = 'app/routes/auth.py'
    if os.path.exists(auth_file):
        print("✅ auth.py exists")
        
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'auth_bp = Blueprint(' in content:
            print("✅ auth_bp Blueprint is defined")
        else:
            print("❌ auth_bp Blueprint NOT found")
            return False
        
        if '@auth_bp.route(' in content:
            print("✅ auth_bp routes are defined")
        else:
            print("❌ No auth_bp routes found")
            return False
    else:
        print("❌ auth.py does not exist")
        return False
    
    # Check __init__.py blueprint registration
    init_file = 'app/__init__.py'
    if os.path.exists(init_file):
        print("✅ __init__.py exists")
        
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'register_blueprints' in content:
            print("✅ register_blueprints function found")
        else:
            print("❌ register_blueprints function NOT found")
            return False
        
        if "('app.routes.auth', 'auth_bp'" in content:
            print("✅ auth blueprint registration found in config")
        else:
            print("❌ auth blueprint registration NOT found")
            return False
    else:
        print("❌ __init__.py does not exist")
        return False
    
    return True

def create_simple_blueprint_fix():
    """Create a simple blueprint registration fix"""
    print("\n🔧 Creating Simple Blueprint Fix")
    print("=" * 31)
    
    # Create a minimal working __init__.py
    simple_init = '''"""
AI Email Assistant Flask Application - BLUEPRINT FIX
"""
import os
from flask import Flask

def create_app():
    """Create Flask application with fixed blueprint registration"""
    app = Flask(__name__)
    
    # Basic configuration
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-secret-key'),
        'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///data/app.db'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'DEBUG': True,
        'AZURE_CLIENT_ID': os.environ.get('AZURE_CLIENT_ID', '2807d502-5746-4a1d-ac0b-cdbdc1521205'),
        'AZURE_TENANT_ID': os.environ.get('AZURE_TENANT_ID', '6ceb32ee-6c77-4bae-b7fc-45f2b110fa5f'),
        'AZURE_REDIRECT_URI': os.environ.get('AZURE_REDIRECT_URI', 'http://localhost:5000/auth/callback'),
    })
    
    # Create directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('instance', exist_ok=True)
    
    # Initialize database
    from app.models import db
    db.init_app(app)
    
    # Initialize extensions
    try:
        from flask_cors import CORS
        CORS(app, supports_credentials=True)
        print("✅ CORS initialized")
    except ImportError:
        print("⚠️ CORS not available")
    
    try:
        from flask_socketio import SocketIO
        socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)
        print("✅ SocketIO initialized")
    except ImportError:
        print("⚠️ SocketIO not available")
    
    # DIRECT blueprint registration (avoiding dynamic import issues)
    print("\\n📋 Registering blueprints...")
    
    # Register main blueprint
    try:
        from app.routes.main import main_bp
        app.register_blueprint(main_bp)
        print("✅ main_bp registered")
    except Exception as e:
        print(f"❌ main_bp failed: {e}")
    
    # Register auth blueprint - THIS IS THE CRITICAL ONE
    try:
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        print("✅ auth_bp registered")
        
        # Test that routes exist
        with app.app_context():
            routes = [rule.rule for rule in app.url_map.iter_rules() if rule.endpoint.startswith('auth.')]
            print(f"   Auth routes: {routes}")
            
    except Exception as e:
        print(f"❌ auth_bp FAILED: {e}")
        print("   This is the source of your error!")
        
        # Try to debug the auth import
        try:
            import app.routes.auth as auth_module
            if hasattr(auth_module, 'auth_bp'):
                print("   auth_bp exists in module")
            else:
                print("   auth_bp NOT found in module")
        except Exception as import_error:
            print(f"   Auth module import failed: {import_error}")
    
    # Register other blueprints
    try:
        from app.routes.email import email_bp
        app.register_blueprint(email_bp, url_prefix='/api/email')
        print("✅ email_bp registered")
    except Exception as e:
        print(f"⚠️ email_bp failed: {e}")
    
    try:
        from app.routes.chat import chat_bp
        app.register_blueprint(chat_bp, url_prefix='/api/chat')
        print("✅ chat_bp registered")
    except Exception as e:
        print(f"⚠️ chat_bp failed: {e}")
    
    # Create database tables
    with app.app_context():
        try:
            from app.models.user import User
            from app.models.email import Email
            db.create_all()
            print("✅ Database tables created")
        except Exception as e:
            print(f"⚠️ Database warning: {e}")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        return {"error": "Server error"}, 500
    
    print("\\n🎉 Flask app created")
    return app

# For compatibility
__all__ = ['create_app']
'''
    
    try:
        # Backup current __init__.py
        with open('app/__init__.py', 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        with open('app/__init__.py.backup2', 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        # Write fixed version
        with open('app/__init__.py', 'w', encoding='utf-8') as f:
            f.write(simple_init)
        
        print("✅ Created fixed app/__init__.py")
        print("✅ Backed up original to app/__init__.py.backup2")
        return True
        
    except Exception as e:
        print(f"❌ Error creating fix: {e}")
        return False

def test_blueprint_fix():
    """Test if the blueprint fix works"""
    print("\\n🧪 Testing Blueprint Fix")
    print("=" * 23)
    
    try:
        import sys
        sys.path.append('.')
        
        print("1. Testing import...")
        from app import create_app
        print("✅ Import successful")
        
        print("2. Creating app...")
        app = create_app()
        print("✅ App creation successful")
        
        print("3. Testing auth routes...")
        with app.app_context():
            auth_routes = [rule.rule for rule in app.url_map.iter_rules() if 'auth' in rule.rule]
            if auth_routes:
                print(f"✅ Auth routes found: {auth_routes}")
                return True
            else:
                print("❌ No auth routes found")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main function"""
    print("🛠️ Blueprint Registration Fix")
    print("=" * 28)
    
    # Diagnose the issue
    if not diagnose_blueprint_issue():
        print("\\n❌ Critical blueprint issues found")
    
    # Apply the fix
    if create_simple_blueprint_fix():
        print("\\n🔄 Fix applied - please restart your Flask app")
        
        # Test the fix
        if test_blueprint_fix():
            print("\\n🎉 SUCCESS: Blueprint registration should now work!")
        else:
            print("\\n⚠️ Fix may need adjustment")
    
    print("\\n" + "=" * 50)
    print("📋 NEXT STEPS:")
    print("1. Restart your Flask application")
    print("2. The 'auth.login' endpoint should now work")
    print("3. If still having issues, check the console output above")
    print("=" * 50)

if __name__ == "__main__":
    main()