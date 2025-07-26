"""
AI Email Assistant Flask Application
"""
import os
import logging
from flask import Flask

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
        'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///instance/app.db'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_recycle': 300,
            'pool_pre_ping': True
        },
        'DEBUG': True,
        'SESSION_TYPE': 'filesystem',
        'SESSION_PERMANENT': False,
        'SESSION_USE_SIGNER': True,
        'SESSION_KEY_PREFIX': 'ai_email_assistant:',
        'AZURE_CLIENT_ID': os.environ.get('AZURE_CLIENT_ID', 'your-client-id'),
        'AZURE_CLIENT_SECRET': os.environ.get('AZURE_CLIENT_SECRET', 'your-client-secret'),
        'AZURE_TENANT_ID': os.environ.get('AZURE_TENANT_ID', 'your-tenant-id'),
        'AZURE_REDIRECT_URI': os.environ.get('AZURE_REDIRECT_URI', 'http://localhost:5000/auth/callback'),
        'GRAPH_API_ENDPOINT': 'https://graph.microsoft.com/v1.0',
        'GRAPH_SCOPES': ['openid', 'profile', 'email', 'User.Read', 'Mail.Read', 'Mail.Send', 'Mail.ReadWrite'],
        'OLLAMA_BASE_URL': os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434'),
        'OLLAMA_MODEL': os.environ.get('OLLAMA_MODEL', 'deepseek-r1:7b'),
        'MAX_EMAILS_PER_SYNC': 50,
        'EMAIL_SYNC_BATCH_SIZE': 20,
        'CHAT_MAX_HISTORY': 10,
        'WTF_CSRF_ENABLED': True,
        'WTF_CSRF_TIME_LIMIT': None,
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file size
        'LOG_LEVEL': 'INFO',
        'LOG_FILE': 'logs/app.log'
    })
    
    # Create necessary directories with proper permissions
    os.makedirs('instance', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/sessions', exist_ok=True)
    
    # Ensure instance directory is writable
    try:
        test_file = os.path.join('instance', 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("✅ Instance directory is writable")
    except Exception as e:
        print(f"⚠️ Instance directory write test failed: {e}")
        # Try to fix permissions
        try:
            import stat
            os.chmod('instance', stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            print("✅ Fixed instance directory permissions")
        except Exception as perm_error:
            print(f"❌ Could not fix permissions: {perm_error}")
    
    # Initialize database FIRST
    from app.models import db
    db.init_app(app)
    
    # Initialize SocketIO (with fallback)
    socketio = None
    try:
        from flask_socketio import SocketIO
        socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)
        print("✅ SocketIO initialized")
    except ImportError:
        print("⚠️ SocketIO not available - continuing without it")
        # Create dummy socketio for compatibility
        class DummySocketIO:
            def emit(self, *args, **kwargs):
                pass
            def on(self, *args, **kwargs):
                pass
            def run(self, app, **kwargs):
                app.run(**kwargs)
        socketio = DummySocketIO()
    
    # Store socketio in app for access
    app.socketio = socketio
    
    # Initialize other extensions
    try:
        from flask_cors import CORS
        CORS(app, supports_credentials=True, origins=['http://localhost:5000', 'http://127.0.0.1:5000'])
        print("✅ CORS initialized")
    except ImportError:
        print("⚠️ Flask-CORS not available")
    
    try:
        from flask_session import Session
        session_ext = Session()
        session_ext.init_app(app)

        # Work around Flask-Session byte/string issue with newer Werkzeug
        try:
            original_save = app.session_interface.save_session

            def patched_save_session(app, session, response):
                sid = getattr(session, "sid", None)
                if isinstance(sid, bytes):
                    session.sid = sid.decode("utf-8")
                return original_save(app, session, response)

            app.session_interface.save_session = patched_save_session
            print("✅ Session initialized (patched)")
        except Exception as patch_error:
            print(f"⚠️ Session patch failed: {patch_error}")
            print("✅ Session initialized")
    except ImportError:
        print("⚠️ Flask-Session not available")
    
    # Setup logging
    setup_logging(app)
    
    # Create database tables within app context
    with app.app_context():
        try:
            # Import models here to avoid circular imports
            from app.models.user import User
            from app.models.email import Email
            from app.models.chat import ChatMessage
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
        except Exception as e:
            print(f"⚠️ Database setup warning: {e}")
    
    # Register blueprints with proper error handling
    register_blueprints(app)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        return {"error": "Internal server error"}, 500
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "message": "AI Email Assistant is running"}
    
    print("✅ Flask app created successfully")
    return app

def setup_logging(app):
    """Configure application logging"""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    log_file = app.config.get('LOG_FILE')
    
    # Create logs directory if it doesn't exist
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    
    # Set Flask's logger level
    app.logger.setLevel(log_level)

def register_blueprints(app):
    """Register all application blueprints with proper error handling"""
    blueprints_config = [
        ('app.routes.main', 'main_bp', None),
        ('app.routes.auth', 'auth_bp', '/auth'),
        ('app.routes.email', 'email_bp', '/api/email'),
        ('app.routes.chat', 'chat_bp', '/api/chat')
    ]
    
    for module_path, blueprint_name, url_prefix in blueprints_config:
        try:
            module = __import__(module_path, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            
            if url_prefix:
                app.register_blueprint(blueprint, url_prefix=url_prefix)
            else:
                app.register_blueprint(blueprint)
                
            print(f"✅ {blueprint_name} registered")
        except Exception as e:
            print(f"⚠️ {blueprint_name} error: {e}")

# Initialize services (if needed)
def initialize_services(app):
    """Initialize application services"""
    try:
        # Initialize vector database if available
        from app.services.vector_db import VectorDBService
        vector_service = VectorDBService()
        vector_service.initialize()
        
        # Store service instances in app context
        app.vector_service = vector_service
        
        print("✅ Services initialized successfully")
    except Exception as e:
        print(f"⚠️ Service initialization warning: {e}")
        app.logger.warning(f"Service initialization failed: {e}")

# Export db for use in routes
from app.models import db

# Version information
__version__ = "1.0.0"
__all__ = ['create_app', 'db']