#!/usr/bin/env python3
"""
Setup Check and Directory Structure Verification
"""
import os
import sys
from pathlib import Path

def check_directory_structure():
    """Check if all required directories and files exist"""
    
    required_dirs = [
        'app',
        'app/models',
        'app/routes', 
        'app/services',
        'app/utils',
        'app/templates',
        'app/templates/errors',
        'app/static',
        'app/static/css',
        'app/static/js',
        'data',
        'logs'
    ]
    
    required_files = [
        'app/__init__.py',
        'app/config.py',
        'app/models/user.py',
        'app/models/email.py',
        'app/models/chat.py',
        'app/routes/main.py',
        'app/routes/auth.py',
        'app/routes/email.py',
        'app/routes/chat.py',
        'app/services/ms_graph.py',
        'app/services/ollama_engine.py',
        'app/services/vector_db.py',
        'app/services/email_processor.py',
        'app/services/chat_processor.py',
        'app/utils/auth_helpers.py',
        'app/utils/email_parser.py',
        'app/templates/base.html',
        'app/templates/index.html',
        'app/templates/dashboard.html',
        'app/templates/chat.html',
        'app/templates/emails.html',
        'app/templates/settings.html',
        'app/templates/errors/404.html',
        'app/templates/errors/500.html',
        'app/static/css/style.css',
        'app/static/js/main.js',
        'requirements.txt',
        'run.py',
        '.env.example',
        'README.md'
    ]
    
    print("🔍 Checking directory structure...")
    
    # Check directories
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
            print(f"❌ Missing directory: {dir_path}")
        else:
            print(f"✅ Found directory: {dir_path}")
    
    # Check files
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            print(f"❌ Missing file: {file_path}")
        else:
            print(f"✅ Found file: {file_path}")
    
    # Create missing directories
    if missing_dirs:
        print("\n📁 Creating missing directories...")
        for dir_path in missing_dirs:
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
            except Exception as e:
                print(f"❌ Failed to create directory {dir_path}: {e}")
    
    # Report missing files
    if missing_files:
        print(f"\n⚠️  {len(missing_files)} files are missing. Please ensure you have all the required files.")
        print("Missing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    print(f"\n✅ All required directories and files are present!")
    return True

def check_environment():
    """Check environment configuration"""
    print("\n🔧 Checking environment configuration...")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ Found .env file")
        
        # Check if required environment variables are set
        required_env_vars = [
            'SECRET_KEY',
            'AZURE_CLIENT_ID',
            'AZURE_CLIENT_SECRET',
            'AZURE_TENANT_ID',
            'OLLAMA_BASE_URL',
            'OLLAMA_MODEL'
        ]
        
        # Load .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            missing_vars = []
            for var in required_env_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
                    print(f"❌ Missing environment variable: {var}")
                else:
                    print(f"✅ Found environment variable: {var}")
            
            if missing_vars:
                print(f"\n⚠️  Please set the following environment variables in your .env file:")
                for var in missing_vars:
                    print(f"  - {var}")
                return False
            
        except ImportError:
            print("❌ python-dotenv not installed. Run: pip install python-dotenv")
            return False
            
    else:
        print("❌ .env file not found. Copy .env.example to .env and configure it.")
        return False
    
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    print("\n📦 Checking Python dependencies...")
    
    try:
        # Check critical imports
        import flask
        print(f"✅ Flask {flask.__version__}")
        
        import sqlalchemy
        print(f"✅ SQLAlchemy {sqlalchemy.__version__}")
        
        try:
            import requests
            print(f"✅ Requests {requests.__version__}")
        except ImportError:
            print("❌ Missing: requests")
            
        try:
            import chromadb
            print(f"✅ ChromaDB {chromadb.__version__}")
        except ImportError:
            print("❌ Missing: chromadb - Run: pip install chromadb")
            
        try:
            import sentence_transformers
            print(f"✅ Sentence Transformers {sentence_transformers.__version__}")
        except ImportError:
            print("❌ Missing: sentence-transformers")
            
        try:
            import flask_socketio
            print(f"✅ Flask-SocketIO {flask_socketio.__version__}")
        except ImportError:
            print("❌ Missing: Flask-SocketIO")
            
        return True
        
    except ImportError as e:
        print(f"❌ Critical dependency missing: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_ollama():
    """Check if Ollama is running and has the required model"""
    print("\n🤖 Checking Ollama setup...")
    
    try:
        import requests
        
        # Check if Ollama is running
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                print("✅ Ollama is running")
                
                # Check if DeepSeek model is available
                models = response.json()
                model_names = [model['name'] for model in models.get('models', [])]
                
                if any('deepseek' in name.lower() for name in model_names):
                    print("✅ DeepSeek model found")
                    return True
                else:
                    print("❌ DeepSeek model not found")
                    print("Run: ollama pull deepseek-r1:7b")
                    return False
            else:
                print("❌ Ollama is not responding properly")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Ollama")
            print("Make sure Ollama is installed and running")
            print("Download from: https://ollama.ai")
            return False
            
    except ImportError:
        print("❌ Requests library not available")
        return False

def create_initial_data_directories():
    """Create initial data directories with proper structure"""
    print("\n📂 Creating data directories...")
    
    data_dirs = [
        'data',
        'data/sessions',
        'data/vector_db',
        'logs'
    ]
    
    for dir_path in data_dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Created/verified: {dir_path}")
        except Exception as e:
            print(f"❌ Failed to create {dir_path}: {e}")

def main():
    """Main setup check function"""
    print("🚀 AI Email Assistant - Setup Check")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 5
    
    # Check directory structure
    if check_directory_structure():
        checks_passed += 1
    
    # Check environment configuration
    if check_environment():
        checks_passed += 1
    
    # Check Python dependencies
    if check_dependencies():
        checks_passed += 1
    
    # Check Ollama setup
    if check_ollama():
        checks_passed += 1
    
    # Create data directories
    create_initial_data_directories()
    checks_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Setup Check Results: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("✅ Setup is complete! You can now run the application.")
        print("\nTo start the application:")
        print("python run.py")
    else:
        print("❌ Setup is incomplete. Please address the issues above.")
        print("\nCommon fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Copy and configure: cp .env.example .env")
        print("3. Install Ollama: https://ollama.ai")
        print("4. Pull AI model: ollama pull deepseek-r1:7b")
        
    return checks_passed == total_checks

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)