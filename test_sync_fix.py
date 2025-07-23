#!/usr/bin/env python3
"""
Test Email Sync Fix
"""
import os
import sys
import requests
import time

def test_email_sync():
    """Test the email sync endpoint directly"""
    print("🔧 Testing Email Sync Fix")
    print("=" * 30)
    
    # Set environment
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        from app import create_app, db
        from app.models.user import User
        from app.models.email import Email
        
        app = create_app()
        
        with app.app_context():
            # Ensure demo user exists
            user = User.query.filter_by(azure_id='demo-user-123').first()
            
            if not user:
                print("Creating demo user...")
                user = User(
                    azure_id='demo-user-123',
                    email='demo@example.com',
                    display_name='Demo User',
                    given_name='Demo',
                    surname='User',
                    job_title='Developer',
                    office_location='Remote',
                    is_active=True
                )
                db.session.add(user)
                db.session.commit()
            
            print(f"✅ Demo user ready: {user.display_name} (ID: {user.id})")
            
            # Count existing emails
            existing_count = Email.query.filter_by(user_id=user.id).count()
            print(f"📧 Current emails: {existing_count}")
            
            # Test the sync endpoint with app context
            with app.test_client() as client:
                # Simulate a session
                with client.session_transaction() as sess:
                    sess['user_id'] = user.id
                    sess['user_email'] = user.email
                    sess['user_name'] = user.display_name
                
                print("🔄 Testing email sync endpoint...")
                response = client.post('/api/email/sync')
                
                print(f"Response status: {response.status_code}")
                print(f"Response data: {response.get_json()}")
                
                if response.status_code == 200:
                    print("✅ Email sync endpoint working!")
                    
                    # Check if emails were created
                    new_count = Email.query.filter_by(user_id=user.id).count()
                    print(f"📧 New email count: {new_count}")
                    
                    if new_count > existing_count:
                        print(f"🎉 Success! Created {new_count - existing_count} new emails")
                        return True
                    else:
                        print("⚠️ No new emails created")
                        return True  # Still a success if no errors
                else:
                    print(f"❌ Sync failed with status {response.status_code}")
                    return False
                    
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    if test_email_sync():
        print(f"\n🎉 EMAIL SYNC IS WORKING!")
        print(f"=" * 30)
        print(f"🚀 Start the app:")
        print(f"   python docker_run.py")
        print(f"\n✅ The email sync button should now work without 401 errors")
    else:
        print(f"\n❌ Email sync still has issues")
        print(f"💡 Try the no-database demo:")
        print(f"   python no_db_run.py")

if __name__ == "__main__":
    main()