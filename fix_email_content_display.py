#!/usr/bin/env python3
"""
Fix Email Content Display Issue
"""
import os

def check_email_content_in_database():
    """Check what email content is actually stored"""
    print("🔍 Checking Email Content in Database")
    print("=" * 35)
    
    check_script = '''#!/usr/bin/env python3
"""
Check Email Content in Database
"""
import os
import sys

def check_email_content():
    """Check email content in database"""
    print("🔍 Checking Email Content in Database")
    print("=" * 35)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        from app import create_app
        from app.models.email import Email
        
        app = create_app()
        
        with app.app_context():
            # Get email 267
            email = Email.query.filter_by(id=267).first()
            
            if email:
                print(f"✅ Found email {email.id}")
                print(f"Subject: {email.subject}")
                print(f"Sender: {email.sender_email}")
                print(f"Body Text: {repr(email.body_text)}")
                print(f"Body HTML: {repr(email.body_html)}")
                print(f"Body Preview: {repr(email.body_preview)}")
                print(f"Message ID: {email.message_id}")
                
                # Check if any content exists
                has_content = any([
                    email.body_text and len(email.body_text.strip()) > 0,
                    email.body_html and len(email.body_html.strip()) > 0,
                    email.body_preview and len(email.body_preview.strip()) > 0
                ])
                
                print(f"\\nHas Content: {has_content}")
                
                if not has_content:
                    print("\\n❌ No email content found!")
                    print("The email sync is not capturing email body content.")
                    print("We need to fix the Microsoft Graph email fetching.")
                else:
                    print("\\n✅ Email content exists in database!")
                    
            else:
                print("❌ Email 267 not found")
                
                # Check what emails we do have
                emails = Email.query.limit(5).all()
                print(f"\\nFound {len(emails)} emails:")
                for e in emails:
                    print(f"  {e.id}: {e.subject} (body_text: {len(e.body_text or '')} chars)")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_email_content()
'''
    
    with open('check_email_content.py', 'w', encoding='utf-8') as f:
        f.write(check_script)
    
    print("✅ Created check_email_content.py")

def create_enhanced_email_sync():
    """Create enhanced email sync that gets full email content"""
    print("\n🔧 Creating Enhanced Email Sync")
    print("=" * 30)
    
    enhanced_sync = '''@email_bp.route('/sync-enhanced', methods=['POST'])
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
                        body_text = re.sub(r'\\s+', ' ', body_text).strip()
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
                            body_text = re.sub(r'\\s+', ' ', body_text).strip()
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
        return jsonify({'success': False, 'error': str(e)}), 500'''
    
    return enhanced_sync

