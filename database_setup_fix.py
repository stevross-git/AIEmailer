#!/usr/bin/env python3
"""
Fix database setup and connection issues
"""
import os
import sqlite3
import stat

def fix_database_setup():
    """Fix database setup issues"""
    print("🔧 Fixing Database Setup")
    print("=" * 24)
    
    # Create required directories
    directories = ['data', 'instance', 'logs', 'data/sessions']
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create {directory}: {e}")
    
    # Fix permissions for Windows
    try:
        for directory in directories:
            if os.path.exists(directory):
                # Set full permissions
                os.chmod(directory, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        print("✅ Fixed directory permissions")
    except Exception as e:
        print(f"⚠️ Could not fix permissions: {e}")
    
    # Test database file creation
    db_file = 'data/app.db'
    try:
        # Create empty database file if it doesn't exist
        if not os.path.exists(db_file):
            conn = sqlite3.connect(db_file)
            conn.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)')
            conn.commit()
            conn.close()
            print(f"✅ Created database file: {db_file}")
        
        # Test write access
        conn = sqlite3.connect(db_file)
        conn.execute('SELECT 1')
        conn.close()
        print("✅ Database file is accessible")
        
    except Exception as e:
        print(f"❌ Database file error: {e}")
    
    # Test instance directory
    instance_db = 'instance/app.db'
    try:
        if not os.path.exists(instance_db):
            conn = sqlite3.connect(instance_db)
            conn.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)')
            conn.commit()
            conn.close()
            print(f"✅ Created instance database: {instance_db}")
    except Exception as e:
        print(f"⚠️ Instance database warning: {e}")

def create_env_fix():
    """Create a simplified .env for testing"""
    print("\n🔧 Creating Simplified .env")
    print("=" * 27)
    
    simplified_env = '''# Simplified Configuration for Testing
SECRET_KEY=dev-secret-key-change-in-production

# Azure AD Configuration
AZURE_CLIENT_ID=2807d502-5746-4a1d-ac0b-cdbdc1521205
AZURE_TENANT_ID=6ceb32ee-6c77-4bae-b7fc-45f2b110fa5f
AZURE_REDIRECT_URI=http://localhost:5000/auth/callback

# Use SQLite for now
DATABASE_URL=sqlite:///data/app.db
USE_DOCKER_CONFIG=false

# Enable debug mode
DEBUG=true
FLASK_ENV=development
'''
    
    try:
        with open('.env.simple', 'w') as f:
            f.write(simplified_env)
        print("✅ Created .env.simple for testing")
        print("📝 To use: rename .env.simple to .env")
    except Exception as e:
        print(f"❌ Could not create .env.simple: {e}")

def test_database_connection():
    """Test database connection"""
    print("\n🧪 Testing Database Connection")
    print("=" * 30)
    
    test_files = ['data/app.db', 'instance/app.db']
    
    for db_file in test_files:
        try:
            if os.path.exists(db_file):
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute('SELECT sqlite_version()')
                version = cursor.fetchone()[0]
                conn.close()
                print(f"✅ {db_file}: SQLite {version}")
            else:
                print(f"⚠️ {db_file}: Does not exist")
        except Exception as e:
            print(f"❌ {db_file}: Error - {e}")

def main():
    """Main function"""
    print("🛠️ Database Setup Fix Utility")
    print("=" * 30)
    
    fix_database_setup()
    create_env_fix()
    test_database_connection()
    
    print("\n" + "=" * 50)
    print("📋 NEXT STEPS:")
    print("1. Replace app/routes/auth.py with the comprehensive fix above")
    print("2. Optionally rename .env.simple to .env for testing")
    print("3. Restart your Flask application")
    print("4. Test authentication at http://localhost:5000/auth/login")
    print("=" * 50)

if __name__ == "__main__":
    main()