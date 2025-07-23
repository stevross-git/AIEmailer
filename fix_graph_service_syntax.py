#!/usr/bin/env python3
"""
Fix Microsoft Graph Service Syntax Error
"""
import os

def create_clean_graph_service():
    """Create a clean, working Microsoft Graph service"""
    print("🔧 Creating Clean Microsoft Graph Service")
    print("=" * 38)
    
    clean_graph_service = '''"""
Microsoft Graph API Service for AI Email Assistant
"""
import requests
import json
from urllib.parse import urlencode
from datetime import datetime, timedelta
from flask import current_app

class GraphService:
    """Microsoft Graph API integration service"""
    
    def __init__(self):
        self.client_id = current_app.config['AZURE_CLIENT_ID']
        self.client_secret = current_app.config['AZURE_CLIENT_SECRET']
        self.tenant_id = current_app.config['AZURE_TENANT_ID']
        self.redirect_uri = current_app.config['AZURE_REDIRECT_URI']
        self.scopes = current_app.config['GRAPH_SCOPES']
        self.graph_endpoint = current_app.config['GRAPH_API_ENDPOINT']
        
        # OAuth endpoints
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.auth_endpoint = f"{self.authority}/oauth2/v2.0/authorize"
        self.token_endpoint = f"{self.authority}/oauth2/v2.0/token"
    
    def get_authorization_url(self, state):
        """Generate Microsoft OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'state': state,
            'response_mode': 'query'
        }
        
        return f"{self.auth_endpoint}?{urlencode(params)}"
    
    def get_token_from_code(self, authorization_code):
        """Exchange authorization code for access token"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_code,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code',
                'scope': ' '.join(self.scopes)
            }
            
            response = requests.post(
                self.token_endpoint,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Token exchange failed: {response.text}")
                return None
        
        except Exception as e:
            current_app.logger.error(f"Token exchange error: {e}")
            return None
    
    def refresh_access_token(self, refresh_token):
        """Refresh expired access token"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
                'scope': ' '.join(self.scopes)
            }
            
            response = requests.post(
                self.token_endpoint,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Token refresh failed: {response.text}")
                return None
        
        except Exception as e:
            current_app.logger.error(f"Token refresh error: {e}")
            return None
    
    def get_user_info(self, access_token):
        """Get user information from Microsoft Graph"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.graph_endpoint}/me",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Get user info failed: {response.text}")
                return None
        
        except Exception as e:
            current_app.logger.error(f"Get user info error: {e}")
            return None
    
    def get_emails(self, access_token, folder='inbox', limit=50, skip=0):
        """Get emails from specified folder"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Build URL based on folder
            if folder.lower() == 'inbox':
                url = f"{self.graph_endpoint}/me/mailFolders/inbox/messages"
            elif folder.lower() == 'sent':
                url = f"{self.graph_endpoint}/me/mailFolders/sentitems/messages"
            else:
                url = f"{self.graph_endpoint}/me/mailFolders/{folder}/messages"
            
            params = {
                '$top': min(limit, 1000),  # Graph API limit
                '$skip': skip,
                '$orderby': 'receivedDateTime desc',
                '$select': 'id,subject,sender,toRecipients,ccRecipients,bccRecipients,receivedDateTime,sentDateTime,bodyPreview,body,importance,isRead,isDraft,hasAttachments,conversationId,parentFolderId'
            }
            
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Get emails failed: {response.text}")
                return None
        
        except Exception as e:
            current_app.logger.error(f"Get emails error: {e}")
            return None
    
    def send_email(self, access_token, to_recipients, subject, body, cc_recipients=None, bcc_recipients=None, importance='normal'):
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
            current_app.logger.info(f"Request payload prepared")
            
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
                current_app.logger.info("Response body is empty (normal for successful send)")
            
            # Microsoft Graph sendMail returns 202 Accepted for success
            if response.status_code == 202:
                current_app.logger.info("SUCCESS: Microsoft Graph accepted the email for sending")
                return True
            else:
                current_app.logger.error(f"FAILED: Microsoft Graph rejected the email: {response.status_code}")
                current_app.logger.error(f"Error details: {response.text}")
                return False
        
        except requests.exceptions.Timeout:
            current_app.logger.error("FAILED: Request timeout")
            return False
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"FAILED: Request error: {e}")
            return False
        except Exception as e:
            current_app.logger.error(f"FAILED: Send email error: {e}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
        finally:
            current_app.logger.info("=== GRAPH SERVICE DEBUG END ===")
    
    def get_email_by_id(self, access_token, message_id):
        """Get specific email by ID"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.graph_endpoint}/me/messages/{message_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Get email by ID failed: {response.text}")
                return None
        
        except Exception as e:
            current_app.logger.error(f"Get email by ID error: {e}")
            return None
    
    def reply_to_email(self, access_token, message_id, reply_body, reply_all=False):
        """Reply to an email"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'comment': reply_body
            }
            
            endpoint = 'replyAll' if reply_all else 'reply'
            
            response = requests.post(
                f"{self.graph_endpoint}/me/messages/{message_id}/{endpoint}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            return response.status_code == 202
        
        except Exception as e:
            current_app.logger.error(f"Reply to email error: {e}")
            return False
    
    def mark_email_read(self, access_token, message_id, is_read=True):
        """Mark email as read or unread"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'isRead': is_read
            }
            
            response = requests.patch(
                f"{self.graph_endpoint}/me/messages/{message_id}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            return response.status_code == 200
        
        except Exception as e:
            current_app.logger.error(f"Mark email read error: {e}")
            return False
    
    def get_mail_folders(self, access_token):
        """Get list of mail folders"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.graph_endpoint}/me/mailFolders",
                headers=headers,
                params={'$select': 'id,displayName,parentFolderId,childFolderCount,unreadItemCount,totalItemCount'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('value', [])
            else:
                current_app.logger.error(f"Get mail folders failed: {response.text}")
                return None
        
        except Exception as e:
            current_app.logger.error(f"Get mail folders error: {e}")
            return None
    
    def search_emails(self, access_token, search_query, limit=50):
        """Search emails using Graph API"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                '$search': f'"{search_query}"',
                '$top': min(limit, 1000),
                '$orderby': 'receivedDateTime desc',
                '$select': 'id,subject,sender,toRecipients,receivedDateTime,bodyPreview,importance,isRead,conversationId'
            }
            
            response = requests.get(
                f"{self.graph_endpoint}/me/messages",
                headers=headers,
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Search emails failed: {response.text}")
                return None
        
        except Exception as e:
            current_app.logger.error(f"Search emails error: {e}")
            return None
'''
    
    return clean_graph_service

