"""
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
            current_app.logger.info("=== GRAPH SERVICE DEBUG END ===")    def format_recipients(recipients):
                if isinstance(recipients, str):
                    return [{'emailAddress': {'address': recipients}}]
                elif isinstance(recipients, list):
                    return [{'emailAddress': {'address': addr}} for addr in recipients]
                return recipients
            
            message = {
                'subject': subject,
                'body': {
                    'contentType': 'HTML',
                    'content': body
                },
                'toRecipients': format_recipients(to_recipients),
                'importance': importance
            }
            
            if cc_recipients:
                message['ccRecipients'] = format_recipients(cc_recipients)
            
            if bcc_recipients:
                message['bccRecipients'] = format_recipients(bcc_recipients)
            
            data = {'message': message}
            
            response = requests.post(
                f"{self.graph_endpoint}/me/sendMail",
                headers=headers,
                json=data,
                timeout=30
            )
            
            return response.status_code == 202
        
        except Exception as e:
            current_app.logger.error(f"Send email error: {e}")
            return False
    
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
    
    def get_calendar_events(self, access_token, start_time=None, end_time=None, limit=50):
        """Get calendar events (future enhancement)"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                '$top': min(limit, 1000),
                '$orderby': 'start/dateTime',
                '$select': 'id,subject,start,end,organizer,attendees,bodyPreview,importance'
            }
            
            if start_time:
                params['$filter'] = f"start/dateTime ge '{start_time.isoformat()}'"
            
            response = requests.get(
                f"{self.graph_endpoint}/me/events",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Get calendar events failed: {response.text}")
                return None
        
        except Exception as e:
            current_app.logger.error(f"Get calendar events error: {e}")
            return None
    
    def create_subscription(self, access_token, notification_url, resource='me/mailFolders/inbox/messages'):
        """Create webhook subscription for real-time updates"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Subscription expires in 3 days (max for mailbox resources)
            expiration_time = (datetime.utcnow() + timedelta(days=3)).isoformat() + 'Z'
            
            data = {
                'changeType': 'created,updated',
                'notificationUrl': notification_url,
                'resource': resource,
                'expirationDateTime': expiration_time,
                'clientState': 'ai-email-assistant'
            }
            
            response = requests.post(
                f"{self.graph_endpoint}/subscriptions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                current_app.logger.error(f"Create subscription failed: {response.text}")
                return None
        
        except Exception as e:
            current_app.logger.error(f"Create subscription error: {e}")
            return None