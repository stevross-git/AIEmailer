#!/usr/bin/env python3
"""
Docker-based Application Runner
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main application entry point with Docker database"""
    try:
        # Set environment to use Docker config
        os.environ['USE_DOCKER_CONFIG'] = 'true'
        
        from app import create_app, socketio
        
        # Create Flask app
        app = create_app()
        
        # Get configuration
        debug = os.getenv('FLASK_ENV') == 'development'
        port = int(os.getenv('PORT', 5000))
        host = os.getenv('HOST', '127.0.0.1')
        
        print(f"🚀 Starting AI Email Assistant (Docker Database Mode)")
        print(f"📍 URL: http://{host}:{port}")
        print(f"🔧 Debug: {debug}")
        print(f"🐳 Database: PostgreSQL (Docker)")
        print(f"🔄 Cache: Redis (Docker)")
        print(f"🔍 Vector DB: ChromaDB (Docker)")
        print(f"🤖 Ollama: {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")
        print()
        
        # Run the application
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print()
        print("💡 Make sure Docker database services are running:")
        print("   python start_docker_db.py")
        sys.exit(1)

if __name__ == '__main__':
    main()