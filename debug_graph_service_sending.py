#!/usr/bin/env python3
"""
Debug Microsoft Graph Service Email Sending
"""
import os

def check_graph_service():
    """Check the Microsoft Graph service send_email method"""
    print("🔍 Checking Microsoft Graph Service")
    print("=" * 33)
    
    graph_file = 'app/services/ms_graph.py'
    
    try:
        with open(graph_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ Graph service file exists")
        
        # Check if send_email method exists
        if 'def send_email(' in content:
            print("✅ send_email method found")
            
            # Look for the actual implementation
            import re
            pattern = r'def send_email\(.*?\):(.*?)(?=def \w+|class \w+|$)'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                method_code = match.group(1)
                print(f"📄 Method length: {len(method_code)} characters")
                
                # Check for key components
                if 'requests.post' in method_code:
                    print("✅ HTTP POST call found")
                else:
                    print("❌ No HTTP POST call found")
                
                if 'sendMail' in method_code:
                    print("✅ Microsoft Graph sendMail endpoint found")
                else:
                    print("❌ sendMail endpoint not found")
                
                if 'return ' in method_code:
                    print("✅ Return statement found")
                else:
                    print("❌ No return statement")
                
                return method_code
            else:
                print("❌ Could not parse send_email method")
                return None
        else:
            print("❌ send_email method not found")
            return None
            
    except Exception as e:
        print(f"❌ Error checking graph service: {e}")
        return None

def create_debug_graph_service():
    """Create a debug version of the graph service send_email method"""
    print("\n🔧 Creating Debug Graph Service")
    print("=" * 30)
    
    debug_send_email = '''    def send_email(self, access_token, to_recipients, subject, body, cc_recipients=None, bcc_recipients=None, importance='normal'):
        """Send an email with detailed debugging"""
        try:
            current_app.logger.info("=== GRAPH SERVICE DEBUG START ===")
            current_app.logger.info(f"Access token length: {len(access_token) if access_token else 0}")
            current_app.logger.info(f"To: {to_recipients}")
            current_app.logger.info(f"CC: {cc_recipients}")
            current_app.logger.info(f"BCC: {bcc_recipients}")
            current_app.logger.info(f"Subject: {subject}")
            current_app.logger.info(f"Body length: {len(body)}")
            current_app.logger.info(f"Importance: {importance}")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            current_app.logger.info("Headers prepared")
            
            # Format recipients
            def format_recipients(recipients):
                if isinstance(recipients, str):
                    return [{'emailAddress': {'address': recipients}}]
                elif isinstance(recipients, list):
                    return [{'emailAddress': {'address': addr}} for addr in recipients]
                return recipients
            
            to_formatted = format_recipients(to_recipients)
            current_app.logger.info(f"Formatted TO recipients: {to_formatted}")
            
            message = {
                'subject': subject,
                'body': {
                    'contentType': 'HTML',
                    'content': body
                },
                'toRecipients': to_formatted,
                'importance': importance
            }
            
            if cc_recipients:
                cc_formatted = format_recipients(cc_recipients)
                message['ccRecipients'] = cc_formatted
                current_app.logger.info(f"Formatted CC recipients: {cc_formatted}")
            
            if bcc_recipients:
                bcc_formatted = format_recipients(bcc_recipients)
                message['bccRecipients'] = bcc_formatted
                current_app.logger.info(f"Formatted BCC recipients: {bcc_formatted}")
            
            data = {'message': message}
            current_app.logger.info(f"Request payload: {json.dumps(data, indent=2)}")
            
            # Microsoft Graph sendMail endpoint
            url = f"{self.graph_endpoint}/me/sendMail"
            current_app.logger.info(f"Request URL: {url}")
            
            current_app.logger.info("Making HTTP POST request to Microsoft Graph...")
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            current_app.logger.info(f"Response status code: {response.status_code}")
            current_app.logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.text:
                current_app.logger.info(f"Response body: {response.text}")
            else:
                current_app.logger.info("Response body is empty")
            
            # Microsoft Graph sendMail returns 202 Accepted for success
            if response.status_code == 202:
                current_app.logger.info("✅ Microsoft Graph accepted the email for sending")
                return True
            else:
                current_app.logger.error(f"❌ Microsoft Graph rejected the email: {response.status_code}")
                current_app.logger.error(f"Error details: {response.text}")
                return False
        
        except requests.exceptions.Timeout:
            current_app.logger.error("❌ Request timeout")
            return False
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"❌ Request error: {e}")
            return False
        except Exception as e:
            current_app.logger.error(f"❌ Send email error: {e}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
        finally:
            current_app.logger.info("=== GRAPH SERVICE DEBUG END ===")'''
    
    return debug_send_email

def update_graph_service_with_debug():
    """Update the graph service with debug version"""
    print("\n🔧 Updating Graph Service with Debug")
    print("=" * 35)
    
    graph_file = 'app/services/ms_graph.py'
    
    try:
        with open(graph_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add json import if not present
        if 'import json' not in content:
            content = content.replace('import requests', 'import requests\nimport json')
        
        debug_method = create_debug_graph_service()
        
        # Replace the send_email method
        import re
        pattern = r'    def send_email\(.*?\):(.*?)(?=    def \w+|class \w+|$)'
        
        match = re.search(pattern, content, re.DOTALL)
        if match:
            new_content = re.sub(pattern, debug_method, content, flags=re.DOTALL)
            
            with open(graph_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ Updated graph service with debug version")
            return True
        else:
            print("❌ Could not find send_email method to replace")
            return False
            
    except Exception as e:
        print(f"❌ Error updating graph service: {e}")
        return False

def create_test_email_permissions():
    """Create a test to check Microsoft Graph permissions"""
    print("\n🧪 Creating Permissions Test")
    print("=" * 26)
    
    test_script = '''#!/usr/bin/env python3
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
            print("\\n🧪 Test 1: Get user info")
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
            print("\\n🧪 Test 2: Check mail folder access")
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
            print("\\n🧪 Test 3: Test email send permissions")
            
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
                    print("\\n🔑 PERMISSIONS ISSUE:")
                    print("Your app needs 'Mail.Send' permission in Azure AD.")
                    print("Contact your admin or check app registration.")
                elif response.status_code == 401:
                    print("\\n🔐 AUTHENTICATION ISSUE:")
                    print("Access token may be expired or invalid.")
    
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    test_graph_permissions()
'''
    
    with open('test_email_permissions.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ Created test_email_permissions.py")

def main():
    """Main function"""
    print("🔍 Debug Microsoft Graph Email Sending")
    print("=" * 37)
    print("📧 The API returned success but email wasn't delivered")
    print("Let's debug the actual Microsoft Graph API call...")
    print()
    
    # Check current graph service
    current_method = check_graph_service()
    
    # Update with debug version
    service_updated = update_graph_service_with_debug()
    
    # Create permissions test
    create_test_email_permissions()
    
    if service_updated:
        print(f"\n🎉 DEBUG VERSION CREATED!")
        print(f"=" * 24)
        print(f"🚀 Restart your app:")
        print(f"   python docker_run.py")
        
        print(f"\n✅ Debug features added:")
        print(f"   - Detailed request/response logging")
        print(f"   - Microsoft Graph endpoint verification")
        print(f"   - HTTP status code analysis")
        print(f"   - Request payload inspection")
        print(f"   - Error response details")
        
        print(f"\n🧪 Test permissions:")
        print(f"   python test_email_permissions.py")
        
        print(f"\n🔍 After restart, send another test email:")
        print(f"   - Logs will show detailed Microsoft Graph API interaction")
        print(f"   - Check if we get HTTP 202 (accepted) response")
        print(f"   - Look for any error messages from Microsoft")
        
        print(f"\n🎯 Possible causes of missing emails:")
        print(f"   - Insufficient permissions (Mail.Send scope)")
        print(f"   - Microsoft 365 security policies")
        print(f"   - Email in spam/junk folder")
        print(f"   - Microsoft Graph API configuration issues")
        
    else:
        print(f"\n❌ Could not create debug version")

if __name__ == "__main__":
    main()