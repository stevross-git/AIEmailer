#!/usr/bin/env python3
"""
Test Microsoft Graph Email Permissions
"""
import os
import sys

def test_graph_permissions():
    """Test if we have the right permissions for email sending"""
    print("🔍 Testing Microsoft Graph Email Permissions")
    print("=" * 42)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        from app import create_app
        from app.models.user import User
        from app.utils.auth_helpers import decrypt_token
        import requests
        import json
        
        app = create_app()
        
        with app.app_context():
            # Find real Microsoft user
            real_user = User.query.filter(
                User.azure_id != 'demo-user-123',
                User.azure_id.isnot(None)
            ).first()
            
            if not real_user:
                print("❌ No real Microsoft user found")
                return
            
            print(f"✅ Found user: {real_user.email}")
            
            if not real_user.access_token_hash:
                print("❌ No access token")
                return
            
            # Decrypt token
            access_token = decrypt_token(real_user.access_token_hash)
            print("✅ Access token decrypted")
            
            # Test 1: Check user info
            print("\n🧪 Test 1: Get user info")
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers,
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                user_info = response.json()
                print(f"✅ User: {user_info.get('displayName')} ({user_info.get('mail')})")
            else:
                print(f"❌ Failed: {response.text}")
                return
            
            # Test 2: Check mail permissions
            print("\n🧪 Test 2: Check mail folder access")
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me/mailFolders',
                headers=headers,
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                folders = response.json()
                print(f"✅ Can access {len(folders.get('value', []))} mail folders")
            else:
                print(f"❌ Cannot access mail folders: {response.text}")
                return
            
            # Test 3: Try to send a test email
            print("\n🧪 Test 3: Test email send permissions")
            
            test_message = {
                'message': {
                    'subject': 'Test Email from AI Assistant',
                    'body': {
                        'contentType': 'HTML',
                        'content': '<p>This is a test email to verify sending permissions.</p>'
                    },
                    'toRecipients': [
                        {
                            'emailAddress': {
                                'address': real_user.email  # Send to self
                            }
                        }
                    ]
                }
            }
            
            response = requests.post(
                'https://graph.microsoft.com/v1.0/me/sendMail',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                json=test_message,
                timeout=30
            )
            
            print(f"Send status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 202:
                print("✅ Email sending permissions work! Test email sent to yourself.")
                print("📧 Check your inbox for the test email.")
            else:
                print(f"❌ Email sending failed: {response.status_code}")
                print(f"Error: {response.text}")
                
                # Check if it's a permissions issue
                if response.status_code == 403:
                    print("\n🔑 PERMISSIONS ISSUE:")
                    print("Your app needs 'Mail.Send' permission in Azure AD.")
                    print("Contact your admin or check app registration.")
                elif response.status_code == 401:
                    print("\n🔐 AUTHENTICATION ISSUE:")
                    print("Access token may be expired or invalid.")
    
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    test_graph_permissions()
