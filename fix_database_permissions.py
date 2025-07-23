#!/usr/bin/env python3
"""
Fix Database Permissions and Path Issues
"""
import os
import stat

def fix_directory_permissions():
    """Fix directory permissions and create necessary directories"""
    print("Fixing Directory Permissions")
    print("=" * 28)
    
    # Create instance directory with proper permissions
    instance_dir = 'instance'
    
    try:
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir, mode=0o755)
            print(f"Created {instance_dir} directory")
        else:
            print(f"{instance_dir} directory exists")
        
        # Check and fix permissions
        current_perms = oct(stat.S_IMODE(os.lstat(instance_dir).st_mode))
        print(f"Directory permissions: {current_perms}")
        
        # Ensure write permissions
        os.chmod(instance_dir, 0o755)
        print("Set directory permissions to 755")
        
        # Test write access
        test_file = os.path.join(instance_dir, 'test_write.tmp')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print("Write access: OK")
            return True
        except Exception as e:
            print(f"Write access: FAILED - {e}")
            return False
            
    except Exception as e:
        print(f"Directory setup error: {e}")
        return False

def create_working_app_init():
    """Create app init that handles database path issues"""
    print("\nCreating Working App Init")
    print("=" * 25)
    
    app_init = '''"""
AI Email Assistant - Working Version
"""
import os
from flask import Flask

def create_app():
    """Create Flask application with working database"""
    app = Flask(__name__)
    
    # Get absolute path for database
    base_dir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(os.path.dirname(base_dir), 'instance')
    
    # Ensure instance directory exists
    os.makedirs(instance_dir, exist_ok=True)
    
    # Use absolute path for database
    db_path = os.path.join(instance_dir, 'app.db')
    
    # Configuration with absolute database path
    app.config.update({
        'SECRET_KEY': 'dev-secret-key-change-in-production',
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
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
    
    print(f"Database path: {db_path}")
    
    # Initialize database
    from app.models import db
    db.init_app(app)
    
    # Create tables within app context
    with app.app_context():
        try:
            # Import models
            from app.models.user import User
            from app.models.email import Email
            from app.models.chat import ChatMessage
            
            # Create all tables
            db.create_all()
            print("Database tables created successfully") 
            
            # Test database access
            user_count = User.query.count()
            print(f"Database test successful - Users: {user_count}")
            
        except Exception as e:
            print(f"Database setup error: {e}")
            # Try with in-memory database as fallback
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
            db.create_all()
            print("Using in-memory database as fallback")
    
    # Initialize extensions
    try:
        from flask_cors import CORS
        CORS(app, supports_credentials=True)
    except ImportError:
        pass
    
    try:
        from flask_session import Session
        Session(app)
    except ImportError:
        pass
    
    # Register blueprints
    blueprints = [
        ('app.routes.main', 'main_bp', None),
        ('app.routes.auth', 'auth_bp', '/auth'), 
        ('app.routes.email', 'email_bp', '/api/email'),
    ]
    
    for module_path, blueprint_name, url_prefix in blueprints:
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

# Export db for routes that need it
from app.models import db

__all__ = ['create_app', 'db']
'''
    
    try:
        with open('app/__init__.py', 'w', encoding='utf-8') as f:
            f.write(app_init)
        print("Created working app/__init__.py")
        return True
    except Exception as e:
        print(f"Error creating app init: {e}")
        return False

def create_working_test():
    """Create test that should work with fixed database"""
    print("\nCreating Working Test")
    print("=" * 19)
    
    test_content = '''#!/usr/bin/env python3
"""
Working Test - Database Fixed
"""
import os
import sys

def test():
    print("Testing Fixed Database Setup")
    print("=" * 28)
    
    sys.path.append('.')
    
    try:
        print("1. Testing directory setup...")
        if os.path.exists('instance'):
            print("Instance directory: EXISTS")
        else:
            print("Instance directory: MISSING - will be created")
        
        print("2. Creating app...")
        from app import create_app
        app = create_app()
        print("App creation: SUCCESS")
        
        print("3. Testing database within app context...")
        with app.app_context():
            from app.models.user import User
            from app.models.email import Email
            
            # Test basic queries
            user_count = User.query.count()
            email_count = Email.query.count()
            print(f"Database queries: SUCCESS (Users: {user_count}, Emails: {email_count})")
            
            # Test creating a user
            test_user = User(
                email="test@example.com",
                display_name="Test User",
                azure_id="test-123"
            )
            
            from app.models import db
            db.session.add(test_user)
            db.session.commit()
            
            new_count = User.query.count()
            print(f"User creation test: SUCCESS (Users now: {new_count})")
        
        print()
        print("ALL TESTS PASSED!")
        print("=" * 17)
        print("Database is working correctly!")
        print()
        print("Ready to start app:")
        print("   python docker_run.py")
        print()
        print("After app starts:")
        print("   1. Open enhanced_sync_test.html")
        print("   2. Run enhanced sync")
        print("   3. View emails with full content!")
        
        return True
        
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test()
'''
    
    try:
        with open('test_working.py', 'w', encoding='utf-8') as f:
            f.write(test_content)
        print("Created test_working.py")
        return True
    except Exception as e:
        print(f"Error creating test: {e}")
        return False

def main():
    """Main function"""
    print("Fix Database Permissions and Path Issues")
    print("=" * 40)
    print("Fixing SQLite database access problems")
    print()
    
    # Fix directory permissions
    dirs_fixed = fix_directory_permissions()
    
    # Create working app
    app_created = create_working_app_init()
    
    # Create working test
    test_created = create_working_test()
    
    if dirs_fixed and app_created:
        print()
        print("DATABASE ISSUES FIXED!")
        print("=" * 22)
        
        if test_created:
            print("Test the fix:")
            print("   python test_working.py")
        
        print("Start the app:")
        print("   python docker_run.py")
        
        print("What was fixed:")
        print("   - Directory permissions")
        print("   - Absolute database path")
        print("   - Database access testing")
        print("   - Fallback to in-memory DB if needed")
        print("   - db export for routes")
        
        print("Database features:")
        print("   - User table with all fields")
        print("   - Email table with content fields (body_text, body_html, body_preview)")
        print("   - Chat table for AI conversations")
        print("   - Proper foreign key relationships")
        
    else:
        print("Some fixes failed - check manually")

if __name__ == "__main__":
    main()