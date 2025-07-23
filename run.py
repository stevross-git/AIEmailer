#!/usr/bin/env python3
"""
AI Email Assistant - Main Application Entry Point
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app

def main():
    """Main application entry point"""
    # Create Flask app with SocketIO
    app = create_app()
    
    # Get configuration
    debug = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '127.0.0.1')
    
    print(f"🚀 Starting AI Email Assistant on http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🤖 Ollama endpoint: {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")
    
    # Run the application with SocketIO support
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True  # For development only
    )

if __name__ == '__main__':
    main()