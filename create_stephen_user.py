#!/usr/bin/env python3
"""
Create Real Microsoft User Manually
"""
import os
import sys

def create_stephen_user():
    """Create Stephen Davies Microsoft user manually"""
    print("Creating Real Microsoft User")
    print("=" * 28)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        from app import create_app, db
        from app.models.user import User
        from datetime import datetime
        
        app = create_app()
        
        with app.app_context():
            # Check if Stephen's user already exists
            stephen_user = User.query.filter_by(email='stephendavies@peoplesainetwork.com').first()
            
            if stephen_user:
                print(f"User already exists: {stephen_user.email}")
                print(f"Azure ID: {stephen_user.azure_id}")
                print(f"Has tokens: {stephen_user.access_token_hash is not None}")
                return stephen_user.id
            
            # Create Stephen's real user
            stephen_user = User(
                azure_id='real-microsoft-user-stephen',  # Temporary until real Microsoft auth
                email='stephendavies@peoplesainetwork.com',
                display_name='Stephen Davies',
                given_name='Stephen',
                surname='Davies',
                job_title='',
                office_location='',
                is_active=True,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            
            db.session.add(stephen_user)
            db.session.commit()
            
            print(f"✅ Created real user: {stephen_user.email}")
            print(f"   ID: {stephen_user.id}")
            print(f"   Azure ID: {stephen_user.azure_id}")
            
            return stephen_user.id
    
    except Exception as e:
        print(f"Error: {e}")
        return None

def login_as_stephen():
    """Create a login session for Stephen"""
    print("\nCreating Login Session for Stephen")
    print("=" * 35)
    
    # This would normally be done through Microsoft auth
    # For now, we need proper Microsoft authentication
    print("⚠️ To get real email sync, you need:")
    print("   1. Proper Microsoft OAuth tokens")
    print("   2. Access to Microsoft Graph API")
    print("   3. Valid Azure AD app registration")
    
    print("\n💡 Next steps:")
    print("   1. Sign in through Microsoft OAuth")
    print("   2. Get real access tokens")
    print("   3. Then email sync will work with real emails")

if __name__ == "__main__":
    user_id = create_stephen_user()
    if user_id:
        login_as_stephen()
