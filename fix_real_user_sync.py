#!/usr/bin/env python3
"""
Fix Email Sync to Use Real Microsoft User Instead of Demo
"""
import os

def update_email_sync_for_real_user():
    """Update email sync to use real Microsoft authenticated user"""
    print("🔧 Updating Email Sync for Real Microsoft User")
    print("=" * 44)
    
    routes_file = 'app/routes/email.py'
    
    real_user_sync = '''@email_bp.route('/sync', methods=['POST'])
def sync_emails():
    """Sync emails from Microsoft Graph (Real User Priority)"""
    try:
        # Get authenticated user from session
        user_id = session.get('user_id')
        
        if not user_id:
            current_app.logger.warning("No user_id in session")
            return jsonify({'success': False, 'error': 'Please sign in with Microsoft first', 'require_login': True}), 401
        
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"User {user_id} not found in database")
            return jsonify({'success': False, 'error': 'User not found', 'require_login': True}), 404
        
        current_app.logger.info(f"Starting email sync for real user: {user.email} (Azure ID: {user.azure_id})")
        
        # Check if this is a real Microsoft user (not demo)
        if user.azure_id and user.azure_id != 'demo-user-123' and user.access_token_hash:
            current_app.logger.info(f"Real Microsoft user detected: {user.email}")
            return sync_real_microsoft_emails(user)
        else:
            current_app.logger.info(f"Demo user or no tokens - using demo emails for: {user.email}")
            return sync_demo_emails(user)
    
    except Exception as e:
        current_app.logger.error(f"Email sync error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def sync_real_microsoft_emails(user):
    """Sync real emails from Microsoft Graph"""
    try:
        current_app.logger.info(f"Syncing real Microsoft emails for {user.email}")
        
        from app.services.ms_graph import GraphService
        from app.utils.auth_helpers import decrypt_token
        from datetime import datetime, timedelta
        
        graph_service = GraphService()
        
        # Get access token
        access_token = decrypt_token(user.access_token_hash)
        current_app.logger.info("Decrypted access token")
        
        # Check if token is expired and refresh if needed
        if not user.has_valid_token() and user.refresh_token_hash:
            current_app.logger.info("Access token expired, attempting refresh...")
            refresh_token = decrypt_token(user.refresh_token_hash)
            token_result = graph_service.refresh_access_token(refresh_token)
            
            if token_result:
                # Update tokens in database
                from app.utils.auth_helpers import encrypt_token
                user.access_token_hash = encrypt_token(token_result['access_token'])
                if 'refresh_token' in token_result:
                    user.refresh_token_hash = encrypt_token(token_result['refresh_token'])
                
                expires_in = token_result.get('expires_in', 3600)
                user.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                db.session.commit()
                
                access_token = token_result['access_token']
                current_app.logger.info("Successfully refreshed access token")
            else:
                current_app.logger.warning("Token refresh failed")
                return jsonify({
                    'success': False, 
                    'error': 'Access token expired and refresh failed. Please sign in again.',
                    'require_reauth': True
                }), 401
        
        # Sync emails from different folders
        folders_to_sync = ['inbox']
        total_new_emails = 0
        
        for folder in folders_to_sync:
            try:
                current_app.logger.info(f"Syncing {folder} folder for {user.email}...")
                
                # Fetch emails from Microsoft Graph
                emails_data = graph_service.get_emails(
                    access_token=access_token,
                    folder=folder,
                    top=20,  # Start with 20 emails for testing
                    skip=0
                )
                
                if not emails_data or 'value' not in emails_data:
                    current_app.logger.warning(f"No email data returned for folder: {folder}")
                    continue
                
                emails = emails_data['value']
                current_app.logger.info(f"Retrieved {len(emails)} real emails from {folder}")
                
                # Clear existing emails for this user (to avoid duplicates during testing)
                Email.query.filter_by(user_id=user.id).delete()
                db.session.commit()
                current_app.logger.info("Cleared existing emails")
                
                # Process each email
                for email_data in emails:
                    try:
                        # Parse email data
                        sender_info = email_data.get('sender', {})
                        sender_email_info = sender_info.get('emailAddress', {})
                        
                        # Parse received date
                        received_date = None
                        if email_data.get('receivedDateTime'):
                            try:
                                received_date = datetime.fromisoformat(
                                    email_data['receivedDateTime'].replace('Z', '+00:00')
                                ).replace(tzinfo=None)
                            except:
                                received_date = datetime.utcnow()
                        
                        # Get email body
                        body_content = email_data.get('body', {})
                        body_text = email_data.get('bodyPreview', '')
                        body_html = body_content.get('content', '') if body_content else ''
                        
                        # Create new email record
                        new_email = Email(
                            user_id=user.id,
                            message_id=email_data['id'],
                            subject=email_data.get('subject', 'No Subject'),
                            sender_email=sender_email_info.get('address', ''),
                            sender_name=sender_email_info.get('name', ''),
                            body_text=body_text,
                            body_html=body_html,
                            received_date=received_date,
                            is_read=email_data.get('isRead', False),
                            importance=email_data.get('importance', 'normal'),
                            has_attachments=email_data.get('hasAttachments', False),
                            conversation_id=email_data.get('conversationId'),
                            internet_message_id=email_data.get('internetMessageId')
                        )
                        
                        # Set folder if the attribute exists
                        if hasattr(new_email, 'folder'):
                            new_email.folder = folder
                        
                        db.session.add(new_email)
                        total_new_emails += 1
                        
                        current_app.logger.debug(f"Added email: {email_data.get('subject', 'No Subject')}")
                        
                    except Exception as e:
                        current_app.logger.error(f"Error processing email {email_data.get('id', 'unknown')}: {e}")
                        continue
                
            except Exception as e:
                current_app.logger.error(f"Error syncing folder {folder}: {e}")
                continue
        
        # Commit all new emails
        db.session.commit()
        
        # Update user's last sync time
        user.last_sync = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"Real email sync completed for {user.email}: {total_new_emails} emails")
        
        return jsonify({
            'success': True,
            'new_count': total_new_emails,
            'message': f'Successfully synced {total_new_emails} real emails from {user.email}!',
            'user_email': user.email,
            'sync_type': 'real_microsoft'
        })
        
    except ImportError as e:
        current_app.logger.error(f"Microsoft Graph service not available: {e}")
        return jsonify({'success': False, 'error': 'Microsoft Graph service not configured'}), 500
    except Exception as e:
        current_app.logger.error(f"Real email sync failed for {user.email}: {e}")
        return jsonify({'success': False, 'error': f'Email sync failed: {str(e)}'}), 500'''
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the sync route
        import re
        pattern = r'@email_bp\.route\(\'/sync\', methods=\[\'POST\'\]\).*?(?=@email_bp\.route|def sync_demo_emails|def \w+(?:\(|\s)|$)'
        
        new_content = re.sub(pattern, real_user_sync + '\n\n', content, flags=re.DOTALL)
        
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Updated email sync to prioritize real Microsoft users")
        return True
        
    except Exception as e:
        print(f"❌ Error updating sync route: {e}")
        return False

