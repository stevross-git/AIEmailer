#!/usr/bin/env python3
"""
Test Real Microsoft Email Sync
"""
import os
import sys

def test_real_sync():
    """Test the real Microsoft email sync"""
    print("🧪 Testing Real Microsoft Email Sync")
    print("=" * 36)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        from app import create_app, db
        from app.models.user import User
        from app.models.email import Email
        
        app = create_app()
        
        with app.app_context():
            # Find the real Microsoft user
            real_user = User.query.filter(
                User.azure_id != 'demo-user-123',
                User.azure_id.isnot(None)
            ).first()
            
            if not real_user:
                print("❌ No real Microsoft user found")
                print("Sign in with Microsoft first")
                return
            
            print(f"✅ Found real user: {real_user.email}")
            print(f"   Azure ID: {real_user.azure_id}")
            print(f"   Has access token: {real_user.access_token_hash is not None}")
            print(f"   Token expires: {real_user.token_expires_at}")
            
            # Check emails
            email_count = Email.query.filter_by(user_id=real_user.id).count()
            print(f"   Current emails: {email_count}")
            
            if real_user.access_token_hash:
                print("\n🎯 Ready for real email sync!")
                print("Click 'Sync Emails' button to pull from Microsoft 365")
            else:
                print("\n⚠️ No access token - need to sign in again")

if __name__ == "__main__":
    test_real_sync()