def backup_and_replace_graph_service():
    """Backup current service and replace with clean version"""
    print("\n🔧 Replacing Graph Service")
    print("=" * 25)
    
    graph_file = 'app/services/ms_graph.py'
    backup_file = 'app/services/ms_graph_backup.py'
    
    try:
        # Backup current file
        with open(graph_file, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(current_content)
        
        print("✅ Backed up current graph service")
        
        # Replace with clean version
        clean_service = create_clean_graph_service()
        
        with open(graph_file, 'w', encoding='utf-8') as f:
            f.write(clean_service)
        
        print("✅ Replaced with clean graph service")
        return True
        
    except Exception as e:
        print(f"❌ Error replacing graph service: {e}")
        return False

def create_simple_email_test():
    """Create a simple email test to verify the fix"""
    print("\n🧪 Creating Simple Email Test")
    print("=" * 28)
    
    test_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Email Send Test - Fixed</title>
    <style>
        body { 
            font-family: Arial; 
            max-width: 500px; 
            margin: 50px auto; 
            padding: 20px; 
            background: #f8f9fa;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #28a745; text-align: center; }
        input, textarea { 
            width: 100%; 
            padding: 10px; 
            margin: 10px 0; 
            border: 1px solid #ddd; 
            border-radius: 4px;
            box-sizing: border-box;
        }
        button { 
            background: #28a745; 
            color: white; 
            padding: 15px 30px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            width: 100%;
            font-size: 16px;
        }
        button:hover { background: #218838; }
        .result { 
            margin-top: 20px; 
            padding: 15px; 
            border-radius: 4px; 
        }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #e7f3ff; color: #0c5460; margin-bottom: 20px; padding: 15px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Email Test - Syntax Fixed</h1>
        
        <div class="info">
            <strong>Fixed Microsoft Graph Service</strong><br>
            The syntax error has been fixed. This should now send real emails.
        </div>
        
        <form id="testForm">
            <input type="email" id="to" placeholder="To: recipient@example.com" required>
            <input type="text" id="subject" placeholder="Subject" required>
            <textarea id="body" placeholder="Message" required rows="4"></textarea>
            <button type="submit" id="sendBtn">📧 Send Real Email</button>
        </form>
        
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('testForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const sendBtn = document.getElementById('sendBtn');
            const resultDiv = document.getElementById('result');
            
            sendBtn.disabled = true;
            sendBtn.textContent = '📤 Sending...';
            resultDiv.innerHTML = '<div class="result">⏳ Sending email via Microsoft Graph...</div>';
            
            const data = {
                to: document.getElementById('to').value,
                subject: document.getElementById('subject').value,
                body: document.getElementById('body').value
            };
            
            console.log('Sending:', data);
            
            fetch('/api/email/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                console.log('Status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Response:', data);
                if (data.success) {
                    resultDiv.innerHTML = `
                        <div class="result success">
                            ✅ <strong>Email Sent!</strong><br>
                            📧 To: ${data.details.to}<br>
                            📝 Subject: "${data.details.subject}"<br>
                            📨 From: ${data.details.from}<br>
                            ⏰ ${new Date(data.details.sent_at).toLocaleString()}
                        </div>
                    `;
                    
                    // Clear form
                    document.getElementById('testForm').reset();
                } else {
                    resultDiv.innerHTML = `
                        <div class="result error">
                            ❌ <strong>Send Failed:</strong> ${data.error}
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                resultDiv.innerHTML = `
                    <div class="result error">
                        ❌ <strong>Error:</strong> ${error.message}
                    </div>
                `;
            })
            .finally(() => {
                sendBtn.disabled = false;
                sendBtn.textContent = '📧 Send Real Email';
            });
        });
    </script>
</body>
</html>'''
    
    with open('email_test_fixed.html', 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print("✅ Created email_test_fixed.html")

def main():
    """Main function"""
    print("🔧 Fix Microsoft Graph Service Syntax Error")
    print("=" * 41)
    print("🐛 Syntax error on line 279 of ms_graph.py")
    print("Creating clean, working version...")
    print()
    
    # Replace graph service
    service_replaced = backup_and_replace_graph_service()
    
    # Create test page
    create_simple_email_test()
    
    if service_replaced:
        print(f"\n🎉 SYNTAX ERROR FIXED!")
        print(f"=" * 21)
        print(f"🚀 Restart your app:")
        print(f"   python docker_run.py")
        
        print(f"\n✅ What was fixed:")
        print(f"   - Clean Microsoft Graph service (no syntax errors)")
        print(f"   - Detailed debug logging for email sending")
        print(f"   - Proper error handling")
        print(f"   - HTTP 202 status check (correct for sendMail)")
        
        print(f"\n🧪 Test the fix:")
        print(f"   1. Open email_test_fixed.html")
        print(f"   2. Send a test email")
        print(f"   3. Check console logs for detailed Microsoft Graph interaction")
        print(f"   4. Look for 'HTTP 202 Accepted' in logs")
        
        print(f"\n🔍 Debug output will show:")
        print(f"   - Request URL and payload")
        print(f"   - Microsoft Graph response status")
        print(f"   - Success/failure reasons")
        print(f"   - Any error messages from Microsoft")
        
        print(f"\n🎯 Expected: HTTP 202 = Email successfully sent")
        print(f"If you see 202 but no email, check spam folder or Microsoft 365 security settings")
        
    else:
        print(f"\n❌ Could not fix syntax error")

if __name__ == "__main__":
    main()