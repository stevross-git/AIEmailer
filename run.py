#!/usr/bin/env python3
"""
AI Email Assistant - Main Application Entry Point
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Main application entry point"""
    try:
        # Import the Flask app
        from app import create_app
        
        # Create the Flask app
        app = create_app()
        
        # Get configuration
        debug = os.getenv('FLASK_ENV', 'development') == 'development'
        port = int(os.getenv('PORT', 5000))
        host = os.getenv('HOST', '127.0.0.1')
        
        print(f"🚀 Starting AI Email Assistant on http://{host}:{port}")
        print(f"🔧 Debug mode: {debug}")
        print(f"🤖 Ollama endpoint: {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")
        print(f"🗄️ Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///instance/app.db')}")
        
        # Check if SocketIO is available and use it, otherwise use regular Flask
        if hasattr(app, 'socketio') and app.socketio:
            try:
                # Try to use SocketIO if available
                app.socketio.run(
                    app,
                    host=host,
                    port=port,
                    debug=debug,
                    allow_unsafe_werkzeug=True  # For development only
                )
            except Exception as e:
                print(f"⚠️ SocketIO error: {e}")
                print("📡 Falling back to regular Flask server...")
                # Fall back to regular Flask if SocketIO fails
                app.run(
                    host=host,
                    port=port,
                    debug=debug,
                    use_reloader=False
                )
        else:
            # Use regular Flask server
            print("📡 Starting regular Flask server...")
            app.run(
                host=host,
                port=port,
                debug=debug,
                use_reloader=False
            )
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Application startup error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()