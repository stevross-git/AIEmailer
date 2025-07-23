#!/usr/bin/env python3
"""
Direct Microsoft Sign-in Helper
"""
import os

def add_microsoft_signin_to_homepage():
    """Add a prominent Microsoft sign-in button to the homepage"""
    print("🔧 Adding Microsoft Sign-in to Homepage")
    print("=" * 37)
    
    index_file = 'app/templates/index.html'
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create a prominent Microsoft sign-in section
        microsoft_section = '''
        <!-- Microsoft Sign-in Section -->
        <div class="row justify-content-center mt-5">
            <div class="col-md-8">
                <div class="card border-primary">
                    <div class="card-header bg-primary text-white">
                        <h4 class="mb-0">🔑 Sign in with Microsoft 365</h4>
                    </div>
                    <div class="card-body text-center">
                        <p class="card-text">Sign in with your Microsoft account to sync real emails from <strong>stephendavies@peoplesainetwork.com</strong></p>
                        <a href="/auth/microsoft" class="btn btn-primary btn-lg mb-3">
                            <i class="bi bi-microsoft"></i> Sign in with Microsoft 365
                        </a>
                        <br>
                        <small class="text-muted">This will create a real user and sync your actual emails</small>
                        <hr>
                        <a href="/auth/login" class="btn btn-secondary">
                            Continue with Demo (current mode)
                        </a>
                        <br>
                        <small class="text-muted">Demo mode only shows sample emails</small>
                    </div>
                </div>
            </div>
        </div>
'''
        
        # Find where to insert (after the header/hero section)
        if '<div class="container">' in content:
            insertion_point = content.find('<div class="container">') + len('<div class="container">')
            new_content = content[:insertion_point] + microsoft_section + content[insertion_point:]
        else:
            # Fallback: add after body tag
            new_content = content.replace('<body>', '<body>' + microsoft_section)
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Added prominent Microsoft sign-in section")
        return True
        
    except Exception as e:
        print(f"❌ Error updating homepage: {e}")
        return False

def add_logout_link_to_dashboard():
    """Add logout link to dashboard"""
    print("\n🔧 Adding Logout Link to Dashboard")
    print("=" * 32)
    
    dashboard_file = 'app/templates/dashboard.html'
    
    try:
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add logout link to navbar or top of dashboard
        logout_section = '''
        <!-- Current User Info -->
        <div class="alert alert-info d-flex justify-content-between align-items-center" role="alert">
            <span>
                <strong>Current User:</strong> {{ user.email if user else 'Unknown' }}
                {% if user and user.azure_id == 'demo-user-123' %}
                    <span class="badge bg-warning">Demo Mode</span>
                {% else %}
                    <span class="badge bg-success">Microsoft 365</span>
                {% endif %}
            </span>
            <div>
                <a href="/auth/logout" class="btn btn-outline-secondary btn-sm me-2">Logout</a>
                {% if user and user.azure_id == 'demo-user-123' %}
                    <a href="/auth/microsoft" class="btn btn-primary btn-sm">Sign in with Microsoft</a>
                {% endif %}
            </div>
        </div>
'''
        
        # Find where to insert (after the content block start)
        if '{% block content %}' in content:
            insertion_point = content.find('{% block content %}') + len('{% block content %}')
            new_content = content[:insertion_point] + logout_section + content[insertion_point:]
        else:
            # Fallback: add at the beginning of main content
            new_content = content.replace('<main', logout_section + '\n<main')
        
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Added logout and Microsoft sign-in to dashboard")
        return True
        
    except Exception as e:
        print(f"❌ Error updating dashboard: {e}")
        return False

def create_direct_microsoft_url():
    """Create a direct URL to test Microsoft authentication"""
    print("\n🔧 Creating Direct Microsoft Auth Test")
    print("=" * 35)
    
    print("📍 Direct URLs to test:")
    print("   Homepage: http://localhost:5000")
    print("   Microsoft Auth: http://localhost:5000/auth/microsoft")
    print("   Logout: http://localhost:5000/auth/logout")
    print("   Dashboard: http://localhost:5000/dashboard")
    
    print("\n💡 Test sequence:")
    print("   1. Visit: http://localhost:5000/auth/logout")
    print("   2. Visit: http://localhost:5000/auth/microsoft")
    print("   3. Sign in as stephendavies@peoplesainetwork.com")
    print("   4. Should redirect back with real user")

def create_test_script():
    """Create a test script to check Microsoft auth"""
    print("\n🔧 Creating Microsoft Auth Test Script")
    print("=" * 36)
    
    test_script = '''#!/usr/bin/env python3
"""
Test Microsoft Authentication
"""
import requests
import webbrowser

def test_microsoft_auth():
    """Test Microsoft authentication URLs"""
    print("Testing Microsoft Authentication")
    print("=" * 32)
    
    base_url = "http://localhost:5000"
    
    # Test if app is running
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ App is running (status: {response.status_code})")
    except:
        print("❌ App is not running - start with: python docker_run.py")
        return
    
    # Test Microsoft auth endpoint
    try:
        auth_url = f"{base_url}/auth/microsoft"
        response = requests.get(auth_url, timeout=5, allow_redirects=False)
        print(f"✅ Microsoft auth endpoint exists (status: {response.status_code})")
        
        if response.status_code in [302, 301]:
            print("✅ Microsoft auth is redirecting (good!)")
            redirect_url = response.headers.get('Location', '')
            if 'login.microsoftonline.com' in redirect_url:
                print("✅ Redirecting to Microsoft login")
            else:
                print(f"⚠️ Redirecting to: {redirect_url}")
        
    except Exception as e:
        print(f"❌ Microsoft auth test failed: {e}")
    
    # Open browser to Microsoft auth
    print("\\n🌐 Opening browser to Microsoft sign-in...")
    webbrowser.open(f"{base_url}/auth/logout")
    print("First logging out...")
    
    import time
    time.sleep(2)
    
    webbrowser.open(f"{base_url}/auth/microsoft")
    print("Now opening Microsoft sign-in...")

if __name__ == "__main__":
    test_microsoft_auth()
'''
    
    with open('test_microsoft_auth.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ Created test_microsoft_auth.py")

def main():
    """Main function"""
    print("🔧 Direct Microsoft Sign-in Setup")
    print("=" * 32)
    
    # Add prominent Microsoft sign-in to homepage
    homepage_updated = add_microsoft_signin_to_homepage()
    
    # Add logout/signin to dashboard
    dashboard_updated = add_logout_link_to_dashboard()
    
    # Create test URLs and script
    create_direct_microsoft_url()
    create_test_script()
    
    if homepage_updated:
        print(f"\n🎉 MICROSOFT SIGN-IN READY!")
        print(f"=" * 26)
        print(f"🚀 Restart your app:")
        print(f"   python docker_run.py")
        
        print(f"\n✅ Then try these options:")
        print(f"   1. Visit homepage - look for big Microsoft sign-in card")
        print(f"   2. Direct URL: http://localhost:5000/auth/microsoft")
        print(f"   3. Run test: python test_microsoft_auth.py")
        
        print(f"\n🎯 What should happen:")
        print(f"   - Microsoft auth redirects to login.microsoftonline.com")
        print(f"   - Sign in as stephendavies@peoplesainetwork.com")
        print(f"   - App creates real user with tokens")
        print(f"   - Email sync uses real Microsoft emails!")
        
    else:
        print(f"\n❌ Could not update templates")
        print(f"💡 Try the direct URL: http://localhost:5000/auth/microsoft")

if __name__ == "__main__":
    main()