#!/usr/bin/env python3
"""
Quick fix script to replace the hardcoded /common endpoint
"""
import os
import re

def fix_auth_endpoint():
    """Fix the hardcoded /common endpoint in auth.py"""
    print("🔧 Fixing OAuth endpoint in auth.py")
    print("=" * 35)
    
    auth_file = 'app/routes/auth.py'
    
    if not os.path.exists(auth_file):
        print(f"❌ Auth file not found: {auth_file}")
        return False
    
    # Read current content
    with open(auth_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Current content check:")
    if "/common/" in content:
        print("✅ Found /common endpoint - will fix")
    else:
        print("⚠️ /common endpoint not found")
        return False
    
    # Create the fixed login function
    fixed_login_function = '''@auth_bp.route('/login')
def login():
    """Initiate OAuth login with Microsoft"""
    try:
        # Generate state parameter for CSRF protection
        state = str(uuid.uuid4())
        session['oauth_state'] = state
        
        # Get Azure configuration
        client_id = current_app.config.get('AZURE_CLIENT_ID')
        tenant_id = current_app.config.get('AZURE_TENANT_ID')  # ✅ USE TENANT ID
        redirect_uri = current_app.config.get('AZURE_REDIRECT_URI')
        scopes = ' '.join(current_app.config.get('GRAPH_SCOPES', ['User.Read']))
        
        if not client_id or not tenant_id:
            current_app.logger.error("Missing Azure configuration")
            return jsonify({'error': 'Authentication not configured'}), 500
        
        # ✅ CRITICAL FIX: Use tenant-specific endpoint
        if tenant_id.lower() == 'common':
            current_app.logger.warning("Using /common endpoint - may cause issues")
            base_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        else:
            # ✅ FIXED: Use your specific tenant
            base_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
        
        # Build OAuth URL
        oauth_url = (
            f"{base_url}?"
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
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500'''
    
    # Replace the login function using regex
    pattern = r'@auth_bp\.route\(\'/login\'\)\s*\ndef login\(\):.*?(?=@auth_bp\.route|def [a-zA-Z_]|$)'
    
    new_content = re.sub(pattern, fixed_login_function + '\n\n', content, flags=re.DOTALL)
    
    if new_content != content:
        # Backup original
        backup_file = auth_file + '.backup'
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Backed up original to: {backup_file}")
        
        # Write fixed version
        with open(auth_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Fixed auth.py - now using tenant-specific endpoint")
        print("🔄 Please restart your Flask application")
        return True
    else:
        print("❌ Could not apply fix - manual replacement needed")
        return False

def manual_fix_instructions():
    """Provide manual fix instructions"""
    print("\n📝 MANUAL FIX INSTRUCTIONS")
    print("=" * 28)
    print("1. Open: app/routes/auth.py")
    print("2. Find this line:")
    print('   oauth_url = ("https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"')
    print("3. Replace with:")
    print('   base_url = f"https://login.microsoftonline.com/{current_app.config.get(\'AZURE_TENANT_ID\')}/oauth2/v2.0/authorize"')
    print('   oauth_url = (f"{base_url}?"')
    print("4. Save and restart your app")

if __name__ == "__main__":
    print("🚀 Quick OAuth Endpoint Fix")
    print("=" * 25)
    
    success = fix_auth_endpoint()
    
    if not success:
        manual_fix_instructions()
    
    print("\n" + "=" * 50)
    print("After fixing, your logs should show:")
    print("'Redirecting to OAuth: https://login.microsoftonline.com/6ceb32ee-6c77-4bae-b7fc-45f2b110fa5f/oauth2...'")
    print("=" * 50)