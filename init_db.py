#!/usr/bin/env python3
"""
Database Initialization Script
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_directories():
    """Create necessary directories"""
    directories = [
        'data',
        'data/sessions',
        'data/vector_db',
        'logs'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created/verified directory: {directory}")
        except Exception as e:
            print(f"❌ Error creating directory {directory}: {e}")
            return False
    
    return True

def initialize_database():
    """Initialize SQLite database"""
    try:
        # Set environment for simple config
        os.environ['USE_SIMPLE_CONFIG'] = 'true'
        
        # Import Flask app
        from app import create_app, db
        
        # Create app
        app = create_app()
        
        # Create database tables
        with app.app_context():
            # Drop all existing tables (fresh start)
            db.drop_all()
            print("🗑️  Dropped existing tables")
            
            # Create all tables
            db.create_all()
            print("✅ Created all database tables")
            
            # Verify database creation
            from sqlalchemy import text
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            print(f"📋 Created tables: {', '.join(tables)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

def test_database():
    """Test database connectivity"""
    try:
        os.environ['USE_SIMPLE_CONFIG'] = 'true'
        
        from app import create_app, db
        from app.models.user import User
        
        app = create_app()
        
        with app.app_context():
            # Test creating a user
            test_user = User(
                azure_id='test-123',
                email='test@example.com',
                display_name='Test User'
            )
            
            db.session.add(test_user)
            db.session.commit()
            
            # Test querying
            found_user = User.query.filter_by(email='test@example.com').first()
            if found_user:
                print(f"✅ Database test successful: Created user {found_user.display_name}")
                
                # Clean up test user
                db.session.delete(found_user)
                db.session.commit()
                print("🧹 Cleaned up test data")
                
                return True
            else:
                print("❌ Database test failed: Could not retrieve test user")
                return False
                
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def main():
    """Main initialization function"""
    print("🔧 AI Email Assistant - Database Initialization")
    print("=" * 50)
    
    # Step 1: Create directories
    print("\n📁 Creating directories...")
    if not create_directories():
        print("❌ Failed to create directories")
        return False
    
    # Step 2: Initialize database
    print("\n🗄️ Initializing database...")
    if not initialize_database():
        print("❌ Failed to initialize database")
        return False
    
    # Step 3: Test database
    print("\n🧪 Testing database...")
    if not test_database():
        print("❌ Database test failed")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Database initialization completed successfully!")
    print("\nYou can now run the application with:")
    print("python minimal_run.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)