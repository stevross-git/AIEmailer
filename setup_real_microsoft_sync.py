#!/usr/bin/env python3
"""
Setup Real Microsoft 365 Email Sync
"""
import os

def check_microsoft_auth_setup():
    """Check if Microsoft authentication is properly set up"""
    print("🔍 Checking Microsoft Authentication Setup")
    print("=" * 42)
    
    # Check .env file
    env_file = '.env'
    required_vars = [
        'AZURE_CLIENT_ID',
        'AZURE_CLIENT_SECRET',
        'AZURE_TENANT_ID',
        'AZURE_REDIRECT_URI'
    ]
    
    config = {}
    missing_vars = []
    
    try:
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                content = f.read()
            
            for var in required_vars:
                for line in content.split('\n'):
                    if line.startswith(f'{var}='):
                        value = line.split('=', 1)[1].strip().strip('"\'')
                        config[var] = value
                        if value and value != 'your_value_here':
                            print(f"✅ {var}: configured")
                        else:
                            print(f"❌ {var}: not set")
                            missing_vars.append(var)
                        break
                else:
                    print(f"❌ {var}: missing")
                    missing_vars.append(var)
        else:
            print("❌ .env file not found")
            missing_vars = required_vars
    
    except Exception as e:
        print(f"❌ Error reading .env: {e}")
        missing_vars = required_vars
    
    return len(missing_vars) == 0, config

def update_auth_routes():
    """Update authentication routes to handle real Microsoft login"""
    print("\n🔧 Setting up Microsoft Authentication Routes")
    print("=" * 44)
    
    auth_file = 'app/routes/auth.py'
    
    # Check if auth routes exist
    try:
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if Microsoft auth is already set up
        if 'microsoft' in content.lower() and 'graph' in content.lower():
            print("✅ Microsoft authentication routes appear to be set up")
            return True
        else:
            print("⚠️ Microsoft authentication routes need to be added")
            return False
    
    except FileNotFoundError:
        print("❌ auth.py file not found")
        return False

def create_microsoft_auth_route():
    """Create Microsoft authentication route"""
    print("\n🔧 Creating Microsoft Authentication Route")
    print("=" * 40)
    
    auth_route = '''
@auth_bp.route('/microsoft')
def microsoft_auth():
    """Redirect to Microsoft for authentication"""
    try:
        import msal
        
        # Get configuration from environment
        client_id = os.getenv('AZURE_CLIENT_ID')
        tenant_id = os.getenv('AZURE_TENANT_ID')
        redirect_uri = os.getenv('AZURE_REDIRECT_URI', 'http://localhost:5000/auth/callback')
        
        if not client_id or not tenant_id:
            flash('Microsoft authentication not configured. Please check your .env file.', 'error')
            return redirect(url_for('main.index'))
        
        # Create MSAL app
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        msal_app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=os.getenv('AZURE_CLIENT_SECRET'),
            authority=authority
        )
        
        # Microsoft Graph scopes for email access
        scopes = [
            'https://graph.microsoft.com/Mail.Read',
            'https://graph.microsoft.com/Mail.Send',
            'https://graph.microsoft.com/User.Read'
        ]
        
        # Generate auth URL
        auth_url = msal_app.get_authorization_request_url(
            scopes=scopes,
            redirect_uri=redirect_uri,
            state=str(uuid.uuid4())
        )
        
        # Store app in session for callback
        session['msal_app'] = {
            'client_id': client_id,
            'authority': authority,
            'client_credential': os.getenv('AZURE_CLIENT_SECRET')
        }
        
        current_app.logger.info(f"Redirecting to Microsoft auth: {auth_url}")
        return redirect(auth_url)
        
    except ImportError:
        flash('Microsoft authentication library not installed. Run: pip install msal', 'error')
        return redirect(url_for('main.index'))
    except Exception as e:
        current_app.logger.error(f"Microsoft auth error: {e}")
        flash('Error setting up Microsoft authentication', 'error')
        return redirect(url_for('main.index'))

@auth_bp.route('/callback')
def auth_callback():
    """Handle Microsoft authentication callback"""
    try:
        import msal
        from app.utils.auth_helpers import encrypt_token
        
        # Get authorization code from callback
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            current_app.logger.error(f"Microsoft auth error: {error}")
            flash(f'Authentication failed: {error}', 'error')
            return redirect(url_for('main.index'))
        
        if not code:
            flash('No authorization code received', 'error')
            return redirect(url_for('main.index'))
        
        # Recreate MSAL app
        msal_config = session.get('msal_app')
        if not msal_config:
            flash('Authentication session expired', 'error')
            return redirect(url_for('main.index'))
        
        msal_app = msal.ConfidentialClientApplication(
            client_id=msal_config['client_id'],
            client_credential=msal_config['client_credential'],
            authority=msal_config['authority']
        )
        
        # Exchange code for token
        redirect_uri = os.getenv('AZURE_REDIRECT_URI', 'http://localhost:5000/auth/callback')
        scopes = [
            'https://graph.microsoft.com/Mail.Read',
            'https://graph.microsoft.com/Mail.Send', 
            'https://graph.microsoft.com/User.Read'
        ]
        
        token_result = msal_app.acquire_token_by_authorization_code(
            code=code,
            scopes=scopes,
            redirect_uri=redirect_uri
        )
        
        if 'error' in token_result:
            current_app.logger.error(f"Token acquisition error: {token_result}")
            flash('Failed to get access token', 'error')
            return redirect(url_for('main.index'))
        
        # Get user information from Microsoft Graph
        access_token = token_result['access_token']
        
        import requests
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
        
        if user_response.status_code != 200:
            flash('Failed to get user information', 'error')
            return redirect(url_for('main.index'))
        
        user_data = user_response.json()
        
        # Create or update user in database
        user = User.query.filter_by(azure_id=user_data['id']).first()
        
        if not user:
            user = User(
                azure_id=user_data['id'],
                email=user_data.get('mail') or user_data.get('userPrincipalName'),
                display_name=user_data.get('displayName', ''),
                given_name=user_data.get('givenName', ''),
                surname=user_data.get('surname', ''),
                job_title=user_data.get('jobTitle', ''),
                office_location=user_data.get('officeLocation', ''),
                is_active=True
            )
            db.session.add(user)
        else:
            # Update existing user
            user.email = user_data.get('mail') or user_data.get('userPrincipalName')
            user.display_name = user_data.get('displayName', '')
            user.given_name = user_data.get('givenName', '')
            user.surname = user_data.get('surname', '')
            user.job_title = user_data.get('jobTitle', '')
            user.office_location = user_data.get('officeLocation', '')
            user.is_active = True
        
        # Store encrypted tokens
        user.access_token_hash = encrypt_token(token_result['access_token'])
        if 'refresh_token' in token_result:
            user.refresh_token_hash = encrypt_token(token_result['refresh_token'])
        
        # Set token expiration
        expires_in = token_result.get('expires_in', 3600)
        user.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        user.last_login = datetime.utcnow()
        
        db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.display_name
        session['authenticated'] = True
        
        current_app.logger.info(f"Microsoft user authenticated: {user.display_name} (ID: {user.id})")
        flash(f'Successfully signed in as {user.display_name}', 'success')
        
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Auth callback error: {e}")
        flash('Authentication failed', 'error')
        return redirect(url_for('main.index'))
'''
    
    # Add to auth routes file
    auth_file = 'app/routes/auth.py'
    
    try:
        with open(auth_file, 'a', encoding='utf-8') as f:
            f.write(auth_route)
        
        print("✅ Added Microsoft authentication routes")
        return True
        
    except Exception as e:
        print(f"❌ Error adding auth routes: {e}")
        return False

