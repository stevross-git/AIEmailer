"""
Authentication routes for AI Email Assistant
"""
import os
import uuid
import hashlib
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, session, jsonify, current_app
from app.models import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/microsoft')
def microsoft_login():
    """Microsoft OAuth login redirect (alias for /login)"""
    return redirect(url_for('auth.login'))

@auth_bp.route('/login')
def login():
    """Initiate OAuth login with Microsoft"""
    try:
        # For demo purposes, create a simple login flow
        # In production, this would redirect to Microsoft OAuth
        
        # Generate state parameter for CSRF protection
        state = str(uuid.uuid4())
        session['oauth_state'] = state
        
        # Microsoft OAuth parameters
        client_id = current_app.config.get('AZURE_CLIENT_ID')
        redirect_uri = current_app.config.get('AZURE_REDIRECT_URI')
        scopes = ' '.join(current_app.config.get('GRAPH_SCOPES', []))
        
        # Microsoft OAuth URL
        oauth_url = (
            f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
            f"client_id={client_id}&"
            f"response_type=code&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scopes}&"
            f"state={state}&"
            f"response_mode=query&"
            f"prompt=select_account"
        )
        
        current_app.logger.info(f"Redirecting to OAuth: {oauth_url[:100]}...")
        return redirect(oauth_url)
        
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@auth_bp.route('/callback')
def callback():
    """Handle OAuth callback from Microsoft"""
    try:
        # Get authorization code from callback
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        # Check for OAuth errors
        if error:
            current_app.logger.error(f"OAuth error: {error}")
            return jsonify({'error': 'OAuth failed', 'details': error}), 400
        
        # Verify state parameter
        if not state or state != session.get('oauth_state'):
            current_app.logger.error("Invalid OAuth state")
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        # Exchange code for tokens (simplified for demo)
        if code:
            # In production, exchange code for access token
            # For demo, create/login user directly
            
            # Demo user creation/login
            demo_user_email = "demo@example.com"
            demo_user_name = "Demo User"
            demo_azure_id = f"demo-{uuid.uuid4()}"
            
            user = User.find_by_email(demo_user_email)
            if not user:
                # Create new user
                user = User(
                    email=demo_user_email,
                    display_name=demo_user_name,
                    azure_id=demo_azure_id,
                    azure_tenant_id="demo-tenant",
                    is_active=True
                )
                db.session.add(user)
                db.session.commit()
                current_app.logger.info(f"Created new user: {demo_user_email}")
            
            # Update login timestamp
            user.update_last_login()
            
            # Store user session
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.display_name
            session.permanent = True
            
            current_app.logger.info(f"User logged in: {user.email}")
            
            # Clean up OAuth state
            session.pop('oauth_state', None)
            
            # Redirect to dashboard
            return redirect(url_for('main.dashboard'))
        
        else:
            current_app.logger.error("No authorization code received")
            return jsonify({'error': 'No authorization code'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Callback error: {e}")
        return jsonify({'error': 'Callback failed', 'details': str(e)}), 500

@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """Log out current user"""
    try:
        user_email = session.get('user_email', 'Unknown')
        
        # Clear session
        session.clear()
        
        current_app.logger.info(f"User logged out: {user_email}")
        
        if request.method == 'POST':
            return jsonify({'success': True, 'message': 'Logged out successfully'})
        else:
            return redirect(url_for('main.index'))
            
    except Exception as e:
        current_app.logger.error(f"Logout error: {e}")
        if request.method == 'POST':
            return jsonify({'error': 'Logout failed', 'details': str(e)}), 500
        else:
            return redirect(url_for('main.index'))

@auth_bp.route('/status')
def status():
    """Get authentication status"""
    try:
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user and user.is_active:
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'display_name': user.display_name,
                        'last_login': user.last_login.isoformat() if user.last_login else None,
                        'last_email_sync': user.last_email_sync.isoformat() if user.last_email_sync else None
                    }
                })
        
        return jsonify({'authenticated': False})
        
    except Exception as e:
        current_app.logger.error(f"Status check error: {e}")
        return jsonify({'authenticated': False, 'error': str(e)})

@auth_bp.route('/demo-login', methods=['POST'])
def demo_login():
    """Demo login for testing purposes"""
    try:
        # Create or get demo user
        demo_email = "demo@aiemailassistant.local"
        demo_name = "Demo User"
        
        user = User.find_by_email(demo_email)
        if not user:
            user = User(
                email=demo_email,
                display_name=demo_name,
                azure_id=f"demo-{uuid.uuid4()}",
                azure_tenant_id="demo-tenant",
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"Created demo user: {demo_email}")
        
        # Update login timestamp
        user.update_last_login()
        
        # Store user session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.display_name
        session.permanent = True
        
        current_app.logger.info(f"Demo login successful: {user.email}")
        
        return jsonify({
            'success': True,
            'message': 'Demo login successful',
            'user': user.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Demo login error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/user')
def get_user():
    """Get current user information"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_active:
            session.clear()
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict(),
            'stats': {
                'total_emails': user.get_email_count(),
                'unread_emails': user.get_unread_email_count()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Get user error: {e}")
        return jsonify({'error': str(e)}), 500

# Token management functions
def hash_token(token):
    """Hash a token for secure storage"""
    if not token:
        return None
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def store_user_tokens(user, access_token, refresh_token=None, expires_in=None):
    """Store user tokens securely"""
    try:
        # Hash tokens before storing
        user.access_token_hash = hash_token(access_token)
        if refresh_token:
            user.refresh_token_hash = hash_token(refresh_token)
        
        # Calculate expiration time
        if expires_in:
            from datetime import timedelta
            user.token_expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
        
        db.session.commit()
        current_app.logger.info(f"Stored tokens for user: {user.email}")
        
    except Exception as e:
        current_app.logger.error(f"Token storage error: {e}")
        raise