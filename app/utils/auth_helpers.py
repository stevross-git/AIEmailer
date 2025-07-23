"""
Authentication Helper Functions for AI Email Assistant
"""
import os
from functools import wraps
from flask import session, redirect, url_for, current_app, request, jsonify
from cryptography.fernet import Fernet
from app.models.user import User

def login_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        # For simplified demo mode, skip database check
        if os.getenv('USE_SIMPLE_CONFIG', 'true').lower() == 'true':
            return f(*args, **kwargs)
        
        # Verify user still exists (only in full mode)
        try:
            user = User.query.get(session['user_id'])
            if not user or not user.is_active:
                session.clear()
                if request.is_json:
                    return jsonify({'error': 'User account not found or inactive'}), 401
                return redirect(url_for('auth.login'))
        except Exception as e:
            # Database error - in demo mode, continue anyway
            current_app.logger.warning(f"Database error in auth check: {e}")
            if not os.getenv('USE_SIMPLE_CONFIG', 'true').lower() == 'true':
                if request.is_json:
                    return jsonify({'error': 'Database error'}), 500
                return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            if request.is_json:
                return jsonify({'error': 'Admin privileges required'}), 403
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_encryption_key():
    """Get or generate encryption key for tokens"""
    try:
        # Try to get key from environment
        key = os.getenv('ENCRYPTION_KEY')
        if key:
            return key.encode()
        
        # Try to get key from file
        key_file = os.path.join(current_app.config.get('DATABASE_PATH', './data'), 'encryption.key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Save key to file
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key)
        
        current_app.logger.info("Generated new encryption key")
        return key
    
    except Exception as e:
        current_app.logger.error(f"Error handling encryption key: {e}")
        # Fallback to a default key (not secure for production)
        return Fernet.generate_key()

def encrypt_token(token: str) -> str:
    """Encrypt a token for secure storage"""
    try:
        if not token:
            return ""
        
        key = get_encryption_key()
        f = Fernet(key)
        encrypted_token = f.encrypt(token.encode())
        return encrypted_token.decode()
    
    except Exception as e:
        current_app.logger.error(f"Error encrypting token: {e}")
        return ""

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a token for use"""
    try:
        if not encrypted_token:
            return ""
        
        key = get_encryption_key()
        f = Fernet(key)
        decrypted_token = f.decrypt(encrypted_token.encode())
        return decrypted_token.decode()
    
    except Exception as e:
        current_app.logger.error(f"Error decrypting token: {e}")
        return ""

def get_user_token(user: User) -> str:
    """Get valid access token for user"""
    try:
        if not user or not user.access_token_hash:
            return ""
        
        # Check if token is still valid
        if user.has_valid_token():
            return decrypt_token(user.access_token_hash)
        
        # Try to refresh token if refresh token is available
        if user.refresh_token_hash:
            refresh_token = decrypt_token(user.refresh_token_hash)
            if refresh_token:
                from app.services.ms_graph import GraphService
                graph_service = GraphService()
                token_result = graph_service.refresh_access_token(refresh_token)
                
                if token_result:
                    # Update stored tokens
                    user.access_token_hash = encrypt_token(token_result['access_token'])
                    if 'refresh_token' in token_result:
                        user.refresh_token_hash = encrypt_token(token_result['refresh_token'])
                    
                    # Update token expiration
                    from datetime import datetime, timedelta
                    expires_in = token_result.get('expires_in', 3600)
                    user.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    from app import db
                    db.session.commit()
                    
                    return token_result['access_token']
        
        return ""
    
    except Exception as e:
        current_app.logger.error(f"Error getting user token: {e}")
        return ""

def store_credentials_windows(user_id: int, service: str, credential_data: dict):
    """Store credentials using Windows Credential Manager"""
    try:
        if not current_app.config.get('USE_WINDOWS_CREDENTIAL_MANAGER', False):
            return False
        
        import keyring
        
        # Store each credential separately
        for key, value in credential_data.items():
            keyring.set_password(
                service_name=f"{current_app.config['WINDOWS_SERVICE_NAME']}_{service}",
                username=f"{user_id}_{key}",
                password=str(value)
            )
        
        current_app.logger.info(f"Stored credentials for user {user_id} in Windows Credential Manager")
        return True
    
    except Exception as e:
        current_app.logger.error(f"Error storing Windows credentials: {e}")
        return False

def get_credentials_windows(user_id: int, service: str, credential_keys: list) -> dict:
    """Retrieve credentials from Windows Credential Manager"""
    try:
        if not current_app.config.get('USE_WINDOWS_CREDENTIAL_MANAGER', False):
            return {}
        
        import keyring
        
        credentials = {}
        for key in credential_keys:
            try:
                credential = keyring.get_password(
                    service_name=f"{current_app.config['WINDOWS_SERVICE_NAME']}_{service}",
                    username=f"{user_id}_{key}"
                )
                if credential:
                    credentials[key] = credential
            except Exception:
                continue
        
        return credentials
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving Windows credentials: {e}")
        return {}

def delete_credentials_windows(user_id: int, service: str, credential_keys: list) -> bool:
    """Delete credentials from Windows Credential Manager"""
    try:
        if not current_app.config.get('USE_WINDOWS_CREDENTIAL_MANAGER', False):
            return False
        
        import keyring
        
        for key in credential_keys:
            try:
                keyring.delete_password(
                    service_name=f"{current_app.config['WINDOWS_SERVICE_NAME']}_{service}",
                    username=f"{user_id}_{key}"
                )
            except Exception:
                continue
        
        current_app.logger.info(f"Deleted credentials for user {user_id} from Windows Credential Manager")
        return True
    
    except Exception as e:
        current_app.logger.error(f"Error deleting Windows credentials: {e}")
        return False

def validate_session():
    """Validate current session and return user if valid"""
    try:
        if 'user_id' not in session:
            return None
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_active:
            session.clear()
            return None
        
        return user
    
    except Exception as e:
        current_app.logger.error(f"Error validating session: {e}")
        return None

def create_session(user: User):
    """Create session for authenticated user"""
    try:
        session.permanent = True
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.display_name
        
        # Update user's last login
        user.update_login_time()
        
        current_app.logger.info(f"Created session for user {user.email}")
        return True
    
    except Exception as e:
        current_app.logger.error(f"Error creating session: {e}")
        return False

def clear_session():
    """Clear current session"""
    try:
        user_email = session.get('user_email', 'unknown')
        session.clear()
        current_app.logger.info(f"Cleared session for user {user_email}")
        return True
    
    except Exception as e:
        current_app.logger.error(f"Error clearing session: {e}")
        return False

def get_current_user():
    """Get current authenticated user"""
    try:
        if 'user_id' not in session:
            return None
        
        return User.query.get(session['user_id'])
    
    except Exception as e:
        current_app.logger.error(f"Error getting current user: {e}")
        return None

def is_authenticated():
    """Check if current user is authenticated"""
    return 'user_id' in session and validate_session() is not None

def has_permission(permission: str):
    """Check if current user has specific permission"""
    user = get_current_user()
    if not user:
        return False
    
    # Basic permission system - can be extended
    if permission == 'admin':
        return user.is_admin
    elif permission == 'active':
        return user.is_active
    else:
        return True  # Default allow for basic permissions

def refresh_user_session():
    """Refresh user session with updated data"""
    try:
        user = get_current_user()
        if not user:
            return False
        
        # Update session with current user data
        session['user_email'] = user.email
        session['user_name'] = user.display_name
        
        return True
    
    except Exception as e:
        current_app.logger.error(f"Error refreshing user session: {e}")
        return False