def update_templates_for_microsoft_auth():
    """Update templates to show Microsoft sign-in option"""
    print("\n🔧 Updating Templates for Microsoft Sign-in")
    print("=" * 41)
    
    # Update index.html to show Microsoft sign-in
    index_file = 'app/templates/index.html'
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if Microsoft sign-in button already exists
        if 'Sign in with Microsoft' in content:
            print("✅ Microsoft sign-in button already exists")
            return True
        
        # Add Microsoft sign-in button
        signin_button = '''
                <div class="mt-4">
                    <a href="/auth/microsoft" class="btn btn-primary btn-lg">
                        <i class="bi bi-microsoft"></i> Sign in with Microsoft 365
                    </a>
                </div>
                <div class="mt-2">
                    <a href="/auth/login" class="btn btn-secondary">
                        Continue with Demo
                    </a>
                </div>
'''
        
        # Find a good place to insert the button (look for existing buttons or forms)
        if '<div class="mt-4">' in content:
            # Replace existing button section
            new_content = content.replace('<div class="mt-4">', signin_button, 1)
        else:
            # Add before closing main div
            new_content = content.replace('</div>\n</div>', signin_button + '\n</div>\n</div>')
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Added Microsoft sign-in button to homepage")
        return True
        
    except Exception as e:
        print(f"❌ Error updating templates: {e}")
        return False

def install_required_packages():
    """Check and install required packages"""
    print("\n📦 Checking Required Packages")
    print("=" * 29)
    
    required_packages = ['msal', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: installed")
        except ImportError:
            print(f"❌ {package}: missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 Install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🔧 Setup Real Microsoft 365 Email Sync")
    print("=" * 38)
    
    # Check configuration
    config_ok, config = check_microsoft_auth_setup()
    
    # Check packages
    packages_ok = install_required_packages()
    
    # Check auth routes
    auth_ok = update_auth_routes()
    
    # Add auth routes if needed
    if not auth_ok:
        auth_added = create_microsoft_auth_route()
    else:
        auth_added = True
    
    # Update templates
    templates_ok = update_templates_for_microsoft_auth()
    
    print(f"\n📊 Setup Status:")
    print(f"=" * 15)
    print(f"{'✅' if config_ok else '❌'} Azure Config: {'COMPLETE' if config_ok else 'NEEDS SETUP'}")
    print(f"{'✅' if packages_ok else '❌'} Packages: {'INSTALLED' if packages_ok else 'NEEDS INSTALL'}")
    print(f"{'✅' if auth_added else '❌'} Auth Routes: {'READY' if auth_added else 'NEEDS SETUP'}")
    print(f"{'✅' if templates_ok else '❌'} Templates: {'UPDATED' if templates_ok else 'NEEDS UPDATE'}")
    
    if config_ok and packages_ok and auth_added and templates_ok:
        print(f"\n🎉 MICROSOFT 365 SYNC READY!")
        print(f"=" * 30)
        print(f"🚀 Restart your app:")
        print(f"   python docker_run.py")
        print(f"\n✅ Then:")
        print(f"   1. Visit: http://localhost:5000")
        print(f"   2. Click 'Sign in with Microsoft 365'")
        print(f"   3. Authorize the app")
        print(f"   4. Click 'Sync Emails' for real emails!")
        
    else:
        print(f"\n⚠️ Setup incomplete. Please:")
        if not config_ok:
            print(f"   - Add Azure configuration to .env file")
        if not packages_ok:
            print(f"   - Install required packages: pip install msal requests")
        if not auth_added:
            print(f"   - Fix authentication routes")
        if not templates_ok:
            print(f"   - Update templates")
        
        print(f"\n💡 For now, demo emails will continue to work")

if __name__ == "__main__":
    main()