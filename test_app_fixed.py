#!/usr/bin/env python3
"""
Simplified App Startup Test
"""
import os
import sys

def test_app_start():
    """Test if the app can start after fixes"""
    print("🧪 Testing App Startup (Fixed)")
    print("=" * 28)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("1. Importing Flask...")
        from flask import Flask
        print("✅ Flask imported")
        
        print("2. Testing models import...")
        try:
            from app.models import db
            print("✅ Database imported")
        except Exception as db_error:
            print(f"❌ Database import failed: {db_error}")
            return False
        
        print("3. Testing individual models...")
        try:
            from app.models.user import User
            print("✅ User model imported")
        except Exception as user_error:
            print(f"❌ User model failed: {user_error}")
        
        try:
            from app.models.email import Email
            print("✅ Email model imported")
        except Exception as email_error:
            print(f"❌ Email model failed: {email_error}")
        
        try:
            from app.models.chat import ChatMessage
            print("✅ Chat model imported")
        except Exception as chat_error:
            print(f"❌ Chat model failed: {chat_error}")
        
        print("4. Creating app...")
        from app import create_app
        app = create_app()
        print("✅ App created successfully")
        
        print("5. Testing app context...")
        with app.app_context():
            print("✅ App context works")
            
            print("6. Creating database tables...")
            db.create_all()
            print("✅ Database tables created")
        
        print("\n🎉 SUCCESS: App can start without errors!")
        print("\n🚀 You can now run: python docker_run.py")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_app_start()
