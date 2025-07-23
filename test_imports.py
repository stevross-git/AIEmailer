#!/usr/bin/env python3
"""
Final Import Test
"""
import os
import sys

def test():
    print("Testing All Imports")
    print("=" * 18)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("1. Testing app import...")
        from app import app, db
        print("App and db imported: SUCCESS")
        
        print("2. Testing socketio import...")
        try:
            from app import socketio
            print("SocketIO imported: SUCCESS")
        except ImportError:
            print("SocketIO imported: NOT AVAILABLE (OK)")
        
        print("3. Testing app functionality...")
        with app.app_context():
            from app.models.user import User
            from app.models.email import Email
            
            user_count = User.query.count()
            email_count = Email.query.count()
            print(f"Database test: SUCCESS (Users: {user_count}, Emails: {email_count})")
        
        print()
        print("ALL IMPORTS WORKING!")
        print("=" * 19)
        print("Ready to start:")
        print("   python docker_run.py")
        print()
        print("After start:")
        print("   1. Open enhanced_sync_test.html")
        print("   2. Run enhanced sync")
        print("   3. See emails with full content!")
        
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test()
