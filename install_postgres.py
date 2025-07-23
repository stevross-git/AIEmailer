#!/usr/bin/env python3
"""
Install PostgreSQL dependencies
"""
import subprocess
import sys

def install_postgres_deps():
    """Install PostgreSQL dependencies"""
    print("📦 Installing PostgreSQL dependencies...")
    
    packages = [
        "psycopg2-binary",  # PostgreSQL adapter
        "redis",            # Redis Python client
    ]
    
    for package in packages:
        try:
            print(f"📥 Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def main():
    """Main installation function"""
    print("🛠️ PostgreSQL Dependencies Installation")
    print("=" * 40)
    
    if install_postgres_deps():
        print("\n✅ All dependencies installed successfully!")
        print("You can now start the Docker database setup:")
        print("python start_docker_db.py")
    else:
        print("\n❌ Some dependencies failed to install")

if __name__ == "__main__":
    main()