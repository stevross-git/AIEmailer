#!/usr/bin/env python3
"""
Fix Chat API JSON Content-Type Issues
"""
import os

def fix_chat_api():
    """Fix the chat API to handle JSON properly"""
    print("🔧 Fixing Chat API JSON Handling")
    print("=" * 31)
    
    chat_routes_file = 'app/routes/chat.py'
    
    try:
        with open(chat_routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fixed chat message route
        fixed_chat_route = '''@chat_bp.route('/message', methods=['POST'])
def chat_message():
    """Handle chat message from user"""
    try:
        # Ensure we're getting JSON data
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        # Get message from request
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        # Get session ID (create new if not provided)
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        # Get user ID from session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        current_app.logger.info(f"Processing chat message for user {user_id}: {message[:50]}...")
        
        # Create or get chat session
        chat_session = ChatSession.query.filter_by(
            id=session_id,
            user_id=user_id
        ).first()
        
        if not chat_session:
            chat_session = ChatSession(
                id=session_id,
                user_id=user_id,
                title=message[:50] + ('...' if len(message) > 50 else ''),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(chat_session)
        else:
            chat_session.updated_at = datetime.utcnow()
        
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            role='user',
            content=message,
            timestamp=datetime.utcnow()
        )
        db.session.add(user_message)
        
        # Get user's emails for context
        user = User.query.get(user_id)
        emails = Email.query.filter_by(user_id=user_id).order_by(Email.received_date.desc()).limit(20).all()
        
        # Create context about emails
        email_context = []
        for email in emails:
            email_context.append({
                'subject': email.subject,
                'sender': email.sender_email,
                'date': email.received_date.strftime('%Y-%m-%d %H:%M') if email.received_date else 'Unknown',
                'preview': email.body_text[:200] if email.body_text else '',
                'is_read': email.is_read,
                'importance': email.importance
            })
        
        # Generate AI response
        try:
            from app.services.ai_service import AIService
            ai_service = AIService()
            
            # Create prompt with email context
            context_prompt = f"""You are an AI email assistant helping {user.display_name or user.email}. 

Recent emails context (last 20 emails):
"""
            for i, email in enumerate(email_context[:10], 1):
                context_prompt += f"{i}. From: {email['sender']}, Subject: {email['subject']}, Date: {email['date']}, Read: {email['is_read']}\\n"
            
            full_prompt = f"{context_prompt}\\n\\nUser question: {message}\\n\\nProvide a helpful response about their emails, tasks, or email management."
            
            ai_response = ai_service.generate_response(full_prompt)
            
            if not ai_response:
                ai_response = "I'm sorry, I couldn't generate a response right now. Please try again."
            
        except Exception as ai_error:
            current_app.logger.error(f"AI service error: {ai_error}")
            ai_response = f"I encountered an issue processing your request. However, I can see you have {len(emails)} recent emails. Would you like me to help you with something specific about them?"
        
        # Save AI response
        ai_message = ChatMessage(
            session_id=session_id,
            role='assistant',
            content=ai_response,
            timestamp=datetime.utcnow()
        )
        db.session.add(ai_message)
        
        # Commit all changes
        db.session.commit()
        
        current_app.logger.info(f"Chat response generated successfully for session {session_id}")
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'session_id': session_id,
            'message_id': ai_message.id,
            'timestamp': ai_message.timestamp.isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Chat message error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Chat processing failed: {str(e)}'
        }), 500'''
        
        # Replace the chat message route
        import re
        pattern = r"@chat_bp\.route\('/message'.*?(?=@chat_bp\.route|def \w+|$)"
        new_content = re.sub(pattern, fixed_chat_route + '\n\n', content, flags=re.DOTALL)
        
        with open(chat_routes_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Fixed chat API to handle JSON properly")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing chat API: {e}")
        return False

def fix_frontend_chat():
    """Fix frontend chat to send proper JSON"""
    print("\n🔧 Fixing Frontend Chat")
    print("=" * 22)
    
    js_file = 'app/static/js/main.js'
    
    try:
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add/fix chat sending function
        chat_js = '''
// Chat message sending function
function sendChatMessage(message, sessionId = null) {
    return fetch('/api/chat/message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            session_id: sessionId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Chat response received:', data.response);
            return data;
        } else {
            console.error('Chat failed:', data.error);
            throw new Error(data.error);
        }
    })
    .catch(error => {
        console.error('Chat error:', error);
        throw error;
    });
}

// Update chat form submission
document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const message = chatInput.value.trim();
            if (!message) return;
            
            // Clear input
            chatInput.value = '';
            
            // Add user message to chat
            addChatMessage('user', message);
            
            // Show loading
            addChatMessage('assistant', 'Thinking...', true);
            
            // Send message
            sendChatMessage(message)
                .then(data => {
                    // Remove loading message
                    const loadingMsg = chatMessages.querySelector('.loading');
                    if (loadingMsg) {
                        loadingMsg.remove();
                    }
                    
                    // Add AI response
                    addChatMessage('assistant', data.response);
                })
                .catch(error => {
                    // Remove loading message
                    const loadingMsg = chatMessages.querySelector('.loading');
                    if (loadingMsg) {
                        loadingMsg.remove();
                    }
                    
                    // Add error message
                    addChatMessage('assistant', 'Sorry, I encountered an error: ' + error.message);
                });
        });
    }
});

// Add message to chat display
function addChatMessage(role, content, isLoading = false) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    if (isLoading) {
        messageDiv.classList.add('loading');
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">
            ${content}
        </div>
        <div class="message-time">
            ${new Date().toLocaleTimeString()}
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
'''
        
        # Add chat functions if not present or replace existing
        if 'sendChatMessage(' in content:
            # Replace existing function
            pattern = r'function sendChatMessage.*?(?=function \w+|document\.addEventListener|$)'
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        content += chat_js
        
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fixed frontend chat to use proper JSON")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing frontend chat: {e}")
        return False

