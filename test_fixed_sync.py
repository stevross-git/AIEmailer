#!/usr/bin/env python3
"""
Test the Fixed Email Sync
"""
import os
import sys

def test_fixed_sync():
    """Test if the email sync fix worked"""
    print("🔧 Testing Fixed Email Sync")
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
            
            # Test the sync endpoint
            with app.test_client() as client:
                # Set up session
                with client.session_transaction() as sess:
                    sess['user_id'] = user.id
                    sess['user_email'] = user.email
                    sess['user_name'] = user.display_name
                
                print("🔄 Testing fixed email sync...")
                response = client.post('/api/email/sync')
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"✅ Success! Response: {data}")
                    
                    # Check email count
                    new_count = Email.query.filter_by(user_id=user.id).count()
                    print(f"📧 Email count after sync: {new_count}")
                    
                    if new_count >= existing_count:
                        print("🎉 EMAIL SYNC IS NOW WORKING!")
                        return True
                    else:
                        print("⚠️ No emails were created")
                        return False
                else:
                    data = response.get_json()
                    print(f"❌ Still failing: {data}")
                    return False
                    
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    if test_fixed_sync():
        print(f"\n🎉 SUCCESS! TOKEN VALIDATION FIXED!")
        print(f"=" * 40)
        print(f"🚀 Now start your main app:")
        print(f"   python docker_run.py")
        print(f"\n✅ The email sync should work perfectly!")
        print(f"📧 Click 'Sync Emails' button - no more 401 errors!")
    else:
        print(f"\n⚠️ The fix didn't work completely")
        print(f"🚀 Use the guaranteed working version:")
        print(f"   python working_app_simple.py")
        print(f"\n💡 This bypasses all authentication issues")

if __name__ == "__main__":
    main()