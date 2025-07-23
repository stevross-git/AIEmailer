#!/usr/bin/env python3
"""
Test SQLAlchemy Relationships
"""
import os
import sys

def test_relationships():
    """Test if models can be imported without relationship errors"""
    print("🧪 Testing SQLAlchemy Relationships")
    print("=" * 33)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("1. Importing models...")
        from app.models import db, User, Email, ChatMessage
        print("✅ All models imported successfully")
        
        print("2. Creating app...")
        from app import create_app
        app = create_app()
        print("✅ App created")
        
        print("3. Testing app context...")
        with app.app_context():
            print("✅ App context active")
            
            print("4. Creating tables...")
            db.create_all()
            print("✅ Tables created successfully")
            
            print("5. Testing model creation...")
            
            # Test user creation
            test_user = User(
                email="test@example.com",
                display_name="Test User",
                azure_id="test-123"
            )
            print("✅ User object created")
            
            # Test email creation
            test_email = Email(
                user_id=1,  # Will be set properly when user is saved
                message_id="test-message-123",
                subject="Test Email",
                sender_email="sender@example.com",
                body_text="Test email content"
            )
            print("✅ Email object created")
            
            print("\n🎉 SUCCESS: All models work without relationship errors!")
            print("\n🚀 You can now start the app: python docker_run.py")
            
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_relationships()