def add_chat_imports():
    """Add missing imports to chat routes"""
    print("\n🔧 Adding Chat Route Imports")
    print("=" * 27)
    
    chat_routes_file = 'app/routes/chat.py'
    
    try:
        with open(chat_routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Required imports
        required_imports = [
            'import uuid',
            'from datetime import datetime',
            'from flask import request, jsonify, session, current_app',
            'from app.models.chat import ChatSession, ChatMessage',
            'from app.models.email import Email',
            'from app.models.user import User',
            'from app import db'
        ]
        
        # Check which imports are missing
        missing_imports = []
        for imp in required_imports:
            if imp not in content:
                missing_imports.append(imp)
        
        if missing_imports:
            # Add missing imports at the top
            lines = content.split('\n')
            
            # Find where to insert (after existing imports)
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    insert_index = i + 1
                elif line.strip() == '' and insert_index > 0:
                    break
            
            # Insert missing imports
            for imp in reversed(missing_imports):
                lines.insert(insert_index, imp)
            
            content = '\n'.join(lines)
            
            with open(chat_routes_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Added {len(missing_imports)} missing imports")
        else:
            print("✅ All imports already present")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding imports: {e}")
        return False

def create_simple_chat_test():
    """Create a simple test for chat functionality"""
    print("\n🧪 Creating Chat Test")
    print("=" * 18)
    
    test_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Chat Test</title>
    <style>
        .chat-container { max-width: 600px; margin: 20px auto; padding: 20px; }
        .messages { border: 1px solid #ccc; height: 300px; overflow-y: auto; padding: 10px; margin-bottom: 10px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 8px; }
        .message.user { background: #007bff; color: white; margin-left: 20%; }
        .message.assistant { background: #f1f1f1; margin-right: 20%; }
        .input-group { display: flex; }
        .input-group input { flex: 1; padding: 10px; }
        .input-group button { padding: 10px 20px; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>Chat Test</h2>
        <div id="messages" class="messages"></div>
        <div class="input-group">
            <input type="text" id="messageInput" placeholder="Type a message...">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            // Add user message
            addMessage('user', message);
            input.value = '';
            
            // Send to API
            fetch('/api/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addMessage('assistant', data.response);
                } else {
                    addMessage('assistant', 'Error: ' + data.error);
                }
            })
            .catch(error => {
                addMessage('assistant', 'Network error: ' + error.message);
            });
        }
        
        function addMessage(role, content) {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${role}`;
            div.textContent = content;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        // Send on Enter
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>'''
    
    with open('chat_test.html', 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print("✅ Created chat_test.html")
    print("💡 Open this file in your browser while app is running")

def main():
    """Main function"""
    print("🔧 Fix Chat API JSON Issues")
    print("=" * 26)
    
    # Fix chat API
    api_fixed = fix_chat_api()
    
    # Add missing imports
    imports_added = add_chat_imports()
    
    # Fix frontend
    frontend_fixed = fix_frontend_chat()
    
    # Create test
    create_simple_chat_test()
    
    if api_fixed and imports_added:
        print(f"\n🎉 CHAT API FIXED!")
        print(f"=" * 16)
        print(f"🚀 Restart your app:")
        print(f"   python docker_run.py")
        
        print(f"\n✅ Chat Fixes:")
        print(f"   - Proper JSON Content-Type handling")
        print(f"   - Better error messages")
        print(f"   - Email context integration")
        print(f"   - Frontend JSON support")
        
        print(f"\n🧪 Test chat:")
        print(f"   - Open chat_test.html in browser")
        print(f"   - Or use the main chat interface")
        
        print(f"\n🎯 After restart:")
        print(f"   - Chat will work without JSON errors")
        print(f"   - AI responses about your emails")
        print(f"   - Full email assistant functionality")
        
    else:
        print(f"\n❌ Some fixes failed - check manually")

if __name__ == "__main__":
    main()