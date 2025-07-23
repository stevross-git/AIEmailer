#!/usr/bin/env python3
"""
Debug the 400 Error in Email Send with Detailed Logging
"""
import os

def create_debug_email_send_route():
    """Create email send route with extensive debugging"""
    print("🔧 Creating Debug Email Send Route")
    print("=" * 32)
    
    debug_route = '''@email_bp.route('/send', methods=['POST'])
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
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
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
        current_app.logger.info("=== EMAIL SEND DEBUG END ===")'''
    
    return debug_route

def add_debug_imports():
    """Add imports needed for debugging"""
    print("\n🔧 Adding Debug Imports")
    print("=" * 21)
    
    routes_file = 'app/routes/email.py'
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Required imports
        required_imports = [
            'import re',
            'import traceback',
            'from datetime import datetime',
            'from app.utils.auth_helpers import decrypt_token',
            'from app.services.ms_graph import GraphService',
        ]
        
        # Check and add missing imports
        missing_imports = []
        for imp in required_imports:
            if imp not in content:
                missing_imports.append(imp)
        
        if missing_imports:
            lines = content.split('\n')
            insert_index = 0
            
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    insert_index = i + 1
            
            for imp in reversed(missing_imports):
                lines.insert(insert_index, imp)
            
            content = '\n'.join(lines)
            
            with open(routes_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Added {len(missing_imports)} debug imports")
        else:
            print("✅ All imports already present")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding imports: {e}")
        return False

def update_routes_with_debug():
    """Update routes with debug version"""
    print("\n🔧 Updating Routes with Debug Version")
    print("=" * 36)
    
    routes_file = 'app/routes/email.py'
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        debug_route = create_debug_email_send_route()
        
        # Replace send route
        import re
        pattern = r"@email_bp\.route\('/send'.*?(?=@email_bp\.route|def \w+(?:\(|\s)|$)"
        
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, debug_route + '\n\n', content, flags=re.DOTALL)
        else:
            new_content = content + '\n\n' + debug_route + '\n'
        
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Updated routes with debug version")
        return True
        
    except Exception as e:
        print(f"❌ Error updating routes: {e}")
        return False

def create_simple_test():
    """Create a simple test to isolate the issue"""
    print("\n🧪 Creating Simple Test")
    print("=" * 22)
    
    test_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Simple Email Debug Test</title>
    <style>
        body { font-family: Arial; max-width: 500px; margin: 50px auto; padding: 20px; }
        input, textarea { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ccc; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        .result { margin-top: 20px; padding: 10px; border-radius: 4px; }
        .error { background: #f8d7da; color: #721c24; }
        .success { background: #d4edda; color: #155724; }
        .debug { background: #f8f9fa; color: #6c757d; font-family: monospace; font-size: 12px; white-space: pre-wrap; }
    </style>
</head>
<body>
    <h2>🔍 Email Send Debug Test</h2>
    
    <form id="testForm">
        <input type="email" id="to" placeholder="To: email@example.com" required>
        <input type="text" id="subject" placeholder="Subject" required>
        <textarea id="body" placeholder="Message body" required></textarea>
        <button type="submit">🚀 Send Test Email</button>
    </form>
    
    <div id="result"></div>

    <script>
        document.getElementById('testForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '<div class="result">⏳ Sending...</div>';
            
            const data = {
                to: document.getElementById('to').value,
                subject: document.getElementById('subject').value,
                body: document.getElementById('body').value
            };
            
            console.log('Sending data:', data);
            
            fetch('/api/email/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                console.log('Response status:', response.status);
                console.log('Response headers:', response.headers);
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                if (data.success) {
                    resultDiv.innerHTML = `
                        <div class="result success">✅ ${data.message}</div>
                        <div class="debug">Debug: ${JSON.stringify(data.details, null, 2)}</div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="result error">❌ ${data.error}</div>
                    `;
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                resultDiv.innerHTML = `
                    <div class="result error">❌ Network error: ${error.message}</div>
                `;
            });
        });
    </script>
</body>
</html>'''
    
    with open('debug_email_test.html', 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print("✅ Created debug_email_test.html")

def main():
    """Main function"""
    print("🔍 Debug Email Send 400 Error with Detailed Logging")
    print("=" * 49)
    
    # Add debug imports
    imports_added = add_debug_imports()
    
    # Update with debug route
    routes_updated = update_routes_with_debug()
    
    # Create simple test
    create_simple_test()
    
    if imports_added and routes_updated:
        print(f"\n🎉 DEBUG VERSION CREATED!")
        print(f"=" * 24)
        print(f"🚀 Restart your app:")
        print(f"   python docker_run.py")
        
        print(f"\n✅ Debug features added:")
        print(f"   - Extensive logging of request details")
        print(f"   - Step-by-step validation logging")
        print(f"   - Detailed error messages")
        print(f"   - Request content-type analysis")
        print(f"   - Token validation logging")
        
        print(f"\n🧪 Test with debug:")
        print(f"   1. Open debug_email_test.html")
        print(f"   2. Fill out simple form")
        print(f"   3. Watch console logs for detailed debugging")
        print(f"   4. Logs will show exactly where the 400 error occurs")
        
        print(f"\n🔍 What to look for in logs:")
        print(f"   - Request content type")
        print(f"   - JSON/form data parsing")
        print(f"   - Field validation results")
        print(f"   - Token validation")
        print(f"   - Microsoft Graph API calls")
        
    else:
        print(f"\n❌ Debug setup failed")

if __name__ == "__main__":
    main()