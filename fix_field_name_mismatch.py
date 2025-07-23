#!/usr/bin/env python3
"""
Fix Field Name Mismatch in Email Send
"""
import os

def create_fixed_email_send_route():
    """Create email send route that handles the actual field names"""
    print("🔧 Creating Fixed Email Send Route")
    print("=" * 32)
    
    fixed_route = '''@email_bp.route('/send', methods=['POST'])
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
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
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
        current_app.logger.info("=== EMAIL SEND END ===")'''
    
    return fixed_route

def update_email_routes_with_fix():
    """Update email routes with the field name fix"""
    print("\n🔧 Updating Email Routes with Field Fix")
    print("=" * 37)
    
    routes_file = 'app/routes/email.py'
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        fixed_route = create_fixed_email_send_route()
        
        # Replace send route
        import re
        pattern = r"@email_bp\.route\('/send'.*?(?=@email_bp\.route|def \w+(?:\(|\s)|$)"
        
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, fixed_route + '\n\n', content, flags=re.DOTALL)
        else:
            new_content = content + '\n\n' + fixed_route + '\n'
        
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Updated email send route with field name fix")
        return True
        
    except Exception as e:
        print(f"❌ Error updating routes: {e}")
        return False

def create_working_email_test():
    """Create a test that uses the correct field names"""
    print("\n🧪 Creating Working Email Test")
    print("=" * 28)
    
    test_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Working Email Send Test</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 600px; 
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
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; }
        input, textarea, select { 
            width: 100%; 
            padding: 12px; 
            border: 1px solid #ddd; 
            border-radius: 4px; 
            box-sizing: border-box;
        }
        textarea { height: 100px; }
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
        button:disabled { background: #6c757d; cursor: not-allowed; }
        .result { 
            margin-top: 20px; 
            padding: 15px; 
            border-radius: 4px; 
            font-weight: bold;
        }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #e7f3ff; color: #0c5460; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>✅ Fixed Email Send Test</h1>
        
        <div class="info">
            <strong>🔧 Field Names Fixed!</strong><br>
            This test uses the correct field names that your backend expects.
            Based on the debug logs, the issue was field name mismatch.
        </div>
        
        <form id="emailForm">
            <div class="form-group">
                <label for="to">📧 To:</label>
                <input type="email" id="to" name="to" required placeholder="recipient@example.com">
            </div>
            
            <div class="form-group">
                <label for="cc">📄 CC (Optional):</label>
                <input type="email" id="cc" name="cc" placeholder="cc@example.com">
            </div>
            
            <div class="form-group">
                <label for="bcc">🔒 BCC (Optional):</label>
                <input type="email" id="bcc" name="bcc" placeholder="bcc@example.com">
            </div>
            
            <div class="form-group">
                <label for="subject">📝 Subject:</label>
                <input type="text" id="subject" name="subject" required placeholder="Email Subject">
            </div>
            
            <div class="form-group">
                <label for="body">✉️ Message:</label>
                <textarea id="body" name="body" required placeholder="Email message..."></textarea>
            </div>
            
            <div class="form-group">
                <label for="importance">⭐ Importance:</label>
                <select id="importance" name="importance">
                    <option value="low">Low</option>
                    <option value="normal" selected>Normal</option>
                    <option value="high">High</option>
                </select>
            </div>
            
            <button type="submit" id="sendBtn">🚀 Send Real Email</button>
        </form>
        
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('emailForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const sendBtn = document.getElementById('sendBtn');
            const resultDiv = document.getElementById('result');
            
            sendBtn.disabled = true;
            sendBtn.textContent = '📤 Sending...';
            resultDiv.innerHTML = '<div class="result">⏳ Sending email...</div>';
            
            const formData = new FormData(this);
            const data = {
                to: formData.get('to'),
                subject: formData.get('subject'),
                body: formData.get('body'),
                importance: formData.get('importance')
            };
            
            // Add optional fields if present
            if (formData.get('cc')) data.cc = formData.get('cc');
            if (formData.get('bcc')) data.bcc = formData.get('bcc');
            
            console.log('Sending data with correct field names:', data);
            
            fetch('/api/email/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Response:', data);
                if (data.success) {
                    resultDiv.innerHTML = `
                        <div class="result success">
                            ✅ <strong>Email Sent Successfully!</strong><br>
                            📧 To: ${data.details.to}<br>
                            📝 Subject: "${data.details.subject}"<br>
                            📨 From: ${data.details.from}<br>
                            ⏰ Sent: ${new Date(data.details.sent_at).toLocaleString()}
                        </div>
                    `;
                    // Clear form on success
                    document.getElementById('emailForm').reset();
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
                        ❌ <strong>Network Error:</strong> ${error.message}
                    </div>
                `;
            })
            .finally(() => {
                sendBtn.disabled = false;
                sendBtn.textContent = '🚀 Send Real Email';
            });
        });
    </script>
</body>
</html>'''
    
    with open('working_email_test.html', 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print("✅ Created working_email_test.html")

def main():
    """Main function"""
    print("🔧 Fix Field Name Mismatch")
    print("=" * 25)
    print("🎯 ISSUE IDENTIFIED!")
    print("Field name mismatch: Form sends 'to_recipients[]', code expects 'to'")
    print()
    
    # Update routes with fix
    routes_updated = update_email_routes_with_fix()
    
    # Create working test
    create_working_email_test()
    
    if routes_updated:
        print(f"\n🎉 FIELD NAME MISMATCH FIXED!")
        print(f"=" * 29)
        print(f"🚀 Restart your app:")
        print(f"   python docker_run.py")
        
        print(f"\n✅ What was fixed:")
        print(f"   - Handles 'to_recipients[]' and 'to' field names")
        print(f"   - Handles 'cc_recipients[]' and 'cc' field names")
        print(f"   - Handles 'bcc_recipients[]' and 'bcc' field names")
        print(f"   - Flexible field name parsing")
        print(f"   - Better logging for debugging")
        
        print(f"\n🧪 Test the fix:")
        print(f"   1. Open working_email_test.html")
        print(f"   2. Fill out the form")
        print(f"   3. Should work without 400 error!")
        print(f"   4. Real email will be sent via Microsoft Graph")
        
        print(f"\n🎯 Expected result:")
        print(f"   - No more 400 error")
        print(f"   - Email sent successfully")
        print(f"   - Real email delivered to recipient")
        print(f"   - Success message with details")
        
        print(f"\n🎉 Your AI Email Assistant will be COMPLETE!")
        print(f"   ✅ Microsoft 365 sync (20 emails)")
        print(f"   ✅ AI email analysis")
        print(f"   ✅ Chat interface")
        print(f"   ✅ REAL email sending")
        
    else:
        print(f"\n❌ Fix failed")

if __name__ == "__main__":
    main()