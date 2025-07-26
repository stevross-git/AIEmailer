"""
Authentication helper functions and decorators
"""
import functools
from flask import session, redirect, url_for, request, jsonify, current_app

def login_required(f):
    """Decorator to require login for routes"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if 'user_id' not in session:
            current_app.logger.warning(f"Unauthenticated access attempt to {request.endpoint}")
            
            # Handle API requests differently
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required', 'redirect': '/auth/login'}), 401
            else:
                return redirect(url_for('auth.login'))
        
        # Verify user still exists and is active
        try:
            from app.models.user import User
            user = User.query.get(session['user_id'])
            if not user or not user.is_active:
                current_app.logger.warning(f"Invalid user session: {session.get('user_id')}")
                session.clear()
                
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Invalid session', 'redirect': '/auth/login'}), 401
                else:
                    return redirect(url_for('auth.login'))
        
        except Exception as e:
            current_app.logger.error(f"Authentication check error: {e}")
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication error'}), 500
            else:
                return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """Get currently logged in user"""
    if 'user_id' not in session:
        return None
    
    try:
        from app.models.user import User
        user = User.query.get(session['user_id'])
        return user if user and user.is_active else None
    except Exception as e:
        current_app.logger.error(f"Get current user error: {e}")
        return None

def require_auth_api(f):
    """Decorator specifically for API endpoints that require authentication"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }), 401
        
        try:
            from app.models.user import User
            user = User.query.get(session['user_id'])
            if not user or not user.is_active:
                session.clear()
                return jsonify({
                    'success': False,
                    'error': 'Invalid or inactive user session',
                    'code': 'INVALID_SESSION'
                }), 401
        
        except Exception as e:
            current_app.logger.error(f"API authentication error: {e}")
            return jsonify({
                'success': False,
                'error': 'Authentication system error',
                'code': 'AUTH_ERROR'
            }), 500
        
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            else:
                return redirect(url_for('auth.login'))
        
        # Check if user has admin privileges (you can extend User model for this)
        if not getattr(user, 'is_admin', False):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Admin privileges required'}), 403
            else:
                return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_session():
    """Validate current session and return user if valid"""
    if 'user_id' not in session:
        return None, 'No active session'
    
    try:
        from app.models.user import User
        user = User.query.get(session['user_id'])
        
        if not user:
            session.clear()
            return None, 'User not found'
        
        if not user.is_active:
            session.clear()
            return None, 'User account inactive'
        
        return user, None
    
    except Exception as e:
        current_app.logger.error(f"Session validation error: {e}")
        return None, 'Session validation failed'

def create_user_session(user):
    """Create session for user"""
    try:
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.display_name
        session.permanent = True
        
        # Update last login
        user.update_last_login()
        
        current_app.logger.info(f"Created session for user: {user.email}")
        return True
    
    except Exception as e:
        current_app.logger.error(f"Session creation error: {e}")
        return False

def clear_user_session():
    """Clear user session"""
    user_email = session.get('user_email', 'Unknown')
    session.clear()
    current_app.logger.info(f"Cleared session for user: {user_email}")

def check_permissions(user, required_permission):
    """Check if user has required permission"""
    # Placeholder for permission system
    # You can extend this based on your needs
    return True

def rate_limit_check(user_id, action, limit=10, window=60):
    """Simple rate limiting check (placeholder)"""
    # This is a placeholder - in production you'd want to use Redis or similar
    # for proper rate limiting
    return True

def log_security_event(event_type, user_id=None, details=None):
    """Log security-related events"""
    try:
        user_info = f"User {user_id}" if user_id else "Anonymous"
        detail_str = f" - {details}" if details else ""
        
        current_app.logger.warning(f"SECURITY: {event_type} - {user_info}{detail_str}")
        
        # In production, you might want to send this to a security monitoring system
        
    except Exception as e:
        current_app.logger.error(f"Security logging error: {e}")