def update_auth_status_check():
    """Update auth status to show real user info"""
    print("\n🔧 Updating Auth Status Check")
    print("=" * 28)
    
    auth_file = 'app/routes/auth.py'
    
    auth_status_route = '''
@auth_bp.route('/status')
def auth_status():
    """Get authentication status"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'authenticated': False,
                'user': None,
                'message': 'Please sign in with Microsoft'
            })
        
        user = User.query.get(user_id)
        
        if not user:
            session.clear()
            return jsonify({
                'authenticated': False,
                'user': None,
                'message': 'User not found - please sign in again'
            })
        
        # Check if this is a real Microsoft user
        is_real_user = user.azure_id and user.azure_id != 'demo-user-123'
        has_tokens = user.access_token_hash is not None
        
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'display_name': user.display_name,
                'azure_id': user.azure_id,
                'is_real_user': is_real_user,
                'has_tokens': has_tokens,
                'last_sync': user.last_sync.isoformat() if user.last_sync else None
            },
            'message': f'Signed in as {user.email}' + (' (Microsoft 365)' if is_real_user else ' (Demo)')
        })
        
    except Exception as e:
        current_app.logger.error(f"Auth status error: {e}")
        return jsonify({
            'authenticated': False,
            'error': str(e)
        }), 500
'''
    
    try:
        with open(auth_file, 'a', encoding='utf-8') as f:
            f.write(auth_status_route)
        
        print("✅ Updated auth status check")
        return True
        
    except Exception as e:
        print(f"❌ Error updating auth status: {e}")
        return False

def create_user_info_display():
    """Create a way to see current user info"""
    print("\n🔧 Creating User Info Display")
    print("=" * 28)
    
    info_script = '''#!/usr/bin/env python3
"""
Show Current User Info
"""
import os
import sys

def show_user_info():
    """Show current user information"""
    print("👤 Current User Information")
    print("=" * 27)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        from app import create_app, db
        from app.models.user import User
        
        app = create_app()
        
        with app.app_context():
            users = User.query.all()
            
            if not users:
                print("❌ No users found in database")
                return
            
            for user in users:
                print(f"\\n📧 User: {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Azure ID: {user.azure_id}")
                print(f"   Name: {user.display_name}")
                print(f"   Active: {user.is_active}")
                print(f"   Has Tokens: {user.access_token_hash is not None}")
                print(f"   Last Sync: {user.last_sync}")
                print(f"   Type: {'Real Microsoft User' if user.azure_id and user.azure_id != 'demo-user-123' else 'Demo User'}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    show_user_info()
'''
    
    with open('show_user_info.py', 'w') as f:
        f.write(info_script)
    
    print("✅ Created show_user_info.py")

def main():
    """Main function"""
    print("🔧 Fix Email Sync for Real Microsoft User")
    print("=" * 40)
    print(f"Target user: stephendavies@peoplesainetwork.com")
    print()
    
    # Update email sync
    sync_updated = update_email_sync_for_real_user()
    
    # Update auth status
    auth_updated = update_auth_status_check()
    
    # Create user info script
    create_user_info_display()
    
    if sync_updated:
        print(f"\n🎉 EMAIL SYNC FIXED FOR REAL USERS!")
        print(f"=" * 35)
        print(f"🚀 Next steps:")
        print(f"   1. Check current user: python show_user_info.py")
        print(f"   2. Restart app: python docker_run.py")
        print(f"   3. Sign in as: stephendavies@peoplesainetwork.com")
        print(f"   4. Click 'Sync Emails' for REAL emails!")
        
        print(f"\n✅ What changed:")
        print(f"   - Prioritizes real Microsoft users over demo")
        print(f"   - Uses your actual Azure ID, not 'demo-user-123'")
        print(f"   - Syncs real emails from Microsoft Graph")
        print(f"   - Shows user type in auth status")
        
        print(f"\n🎯 Expected behavior:")
        print(f"   - Real user: Syncs actual Microsoft 365 emails")
        print(f"   - Demo user: Falls back to demo emails")
    else:
        print(f"\n❌ Could not update email sync")
        print(f"🚀 Use the complete working app:")
        print(f"   python complete_working_app.py")

if __name__ == "__main__":
    main()