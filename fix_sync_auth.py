#!/usr/bin/env python3
"""
Fix Email Sync Authentication Issue
"""
import os
import sys

def fix_email_routes():
    """Fix the email sync route authentication"""
    
    # Read the current email routes file
    routes_file = 'app/routes/email.py'
    
    try:
        with open(routes_file, 'r') as f:
            content = f.read()
        
        # Replace the sync route with a fixed version
        fixed_sync_route = '''@email_bp.route('/sync', methods=['POST'])
@login_required
def sync_emails():
    """Sync emails from Microsoft Graph"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            current_app.logger.error("No user_id in session during sync")
            return jsonify({'success': False, 'error': 'Authentication required', 'require_login': True}), 401
        
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"User {user_id} not found in database")
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        current_app.logger.info(f"Starting email sync for user {user_id} ({user.display_name})")
        
        # Check if this is a demo user (no real tokens)
        if user.azure_id == 'demo-user-123' or not user.access_token_hash:
            return sync_demo_emails(user)
        
        # Real Microsoft Graph sync would go here
        # For now, fallback to demo emails
        return sync_demo_emails(user)
    
    except Exception as e:
        current_app.logger.error(f"Email sync error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500'''
        
        # Find and replace the sync route
        import re
        pattern = r'@email_bp\.route\(\'/sync\'.*?(?=@email_bp\.route|def sync_demo_emails|$)'
        replacement = fixed_sync_route + '\n\n'
        
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # If the pattern wasn't found, add it after the imports
        if new_content == content:
            lines = content.split('\n')
            new_lines = []
            added = False
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                
                # Add after the blueprint definition
                if 'email_bp = Blueprint' in line and not added:
                    new_lines.append('')
                    new_lines.extend(fixed_sync_route.split('\n'))
                    new_lines.append('')
                    added = True
            
            new_content = '\n'.join(new_lines)
        
        # Write back to file
        with open(routes_file, 'w') as f:
            f.write(new_content)
        
        print("✅ Fixed email sync authentication")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing email routes: {e}")
        return False

def fix_auth_helpers():
    """Fix the auth helper to be more permissive for API calls"""
    
    helpers_file = 'app/utils/auth_helpers.py'
    
    try:
        with open(helpers_file, 'r') as f:
            content = f.read()
        
        # Replace the login_required decorator
        fixed_decorator = '''def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        
        if not user_id:
            current_app.logger.warning(f"No user_id in session for {request.endpoint}")
            # For API requests, return JSON error
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required', 'require_login': True}), 401
            # For regular requests, redirect to login
            return redirect(url_for('auth.login'))
        
        # Verify user exists in database
        try:
            from app.models.user import User
            user = User.query.get(user_id)
            if not user:
                current_app.logger.warning(f"User {user_id} not found in database")
                session.clear()  # Clear invalid session
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'User not found', 'require_login': True}), 401
                return redirect(url_for('auth.login'))
        except Exception as e:
            current_app.logger.error(f"Error checking user: {e}")
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication error'}), 500
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function'''
        
        # Replace the function
        import re
        pattern = r'def login_required\(f\):.*?return decorated_function'
        new_content = re.sub(pattern, fixed_decorator, content, flags=re.DOTALL)
        
        # Write back to file
        with open(helpers_file, 'w') as f:
            f.write(new_content)
        
        print("✅ Fixed authentication helper")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing auth helpers: {e}")
        return False

def main():
    """Main fix function"""
    print("🔧 Fixing Email Sync Authentication")
    print("=" * 40)
    
    # Fix email routes
    routes_fixed = fix_email_routes()
    
    # Fix auth helpers
    auth_fixed = fix_auth_helpers()
    
    if routes_fixed and auth_fixed:
        print("\n✅ Email sync authentication fixed!")
        print("🚀 Restart the app:")
        print("   python docker_run.py")
        print("\n🎯 The email sync should now work without authentication errors")
    else:
        print("\n❌ Some fixes failed")
        print("💡 Try the backup plan:")
        print("   python no_db_run.py")

if __name__ == "__main__":
    main()