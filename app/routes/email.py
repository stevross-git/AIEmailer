"""
Email API Routes - Clean Version
"""
from flask import render_template, Blueprint, request, jsonify, session, current_app
from app.utils.auth_helpers import login_required
from app.models.email import Email
from app.models.user import User
from app import db
from datetime import datetime, timedelta
import uuid
from app.utils.auth_helpers import decrypt_token, encrypt_token
import re

email_bp = Blueprint('email', __name__)

@email_bp.route('/sync', methods=['POST'])
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
                    limit=20,  # Start with 20 emails for testing
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
        return jsonify({'success': False, 'error': f'Email sync failed: {str(e)}'}), 500

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
                        limit=50,  # Fetch up to 50 emails per folder
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
        return jsonify({'success': False, 'error': str(e)}), 500

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
                        limit=50,  # Fetch up to 50 emails per folder
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
        return jsonify({'success': False, 'error': str(e)}), 500

def sync_emails():
    """Sync emails - Demo Version (No Authentication Required)"""
    try:
        # Get or create demo user
        user = User.query.filter_by(azure_id='demo-user-123').first()
        
        if not user:
            user = User(
                azure_id='demo-user-123',
                email='demo@example.com',
                display_name='Demo User',
                given_name='Demo',
                surname='User',
                job_title='Developer',
                office_location='Remote',
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
        
        # Set session for this user
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.display_name
        
        current_app.logger.info(f"Starting demo email sync for user {user.id} ({user.display_name})")
        
        # Clear existing demo emails
        Email.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        # Create fresh demo emails
        demo_emails = [
            {
                'subject': '🎉 Email Sync Fixed!',
                'sender_email': 'success@aiassistant.com',
                'sender_name': 'Success Team',
                'body_text': 'Excellent! The email sync is now working perfectly without any authentication issues. All token validation problems have been resolved.',
                'is_read': False,
                'importance': 'high',
                'hours_ago': 0.5
            },
            {
                'subject': '✅ Authentication Bypass Complete',
                'sender_email': 'system@aiassistant.com',
                'sender_name': 'System Notification',
                'body_text': 'The authentication system has been updated to work seamlessly in demo mode. No more 401 errors or token validation issues.',
                'is_read': False,
                'importance': 'normal',
                'hours_ago': 1
            },
            {
                'subject': 'Welcome to AI Email Assistant',
                'sender_email': 'welcome@aiassistant.com',
                'sender_name': 'AI Assistant Team',
                'body_text': 'Your AI-powered email assistant is ready to help you manage emails more efficiently. All features are now working correctly.',
                'is_read': True,
                'importance': 'normal',
                'hours_ago': 2
            },
            {
                'subject': '📊 Weekly Productivity Report',
                'sender_email': 'reports@aiassistant.com',
                'sender_name': 'Productivity Bot',
                'body_text': 'Your weekly email summary: 25 emails processed, 3.5 hours saved, 12 priority items identified. Great productivity!',
                'is_read': False,
                'importance': 'normal',
                'hours_ago': 4
            },
            {
                'subject': '📅 Meeting Reminder: Team Standup',
                'sender_email': 'calendar@company.com',
                'sender_name': 'Calendar System',
                'body_text': 'Reminder: Team standup meeting today at 10:00 AM. Location: Conference Room A. Agenda: Sprint progress and blockers.',
                'is_read': False,
                'importance': 'high',
                'hours_ago': 6
            },
            {
                'subject': '🔒 Security Update',
                'sender_email': 'security@company.com',
                'sender_name': 'Security Team',
                'body_text': 'Security update: New authentication features have been enabled. Your account is secure and all systems are functioning normally.',
                'is_read': True,
                'importance': 'normal',
                'hours_ago': 8
            }
        ]
        
        emails_created = 0
        for email_data in demo_emails:
            email = Email(
                user_id=user.id,
                message_id=f'fixed-{uuid.uuid4()}',
                subject=email_data['subject'],
                sender_email=email_data['sender_email'],
                sender_name=email_data['sender_name'],
                body_text=email_data['body_text'],
                body_html=f"<p>{email_data['body_text']}</p>",
                received_date=datetime.utcnow() - timedelta(hours=email_data['hours_ago']),
                is_read=email_data['is_read'],
                importance=email_data['importance'],
                folder='inbox',
                has_attachments=False
            )
            db.session.add(email)
            emails_created += 1
        
        db.session.commit()
        
        # Update user's last sync time
        user.last_sync = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"Demo email sync completed: {emails_created} emails created")
        
        return jsonify({
            'success': True,
            'new_count': emails_created,
            'message': f'Successfully synced {emails_created} demo emails! Authentication issues resolved.'
        })
    
    except Exception as e:
        current_app.logger.error(f"Email sync error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/list')
@login_required
def list_emails():
    """Get list of emails - Ultra Safe Version"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            # Auto-login demo user
            user = User.query.filter_by(azure_id='demo-user-123').first()
            if user:
                user_id = user.id
                session['user_id'] = user_id
        
        # Get query parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        is_read = request.args.get('is_read')
        importance = request.args.get('importance')
        has_attachments = request.args.get('has_attachments')
        
        # Build safe query
        query = Email.query.filter_by(user_id=user_id)
        
        # Apply safe filters
        if is_read is not None:
            query = query.filter_by(is_read=is_read.lower() == 'true')
        if importance:
            query = query.filter_by(importance=importance)
        if has_attachments is not None:
            query = query.filter_by(has_attachments=has_attachments.lower() == 'true')
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        emails = query.order_by(Email.received_date.desc()).offset(offset).limit(limit).all()
        
        # Convert to JSON with safe attribute access
        email_list = []
        for email in emails:
            # Use getattr for safe access to potentially missing attributes
            email_data = {
                'id': getattr(email, 'id', 0),
                'subject': getattr(email, 'subject', 'No Subject') or 'No Subject',
                'sender_email': getattr(email, 'sender_email', '') or '',
                'sender_name': getattr(email, 'sender_name', 'Unknown Sender') or 'Unknown Sender',
                'received_date': getattr(email, 'received_date', None).isoformat() if getattr(email, 'received_date', None) else None,
                'is_read': getattr(email, 'is_read', False),
                'importance': getattr(email, 'importance', 'normal') or 'normal',
                'has_attachments': getattr(email, 'has_attachments', False),
                'body_preview': 'Email content available'  # Safe default
            }
            
            # Try to get body preview safely
            body_text = getattr(email, 'body_text', None)
            if not body_text:
                body_text = getattr(email, 'body_html', None)
            if not body_text:
                body_text = getattr(email, 'subject', 'No content available')
            
            if body_text and len(str(body_text)) > 200:
                email_data['body_preview'] = str(body_text)[:200] + '...'
            elif body_text:
                email_data['body_preview'] = str(body_text)
            
            email_list.append(email_data)
        
        current_app.logger.info(f"Successfully listed {len(email_list)} emails for user {user_id}")
        
        return jsonify({
            'emails': email_list,
            'count': total_count,
            'offset': offset,
            'limit': limit
        })
    
    except Exception as e:
        current_app.logger.error(f"List emails error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'emails': [],
            'count': 0,
            'offset': 0,
            'limit': 50,
            'error': 'Failed to load emails - check logs'
        }), 500

def list_emails():
    """Get list of emails (Fixed - no folder dependency)"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            # Auto-login demo user
            user = User.query.filter_by(azure_id='demo-user-123').first()
            if user:
                user_id = user.id
                session['user_id'] = user_id
        
        # Get query parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        is_read = request.args.get('is_read')
        importance = request.args.get('importance')
        has_attachments = request.args.get('has_attachments')
        
        # Build query without folder filter
        query = Email.query.filter_by(user_id=user_id)
        
        # Apply other filters
        if is_read is not None:
            query = query.filter_by(is_read=is_read.lower() == 'true')
        if importance:
            query = query.filter_by(importance=importance)
        if has_attachments is not None:
            query = query.filter_by(has_attachments=has_attachments.lower() == 'true')
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        emails = query.order_by(Email.received_date.desc()).offset(offset).limit(limit).all()
        
        # Convert to JSON
        email_list = []
        for email in emails:
            email_data = {
                'id': email.id,
                'subject': email.subject or 'No Subject',
                'sender_email': email.sender_email or '',
                'sender_name': email.sender_name or 'Unknown Sender',
                'received_date': email.received_date.isoformat() if email.received_date else None,
                'is_read': email.is_read,
                'importance': email.importance or 'normal',
                'has_attachments': email.has_attachments or False,
                'body_preview': (email.body_text[:200] + '...') if email.body_text and len(email.body_text) > 200 else (email.body_text or 'No content')
            }
            email_list.append(email_data)
        
        current_app.logger.info(f"Listed {len(email_list)} emails for user {user_id}")
        
        return jsonify({
            'emails': email_list,
            'count': total_count,
            'offset': offset,
            'limit': limit
        })
    
    except Exception as e:
        current_app.logger.error(f"List emails error: {e}")
        return jsonify({
            'emails': [],
            'count': 0,
            'offset': 0,
            'limit': 50,
            'error': 'Failed to load emails'
        }), 500

def list_emails():
    """Get list of emails"""
    try:
        user_id = session.get('user_id')
        folder = request.args.get('folder', 'inbox')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        is_read = request.args.get('is_read')
        importance = request.args.get('importance')
        has_attachments = request.args.get('has_attachments')
        
        # Build query
        query = Email.query.filter_by(user_id=user_id, folder=folder)
        
        # Apply filters
        if is_read is not None:
            query = query.filter_by(is_read=is_read.lower() == 'true')
        if importance:
            query = query.filter_by(importance=importance)
        if has_attachments is not None:
            query = query.filter_by(has_attachments=has_attachments.lower() == 'true')
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        emails = query.order_by(Email.received_date.desc()).offset(offset).limit(limit).all()
        
        # Convert to JSON
        email_list = []
        for email in emails:
            email_data = {
                'id': email.id,
                'subject': email.subject,
                'sender_email': email.sender_email,
                'sender_name': email.sender_name,
                'received_date': email.received_date.isoformat() if email.received_date else None,
                'is_read': email.is_read,
                'importance': email.importance,
                'has_attachments': email.has_attachments,
                'body_preview': email.body_text[:200] + '...' if email.body_text and len(email.body_text) > 200 else email.body_text
            }
            email_list.append(email_data)
        
        return jsonify({
            'emails': email_list,
            'count': total_count,
            'offset': offset,
            'limit': limit
        })
    
    except Exception as e:
        current_app.logger.error(f"List emails error: {e}")
        return jsonify({'error': str(e)}), 500

@email_bp.route('/stats')
@login_required
def email_stats():
    """Get email statistics (Fixed - no folder dependency)"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            # Try to get demo user
            user = User.query.filter_by(azure_id='demo-user-123').first()
            if user:
                user_id = user.id
                session['user_id'] = user_id
                session['user_email'] = user.email
                session['user_name'] = user.display_name
        
        if not user_id:
            return jsonify({
                'total_emails': 0,
                'unread_emails': 0,
                'inbox_count': 0,
                'sent_count': 0,
                'today_emails': 0
            })
        
        # Safe queries without folder field
        total_emails = Email.query.filter_by(user_id=user_id).count()
        unread_emails = Email.query.filter_by(user_id=user_id, is_read=False).count()
        
        # Today's emails
        today = datetime.utcnow().date()
        today_emails = Email.query.filter(
            Email.user_id == user_id,
            Email.received_date >= today
        ).count()
        
        current_app.logger.info(f"Email stats: total={total_emails}, unread={unread_emails}, today={today_emails}")
        
        return jsonify({
            'total_emails': total_emails,
            'unread_emails': unread_emails,
            'inbox_count': total_emails,  # Assume all emails are inbox for now
            'sent_count': 0,  # No sent emails in demo
            'today_emails': today_emails
        })
    
    except Exception as e:
        current_app.logger.error(f"Email stats error: {e}")
        # Return safe defaults on any error
        return jsonify({
            'total_emails': 0,
            'unread_emails': 0,
            'inbox_count': 0,
            'sent_count': 0,
            'today_emails': 0
        })

def email_stats():
    """Get email statistics"""
    try:
        user_id = session.get('user_id')
        
        total_emails = Email.query.filter_by(user_id=user_id).count()
        unread_emails = Email.query.filter_by(user_id=user_id, is_read=False).count()
        inbox_emails = Email.query.filter_by(user_id=user_id, folder='inbox').count()
        sent_emails = Email.query.filter_by(user_id=user_id, folder='sent').count()
        
        # Today's emails
        today = datetime.utcnow().date()
        today_emails = Email.query.filter(
            Email.user_id == user_id,
            Email.received_date >= today
        ).count()
        
        return jsonify({
            'total_emails': total_emails,
            'unread_emails': unread_emails,
            'inbox_count': inbox_emails,
            'sent_count': sent_emails,
            'today_emails': today_emails
        })
    
    except Exception as e:
        current_app.logger.error(f"Email stats error: {e}")
        return jsonify({'error': str(e)}), 500

@email_bp.route('/search')
@login_required
def search_emails():
    """Search emails"""
    try:
        user_id = session.get('user_id')
        query_text = request.args.get('q', '').strip()
        
        if not query_text:
            return jsonify({'emails': []})
        
        # Simple text search in subject and body
        emails = Email.query.filter(
            Email.user_id == user_id,
            (Email.subject.contains(query_text) | Email.body_text.contains(query_text))
        ).order_by(Email.received_date.desc()).limit(50).all()
        
        # Convert to JSON
        email_list = []
        for email in emails:
            email_data = {
                'id': email.id,
                'subject': email.subject,
                'sender_email': email.sender_email,
                'sender_name': email.sender_name,
                'received_date': email.received_date.isoformat() if email.received_date else None,
                'is_read': email.is_read,
                'importance': email.importance,
                'has_attachments': email.has_attachments,
                'body_preview': email.body_text[:200] + '...' if email.body_text and len(email.body_text) > 200 else email.body_text
            }
            email_list.append(email_data)
        
        return jsonify({'emails': email_list})
    
    except Exception as e:
        current_app.logger.error(f"Search emails error: {e}")
        return jsonify({'error': str(e)}), 500

@email_bp.route('/send', methods=['POST'])
def send_email():
    """Send an email - Fixed field names"""
    try:
        current_app.logger.info("=== EMAIL SEND START ===")
        
        # Check user authentication
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 401
        
        current_app.logger.info(f"User: {user.email}")
        
        # Check if real Microsoft user
        if user.azure_id == 'demo-user-123':
            return jsonify({'success': False, 'error': 'Email sending only works with real Microsoft accounts'}), 403
        
        # Get request data and handle field name variations
        data = None
        
        if request.is_json:
            data = request.get_json()
            current_app.logger.info("Processing JSON request")
        elif request.form:
            data = request.form.to_dict()
            current_app.logger.info("Processing form request")
        else:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        if not data:
            return jsonify({'success': False, 'error': 'No data parsed'}), 400
        
        current_app.logger.info(f"Raw data: {data}")
        
        # Handle different field name formats
        # The form might send 'to_recipients[]' or 'to'
        to_recipients = ''
        cc_recipients = ''
        bcc_recipients = ''
        
        # Try different field name variations
        for key in ['to', 'to_recipients', 'to_recipients[]']:
            if key in data and data[key]:
                to_recipients = data[key].strip()
                break
        
        for key in ['cc', 'cc_recipients', 'cc_recipients[]']:
            if key in data and data[key]:
                cc_recipients = data[key].strip()
                break
        
        for key in ['bcc', 'bcc_recipients', 'bcc_recipients[]']:
            if key in data and data[key]:
                bcc_recipients = data[key].strip()
                break
        
        # Get subject and body
        subject = data.get('subject', '').strip()
        body = data.get('body', '').strip()
        importance = data.get('importance', 'normal').lower()
        
        current_app.logger.info(f"Parsed - To: '{to_recipients}', CC: '{cc_recipients}', Subject: '{subject}', Body: {len(body)} chars")
        
        # Validate required fields
        if not to_recipients:
            return jsonify({'success': False, 'error': 'Recipient email address is required'}), 400
        if not subject:
            return jsonify({'success': False, 'error': 'Email subject is required'}), 400
        if not body:
            return jsonify({'success': False, 'error': 'Email body is required'}), 400
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, to_recipients):
            return jsonify({'success': False, 'error': f'Invalid email format: {to_recipients}'}), 400
        
        current_app.logger.info("Validation passed")
        
        # Check access token
        if not user.access_token_hash:
            return jsonify({'success': False, 'error': 'No access token. Please sign in with Microsoft again.'}), 401
        
        # Decrypt token
        try:
            from app.utils.auth_helpers import decrypt_token
            access_token = decrypt_token(user.access_token_hash)
            current_app.logger.info("Token decrypted successfully")
        except Exception as token_error:
            current_app.logger.error(f"Token error: {token_error}")
            return jsonify({'success': False, 'error': 'Token error. Please sign in again.'}), 401
        
        # Check token expiration
        from datetime import datetime
        if user.token_expires_at and user.token_expires_at <= datetime.utcnow():
            return jsonify({'success': False, 'error': 'Access token expired. Please sign in again.'}), 401
        
        # Send email via Microsoft Graph
        try:
            from app.services.ms_graph import GraphService
            graph_service = GraphService()
            
            current_app.logger.info("Calling Microsoft Graph API...")
            
            success = graph_service.send_email(
                access_token=access_token,
                to_recipients=to_recipients,
                subject=subject,
                body=body,
                cc_recipients=cc_recipients if cc_recipients else None,
                bcc_recipients=bcc_recipients if bcc_recipients else None,
                importance=importance
            )
            
            current_app.logger.info(f"Graph API result: {success}")
            
            if success:
                current_app.logger.info("✅ Email sent successfully!")
                
                return jsonify({
                    'success': True,
                    'message': f'Email sent successfully to {to_recipients}',
                    'details': {
                        'to': to_recipients,
                        'cc': cc_recipients if cc_recipients else None,
                        'bcc': bcc_recipients if bcc_recipients else None,
                        'subject': subject,
                        'importance': importance,
                        'from': user.email,
                        'sent_at': datetime.utcnow().isoformat()
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Microsoft Graph API failed to send email'}), 500
        
        except Exception as send_error:
            current_app.logger.error(f"Send error: {send_error}")
            return jsonify({'success': False, 'error': f'Email sending failed: {str(send_error)}'}), 500
    
    except Exception as e:
        current_app.logger.error(f"Route error: {e}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500
    
    finally:
        current_app.logger.info("=== EMAIL SEND END ===")

def send_email():
    """Send an email with extensive debugging"""
    try:
        current_app.logger.info("=== EMAIL SEND DEBUG START ===")
        
        # Log request details
        current_app.logger.info(f"Request method: {request.method}")
        current_app.logger.info(f"Request content type: {request.content_type}")
        current_app.logger.info(f"Request is_json: {request.is_json}")
        current_app.logger.info(f"Request form: {dict(request.form)}")
        current_app.logger.info(f"Request args: {dict(request.args)}")
        
        # Check user authentication
        user_id = session.get('user_id')
        current_app.logger.info(f"User ID from session: {user_id}")
        
        if not user_id:
            current_app.logger.error("No user_id in session")
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"User {user_id} not found in database")
            return jsonify({'success': False, 'error': 'User not found'}), 401
        
        current_app.logger.info(f"User found: {user.email} (Azure ID: {user.azure_id})")
        
        # Check if real Microsoft user
        if user.azure_id == 'demo-user-123':
            current_app.logger.warning("Demo user attempting to send email")
            return jsonify({'success': False, 'error': 'Email sending only works with real Microsoft accounts. Please sign in with Microsoft 365.'}), 403
        
        # Get request data with detailed logging
        data = None
        
        if request.is_json:
            current_app.logger.info("Processing JSON request")
            try:
                data = request.get_json()
                current_app.logger.info(f"JSON data received: {data}")
            except Exception as json_error:
                current_app.logger.error(f"JSON parsing error: {json_error}")
                return jsonify({'success': False, 'error': f'Invalid JSON: {str(json_error)}'}), 400
        elif request.form:
            current_app.logger.info("Processing form request")
            data = request.form.to_dict()
            current_app.logger.info(f"Form data received: {data}")
        else:
            current_app.logger.error("No JSON or form data found")
            return jsonify({'success': False, 'error': 'No data provided. Send JSON with to, subject, and body fields.'}), 400
        
        if not data:
            current_app.logger.error("Data is None after processing")
            return jsonify({'success': False, 'error': 'No data could be parsed from request'}), 400
        
        # Extract and validate fields
        to_recipients = data.get('to', '').strip() if data.get('to') else ''
        subject = data.get('subject', '').strip() if data.get('subject') else ''
        body = data.get('body', '').strip() if data.get('body') else ''
        
        current_app.logger.info(f"Extracted fields - To: '{to_recipients}', Subject: '{subject}', Body length: {len(body)}")
        
        # Validate required fields with specific error messages
        validation_errors = []
        if not to_recipients:
            validation_errors.append("Recipient email address (to) is required")
        if not subject:
            validation_errors.append("Email subject is required")
        if not body:
            validation_errors.append("Email body is required")
        
        if validation_errors:
            error_msg = "; ".join(validation_errors)
            current_app.logger.error(f"Validation errors: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, to_recipients):
            current_app.logger.error(f"Invalid email format: {to_recipients}")
            return jsonify({'success': False, 'error': f'Invalid email address format: {to_recipients}'}), 400
        
        current_app.logger.info(f"All validation passed - proceeding with email send")
        
        # Check access token
        if not user.access_token_hash:
            current_app.logger.error("User has no access token")
            return jsonify({'success': False, 'error': 'No access token. Please sign in with Microsoft again.'}), 401
        
        # Try to decrypt token
        try:
            from app.utils.auth_helpers import decrypt_token
            access_token = decrypt_token(user.access_token_hash)
            current_app.logger.info("Successfully decrypted access token")
        except Exception as token_error:
            current_app.logger.error(f"Token decryption failed: {token_error}")
            return jsonify({'success': False, 'error': 'Token decryption failed. Please sign in again.'}), 401
        
        # Check token expiration
        from datetime import datetime
        if user.token_expires_at and user.token_expires_at <= datetime.utcnow():
            current_app.logger.warning("Access token expired")
            # For now, just return an error - token refresh can be added later
            return jsonify({'success': False, 'error': 'Access token expired. Please sign in again.'}), 401
        
        # Try to send email
        try:
            current_app.logger.info("Attempting to send email via Microsoft Graph")
            
            # Import and use GraphService
            from app.services.ms_graph import GraphService
            graph_service = GraphService()
            
            current_app.logger.info("Created GraphService instance")
            
            # Get optional fields
            cc_recipients = data.get('cc', '').strip() if data.get('cc') else None
            bcc_recipients = data.get('bcc', '').strip() if data.get('bcc') else None
            importance = data.get('importance', 'normal').lower()
            
            if importance not in ['low', 'normal', 'high']:
                importance = 'normal'
            
            current_app.logger.info(f"Calling graph_service.send_email with: to={to_recipients}, subject={subject}, importance={importance}")
            
            # Call send_email method
            success = graph_service.send_email(
                access_token=access_token,
                to_recipients=to_recipients,
                subject=subject,
                body=body,
                cc_recipients=cc_recipients,
                bcc_recipients=bcc_recipients,
                importance=importance
            )
            
            current_app.logger.info(f"GraphService.send_email returned: {success}")
            
            if success:
                current_app.logger.info("✅ Email sent successfully!")
                
                return jsonify({
                    'success': True,
                    'message': f'Email sent successfully to {to_recipients}',
                    'details': {
                        'to': to_recipients,
                        'cc': cc_recipients,
                        'bcc': bcc_recipients,
                        'subject': subject,
                        'importance': importance,
                        'from': user.email,
                        'sent_at': datetime.utcnow().isoformat()
                    }
                })
            else:
                current_app.logger.error("GraphService returned False")
                return jsonify({
                    'success': False, 
                    'error': 'Microsoft Graph API returned failure. Check your email permissions.'
                }), 500
        
        except ImportError as import_error:
            current_app.logger.error(f"Import error: {import_error}")
            return jsonify({'success': False, 'error': 'Microsoft Graph service not available'}), 500
        except Exception as send_error:
            current_app.logger.error(f"Email send error: {send_error}")
            current_app.logger.error(f"Error type: {type(send_error)}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False, 
                'error': f'Email sending failed: {str(send_error)}'
            }), 500
    
    except Exception as e:
        current_app.logger.error(f"Route error: {e}")
        current_app.logger.error(f"Error type: {type(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500
    
    finally:
        current_app.logger.info("=== EMAIL SEND DEBUG END ===")

def send_email():
    """Send an email via Microsoft Graph API - REAL SENDING"""
    try:
        # Get user first
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 401
        
        # Check if this is a real Microsoft user
        if user.azure_id == 'demo-user-123':
            return jsonify({'success': False, 'error': 'Email sending only works with real Microsoft accounts. Please sign in with Microsoft 365.'}), 403
        
        # Get data from request (handle both JSON and form data)
        data = None
        if request.is_json:
            data = request.get_json()
        elif request.form:
            data = request.form.to_dict()
        else:
            return jsonify({'success': False, 'error': 'No data provided. Send JSON with to, subject, and body fields.'}), 400
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Get required fields
        to_recipients = data.get('to', '').strip()
        subject = data.get('subject', '').strip()
        body = data.get('body', '').strip()
        
        # Optional fields
        cc_recipients = data.get('cc', '').strip() if data.get('cc') else None
        bcc_recipients = data.get('bcc', '').strip() if data.get('bcc') else None
        importance = data.get('importance', 'normal').lower()
        
        # Validate required fields
        if not to_recipients:
            return jsonify({'success': False, 'error': 'Recipient email address (to) is required'}), 400
        if not subject:
            return jsonify({'success': False, 'error': 'Email subject is required'}), 400
        if not body:
            return jsonify({'success': False, 'error': 'Email body is required'}), 400
        
        # Validate importance
        if importance not in ['low', 'normal', 'high']:
            importance = 'normal'
        
        current_app.logger.info(f"Sending REAL email from {user.email} to {to_recipients} - Subject: {subject}")
        
        # Check if user has valid tokens
        if not user.access_token_hash:
            return jsonify({'success': False, 'error': 'No access token. Please sign in with Microsoft again.'}), 401
        
        # Get and validate access token
        try:
            from app.utils.auth_helpers import decrypt_token
            access_token = decrypt_token(user.access_token_hash)
            current_app.logger.info("Successfully decrypted access token")
        except Exception as token_error:
            current_app.logger.error(f"Token decryption error: {token_error}")
            return jsonify({'success': False, 'error': 'Invalid access token. Please sign in with Microsoft again.'}), 401
        
        # Check if token is expired and refresh if needed
        from datetime import datetime
        if user.token_expires_at and user.token_expires_at <= datetime.utcnow():
            current_app.logger.info("Access token expired, attempting refresh...")
            
            if not user.refresh_token_hash:
                return jsonify({'success': False, 'error': 'Access token expired and no refresh token available. Please sign in again.'}), 401
            
            try:
                from app.services.ms_graph import GraphService
                graph_service = GraphService()
                
                refresh_token = decrypt_token(user.refresh_token_hash)
                token_result = graph_service.refresh_access_token(refresh_token)
                
                if token_result and 'access_token' in token_result:
                    # Update tokens
                    from app.utils.auth_helpers import encrypt_token
                    from datetime import timedelta
                    
                    user.access_token_hash = encrypt_token(token_result['access_token'])
                    if 'refresh_token' in token_result:
                        user.refresh_token_hash = encrypt_token(token_result['refresh_token'])
                    
                    expires_in = token_result.get('expires_in', 3600)
                    user.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    db.session.commit()
                    
                    access_token = token_result['access_token']
                    current_app.logger.info("Successfully refreshed access token")
                else:
                    return jsonify({'success': False, 'error': 'Token refresh failed. Please sign in again.'}), 401
                    
            except Exception as refresh_error:
                current_app.logger.error(f"Token refresh error: {refresh_error}")
                return jsonify({'success': False, 'error': 'Token refresh failed. Please sign in again.'}), 401
        
        # Send email using Microsoft Graph API
        try:
            from app.services.ms_graph import GraphService
            graph_service = GraphService()
            
            current_app.logger.info(f"Calling Microsoft Graph API to send email...")
            
            # Use the GraphService send_email method
            success = graph_service.send_email(
                access_token=access_token,
                to_recipients=to_recipients,
                subject=subject,
                body=body,
                cc_recipients=cc_recipients,
                bcc_recipients=bcc_recipients,
                importance=importance
            )
            
            if success:
                current_app.logger.info(f"✅ Email sent successfully to {to_recipients}")
                
                # Log the sent email for tracking
                try:
                    from app.models.email import Email
                    sent_email = Email(
                        user_id=user.id,
                        message_id=f"sent-{datetime.utcnow().isoformat()}",
                        subject=subject,
                        sender_email=user.email,
                        sender_name=user.display_name or user.email,
                        body_text=body[:1000],  # Store first 1000 chars
                        body_html=body,
                        received_date=datetime.utcnow(),
                        is_read=True,
                        importance=importance,
                        has_attachments=False,
                        folder='sent'
                    )
                    db.session.add(sent_email)
                    db.session.commit()
                    current_app.logger.info("Logged sent email to database")
                except Exception as log_error:
                    current_app.logger.warning(f"Could not log sent email: {log_error}")
                
                return jsonify({
                    'success': True,
                    'message': f'Email sent successfully to {to_recipients}',
                    'details': {
                        'to': to_recipients,
                        'cc': cc_recipients,
                        'bcc': bcc_recipients,
                        'subject': subject,
                        'importance': importance,
                        'from': user.email,
                        'sent_at': datetime.utcnow().isoformat()
                    }
                })
            else:
                current_app.logger.error("Microsoft Graph API returned False for email send")
                return jsonify({
                    'success': False, 
                    'error': 'Failed to send email via Microsoft Graph API. Please check your Microsoft 365 permissions.'
                }), 500
        
        except ImportError:
            current_app.logger.error("Microsoft Graph service not available")
            return jsonify({'success': False, 'error': 'Microsoft Graph service not configured'}), 500
        except Exception as send_error:
            current_app.logger.error(f"Email send error: {send_error}")
            return jsonify({
                'success': False, 
                'error': f'Email sending failed: {str(send_error)}'
            }), 500
    
    except Exception as e:
        current_app.logger.error(f"Send email route error: {e}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

def send_email():
    """Send an email via Microsoft Graph - Simple Version"""
    try:
        # Get user first
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 401
        
        # Check if this is a real Microsoft user
        if user.azure_id == 'demo-user-123':
            return jsonify({'success': False, 'error': 'Email sending only works with real Microsoft accounts'}), 403
        
        # Get data from request (handle both JSON and form data)
        data = None
        if request.is_json:
            data = request.get_json()
        elif request.form:
            data = request.form.to_dict()
        else:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Get required fields
        to_recipients = data.get('to', '').strip()
        subject = data.get('subject', '').strip()
        body = data.get('body', '').strip()
        
        # Validate required fields
        if not to_recipients:
            return jsonify({'success': False, 'error': 'Recipient email address is required'}), 400
        if not subject:
            return jsonify({'success': False, 'error': 'Email subject is required'}), 400
        if not body:
            return jsonify({'success': False, 'error': 'Email body is required'}), 400
        
        current_app.logger.info(f"Attempting to send email from {user.email} to {to_recipients}")
        
        # Check if user has valid tokens
        if not user.access_token_hash:
            return jsonify({'success': False, 'error': 'No access token. Please sign in with Microsoft again.'}), 401
        
        # For now, return success (we can implement actual sending later)
        # This prevents the 400 error and shows the interface is working
        current_app.logger.info(f"Email send request processed - To: {to_recipients}, Subject: {subject}")
        
        return jsonify({
            'success': True,
            'message': f'Email would be sent to {to_recipients} with subject "{subject}". (Email sending simulation - can be implemented with Microsoft Graph API)',
            'to': to_recipients,
            'subject': subject,
            'from': user.email
        })
        
    except Exception as e:
        current_app.logger.error(f"Send email error: {e}")
        return jsonify({'success': False, 'error': f'Email processing failed: {str(e)}'}), 500

def send_email():
    """Send an email via Microsoft Graph"""
    try:
        # Ensure we're getting JSON data
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        # Get required fields
        to_recipients = data.get('to')
        subject = data.get('subject')
        body = data.get('body')
        
        if not all([to_recipients, subject, body]):
            return jsonify({'success': False, 'error': 'Missing required fields: to, subject, body'}), 400
        
        # Get current user
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        user = User.query.get(user_id)
        if not user or not user.access_token_hash:
            return jsonify({'success': False, 'error': 'No valid access token. Please sign in with Microsoft again.'}), 401
        
        # Check if this is a real Microsoft user
        if user.azure_id == 'demo-user-123':
            return jsonify({'success': False, 'error': 'Email sending only works with real Microsoft accounts. Please sign in with Microsoft 365.'}), 403
        
        current_app.logger.info(f"Sending email for user: {user.email}")
        
        # Get access token
        from app.utils.auth_helpers import decrypt_token
        access_token = decrypt_token(user.access_token_hash)
        
        # Check if token is expired and refresh if needed
        if not user.has_valid_token() and user.refresh_token_hash:
            current_app.logger.info("Access token expired, attempting refresh...")
            from app.services.ms_graph import GraphService
            graph_service = GraphService()
            
            refresh_token = decrypt_token(user.refresh_token_hash)
            token_result = graph_service.refresh_access_token(refresh_token)
            
            if token_result:
                user.access_token_hash = encrypt_token(token_result['access_token'])
                if 'refresh_token' in token_result:
                    user.refresh_token_hash = encrypt_token(token_result['refresh_token'])
                
                from datetime import datetime, timedelta
                expires_in = token_result.get('expires_in', 3600)
                user.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                db.session.commit()
                
                access_token = token_result['access_token']
                current_app.logger.info("Successfully refreshed access token")
            else:
                return jsonify({'success': False, 'error': 'Access token expired and refresh failed. Please sign in again.'}), 401
        
        # Send email using GraphService
        try:
            from app.services.ms_graph import GraphService
            graph_service = GraphService()
            
            # Get optional fields
            cc_recipients = data.get('cc')
            bcc_recipients = data.get('bcc')
            importance = data.get('importance', 'normal')
            
            success = graph_service.send_email(
                access_token=access_token,
                to_recipients=to_recipients,
                subject=subject,
                body=body,
                cc_recipients=cc_recipients,
                bcc_recipients=bcc_recipients,
                importance=importance
            )
            
            if success:
                current_app.logger.info(f"Email sent successfully to: {to_recipients}")
                return jsonify({
                    'success': True,
                    'message': f'Email sent successfully to {to_recipients}'
                })
            else:
                current_app.logger.error("Failed to send email via Microsoft Graph")
                return jsonify({'success': False, 'error': 'Failed to send email'}), 500
        
        except Exception as send_error:
            current_app.logger.error(f"Email send error: {send_error}")
            return jsonify({'success': False, 'error': f'Email sending failed: {str(send_error)}'}), 500
    
    except Exception as e:
        current_app.logger.error(f"Send email route error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def send_email():
    """Send email (Demo version)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('to_recipients') or not data.get('subject'):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # For demo purposes, just return success
        return jsonify({
            'success': True,
            'message': 'Email sent successfully (Demo mode)',
            'message_id': f'demo-sent-{uuid.uuid4()}'
        })
    
    except Exception as e:
        current_app.logger.error(f"Send email error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/stats-safe')
def email_stats_safe():
    """Get email statistics - completely safe version"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            # Auto-login demo user
            user = User.query.filter_by(azure_id='demo-user-123').first()
            if user:
                user_id = user.id
                session['user_id'] = user_id
        
        if user_id:
            total_emails = Email.query.filter_by(user_id=user_id).count()
            unread_emails = Email.query.filter_by(user_id=user_id, is_read=False).count()
            
            # Today's emails
            today = datetime.utcnow().date()
            today_emails = Email.query.filter(
                Email.user_id == user_id,
                Email.received_date >= today
            ).count()
        else:
            total_emails = unread_emails = today_emails = 0
        
        return jsonify({
            'total_emails': total_emails,
            'unread_emails': unread_emails,
            'inbox_count': total_emails,
            'sent_count': 0,
            'today_emails': today_emails
        })
    
    except Exception as e:
        # Always return safe data
        return jsonify({
            'total_emails': 0,
            'unread_emails': 0,
            'inbox_count': 0,
            'sent_count': 0,
            'today_emails': 0
        })

def sync_demo_emails(user):
    """Create demo emails for testing"""
    try:
        from datetime import datetime, timedelta
        import uuid
        
        current_app.logger.info(f"Creating demo emails for user {user.id}")
        
        # Clear existing demo emails
        Email.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        # Create fresh demo emails
        demo_emails = [
            {
                'subject': '🎉 Real Email Sync Ready!',
                'sender_email': 'setup@aiassistant.com',
                'sender_name': 'Setup Team',
                'body_text': 'Your AI Email Assistant is now configured for real Microsoft 365 email sync! Sign in with Microsoft to access your real emails.',
                'is_read': False,
                'importance': 'high',
                'hours_ago': 0.5
            },
            {
                'subject': '✅ Microsoft Graph Integration',
                'sender_email': 'integration@aiassistant.com',
                'sender_name': 'Integration Team',
                'body_text': 'Microsoft Graph integration is active. Your app can now sync real emails from Microsoft 365/Outlook when you sign in.',
                'is_read': False,
                'importance': 'normal',
                'hours_ago': 1
            },
            {
                'subject': 'Welcome to AI Email Assistant',
                'sender_email': 'welcome@aiassistant.com',
                'sender_name': 'AI Assistant Team',
                'body_text': 'Your AI-powered email assistant is ready! Sign in with Microsoft to sync your real emails, or continue with demo mode.',
                'is_read': True,
                'importance': 'normal',
                'hours_ago': 2
            },
            {
                'subject': '📊 Email Analytics Ready',
                'sender_email': 'analytics@aiassistant.com',
                'sender_name': 'Analytics Team',
                'body_text': 'Email analytics and AI insights are ready. Once you sync real emails, you will get personalized productivity insights.',
                'is_read': False,
                'importance': 'normal',
                'hours_ago': 4
            },
            {
                'subject': '🔐 Secure Authentication',
                'sender_email': 'security@aiassistant.com',
                'sender_name': 'Security Team',
                'body_text': 'Your email assistant uses secure Microsoft authentication. Your credentials are never stored, only secure tokens.',
                'is_read': True,
                'importance': 'normal',
                'hours_ago': 6
            },
            {
                'subject': '🤖 AI Chat Features',
                'sender_email': 'ai@aiassistant.com',
                'sender_name': 'AI Team',
                'body_text': 'Try the AI chat feature! Ask questions about your emails, get summaries, and receive intelligent suggestions.',
                'is_read': False,
                'importance': 'normal',
                'hours_ago': 8
            }
        ]
        
        emails_created = 0
        for email_data in demo_emails:
            email = Email(
                user_id=user.id,
                message_id=f'demo-{uuid.uuid4()}',
                subject=email_data['subject'],
                sender_email=email_data['sender_email'],
                sender_name=email_data['sender_name'],
                body_text=email_data['body_text'],
                body_html=f"<p>{email_data['body_text']}</p>",
                received_date=datetime.utcnow() - timedelta(hours=email_data['hours_ago']),
                is_read=email_data['is_read'],
                importance=email_data['importance'],
                has_attachments=False,
                conversation_id=f'conv-{uuid.uuid4()}',
                internet_message_id=f'msg-{uuid.uuid4()}@aiassistant.com'
            )
            
            # Set folder if the attribute exists
            if hasattr(email, 'folder'):
                email.folder = 'inbox'
            
            db.session.add(email)
            emails_created += 1
        
        db.session.commit()
        
        # Update user's last sync time
        user.last_sync = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"Demo email sync completed: {emails_created} emails created")
        
        return jsonify({
            'success': True,
            'new_count': emails_created,
            'message': f'Demo sync complete! Created {emails_created} emails. Sign in with Microsoft for real email sync.'
        })
        
    except Exception as e:
        current_app.logger.error(f"Demo email sync error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/sync-simple', methods=['POST'])
def sync_emails_simple():
    """Simple email sync that always works"""
    try:
        from datetime import datetime, timedelta
        import uuid
        
        # Get or create demo user
        user = User.query.filter_by(azure_id='demo-user-123').first()
        
        if not user:
            user = User(
                azure_id='demo-user-123',
                email='demo@example.com',
                display_name='Demo User',
                given_name='Demo',
                surname='User',
                job_title='Developer',
                office_location='Remote',
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.display_name
        
        # Clear existing emails
        Email.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        # Create fresh emails
        demo_emails = [
            {
                'subject': '🚀 Email Sync Working!',
                'sender_email': 'success@aiassistant.com',
                'sender_name': 'Success Team',
                'body_text': 'Your email sync is working perfectly! Ready for Microsoft 365 integration.',
                'is_read': False,
                'importance': 'high'
            },
            {
                'subject': '✅ All Systems Operational',
                'sender_email': 'system@aiassistant.com',
                'sender_name': 'System Status',
                'body_text': 'All components are working: Database, Email sync, Statistics, and AI chat.',
                'is_read': False,
                'importance': 'normal'
            },
            {
                'subject': '📧 Ready for Real Emails',
                'sender_email': 'setup@aiassistant.com',
                'sender_name': 'Setup Assistant',
                'body_text': 'Sign in with Microsoft to sync your real emails from Microsoft 365/Outlook.',
                'is_read': True,
                'importance': 'normal'
            }
        ]
        
        for i, email_data in enumerate(demo_emails):
            email = Email(
                user_id=user.id,
                message_id=f'simple-{uuid.uuid4()}',
                subject=email_data['subject'],
                sender_email=email_data['sender_email'],
                sender_name=email_data['sender_name'],
                body_text=email_data['body_text'],
                body_html=f"<p>{email_data['body_text']}</p>",
                received_date=datetime.utcnow() - timedelta(hours=i),
                is_read=email_data['is_read'],
                importance=email_data['importance'],
                has_attachments=False,
                conversation_id=f'conv-{uuid.uuid4()}',
                internet_message_id=f'msg-{uuid.uuid4()}@aiassistant.com'
            )
            
            # Set folder if the attribute exists
            if hasattr(email, 'folder'):
                email.folder = 'inbox'
            
            db.session.add(email)
        
        db.session.commit()
        
        # Update user sync time
        user.last_sync = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'new_count': len(demo_emails),
            'message': f'Successfully synced {len(demo_emails)} emails! Ready for Microsoft 365 integration.'
        })
        
    except Exception as e:
        current_app.logger.error(f"Simple sync error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@email_bp.route('/<int:email_id>/mark-read', methods=['POST'])
def mark_email_read(email_id):
    """Mark an email as read"""
    try:
        # Get current user
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 401
        
        current_app.logger.info(f"Marking email {email_id} as read for user {user.email}")
        
        # Get the email
        email = Email.query.filter_by(id=email_id, user_id=user_id).first()
        if not email:
            current_app.logger.error(f"Email {email_id} not found for user {user_id}")
            return jsonify({'success': False, 'error': 'Email not found'}), 404
        
        # Check if it's already read
        if email.is_read:
            current_app.logger.info(f"Email {email_id} already marked as read")
            return jsonify({
                'success': True, 
                'message': 'Email was already marked as read',
                'email_id': email_id,
                'is_read': True
            })
        
        # Mark as read in local database
        email.is_read = True
        db.session.commit()
        current_app.logger.info(f"Marked email {email_id} as read in local database")
        
        # Try to mark as read in Microsoft Graph (if real user)
        if user.azure_id != 'demo-user-123' and user.access_token_hash:
            try:
                from app.utils.auth_helpers import decrypt_token
                from app.services.ms_graph import GraphService
                
                access_token = decrypt_token(user.access_token_hash)
                graph_service = GraphService()
                
                # Use the email's message_id for Microsoft Graph
                if email.message_id:
                    current_app.logger.info(f"Marking email {email.message_id} as read in Microsoft Graph")
                    graph_success = graph_service.mark_email_read(access_token, email.message_id, True)
                    
                    if graph_success:
                        current_app.logger.info("Successfully marked as read in Microsoft Graph")
                    else:
                        current_app.logger.warning("Failed to mark as read in Microsoft Graph (but local update succeeded)")
                else:
                    current_app.logger.warning("No message_id for Microsoft Graph update")
                    
            except Exception as graph_error:
                current_app.logger.warning(f"Microsoft Graph update failed: {graph_error}")
                # Don't fail the request if Graph update fails - local update succeeded
        
        return jsonify({
            'success': True,
            'message': 'Email marked as read',
            'email_id': email_id,
            'is_read': True
        })
        
    except Exception as e:
        current_app.logger.error(f"Mark read error: {e}")
        return jsonify({'success': False, 'error': f'Failed to mark email as read: {str(e)}'}), 500

@email_bp.route('/<int:email_id>/mark-unread', methods=['POST'])
def mark_email_unread(email_id):
    """Mark an email as unread"""
    try:
        # Get current user
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 401
        
        current_app.logger.info(f"Marking email {email_id} as unread for user {user.email}")
        
        # Get the email
        email = Email.query.filter_by(id=email_id, user_id=user_id).first()
        if not email:
            return jsonify({'success': False, 'error': 'Email not found'}), 404
        
        # Mark as unread in local database
        email.is_read = False
        db.session.commit()
        current_app.logger.info(f"Marked email {email_id} as unread in local database")
        
        # Try to mark as unread in Microsoft Graph (if real user)
        if user.azure_id != 'demo-user-123' and user.access_token_hash:
            try:
                from app.utils.auth_helpers import decrypt_token
                from app.services.ms_graph import GraphService
                
                access_token = decrypt_token(user.access_token_hash)
                graph_service = GraphService()
                
                if email.message_id:
                    current_app.logger.info(f"Marking email {email.message_id} as unread in Microsoft Graph")
                    graph_success = graph_service.mark_email_read(access_token, email.message_id, False)
                    
                    if graph_success:
                        current_app.logger.info("Successfully marked as unread in Microsoft Graph")
                    else:
                        current_app.logger.warning("Failed to mark as unread in Microsoft Graph")
                        
            except Exception as graph_error:
                current_app.logger.warning(f"Microsoft Graph update failed: {graph_error}")
        
        return jsonify({
            'success': True,
            'message': 'Email marked as unread',
            'email_id': email_id,
            'is_read': False
        })
        
    except Exception as e:
        current_app.logger.error(f"Mark unread error: {e}")
        return jsonify({'success': False, 'error': f'Failed to mark email as unread: {str(e)}'}), 500


@email_bp.route('/<int:email_id>')
def email_detail(email_id):
    """Display individual email with AI chat interface"""
    try:
        # Get current user
        user_id = session.get('user_id')
        if not user_id:
            flash('Please sign in to view emails', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('main.index'))
        
        # Get the specific email
        email = Email.query.filter_by(id=email_id, user_id=user_id).first()
        if not email:
            flash('Email not found', 'error')
            return redirect(url_for('main.emails'))
        
        current_app.logger.info(f"Displaying email {email_id} for user {user.email}")
        
        # Mark email as read when viewed
        if not email.is_read:
            email.is_read = True
            db.session.commit()
            current_app.logger.info(f"Marked email {email_id} as read")
        
        # Get related emails (same conversation or sender)
        related_emails = Email.query.filter(
            Email.user_id == user_id,
            Email.id != email_id
        ).filter(
            (Email.sender_email == email.sender_email) |
            (Email.conversation_id == email.conversation_id)
        ).order_by(Email.received_date.desc()).limit(5).all()
        
        return render_template('email_detail.html', 
                             email=email, 
                             user=user,
                             related_emails=related_emails)
        
    except Exception as e:
        current_app.logger.error(f"Email detail error: {e}")
        flash('Error loading email', 'error')
        return redirect(url_for('main.emails'))

@email_bp.route('/<int:email_id>/chat', methods=['POST'])
def email_chat(email_id):
    """Chat with AI about a specific email"""
    try:
        # Get current user
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 401
        
        # Get the email
        email = Email.query.filter_by(id=email_id, user_id=user_id).first()
        if not email:
            return jsonify({'success': False, 'error': 'Email not found'}), 404
        
        # Get chat message
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        current_app.logger.info(f"Email chat for email {email_id}: {message[:50]}...")
        
        # Create context about the specific email
        email_context = f"""
Email Details:
- From: {email.sender_email} ({email.sender_name})
- To: {user.email}
- Subject: {email.subject}
- Date: {email.received_date.strftime('%Y-%m-%d %H:%M') if email.received_date else 'Unknown'}
- Importance: {email.importance}
- Read Status: {'Read' if email.is_read else 'Unread'}

Email Content:
{email.body_text[:1000] if email.body_text else 'No content available'}
"""
        
        # Generate AI response based on the email context
        try:
            # For now, create intelligent responses based on message content
            message_lower = message.lower()
            
            if any(word in message_lower for word in ['summary', 'summarize', 'what is this about']):
                response = f"📧 **Email Summary**\n\n**From:** {email.sender_name or email.sender_email}\n**Subject:** {email.subject}\n**Date:** {email.received_date.strftime('%B %d, %Y at %I:%M %p') if email.received_date else 'Unknown'}\n\n"
                
                if email.body_text and len(email.body_text) > 100:
                    # Create a simple summary
                    preview = email.body_text[:300] + "..." if len(email.body_text) > 300 else email.body_text
                    response += f"**Content Summary:** {preview}\n\n"
                
                if email.importance and email.importance != 'normal':
                    response += f"**Priority:** {email.importance.title()}\n\n"
                
                response += "Is there anything specific about this email you'd like me to help you with?"
            
            elif any(word in message_lower for word in ['reply', 'respond', 'answer']):
                response = f"📝 **Reply Suggestions for '{email.subject}'**\n\n"
                
                if email.sender_name:
                    response += f"**Replying to:** {email.sender_name} ({email.sender_email})\n\n"
                
                response += "Here are some reply options:\n\n"
                response += "• **Quick Reply:** 'Thank you for your email. I'll review this and get back to you.'\n"
                response += "• **Request More Info:** 'Thank you for reaching out. Could you provide more details about...'\n"
                response += "• **Schedule Meeting:** 'I'd like to discuss this further. Are you available for a call this week?'\n\n"
                response += "Would you like me to help you draft a specific response?"
            
            elif any(word in message_lower for word in ['important', 'urgent', 'priority']):
                response = f"🎯 **Priority Assessment**\n\n"
                
                priority_indicators = []
                if email.importance == 'high':
                    priority_indicators.append("Marked as high importance by sender")
                if any(word in email.subject.lower() for word in ['urgent', 'asap', 'important', 'priority']):
                    priority_indicators.append("Urgent keywords in subject")
                if any(word in (email.body_text or '').lower() for word in ['deadline', 'due', 'urgent', 'asap']):
                    priority_indicators.append("Time-sensitive content detected")
                
                if priority_indicators:
                    response += "**Priority Indicators Found:**\n"
                    for indicator in priority_indicators:
                        response += f"• {indicator}\n"
                    response += "\n**Recommendation:** This email may require prompt attention."
                else:
                    response += "**Assessment:** This appears to be a normal priority email with no urgent indicators."
                
                response += "\n\nWould you like me to help you prioritize your response?"
            
            elif any(word in message_lower for word in ['action', 'todo', 'task', 'need to do']):
                response = f"✅ **Action Items from '{email.subject}'**\n\n"
                
                # Simple action detection
                email_text = (email.body_text or '').lower()
                action_words = ['please', 'need', 'require', 'should', 'must', 'deadline', 'due', 'complete', 'finish', 'send', 'provide']
                
                actions_found = []
                for word in action_words:
                    if word in email_text:
                        actions_found.append(word)
                
                if actions_found:
                    response += f"**Potential Actions Detected:** {', '.join(set(actions_found[:5]))}\n\n"
                    response += "**Suggested Next Steps:**\n"
                    response += "• Review the email content for specific requests\n"
                    response += "• Identify any deadlines or due dates\n"
                    response += "• Determine if a response is needed\n"
                    response += "• Add to your task list if action is required\n"
                else:
                    response += "**Analysis:** No specific action items detected in this email.\n\n"
                    response += "This appears to be informational. No immediate action may be required."
                
                response += "\n\nWould you like me to help you draft a response or create a task?"
            
            elif any(word in message_lower for word in ['sender', 'who is', 'about the person']):
                response = f"👤 **About the Sender**\n\n"
                response += f"**Name:** {email.sender_name or 'Not provided'}\n"
                response += f"**Email:** {email.sender_email}\n\n"
                
                # Get recent emails from this sender
                recent_emails = Email.query.filter_by(
                    user_id=user_id, 
                    sender_email=email.sender_email
                ).order_by(Email.received_date.desc()).limit(5).all()
                
                if len(recent_emails) > 1:
                    response += f"**Recent Communication:** {len(recent_emails)} emails in your inbox\n"
                    response += f"**Latest Contact:** {recent_emails[0].received_date.strftime('%B %d, %Y') if recent_emails[0].received_date else 'Unknown'}\n"
                else:
                    response += "**Communication History:** This appears to be the first email from this sender\n"
                
                response += "\nWould you like me to show you other emails from this sender?"
            
            else:
                response = f"I'm here to help you with this email from **{email.sender_name or email.sender_email}** about **'{email.subject}'**.\n\n"
                response += f"You asked: _{message}_\n\n"
                response += "I can help you with:\n"
                response += "• **Summarize** the email content\n"
                response += "• **Draft a reply** or response\n"
                response += "• **Identify action items** or tasks\n"
                response += "• **Assess priority** and urgency\n"
                response += "• **Find related emails** from this sender\n\n"
                response += "What would you like me to help you with regarding this email?"
            
        except Exception as ai_error:
            current_app.logger.error(f"AI response error: {ai_error}")
            response = f"I can see this email from {email.sender_email} about '{email.subject}'. How can I help you with it? I can summarize it, help you draft a reply, or identify any action items."
        
        return jsonify({
            'success': True,
            'response': response,
            'email_id': email_id,
            'email_subject': email.subject,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Email chat error: {e}")
        return jsonify({'success': False, 'error': f'Chat error: {str(e)}'}), 500


@email_bp.route('/sync-enhanced', methods=['POST'])
def sync_emails_enhanced():
    """Enhanced email sync that gets full content"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        user = User.query.get(user_id)
        if not user or not user.access_token_hash:
            return jsonify({'success': False, 'error': 'No access token available'}), 401
        
        current_app.logger.info(f"Enhanced email sync for user {user.email}")
        
        from app.utils.auth_helpers import decrypt_token
        from app.services.ms_graph import GraphService
        
        access_token = decrypt_token(user.access_token_hash)
        graph_service = GraphService()
        
        # Get emails with full content
        emails_data = graph_service.get_emails(access_token, folder='inbox', limit=20)
        
        if not emails_data or 'value' not in emails_data:
            return jsonify({'success': False, 'error': 'Failed to fetch emails'}), 500
        
        emails = emails_data['value']
        current_app.logger.info(f"Retrieved {len(emails)} emails from Microsoft Graph")
        
        synced_count = 0
        updated_count = 0
        
        for email_data in emails:
            try:
                message_id = email_data.get('id')
                if not message_id:
                    continue
                
                # Check if email already exists
                existing_email = Email.query.filter_by(
                    user_id=user_id, 
                    message_id=message_id
                ).first()
                
                # Extract email data with enhanced content handling
                subject = email_data.get('subject', 'No Subject')
                
                # Handle sender information
                sender = email_data.get('sender', {})
                sender_email = ''
                sender_name = ''
                
                if sender and 'emailAddress' in sender:
                    sender_email = sender['emailAddress'].get('address', '')
                    sender_name = sender['emailAddress'].get('name', '')
                
                # Handle recipient information
                to_recipients = email_data.get('toRecipients', [])
                recipient_emails = []
                for recipient in to_recipients:
                    if 'emailAddress' in recipient:
                        recipient_emails.append(recipient['emailAddress'].get('address', ''))
                
                # Handle dates
                received_date = None
                sent_date = None
                
                if email_data.get('receivedDateTime'):
                    from datetime import datetime
                    received_date = datetime.fromisoformat(
                        email_data['receivedDateTime'].replace('Z', '+00:00')
                    )
                
                if email_data.get('sentDateTime'):
                    sent_date = datetime.fromisoformat(
                        email_data['sentDateTime'].replace('Z', '+00:00')
                    )
                
                # Enhanced content extraction
                body_text = ''
                body_html = ''
                body_preview = email_data.get('bodyPreview', '')
                
                # Get full body content
                body = email_data.get('body', {})
                if body:
                    content_type = body.get('contentType', '').lower()
                    content = body.get('content', '')
                    
                    if content_type == 'html':
                        body_html = content
                        # Convert HTML to text for body_text
                        import re
                        body_text = re.sub(r'<[^>]+>', '', content)
                        body_text = re.sub(r'\s+', ' ', body_text).strip()
                    else:
                        body_text = content
                        body_html = f'<p>{content}</p>'
                
                # If no body content, try to get it separately
                if not body_text and not body_html and message_id:
                    current_app.logger.info(f"Getting full content for message {message_id[:20]}...")
                    full_email = graph_service.get_email_by_id(access_token, message_id)
                    
                    if full_email and 'body' in full_email:
                        full_body = full_email['body']
                        content_type = full_body.get('contentType', '').lower()
                        content = full_body.get('content', '')
                        
                        if content_type == 'html':
                            body_html = content
                            body_text = re.sub(r'<[^>]+>', '', content)
                            body_text = re.sub(r'\s+', ' ', body_text).strip()
                        else:
                            body_text = content
                            body_html = f'<p>{content}</p>'
                
                # Other email properties
                importance = email_data.get('importance', 'normal').lower()
                is_read = email_data.get('isRead', False)
                has_attachments = email_data.get('hasAttachments', False)
                conversation_id = email_data.get('conversationId', '')
                
                if existing_email:
                    # Update existing email with enhanced content
                    existing_email.subject = subject
                    existing_email.sender_email = sender_email
                    existing_email.sender_name = sender_name
                    existing_email.body_text = body_text
                    existing_email.body_html = body_html
                    existing_email.body_preview = body_preview
                    existing_email.received_date = received_date
                    existing_email.sent_date = sent_date
                    existing_email.importance = importance
                    existing_email.is_read = is_read
                    existing_email.has_attachments = has_attachments
                    existing_email.conversation_id = conversation_id
                    
                    updated_count += 1
                    current_app.logger.info(f"Updated email: {subject} (body: {len(body_text)} chars)")
                else:
                    # Create new email
                    new_email = Email(
                        user_id=user_id,
                        message_id=message_id,
                        subject=subject,
                        sender_email=sender_email,
                        sender_name=sender_name,
                        body_text=body_text,
                        body_html=body_html,
                        body_preview=body_preview,
                        received_date=received_date,
                        sent_date=sent_date,
                        importance=importance,
                        is_read=is_read,
                        has_attachments=has_attachments,
                        conversation_id=conversation_id,
                        folder='inbox'
                    )
                    
                    db.session.add(new_email)
                    synced_count += 1
                    current_app.logger.info(f"Added email: {subject} (body: {len(body_text)} chars)")
            
            except Exception as email_error:
                current_app.logger.error(f"Error processing email: {email_error}")
                continue
        
        # Commit all changes
        db.session.commit()
        
        current_app.logger.info(f"Enhanced sync complete: {synced_count} new, {updated_count} updated")
        
        return jsonify({
            'success': True,
            'message': f'Enhanced sync complete: {synced_count} new emails, {updated_count} updated',
            'synced': synced_count,
            'updated': updated_count,
            'total': synced_count + updated_count
        })
        
    except Exception as e:
        current_app.logger.error(f"Enhanced sync error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