def add_enhanced_sync_route():
    """Add enhanced sync route to email.py"""
    print("\n🔧 Adding Enhanced Sync Route")
    print("=" * 27)
    
    routes_file = 'app/routes/email.py'
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        enhanced_route = create_enhanced_email_sync()
        
        # Add the enhanced sync route
        if 'sync-enhanced' not in content:
            content += '\n\n' + enhanced_route + '\n'
            
            with open(routes_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Added enhanced sync route")
        else:
            print("✅ Enhanced sync route already exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding enhanced sync route: {e}")
        return False

def update_email_detail_template_for_content():
    """Update email detail template to handle missing content better"""
    print("\n🔧 Updating Email Detail Template")
    print("=" * 32)
    
    template_file = 'app/templates/email_detail.html'
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the email body section and replace it
        old_body_section = '''<!-- Email Body -->
                    <div class="email-body">
                        {% if email.body_html %}
                            <div class="email-html-body">
                                {{ email.body_html|safe }}
                            </div>
                        {% elif email.body_text %}
                            <div class="email-text-body">
                                <pre style="white-space: pre-wrap; font-family: inherit;">{{ email.body_text }}</pre>
                            </div>
                        {% else %}
                            <p class="text-muted"><em>No email content available</em></p>
                        {% endif %}
                    </div>'''
        
        new_body_section = '''<!-- Email Body -->
                    <div class="email-body">
                        {% if email.body_html and email.body_html.strip() %}
                            <div class="email-html-body">
                                {{ email.body_html|safe }}
                            </div>
                        {% elif email.body_text and email.body_text.strip() %}
                            <div class="email-text-body">
                                <pre style="white-space: pre-wrap; font-family: inherit;">{{ email.body_text }}</pre>
                            </div>
                        {% elif email.body_preview and email.body_preview.strip() %}
                            <div class="email-preview-body">
                                <div class="alert alert-info">
                                    <strong>Preview:</strong> {{ email.body_preview }}
                                </div>
                                <p class="text-muted">
                                    <em>Full content not available. <button class="btn btn-sm btn-primary" onclick="syncFullContent()">Sync Full Content</button></em>
                                </p>
                            </div>
                        {% else %}
                            <div class="no-content-section">
                                <div class="alert alert-warning">
                                    <h6>📭 No Email Content Available</h6>
                                    <p class="mb-2">This email's content wasn't synced properly.</p>
                                    <button class="btn btn-primary btn-sm" onclick="syncFullContent()">
                                        🔄 Sync Full Content
                                    </button>
                                </div>
                            </div>
                        {% endif %}
                    </div>'''
        
        # Replace the section
        if old_body_section in content:
            content = content.replace(old_body_section, new_body_section)
        
        # Add sync function to the script section
        sync_script = '''
function syncFullContent() {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '🔄 Syncing...';
    
    fetch('/api/email/sync-enhanced', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload page to show updated content
            location.reload();
        } else {
            alert('Sync failed: ' + data.error);
            btn.disabled = false;
            btn.textContent = '🔄 Sync Full Content';
        }
    })
    .catch(error => {
        alert('Sync error: ' + error.message);
        btn.disabled = false;
        btn.textContent = '🔄 Sync Full Content';
    });
}
'''
        
        # Add the sync function before the closing script tag
        if 'syncFullContent' not in content:
            content = content.replace('</script>', sync_script + '</script>')
        
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Updated email detail template")
        return True
        
    except Exception as e:
        print(f"❌ Error updating template: {e}")
        return False

def create_test_enhanced_sync():
    """Create a test page for enhanced sync"""
    print("\n🧪 Creating Enhanced Sync Test")
    print("=" * 28)
    
    test_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Email Sync Test</title>
    <style>
        body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .result { margin-top: 20px; padding: 15px; border-radius: 4px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #e7f3ff; color: #0c5460; }
    </style>
</head>
<body>
    <h1>🔄 Enhanced Email Sync Test</h1>
    <p>This will sync emails with full content including email bodies.</p>
    
    <button onclick="runEnhancedSync()" class="btn" id="syncBtn">
        🔄 Run Enhanced Sync
    </button>
    
    <div id="result"></div>

    <script>
        function runEnhancedSync() {
            const btn = document.getElementById('syncBtn');
            const resultDiv = document.getElementById('result');
            
            btn.disabled = true;
            btn.textContent = '🔄 Syncing...';
            resultDiv.innerHTML = '<div class="result info">📡 Syncing emails with full content...</div>';
            
            fetch('/api/email/sync-enhanced', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    resultDiv.innerHTML = `
                        <div class="result success">
                            ✅ <strong>Enhanced Sync Complete!</strong><br>
                            📧 New emails: ${data.synced}<br>
                            🔄 Updated emails: ${data.updated}<br>
                            📊 Total processed: ${data.total}
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="result error">
                            ❌ <strong>Sync Failed:</strong> ${data.error}
                        </div>
                    `;
                }
            })
            .catch(error => {
                resultDiv.innerHTML = `
                    <div class="result error">
                        ❌ <strong>Network Error:</strong> ${error.message}
                    </div>
                `;
            })
            .finally(() => {
                btn.disabled = false;
                btn.textContent = '🔄 Run Enhanced Sync';
            });
        }
    </script>
</body>
</html>'''
    
    with open('enhanced_sync_test.html', 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print("✅ Created enhanced_sync_test.html")

def main():
    """Main function"""
    print("🔧 Fix Email Content Display Issue")
    print("=" * 32)
    print("🐛 Emails showing 'No email content available'")
    print("The email sync is not capturing email body content properly")
    print()
    
    # Create database check script
    check_email_content_in_database()
    
    # Add enhanced sync route
    sync_added = add_enhanced_sync_route()
    
    # Update email detail template
    template_updated = update_email_detail_template_for_content()
    
    # Create test page
    create_test_enhanced_sync()
    
    if sync_added and template_updated:
        print(f"\n🎉 EMAIL CONTENT FIX IMPLEMENTED!")
        print(f"=" * 33)
        print(f"🚀 Restart your app:")
        print(f"   python docker_run.py")
        
        print(f"\n🔍 First, check what's in the database:")
        print(f"   python check_email_content.py")
        
        print(f"\n✅ What was added:")
        print(f"   - Enhanced email sync with full content retrieval")
        print(f"   - Individual email content fetching")
        print(f"   - Better HTML/text content handling")
        print(f"   - Fallback to preview content")
        print(f"   - Sync full content button")
        
        print(f"\n🔄 Fix the content issue:")
        print(f"   1. Run: python check_email_content.py")
        print(f"   2. Open: enhanced_sync_test.html")
        print(f"   3. Click 'Run Enhanced Sync'")
        print(f"   4. Visit: http://localhost:5000/emails/267")
        print(f"   5. Should now show full email content!")
        
        print(f"\n🎯 Enhanced sync features:")
        print(f"   - Gets full email body content from Microsoft Graph")
        print(f"   - Handles both HTML and text content")
        print(f"   - Fetches individual emails if body is missing")
        print(f"   - Updates existing emails with content")
        print(f"   - Better error handling and logging")
        
        print(f"\n📧 After enhanced sync:")
        print(f"   - Email details page will show full content")
        print(f"   - AI chat will have email context")
        print(f"   - Rich HTML formatting preserved")
        print(f"   - Fallback to text content if needed")
        
    else:
        print(f"\n❌ Fix implementation failed")

if __name__ == "__main__":
    main()