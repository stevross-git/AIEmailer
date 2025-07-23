#!/usr/bin/env python3
"""
Fix Azure Client Type Configuration
"""
import os

def fix_microsoft_auth_for_public_client():
    """Fix Microsoft authentication to handle public client configuration"""
    print("🔧 Fixing Microsoft Auth for Public Client")
    print("=" * 40)
    
    auth_file = 'app/routes/auth.py'
    
    # Updated Microsoft auth route that handles both public and confidential clients
    fixed_microsoft_route = '''@auth_bp.route('/microsoft')
def microsoft_auth():
    """Redirect to Microsoft for authentication"""
    try:
        import msal
        
        # Get configuration from environment
        client_id = os.getenv('AZURE_CLIENT_ID')
        tenant_id = os.getenv('AZURE_TENANT_ID')
        client_secret = os.getenv('AZURE_CLIENT_SECRET')
        redirect_uri = os.getenv('AZURE_REDIRECT_URI', 'http://localhost:5000/auth/callback')
        
        if not client_id or not tenant_id:
            current_app.logger.error("Microsoft authentication not configured")
            flash('Microsoft authentication not configured. Please check your .env file.', 'error')
            return redirect(url_for('main.index'))
        
        current_app.logger.info(f"Starting Microsoft auth for client: {client_id}")
        
        # Create MSAL app - handle both public and confidential clients
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        
        if client_secret:
            # Confidential client application
            current_app.logger.info("Using confidential client (with secret)")
            msal_app = msal.ConfidentialClientApplication(
                client_id=client_id,
                client_credential=client_secret,
                authority=authority
            )
        else:
            # Public client application (no secret)
            current_app.logger.info("Using public client (no secret)")
            msal_app = msal.PublicClientApplication(
                client_id=client_id,
                authority=authority
            )
        
        # Microsoft Graph scopes for email access
        scopes = [
            'https://graph.microsoft.com/Mail.Read',
            'https://graph.microsoft.com/Mail.Send',
            'https://graph.microsoft.com/User.Read'
        ]
        
        # Generate auth URL
        state = str(uuid.uuid4())
        auth_url = msal_app.get_authorization_request_url(
            scopes=scopes,
            redirect_uri=redirect_uri,
            state=state
        )
        
        # Store app config in session for callback
        session['msal_state'] = state
        session['msal_config'] = {
            'client_id': client_id,
            'authority': authority,
            'client_credential': client_secret,  # Will be None for public clients
            'redirect_uri': redirect_uri,
            'is_public_client': not bool(client_secret)
        }
        
        current_app.logger.info(f"Redirecting to Microsoft auth: {auth_url[:100]}...")
        return redirect(auth_url)
        
    except ImportError:
        current_app.logger.error("MSAL library not installed")
        flash('Microsoft authentication library not installed. Run: pip install msal', 'error')
        return redirect(url_for('main.index'))
    except Exception as e:
        current_app.logger.error(f"Microsoft auth error: {e}")
        flash(f'Error setting up Microsoft authentication: {str(e)}', 'error')
        return redirect(url_for('main.index'))'''
    
    # Updated callback route that handles both client types
    fixed_callback_route = '''@auth_bp.route('/callback')
def auth_callback():
    """Handle Microsoft authentication callback"""
    try:
        import msal
        from app.utils.auth_helpers import encrypt_token
        
        current_app.logger.info("Processing Microsoft auth callback")
        
        # Get authorization code from callback
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        error_description = request.args.get('error_description')
        
        if error:
            current_app.logger.error(f"Microsoft auth error: {error} - {error_description}")
            flash(f'Authentication failed: {error_description}', 'error')
            return redirect(url_for('main.index'))
        
        if not code:
            current_app.logger.error("No authorization code received")
            flash('No authorization code received', 'error')
            return redirect(url_for('main.index'))
        
        # Verify state
        expected_state = session.get('msal_state')
        if state != expected_state:
            current_app.logger.error(f"State mismatch: expected {expected_state}, got {state}")
            flash('Authentication state mismatch', 'error')
            return redirect(url_for('main.index'))
        
        # Get MSAL config from session
        msal_config = session.get('msal_config')
        if not msal_config:
            current_app.logger.error("MSAL config not found in session")
            flash('Authentication session expired', 'error')
            return redirect(url_for('main.index'))
        
        # Recreate MSAL app based on client type
        if msal_config.get('is_public_client', False):
            current_app.logger.info("Using public client for token exchange")
            msal_app = msal.PublicClientApplication(
                client_id=msal_config['client_id'],
                authority=msal_config['authority']
            )
        else:
            current_app.logger.info("Using confidential client for token exchange")
            msal_app = msal.ConfidentialClientApplication(
                client_id=msal_config['client_id'],
                client_credential=msal_config['client_credential'],
                authority=msal_config['authority']
            )
        
        # Exchange code for token
        scopes = [
            'https://graph.microsoft.com/Mail.Read',
            'https://graph.microsoft.com/Mail.Send',
            'https://graph.microsoft.com/User.Read'
        ]
        
        current_app.logger.info("Exchanging code for token")
        token_result = msal_app.acquire_token_by_authorization_code(
            code=code,
            scopes=scopes,
            redirect_uri=msal_config['redirect_uri']
        )
        
        if 'error' in token_result:
            current_app.logger.error(f"Token acquisition error: {token_result}")
            flash(f"Failed to get access token: {token_result.get('error_description', 'Unknown error')}", 'error')
            return redirect(url_for('main.index'))
        
        current_app.logger.info("Token acquisition successful")
        
        # Get user information from Microsoft Graph
        access_token = token_result['access_token']
        current_app.logger.info("Getting user info from Microsoft Graph")
        
        import requests
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers, timeout=30)
        
        if user_response.status_code != 200:
            current_app.logger.error(f"Failed to get user info: {user_response.status_code} - {user_response.text}")
            flash('Failed to get user information from Microsoft', 'error')
            return redirect(url_for('main.index'))
        
        user_data = user_response.json()
        current_app.logger.info(f"Got user info for: {user_data.get('userPrincipalName')}")
        
        # Create or update user in database
        user = User.query.filter_by(azure_id=user_data['id']).first()
        
        if not user:
            current_app.logger.info(f"Creating new user: {user_data.get('userPrincipalName')}")
            user = User(
                azure_id=user_data['id'],
                email=user_data.get('mail') or user_data.get('userPrincipalName'),
                display_name=user_data.get('displayName', ''),
                given_name=user_data.get('givenName', ''),
                surname=user_data.get('surname', ''),
                job_title=user_data.get('jobTitle', ''),
                office_location=user_data.get('officeLocation', ''),
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(user)
        else:
            current_app.logger.info(f"Updating existing user: {user.email}")
            # Update existing user
            user.email = user_data.get('mail') or user_data.get('userPrincipalName')
            user.display_name = user_data.get('displayName', '')
            user.given_name = user_data.get('givenName', '')
            user.surname = user_data.get('surname', '')
            user.job_title = user_data.get('jobTitle', '')
            user.office_location = user_data.get('officeLocation', '')
            user.is_active = True
        
        # Store encrypted tokens
        try:
            user.access_token_hash = encrypt_token(token_result['access_token'])
            if 'refresh_token' in token_result:
                user.refresh_token_hash = encrypt_token(token_result['refresh_token'])
                current_app.logger.info("Stored refresh token")
            else:
                current_app.logger.warning("No refresh token received (normal for public clients)")
            
            # Set token expiration
            expires_in = token_result.get('expires_in', 3600)
            user.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            user.last_login = datetime.utcnow()
            
            current_app.logger.info("Stored encrypted tokens")
        except Exception as token_error:
            current_app.logger.warning(f"Could not encrypt tokens: {token_error}")
            # Continue without token encryption if the utility is not available
            user.last_login = datetime.utcnow()
        
        db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.display_name
        session['authenticated'] = True
        
        # Clear MSAL session data
        session.pop('msal_state', None)
        session.pop('msal_config', None)
        
        current_app.logger.info(f"Microsoft user authenticated: {user.display_name} (ID: {user.id})")
        flash(f'Successfully signed in as {user.display_name}', 'success')
        
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Auth callback error: {e}")
        import traceback
        traceback.print_exc()
        flash('Authentication failed - please try again', 'error')
        return redirect(url_for('main.index'))'''
    
    try:
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the Microsoft auth route
        import re
        
        # Replace microsoft route
        pattern_microsoft = r"@auth_bp\.route\('/microsoft'\).*?(?=@auth_bp\.route|def auth_callback|$)"
        new_content = re.sub(pattern_microsoft, fixed_microsoft_route + '\n\n', content, flags=re.DOTALL)
        
        # Replace callback route
        pattern_callback = r"@auth_bp\.route\('/callback'\).*?(?=@auth_bp\.route|def \w+|$)"
        new_content = re.sub(pattern_callback, fixed_callback_route + '\n\n', new_content, flags=re.DOTALL)
        
        with open(auth_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Fixed Microsoft authentication for public client")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing auth routes: {e}")
        return False

