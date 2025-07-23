#!/usr/bin/env python3
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
    print("\n🚪 Logging out...")
    webbrowser.open("http://localhost:5000/auth/logout")
    time.sleep(2)
    
    # Microsoft auth
    print("🔐 Opening Microsoft sign-in...")
    webbrowser.open("http://localhost:5000/auth/microsoft")
    
    print("\n✅ What should happen:")
    print("1. Redirects to Microsoft login")
    print("2. Sign in as stephendavies@peoplesainetwork.com")
    print("3. Authorize permissions")
    print("4. Redirects back successfully")
    print("5. Creates real user in database")
    print("6. Email sync will use real Microsoft emails!")

if __name__ == "__main__":
    test_auth()
