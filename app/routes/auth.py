"""
Authentication routes for AI Email Assistant
"""
from flask import Blueprint, request, session, redirect, url_for, flash, jsonify, current_app
from app.models.user import User
from app import db
from datetime import datetime, timedelta
import uuid
import os

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login')
def login():
    """Demo login - creates demo user session"""
    try:
        # Get or create demo user
        demo_user = User.query.filter_by(azure_id='demo-user-123').first()
        
        if not demo_user:
            demo_user = User(
                azure_id='demo-user-123',
                email='demo@example.com',
                display_name='Demo User',
                given_name='Demo',
                surname='User',
                job_title='Developer',
                office_location='Remote',
                is_active=True,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            db.session.add(demo_user)
            db.session.commit()
        else:
            demo_user.last_login = datetime.utcnow()
            db.session.commit()
        
        # Set session
        session['user_id'] = demo_user.id
        session['user_email'] = demo_user.email
        session['user_name'] = demo_user.display_name
        session['authenticated'] = True
        
        current_app.logger.info(f"Demo user login, ID: {demo_user.id}")
        flash('Signed in as Demo User', 'success')
        
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Demo login error: {e}")
        flash('Login failed', 'error')
        return redirect(url_for('main.index'))

@auth_bp.route('/microsoft')
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
        return redirect(url_for('main.index'))

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

@auth_bp.route('/status')
def auth_status():
    """Get authentication status"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'authenticated': False,
                'user': None,
                'message': 'Please sign in'
            })
        
        user = User.query.get(user_id)
        
        if not user:
            session.clear()
            return jsonify({
                'authenticated': False,
                'user': None,
                'message': 'User not found - please sign in again'
            })
        
        # Check if this is a real Microsoft user
        is_real_user = user.azure_id and user.azure_id != 'demo-user-123'
        has_tokens = user.access_token_hash is not None
        
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'display_name': user.display_name,
                'azure_id': user.azure_id,
                'is_real_user': is_real_user,
                'has_tokens': has_tokens,
                'last_sync': user.last_sync.isoformat() if user.last_sync else None
            },
            'message': f'Signed in as {user.email}' + (' (Microsoft 365)' if is_real_user else ' (Demo)')
        })
        
    except Exception as e:
        current_app.logger.error(f"Auth status error: {e}")
        return jsonify({
            'authenticated': False,
            'error': str(e)
        }), 500