def check_azure_app_configuration():
    """Check and recommend Azure app configuration"""
    print("\n🔍 Checking Azure App Configuration")
    print("=" * 34)
    
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    
    if client_secret:
        print("🔧 Current setup: Confidential Client (has secret)")
        print("💡 Your Azure app should be configured as:")
        print("   - Application type: Web")
        print("   - Redirect URI: http://localhost:5000/auth/callback")
        print("   - Client secret: Present")
    else:
        print("🔧 Current setup: Public Client (no secret)")
        print("💡 Your Azure app should be configured as:")
        print("   - Application type: Mobile and desktop applications")
        print("   - Redirect URI: http://localhost:5000/auth/callback")
        print("   - No client secret needed")
    
    print("\n🛠️ Azure Portal Steps:")
    print("1. Go to: https://portal.azure.com")
    print("2. Navigate to: Azure Active Directory > App registrations")
    print("3. Find your app: AI Email Assistant")
    print("4. Check 'Authentication' section:")
    print("   - Platform configuration should match your setup")
    print("   - Redirect URIs should include: http://localhost:5000/auth/callback")
    print("5. If using secrets, check 'Certificates & secrets'")

def create_test_auth():
    """Create a test for the authentication"""
    print("\n🧪 Creating Auth Test")
    print("=" * 18)
    
    test_script = '''#!/usr/bin/env python3
"""
Test Microsoft Authentication After Fix
"""
import webbrowser
import time

def test_auth():
    print("🧪 Testing Microsoft Authentication")
    print("=" * 34)
    
    print("This will:")
    print("1. Open logout URL to clear session")
    print("2. Open Microsoft auth URL")
    print("3. You sign in as stephendavies@peoplesainetwork.com")
    print("4. Should work without 'invalid_client' error")
    
    input("Press Enter to start test...")
    
    # Logout first
    print("\\n🚪 Logging out...")
    webbrowser.open("http://localhost:5000/auth/logout")
    time.sleep(2)
    
    # Microsoft auth
    print("🔐 Opening Microsoft sign-in...")
    webbrowser.open("http://localhost:5000/auth/microsoft")
    
    print("\\n✅ What should happen:")
    print("1. Redirects to Microsoft login")
    print("2. Sign in as stephendavies@peoplesainetwork.com")
    print("3. Authorize permissions")
    print("4. Redirects back successfully")
    print("5. Creates real user in database")
    print("6. Email sync will use real Microsoft emails!")

if __name__ == "__main__":
    test_auth()
'''
    
    with open('test_auth_fix.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ Created test_auth_fix.py")

def main():
    """Main function"""
    print("🔧 Fix Azure Client Type Configuration")
    print("=" * 37)
    
    # Fix the authentication routes
    auth_fixed = fix_microsoft_auth_for_public_client()
    
    # Check Azure configuration
    check_azure_app_configuration()
    
    # Create test script
    create_test_auth()
    
    if auth_fixed:
        print(f"\n🎉 AZURE CLIENT TYPE FIXED!")
        print(f"=" * 26)
        print(f"🚀 Restart your app:")
        print(f"   python docker_run.py")
        
        print(f"\n✅ What was fixed:")
        print(f"   - Handles both public and confidential clients")
        print(f"   - Better error handling for token exchange")
        print(f"   - Improved logging for debugging")
        
        print(f"\n🧪 Test the fix:")
        print(f"   python test_auth_fix.py")
        
        print(f"\n🎯 Expected result:")
        print(f"   - No more 'invalid_client' error")
        print(f"   - Successful Microsoft sign-in")
        print(f"   - Real user created with tokens")
        print(f"   - Email sync works with real emails!")
        
    else:
        print(f"\n❌ Could not fix authentication")

if __name__ == "__main__":
    main()