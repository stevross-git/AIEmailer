#!/usr/bin/env python3
"""
Working Test - Database Fixed
"""
import os
import sys

def test():
    print("Testing Fixed Database Setup")
    print("=" * 28)
    
    sys.path.append('.')
    
    try:
        print("1. Testing directory setup...")
        if os.path.exists('instance'):
            print("Instance directory: EXISTS")
        else:
            print("Instance directory: MISSING - will be created")
        
        print("2. Creating app...")
        from app import create_app
        app = create_app()
        print("App creation: SUCCESS")
        
        print("3. Testing database within app context...")
        with app.app_context():
            from app.models.user import User
            from app.models.email import Email
            
            # Test basic queries
            user_count = User.query.count()
            email_count = Email.query.count()
            print(f"Database queries: SUCCESS (Users: {user_count}, Emails: {email_count})")
            
            # Test creating a user
            test_user = User(
                email="test@example.com",
                display_name="Test User",
                azure_id="test-123"
            )
            
            from app.models import db
            db.session.add(test_user)
            db.session.commit()
            
            new_count = User.query.count()
            print(f"User creation test: SUCCESS (Users now: {new_count})")
        
        print()
        print("ALL TESTS PASSED!")
        print("=" * 17)
        print("Database is working correctly!")
        print()
        print("Ready to start app:")
        print("   python docker_run.py")
        print()
        print("After app starts:")
        print("   1. Open enhanced_sync_test.html")
        print("   2. Run enhanced sync")
        print("   3. View emails with full content!")
        
        return True
        
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test()
