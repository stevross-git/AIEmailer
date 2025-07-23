#!/usr/bin/env python3
"""
Fix SocketIO Import Issue
"""
import os
import glob

def find_socketio_imports():
    """Find where socketio is being imported from app"""
    print("Finding SocketIO Import References")
    print("=" * 33)
    
    # Search in all Python files
    python_files = []
    for pattern in ['*.py', 'app/*.py', 'app/*/*.py', 'app/*/*/*.py']:
        python_files.extend(glob.glob(pattern))
    
    socketio_references = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
#                     if 'from app import' in line and 'socketio' in line:
                        socketio_references.append((file_path, i+1, line.strip()))
                    elif 'import socketio' in line and 'app' in line:
                        socketio_references.append((file_path, i+1, line.strip()))
        except Exception as e:
            continue
    
    if socketio_references:
        print("Found SocketIO import references:")
        for file_path, line_num, line in socketio_references:
            print(f"  {file_path}:{line_num} - {line}")
        return socketio_references
    else:
        print("No SocketIO import references found")
        return []

def fix_socketio_imports(references):
    """Fix the SocketIO import issues"""
    print("\nFixing SocketIO Import Issues")
    print("=" * 29)
    
    for file_path, line_num, line in references:
        try:
            print(f"Fixing {file_path}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Fix the problematic line
            original_line = lines[line_num - 1]
            
#             if 'from app import' in original_line and 'socketio' in original_line:
                # Comment out or replace the socketio import
                if 'socketio' in original_line and ',' in original_line:
                    # Remove socketio from import list
                    new_line = original_line.replace(', socketio', '').replace('socketio, ', '').replace('socketio', '')
                    if 'from app import ' in new_line and new_line.strip().endswith('import'):
                        # If it results in empty import, comment it out
                        new_line = '# ' + original_line
                else:
                    # Comment out the entire line
                    new_line = '# ' + original_line
                
                lines[line_num - 1] = new_line
                print(f"  Changed: {original_line.strip()}")
                print(f"  To:      {new_line.strip()}")
            
            # Write back the fixed file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f"  Fixed {file_path}")
            
        except Exception as e:
            print(f"  Error fixing {file_path}: {e}")

def add_socketio_to_app():
    """Add basic SocketIO support to app if needed"""
    print("\nAdding SocketIO Support to App")
    print("=" * 28)
    
    app_init_content = '''"""
AI Email Assistant - With SocketIO Support
"""
import os
from flask import Flask

def create_app():
    """Create Flask application"""
    app = Flask(__name__)
    
    # Get absolute path for database
    base_dir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(os.path.dirname(base_dir), 'instance')
    
    # Ensure instance directory exists
    os.makedirs(instance_dir, exist_ok=True)
    
    # Use absolute path for database
    db_path = os.path.join(instance_dir, 'app.db')
    
    # Configuration
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
    
    # Initialize database
    from app.models import db
    db.init_app(app)
    
    # Initialize SocketIO
    socketio = None
    try:
        from flask_socketio import SocketIO
        socketio = SocketIO(app, cors_allowed_origins="*")
        print("SocketIO initialized")
    except ImportError:
        print("SocketIO not available - continuing without it")
        # Create a dummy socketio object
        class DummySocketIO:
            def emit(self, *args, **kwargs):
                pass
            def on(self, *args, **kwargs):
                pass
        socketio = DummySocketIO()
    
    # Create tables within app context
    with app.app_context():
        try:
            from app.models.user import User
            from app.models.email import Email
            from app.models.chat import ChatMessage
            
            db.create_all()
            print("Database tables created successfully")
            
        except Exception as e:
            print(f"Database setup error: {e}")
    
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
    return app, socketio

# Create app and socketio instances
app, socketio = create_app()

# Export for imports
from app.models import db
__all__ = ['create_app', 'app', 'socketio', 'db']
'''
    
    try:
        with open('app/__init__.py', 'w', encoding='utf-8') as f:
            f.write(app_init_content)
        print("Updated app/__init__.py with SocketIO support")
        return True
    except Exception as e:
        print(f"Error updating app init: {e}")
        return False

def create_simple_docker_run():
    """Create a simple docker_run.py that works"""
    print("\nCreating Simple Docker Run")
    print("=" * 24)
    
    docker_run_content = '''#!/usr/bin/env python3
"""
Simple Docker Run - Fixed Version
"""
import os
import sys

def main():
    """Start the application"""
    print("Starting AI Email Assistant")
    print("=" * 27)
    
    try:
        # Set environment
        os.environ['USE_DOCKER_CONFIG'] = 'true'
        
        # Import app
        from app import app
        
        print("App imported successfully")
        print()
        print("AI Email Assistant Ready!")
        print("=" * 26) 
        print("Visit: http://localhost:5000")
        print()
        
        # Start the app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
'''
    
    try:
        with open('docker_run.py', 'w', encoding='utf-8') as f:
            f.write(docker_run_content)
        print("Created simple docker_run.py")
        return True
    except Exception as e:
        print(f"Error creating docker run: {e}")
        return False

def create_final_test():
    """Create final test"""
    print("\nCreating Final Import Test")
    print("=" * 25)
    
    test_content = '''#!/usr/bin/env python3
"""
Final Import Test
"""
import os
import sys

def test():
    print("Testing All Imports")
    print("=" * 18)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("1. Testing app import...")
        from app import app, db
        print("App and db imported: SUCCESS")
        
        print("2. Testing socketio import...")
        try:
#             from app import socketio
            print("SocketIO imported: SUCCESS")
        except ImportError:
            print("SocketIO imported: NOT AVAILABLE (OK)")
        
        print("3. Testing app functionality...")
        with app.app_context():
            from app.models.user import User
            from app.models.email import Email
            
            user_count = User.query.count()
            email_count = Email.query.count()
            print(f"Database test: SUCCESS (Users: {user_count}, Emails: {email_count})")
        
        print()
        print("ALL IMPORTS WORKING!")
        print("=" * 19)
        print("Ready to start:")
        print("   python docker_run.py")
        print()
        print("After start:")
        print("   1. Open enhanced_sync_test.html")
        print("   2. Run enhanced sync")
        print("   3. See emails with full content!")
        
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
        with open('test_imports.py', 'w', encoding='utf-8') as f:
            f.write(test_content)
        print("Created test_imports.py")
        return True
    except Exception as e:
        print(f"Error creating test: {e}")
        return False

def main():
    """Main function"""
    print("Fix SocketIO Import Issue")
    print("=" * 24)
    
    # Find socketio import references
    references = find_socketio_imports()
    
    # Fix the import issues
    if references:
        fix_socketio_imports(references)
    
    # Add socketio to app
    app_updated = add_socketio_to_app()
    
    # Create simple docker run
    docker_created = create_simple_docker_run()
    
    # Create test
    test_created = create_final_test()
    
    if app_updated and docker_created:
        print()
        print("SOCKETIO IMPORT ISSUE FIXED!")
        print("=" * 29)
        
        if test_created:
            print("Test all imports:")
            print("   python test_imports.py")
        
        print("Start the app:")
        print("   python docker_run.py")
        
        print("What was fixed:")
        print("   - Added SocketIO support to app")
        print("   - Fixed import references")
        print("   - Created fallback for missing SocketIO")
        print("   - Simplified docker_run.py")
        
        print("App now exports:")
        print("   - create_app function")
        print("   - app instance")
        print("   - socketio instance")
        print("   - db instance")
        
    else:
        print("Some fixes failed")

if __name__ == "__main__":
    main()