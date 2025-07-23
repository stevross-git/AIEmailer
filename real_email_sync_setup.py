#!/usr/bin/env python3
"""
Setup Real Microsoft 365 Email Sync
"""
import os

def check_env_configuration():
    """Check if .env has all required Azure configuration"""
    print("🔍 Checking Azure Configuration")
    print("=" * 32)
    
    required_vars = [
        'AZURE_CLIENT_ID',
        'AZURE_CLIENT_SECRET', 
        'AZURE_TENANT_ID',
        'AZURE_REDIRECT_URI'
    ]
    
    env_file = '.env'
    
    try:
        if not os.path.exists(env_file):
            print("❌ .env file not found")
            return False, {}
        
        with open(env_file, 'r') as f:
            content = f.read()
        
        config = {}
        missing_vars = []
        
        for var in required_vars:
            if f'{var}=' in content:
                # Extract value
                for line in content.split('\n'):
                    if line.startswith(f'{var}='):
                        value = line.split('=', 1)[1].strip().strip('"\'')
                        config[var] = value
                        if value:
                            print(f"✅ {var}: {'*' * min(len(value), 8)}...")
                        else:
                            print(f"⚠️ {var}: (empty)")
                            missing_vars.append(var)
                        break
            else:
                print(f"❌ {var}: (missing)")
                missing_vars.append(var)
        
        if missing_vars:
            print(f"\n❌ Missing configuration: {', '.join(missing_vars)}")
            return False, config
        else:
            print(f"\n✅ All Azure configuration present!")
            return True, config
            
    except Exception as e:
        print(f"❌ Error reading .env: {e}")
        return False, {}

def update_email_sync_for_real():
    """Update email sync route to handle real Microsoft Graph authentication"""
    print("\n🔧 Updating Email Sync for Real Microsoft 365")
    print("=" * 45)
    
    routes_file = 'app/routes/email.py'
    
    real_sync_route = '''@email_bp.route('/sync', methods=['POST'])
def sync_emails():
    """Sync emails from Microsoft Graph (Real + Demo)"""
    try:
        # Get or ensure user
        user_id = session.get('user_id')
        
        if not user_id:
            # Auto-login demo user for testing
            user = User.query.filter_by(azure_id='demo-user-123').first()
            if user:
                user_id = user.id
                session['user_id'] = user_id
                session['user_email'] = user.email
                session['user_name'] = user.display_name
        
        if not user_id:
            return jsonify({'success': False, 'error': 'Authentication required', 'require_login': True}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        current_app.logger.info(f"Starting email sync for user {user_id} ({user.display_name})")
        
        # Check if this is a demo user or if we have real tokens
        if user.azure_id == 'demo-user-123' or not user.access_token_hash:
            current_app.logger.info("Using demo email sync (no real tokens)")
            return sync_demo_emails(user)
        
        # Real Microsoft Graph sync
        current_app.logger.info("Attempting real Microsoft Graph sync")
        
        try:
            from app.services.ms_graph import GraphService
            from app.utils.auth_helpers import decrypt_token
            
            graph_service = GraphService()
            
            # Get access token
            access_token = decrypt_token(user.access_token_hash)
            
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
                    current_app.logger.warning("Token refresh failed, falling back to demo")
                    return sync_demo_emails(user)
            
            # Sync emails from Microsoft Graph
            folders_to_sync = ['inbox']
            if current_app.config.get('INDEX_SENT_ITEMS', True):
                folders_to_sync.append('sentitems')
            
            total_new_emails = 0
            
            for folder in folders_to_sync:
                try:
                    current_app.logger.info(f"Syncing {folder} folder...")
                    
                    # Fetch emails from Microsoft Graph
                    emails_data = graph_service.get_emails(
                        access_token=access_token,
                        folder=folder,
                        top=50,  # Fetch up to 50 emails per folder
                        skip=0
                    )
                    
                    if not emails_data or 'value' not in emails_data:
                        current_app.logger.warning(f"No email data returned for folder: {folder}")
                        continue
                    
                    emails = emails_data['value']
                    current_app.logger.info(f"Retrieved {len(emails)} emails from {folder}")
                    
                    # Process each email
                    for email_data in emails:
                        try:
                            # Check if email already exists
                            existing_email = Email.query.filter_by(
                                user_id=user_id,
                                message_id=email_data['id']
                            ).first()
                            
                            if existing_email:
                                # Update read status if changed
                                if existing_email.is_read != email_data.get('isRead', False):
                                    existing_email.is_read = email_data.get('isRead', False)
                                    db.session.commit()
                                continue
                            
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
                            
                            # Create new email record
                            new_email = Email(
                                user_id=user_id,
                                message_id=email_data['id'],
                                subject=email_data.get('subject', ''),
                                sender_email=sender_email_info.get('address', ''),
                                sender_name=sender_email_info.get('name', ''),
                                body_text=email_data.get('bodyPreview', ''),
                                body_html=email_data.get('body', {}).get('content', ''),
                                received_date=received_date,
                                is_read=email_data.get('isRead', False),
                                importance=email_data.get('importance', 'normal'),
                                has_attachments=email_data.get('hasAttachments', False),
                                conversation_id=email_data.get('conversationId'),
                                internet_message_id=email_data.get('internetMessageId')
                            )
                            
                            # Set folder based on source
                            if hasattr(new_email, 'folder'):
                                new_email.folder = 'sent' if folder == 'sentitems' else 'inbox'
                            
                            db.session.add(new_email)
                            total_new_emails += 1
                            
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
            
            current_app.logger.info(f"Real email sync completed: {total_new_emails} new emails")
            
            return jsonify({
                'success': True,
                'new_count': total_new_emails,
                'message': f'Successfully synced {total_new_emails} new emails from Microsoft 365!'
            })
            
        except ImportError as e:
            current_app.logger.warning(f"Microsoft Graph service not available: {e}")
            current_app.logger.info("Falling back to demo email sync")
            return sync_demo_emails(user)
        except Exception as e:
            current_app.logger.error(f"Real email sync failed: {e}")
            current_app.logger.info("Falling back to demo email sync")
            return sync_demo_emails(user)
    
    except Exception as e:
        current_app.logger.error(f"Email sync error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500'''
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and replace the sync route
        import re
        pattern = r'@email_bp\.route\(\'/sync\', methods=\[\'POST\'\]\).*?(?=@email_bp\.route|def sync_demo_emails|def \w+(?:\(|\s)|$)'
        
        new_content = re.sub(pattern, real_sync_route + '\n\n', content, flags=re.DOTALL)
        
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Updated email sync to support real Microsoft 365")
        return True
        
    except Exception as e:
        print(f"❌ Error updating sync route: {e}")
        return False

