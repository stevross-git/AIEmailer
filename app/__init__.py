"""
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
    print("\n📋 Registering blueprints...")
    
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
    
    print("\n🎉 Flask app created")
    return app

# For compatibility
__all__ = ['create_app']
