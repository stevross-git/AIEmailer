#!/usr/bin/env python3
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
    print("\n🌐 Opening browser to Microsoft sign-in...")
    webbrowser.open(f"{base_url}/auth/logout")
    print("First logging out...")
    
    import time
    time.sleep(2)
    
    webbrowser.open(f"{base_url}/auth/microsoft")
    print("Now opening Microsoft sign-in...")

if __name__ == "__main__":
    test_microsoft_auth()
