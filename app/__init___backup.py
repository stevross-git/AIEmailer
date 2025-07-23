"""
AI Email Assistant Flask Application Factory
"""
import os
import logging
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__, 
                template_folder='templates',  # Explicitly set template folder
                static_folder='static')       # Explicitly set static folder
    
    # Load configuration based on environment
    if os.getenv('USE_DOCKER_CONFIG', 'false').lower() == 'true':
        from app.docker_config import DockerConfig
        app.config.from_object(DockerConfig)
        print("🐳 Using Docker configuration")
    elif os.getenv('USE_SIMPLE_CONFIG', 'false').lower() == 'true':
        from app.simple_config import SimpleConfig
        app.config.from_object(SimpleConfig)
        print("🔧 Using Simple configuration")
    else:
        app.config.from_object('app.config.Config')
        print("⚙️ Using Default configuration")
    
    # Override with environment-specific config if provided
    if config_name:
        app.config.from_object(f'app.config.{config_name}')
    
    # Initialize extensions with app
    db.init_app(app)
    socketio.init_app(app)
    
    # Register template filters
    register_template_filters(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize database tables
    with app.app_context():
        create_tables()
    
    # Initialize services (skip in Docker mode if there are import issues)
    if not os.getenv('USE_DOCKER_CONFIG', 'false').lower() == 'true':
        initialize_services(app)
    
    return app

def register_template_filters(app):
    """Register custom template filters"""
    from datetime import datetime
    
    @app.template_filter('datetime_format')
    def datetime_format(value, format='%Y-%m-%d %H:%M'):
        """Format datetime for display"""
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                # Try to parse string to datetime
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return value
        if hasattr(value, 'strftime'):
            return value.strftime(format)
        return str(value)
    
    @app.template_filter('timeago')
    def timeago(value):
        """Show time ago format"""
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return value
        
        now = datetime.utcnow()
        if hasattr(value, 'tzinfo') and value.tzinfo is not None:
            value = value.replace(tzinfo=None)
        
        diff = now - value
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    
    @app.template_filter('truncate_words')
    def truncate_words(value, length=20):
        """Truncate text to specified number of words"""
        if not value:
            return ''
        words = str(value).split()
        if len(words) <= length:
            return value
        return ' '.join(words[:length]) + '...'

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
    """Register all application blueprints"""
    from app.routes.auth import auth_bp
    from app.routes.email import email_bp
    from app.routes.chat import chat_bp
    from app.routes.main import main_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(email_bp, url_prefix='/api/email')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

def create_tables():
    """Create database tables"""
    try:
        db.create_all()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")

def initialize_services(app):
    """Initialize application services"""
    try:
        # Initialize vector database
        from app.services.vector_db import VectorDBService
        vector_service = VectorDBService()
        vector_service.initialize()
        
        # Store service instances in app context
        app.vector_service = vector_service
        
        print("✅ Services initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing services: {e}")
        app.logger.error(f"Service initialization failed: {e}")

# Import models to ensure they're registered with SQLAlchemy
from app.models.user import User
from app.models.email import Email, EmailThread
from app.models.chat import ChatMessage

__version__ = "1.0.0"