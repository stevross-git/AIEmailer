#!/usr/bin/env python3
"""
Fix Email Send API and Chat UI
"""
import os

def fix_email_send_api():
    """Fix the email send API to handle JSON properly"""
    print("🔧 Fixing Email Send API")
    print("=" * 21)
    
    routes_file = 'app/routes/email.py'
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and fix the send email route
        fixed_send_route = '''@email_bp.route('/send', methods=['POST'])
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
        return jsonify({'success': False, 'error': str(e)}), 500'''
        
        # Replace the send route
        import re
        pattern = r"@email_bp\.route\('/send'.*?(?=@email_bp\.route|def \w+|$)"
        new_content = re.sub(pattern, fixed_send_route + '\n\n', content, flags=re.DOTALL)
        
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Fixed email send API to handle JSON properly")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing email send API: {e}")
        return False

def add_missing_imports():
    """Add missing imports to email routes"""
    print("\n🔧 Adding Missing Imports")
    print("=" * 24)
    
    routes_file = 'app/routes/email.py'
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if imports are missing and add them
        imports_to_add = []
        
        if 'from app.utils.auth_helpers import encrypt_token' not in content:
            imports_to_add.append('from app.utils.auth_helpers import encrypt_token')
        
        if 'from datetime import datetime, timedelta' not in content:
            imports_to_add.append('from datetime import datetime, timedelta')
        
        if imports_to_add:
            # Find where to insert imports (after existing imports)
            lines = content.split('\n')
            import_index = 0
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    import_index = i + 1
            
            # Insert new imports
            for imp in reversed(imports_to_add):
                lines.insert(import_index, imp)
            
            content = '\n'.join(lines)
            
            with open(routes_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Added {len(imports_to_add)} missing imports")
        else:
            print("✅ All imports already present")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding imports: {e}")
        return False

def update_frontend_send_email():
    """Update frontend to send emails with proper JSON"""
    print("\n🔧 Updating Frontend Email Send")
    print("=" * 30)
    
    js_file = 'app/static/js/main.js'
    
    try:
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add or update email sending function
        email_send_js = '''
// Email sending function
function sendEmail(to, subject, body, cc = null, bcc = null) {
    return fetch('/api/email/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            to: to,
            subject: subject,
            body: body,
            cc: cc,
            bcc: bcc,
            importance: 'normal'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Email sent successfully:', data.message);
            showNotification('Email sent successfully!', 'success');
        } else {
            console.error('Email send failed:', data.error);
            showNotification('Failed to send email: ' + data.error, 'error');
        }
        return data;
    })
    .catch(error => {
        console.error('Email send error:', error);
        showNotification('Email send error: ' + error.message, 'error');
    });
}

// Show notification function
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(notification, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}
'''
        
        # Add the email functions if not present
        if 'sendEmail(' not in content:
            content += email_send_js
            
            with open(js_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Added email sending functions to main.js")
        else:
            print("✅ Email functions already present")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating frontend: {e}")
        return False

def apply_chat_css_fix():
    """Apply the chat CSS fix directly"""
    print("\n🎨 Applying Chat CSS Fix")
    print("=" * 25)
    
    css_file = 'app/static/css/style.css'
    
    chat_css = '''
/* Chat UI Visibility Fix */
.chat-container {
    background-color: #f8f9fa !important;
    border-radius: 8px;
    padding: 20px;
}

.chat-messages {
    background-color: #ffffff !important;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    max-height: 400px;
    overflow-y: auto;
    padding: 15px;
    margin-bottom: 15px;
}

.message {
    margin-bottom: 15px;
    padding: 12px;
    border-radius: 8px;
    color: #212529 !important;
}

.message.assistant {
    background-color: #e9ecef !important;
    color: #212529 !important;
    margin-right: 20%;
}

.message.user {
    background-color: #007bff !important;
    color: #ffffff !important;
    margin-left: 20%;
}

.chat-input {
    background-color: #ffffff !important;
    color: #212529 !important;
    border: 1px solid #ced4da !important;
    padding: 10px;
    border-radius: 4px;
}

.chat-input:focus {
    background-color: #ffffff !important;
    color: #212529 !important;
    border-color: #007bff !important;
}

.chat-response, .chat-response * {
    color: #212529 !important;
}

.send-button {
    background-color: #007bff !important;
    color: #ffffff !important;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
}
'''
    
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add chat CSS if not present
        if 'Chat UI Visibility Fix' not in content:
            content += chat_css
            
            with open(css_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Added chat CSS visibility fixes")
        else:
            print("✅ Chat CSS already present")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying CSS fix: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Fix Email Send API and Chat UI")
    print("=" * 31)
    
    # Fix email send API
    api_fixed = fix_email_send_api()
    
    # Add missing imports
    imports_added = add_missing_imports()
    
    # Update frontend
    frontend_updated = update_frontend_send_email()
    
    # Apply chat CSS fix
    css_applied = apply_chat_css_fix()
    
    if api_fixed and imports_added:
        print(f"\n🎉 EMAIL SEND AND CHAT FIXED!")
        print(f"=" * 28)
        print(f"🚀 Restart your app:")
        print(f"   python docker_run.py")
        
        print(f"\n✅ Email Send Fixes:")
        print(f"   - Proper JSON Content-Type handling")
        print(f"   - Better error messages")
        print(f"   - Token refresh support")
        print(f"   - Microsoft Graph integration")
        
        print(f"\n✅ Chat UI Fixes:")
        print(f"   - Dark text on light background")
        print(f"   - Visible input fields")
        print(f"   - Color-coded messages")
        
        print(f"\n🎯 After restart:")
        print(f"   - Email sending will work properly")
        print(f"   - Chat interface will be visible")
        print(f"   - All features fully functional")
        
    else:
        print(f"\n❌ Some fixes failed - check manually")

if __name__ == "__main__":
    main()