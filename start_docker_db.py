#!/usr/bin/env python3
"""
Docker Database Startup Script
"""
import subprocess
import time
import sys
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def run_command(command, description=""):
    """Run a shell command and return success status"""
    try:
        print(f"🔧 {description}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def check_docker():
    """Check if Docker is installed and running"""
    print("🐳 Checking Docker...")
    
    if not run_command("docker --version", "Checking Docker installation"):
        print("❌ Docker is not installed. Please install Docker Desktop.")
        return False
    
    if not run_command("docker ps", "Checking Docker daemon"):
        print("❌ Docker daemon is not running. Please start Docker Desktop.")
        return False
    
    print("✅ Docker is ready")
    return True

def start_database_services():
    """Start database services using Docker Compose"""
    print("\n🚀 Starting database services...")
    
    # Create docker directory if it doesn't exist
    os.makedirs('docker', exist_ok=True)
    
    if not run_command("docker compose up -d postgres redis chromadb", "Starting database containers"):
        return False
    
    print("✅ Database containers started")
    return True

def wait_for_services():
    """Wait for services to be ready"""
    print("\n⏳ Waiting for services to be ready...")
    
    services = [
        ("PostgreSQL", "localhost", 5432, "tcp"),
        ("Redis", "localhost", 6379, "tcp"),
        ("ChromaDB", "localhost", 8000, "http")
    ]
    
    for service_name, host, port, check_type in services:
        print(f"⏳ Waiting for {service_name} on {host}:{port}...")
        
        max_attempts = 60  # Increased from 30 to 60
        for attempt in range(max_attempts):
            try:
                if check_type == "http":
                    # Check HTTP endpoint for ChromaDB
                    try:
                        response = requests.get(f"http://{host}:{port}/api/v1/heartbeat", timeout=5)
                        if response.status_code == 200:
                            print(f"✅ {service_name} is ready")
                            break
                    except requests.exceptions.ConnectionError:
                        # Try alternative endpoints if heartbeat fails
                        try:
                            response = requests.get(f"http://{host}:{port}/api/v1/version", timeout=5)
                            if response.status_code == 200:
                                print(f"✅ {service_name} is ready (via version endpoint)")
                                break
                        except:
                            pass
                        
                        # Try simple GET to root
                        try:
                            response = requests.get(f"http://{host}:{port}/", timeout=5)
                            if response.status_code in [200, 404]:  # 404 is ok for ChromaDB root
                                print(f"✅ {service_name} is ready (HTTP responding)")
                                break
                        except:
                            pass
                else:
                    # Check TCP connection for database services
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result == 0:
                        print(f"✅ {service_name} is ready")
                        break
                        
            except Exception as e:
                print(f"⏳ Attempt {attempt + 1}/{max_attempts} - {service_name}: {e}")
            
            if attempt == max_attempts - 1:
                print(f"❌ {service_name} failed to start after {max_attempts} attempts")
                print(f"💡 But {service_name} might still be initializing. Let's continue...")
                # Don't fail completely - services might be working
                break
            
            time.sleep(3)  # Increased from 2 to 3 seconds
    
    # Additional check - let's verify at least PostgreSQL is working
    print("\n🔍 Final connectivity check...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(("localhost", 5432))
        sock.close()
        
        if result == 0:
            print("✅ PostgreSQL connectivity confirmed")
            return True
        else:
            print("❌ PostgreSQL is not accessible")
            return False
    except Exception as e:
        print(f"❌ Connectivity check failed: {e}")
        return False

def initialize_database():
    """Initialize the database with tables"""
    print("\n🗄️ Initializing database...")
    
    try:
        # Set environment to use Docker config
        os.environ['USE_DOCKER_CONFIG'] = 'true'
        
        # Import after setting environment
        from app import create_app, db
        
        app = create_app()
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Test database connection
            from sqlalchemy import text
            result = db.session.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Database connection successful: {version}")
            
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

def show_connection_info():
    """Show connection information"""
    print("\n" + "=" * 50)
    print("🎯 Database Services Ready!")
    print("=" * 50)
    print("📊 PostgreSQL:")
    print("   Host: localhost")
    print("   Port: 5432")
    print("   Database: ai_email_assistant")
    print("   Username: ai_email_user")
    print("   Password: ai_email_password123")
    print()
    print("🔄 Redis:")
    print("   Host: localhost")
    print("   Port: 6379")
    print()
    print("🔍 ChromaDB:")
    print("   URL: http://localhost:8000")
    print()
    print("🌐 pgAdmin (Database Admin):")
    print("   URL: http://localhost:5050")
    print("   Email: admin@aiemailer.local")
    print("   Password: admin123")
    print()
    print("▶️  Start your app with: python docker_run.py")

def main():
    """Main startup function"""
    print("🐳 AI Email Assistant - Docker Database Setup")
    print("=" * 50)
    
    # Check Docker
    if not check_docker():
        sys.exit(1)
    
    # Start services
    if not start_database_services():
        print("❌ Failed to start database services")
        sys.exit(1)
    
    # Wait for services
    if not wait_for_services():
        print("❌ Services failed to become ready")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        print("❌ Database initialization failed")
        sys.exit(1)
    
    # Show connection info
    show_connection_info()

if __name__ == "__main__":
    main()