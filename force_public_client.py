#!/usr/bin/env python3
"""
Force Public Client Configuration
"""
import os

def update_env_for_public_client():
    """Update .env to force public client mode"""
    print("🔧 Updating .env for Public Client Mode")
    print("=" * 37)
    
    env_file = '.env'
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Comment out or remove the client secret
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if line.startswith('AZURE_CLIENT_SECRET='):
                # Comment out the secret to force public client mode
                new_lines.append(f'# {line}  # Commented out for public client')
                print(f"✅ Commented out: {line[:30]}...")
            else:
                new_lines.append(line)
        
        # Add a public client flag
        new_lines.append('')
        new_lines.append('# Force public client mode (no secret)')
        new_lines.append('AZURE_USE_PUBLIC_CLIENT=true')
        
        with open(env_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ Updated .env file for public client mode")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env: {e}")
        return False

def create_simple_public_auth():
    """Create a simple public client only authentication"""
    print("\n🔧 Creating Simple Public Client Auth")
    print("=" * 35)
    
    simple_auth = '''@auth_bp.route('/microsoft')
def microsoft_auth():
    """Redirect to Microsoft for authentication (Public Client Only)"""
    try:
        import msal
        
        # Get configuration from environment
        client_id = os.getenv('AZURE_CLIENT_ID')
        tenant_id = os.getenv('AZURE_TENANT_ID')
        redirect_uri = os.getenv('AZURE_REDIRECT_URI', 'http://localhost:5000/auth/callback')
        
        if not client_id or not tenant_id:
            current_app.logger.error("Microsoft authentication not configured")
            flash('Microsoft authentication not configured. Please check your .env file.', 'error')
            return redirect(url_for('main.index'))
        
        current_app.logger.info(f"Starting Microsoft auth for PUBLIC client: {client_id}")
        
        # ALWAYS use public client (no secret)
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        msal_app = msal.PublicClientApplication(
            client_id=client_id,
            authority=authority
        )
        
        current_app.logger.info("Created PUBLIC client application (no secret)")
        
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
            'redirect_uri': redirect_uri,
            'is_public_client': True  # Always true
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
        return redirect(url_for('main.index'))

@auth_bp.route('/callback')
def auth_callback():
    """Handle Microsoft authentication callback (Public Client Only)"""
    try:
        import msal
        from app.utils.auth_helpers import encrypt_token
        
        current_app.logger.info("Processing Microsoft auth callback for PUBLIC client")
        
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
        
        # ALWAYS use public client
        current_app.logger.info("Using PUBLIC client for token exchange (no secret)")
        msal_app = msal.PublicClientApplication(
            client_id=msal_config['client_id'],
            authority=msal_config['authority']
        )
        
        # Exchange code for token
        scopes = [
            'https://graph.microsoft.com/Mail.Read',
            'https://graph.microsoft.com/Mail.Send',
            'https://graph.microsoft.com/User.Read'
        ]
        
        current_app.logger.info("Exchanging code for token (PUBLIC client)")
        token_result = msal_app.acquire_token_by_authorization_code(
            code=code,
            scopes=scopes,
            redirect_uri=msal_config['redirect_uri']
        )
        
        if 'error' in token_result:
            current_app.logger.error(f"Token acquisition error: {token_result}")
            flash(f"Failed to get access token: {token_result.get('error_description', 'Unknown error')}", 'error')
            return redirect(url_for('main.index'))
        
        current_app.logger.info("✅ Token acquisition successful with PUBLIC client!")
        
        # Get user information from Microsoft Graph
        access_token = token_result['access_token']
        current_app.logger.info("Getting user info from Microsoft Graph")
        
        import requests
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers, timeout=30)
        
        if user_response.status_code != 200:
            current_app.logger.error(f"Failed to get user info: {user_response.status_code}")
            flash('Failed to get user information from Microsoft', 'error')
            return redirect(url_for('main.index'))
        
        user_data = user_response.json()
        current_app.logger.info(f"✅ Got user info for: {user_data.get('userPrincipalName')}")
        
        # Create or update user in database
        user = User.query.filter_by(azure_id=user_data['id']).first()
        
        if not user:
            current_app.logger.info(f"Creating new REAL user: {user_data.get('userPrincipalName')}")
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
            current_app.logger.info(f"Updating existing real user: {user.email}")
            user.email = user_data.get('mail') or user_data.get('userPrincipalName')
            user.display_name = user_data.get('displayName', '')
            user.is_active = True
        
        # Store encrypted tokens
        try:
            user.access_token_hash = encrypt_token(token_result['access_token'])
            current_app.logger.info("✅ Stored encrypted access token")
            
            # Public clients might not get refresh tokens
            if 'refresh_token' in token_result:
                user.refresh_token_hash = encrypt_token(token_result['refresh_token'])
                current_app.logger.info("✅ Stored refresh token")
            else:
                current_app.logger.info("ℹ️ No refresh token (normal for public clients)")
            
            # Set token expiration
            expires_in = token_result.get('expires_in', 3600)
            user.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            user.last_login = datetime.utcnow()
            
        except Exception as token_error:
            current_app.logger.warning(f"Could not encrypt tokens: {token_error}")
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
        
        current_app.logger.info(f"🎉 REAL Microsoft user authenticated: {user.display_name} (ID: {user.id})")
        flash(f'Successfully signed in as {user.display_name} - Ready for real email sync!', 'success')
        
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Auth callback error: {e}")
        import traceback
        traceback.print_exc()
        flash('Authentication failed - please try again', 'error')
        return redirect(url_for('main.index'))'''
    
    # Replace the auth routes
    auth_file = 'app/routes/auth.py'
    
    try:
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace both microsoft and callback routes
        import re
        
        # Remove existing microsoft and callback routes
        pattern = r"@auth_bp\.route\('/microsoft'\).*?(?=@auth_bp\.route\('/logout'\)|@auth_bp\.route\('/status'\)|$)"
        new_content = re.sub(pattern, simple_auth + '\n\n', content, flags=re.DOTALL)
        
        with open(auth_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Created public-client-only authentication")
        return True
        
    except Exception as e:
        print(f"❌ Error creating public auth: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Force Public Client Configuration")
    print("=" * 34)
    
    # Update .env to remove client secret
    env_updated = update_env_for_public_client()
    
    # Create simple public client auth
    auth_created = create_simple_public_auth()
    
    if env_updated and auth_created:
        print(f"\n🎉 PUBLIC CLIENT MODE ENABLED!")
        print(f"=" * 28)
        print(f"🚀 Restart your app:")
        print(f"   python docker_run.py")
        
        print(f"\n✅ Changes made:")
        print(f"   - Commented out AZURE_CLIENT_SECRET in .env")
        print(f"   - Forced public client mode")
        print(f"   - Simplified authentication flow")
        
        print(f"\n🎯 Test authentication:")
        print(f"   1. Visit: http://localhost:5000/auth/microsoft")
        print(f"   2. Should work without 'invalid_client' error")
        print(f"   3. Sign in as: stephendavies@peoplesainetwork.com")
        print(f"   4. Real user created with tokens")
        print(f"   5. Email sync will use real Microsoft emails!")
        
        print(f"\n💡 Azure app requirements:")
        print(f"   - Must be configured as 'Mobile and desktop applications'")
        print(f"   - Redirect URI: http://localhost:5000/auth/callback")
        print(f"   - No client secret needed")
        
    else:
        print(f"\n❌ Configuration failed")

if __name__ == "__main__":
    main()