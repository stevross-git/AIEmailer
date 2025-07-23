#!/usr/bin/env python3
"""
Test App Startup
"""
import os
import sys

def test_app_start():
    """Test if the app can start without circular import errors"""
    print("🧪 Testing App Startup")
    print("=" * 19)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("1. Importing Flask...")
        from flask import Flask
        print("✅ Flask imported")
        
        print("2. Importing models...")
        from app.models import db
        print("✅ Models imported")
        
        print("3. Creating app...")
        from app import create_app
        app = create_app()
        print("✅ App created")
        
        print("4. Testing app context...")
        with app.app_context():
            print("✅ App context works")
            
            print("5. Creating database tables...")
            db.create_all()
            print("✅ Database tables created")
            
            print("6. Testing models...")
            from app.models.user import User
            from app.models.email import Email
            print("✅ Models can be imported")
        
        print("\n🎉 SUCCESS: App can start without circular import errors!")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_app_start()
