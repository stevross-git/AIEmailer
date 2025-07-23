#!/usr/bin/env python3
"""
Force Microsoft Login and Check Real User
"""
import os

def check_current_session():
    """Check what user is currently logged in"""
    print("🔍 Checking Current Session")
    print("=" * 26)
    
    # Check if we can see session data from app
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    
    try:
        import sys
        sys.path.append('.')
        
        from app import create_app, db
        from app.models.user import User
        
        app = create_app()
        
        with app.app_context():
            users = User.query.all()
            
            print(f"Users in database:")
            for user in users:
                is_real = user.azure_id and user.azure_id != 'demo-user-123'
                user_type = 'Real Microsoft User' if is_real else 'Demo User'
                has_tokens = 'Yes' if user.access_token_hash else 'No'
                
                print(f"\n📧 {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Azure ID: {user.azure_id}")
                print(f"   Type: {user_type}")
                print(f"   Has Tokens: {has_tokens}")
                print(f"   Last Login: {user.last_login}")
                
                if is_real:
                    print(f"   ✅ This is your real Microsoft account!")
                else:
                    print(f"   ⚠️ This is a demo account")
    
    except Exception as e:
        print(f"Error checking users: {e}")

def create_logout_route():
    """Add a logout route to clear session"""
    print("\n🔧 Adding Logout Route")
    print("=" * 20)
    
    logout_route = '''
@auth_bp.route('/logout')
def logout():
    """Logout user and clear session"""
    try:
        user_email = session.get('user_email', 'Unknown')
        session.clear()
        current_app.logger.info(f"User {user_email} logged out")
        flash('Successfully logged out', 'success')
        return redirect(url_for('main.index'))
    except Exception as e:
        current_app.logger.error(f"Logout error: {e}")
        session.clear()
        return redirect(url_for('main.index'))
'''
    
    auth_file = 'app/routes/auth.py'
    
    try:
        # Check if logout already exists
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '/logout' in content:
            print("✅ Logout route already exists")
            return True
        
        # Add logout route
        with open(auth_file, 'a', encoding='utf-8') as f:
            f.write(logout_route)
        
        print("✅ Added logout route")
        return True
        
    except Exception as e:
        print(f"❌ Error adding logout route: {e}")
        return False

def update_index_template():
    """Update index template to show logout and Microsoft sign-in options"""
    print("\n🔧 Updating Index Template")
    print("=" * 26)
    
    index_file = 'app/templates/index.html'
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add logout link and clear Microsoft sign-in option
        auth_section = '''
        <div class="auth-section mt-4">
            <h3>Sign In Options</h3>
            <div class="mt-3">
                <a href="/auth/logout" class="btn btn-warning me-2">
                    Logout Current User
                </a>
                <a href="/auth/microsoft" class="btn btn-primary me-2">
                    Sign in with Microsoft 365
                </a>
                <a href="/auth/login" class="btn btn-secondary">
                    Continue with Demo
                </a>
            </div>
            <div class="mt-2">
                <small class="text-muted">
                    Use "Sign in with Microsoft 365" for real email sync from stephendavies@peoplesainetwork.com
                </small>
            </div>
        </div>
'''
        
        # Find where to insert (look for existing buttons or before closing container)
        if '<div class="mt-4">' in content:
            new_content = content.replace('<div class="mt-4">', auth_section, 1)
        else:
            # Add before closing main container
            new_content = content.replace('</div>\n</main>', auth_section + '\n</div>\n</main>')
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Updated index template with logout and Microsoft sign-in")
        return True
        
    except Exception as e:
        print(f"❌ Error updating template: {e}")
        return False

def create_manual_user_creation():
    """Create a script to manually create your Microsoft user"""
    print("\n🔧 Creating Manual User Creation Script")
    print("=" * 38)
    
    user_script = '''#!/usr/bin/env python3
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
    print("\\nCreating Login Session for Stephen")
    print("=" * 35)
    
    # This would normally be done through Microsoft auth
    # For now, we need proper Microsoft authentication
    print("⚠️ To get real email sync, you need:")
    print("   1. Proper Microsoft OAuth tokens")
    print("   2. Access to Microsoft Graph API")
    print("   3. Valid Azure AD app registration")
    
    print("\\n💡 Next steps:")
    print("   1. Sign in through Microsoft OAuth")
    print("   2. Get real access tokens")
    print("   3. Then email sync will work with real emails")

if __name__ == "__main__":
    user_id = create_stephen_user()
    if user_id:
        login_as_stephen()
'''
    
    with open('create_stephen_user.py', 'w', encoding='utf-8') as f:
        f.write(user_script)
    
    print("✅ Created create_stephen_user.py")

def main():
    """Main function"""
    print("🔧 Force Microsoft Login Setup")
    print("=" * 29)
    
    # Check current session
    check_current_session()
    
    # Add logout route
    logout_added = create_logout_route()
    
    # Update templates
    template_updated = update_index_template()
    
    # Create manual user script
    create_manual_user_creation()
    
    print(f"\n🎯 Current Issue:")
    print(f"You're logged in as: demo@example.com (demo user)")
    print(f"Need to login as: stephendavies@peoplesainetwork.com (real user)")
    
    print(f"\n🚀 Solutions:")
    print(f"1. Restart app: python docker_run.py")
    print(f"2. Visit: http://localhost:5000")
    print(f"3. Click 'Logout Current User'")
    print(f"4. Click 'Sign in with Microsoft 365'")
    print(f"5. Authorize as stephendavies@peoplesainetwork.com")
    print(f"6. Then email sync will use real emails!")
    
    print(f"\n💡 Alternative:")
    print(f"1. Run: python create_stephen_user.py")
    print(f"2. But you'll still need real Microsoft tokens for email sync")
    
    if logout_added and template_updated:
        print(f"\n✅ Logout and sign-in options added to homepage")

if __name__ == "__main__":
    main()