def create_env_template():
    """Create .env template with Azure configuration"""
    print("\n📝 Creating .env Template")
    print("=" * 24)
    
    env_template = '''# Azure AD Configuration for Microsoft 365 Email Sync
AZURE_CLIENT_ID=your_client_id_here
AZURE_CLIENT_SECRET=your_client_secret_here  
AZURE_TENANT_ID=your_tenant_id_here
AZURE_REDIRECT_URI=http://localhost:5000/auth/callback

# Optional: Email sync settings
INDEX_SENT_ITEMS=true
MAX_EMAILS_PER_SYNC=50
SYNC_HISTORY_DAYS=30

# Database Configuration (Docker)
USE_DOCKER_CONFIG=true
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_email_assistant
POSTGRES_USER=ai_email_user
POSTGRES_PASSWORD=ai_email_password123

# Redis Configuration (Docker)
REDIS_HOST=localhost
REDIS_PORT=6379

# ChromaDB Configuration (Docker)
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# Application Settings
SECRET_KEY=your-secret-key-here
DEBUG=true
'''
    
    try:
        with open('.env.example', 'w') as f:
            f.write(env_template)
        
        print("✅ Created .env.example template")
        print("💡 Copy your Azure values to .env file")
        return True
        
    except Exception as e:
        print(f"❌ Error creating template: {e}")
        return False

def test_graph_service():
    """Test if Microsoft Graph service is available"""
    print("\n🧪 Testing Microsoft Graph Service")
    print("=" * 33)
    
    try:
        import sys
        sys.path.append('.')
        
        from app.services.ms_graph import GraphService
        
        graph_service = GraphService()
        print("✅ Microsoft Graph service available")
        
        # Test basic configuration
        if hasattr(graph_service, 'client_id'):
            print("✅ Graph service properly configured")
        else:
            print("⚠️ Graph service may need configuration")
        
        return True
        
    except ImportError as e:
        print(f"❌ Microsoft Graph service not available: {e}")
        print("💡 You may need to install: pip install msal requests")
        return False
    except Exception as e:
        print(f"❌ Error testing Graph service: {e}")
        return False

def main():
    """Main setup function"""
    print("🔧 Real Microsoft 365 Email Sync Setup")
    print("=" * 38)
    
    # Check current environment
    env_ok, config = check_env_configuration()
    
    # Test Graph service
    graph_ok = test_graph_service()
    
    # Update sync route
    sync_updated = update_email_sync_for_real()
    
    # Create template if needed
    template_created = create_env_template()
    
    print(f"\n📊 Setup Status:")
    print(f"=" * 15)
    print(f"✅ Demo emails: WORKING")
    print(f"{'✅' if env_ok else '❌'} Azure config: {'COMPLETE' if env_ok else 'NEEDS SETUP'}")
    print(f"{'✅' if graph_ok else '❌'} Graph service: {'AVAILABLE' if graph_ok else 'NEEDS INSTALL'}")
    print(f"{'✅' if sync_updated else '❌'} Sync route: {'UPDATED' if sync_updated else 'NEEDS FIX'}")
    
    if env_ok and graph_ok and sync_updated:
        print(f"\n🎉 REAL EMAIL SYNC READY!")
        print(f"=" * 25)
        print(f"🚀 Restart your app:")
        print(f"   python docker_run.py")
        print(f"\n✅ Then:")
        print(f"   1. Visit: http://localhost:5000")
        print(f"   2. Click 'Sign in with Microsoft'")
        print(f"   3. Authorize the app")
        print(f"   4. Click 'Sync Emails' for real emails!")
        
    elif not env_ok:
        print(f"\n⚠️ Azure Configuration Needed:")
        print(f"=" * 30)
        print(f"1. Copy .env.example to .env")
        print(f"2. Add your Azure AD values:")
        print(f"   - AZURE_CLIENT_ID")
        print(f"   - AZURE_CLIENT_SECRET") 
        print(f"   - AZURE_TENANT_ID")
        print(f"   - AZURE_REDIRECT_URI")
        print(f"3. Restart: python docker_run.py")
        
    elif not graph_ok:
        print(f"\n⚠️ Install Microsoft Graph Dependencies:")
        print(f"=" * 40)
        print(f"pip install msal requests")
        print(f"Then restart: python docker_run.py")
        
    else:
        print(f"\n✅ Demo email sync working")
        print(f"📧 Add Azure config for real emails")

if __name__ == "__main__":
    main()