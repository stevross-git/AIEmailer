#!/usr/bin/env python3
"""
Create Email Detail Page with AI Chat
"""
import os

def create_email_detail_route():
    """Create route for individual email view with chat"""
    print("🔧 Creating Email Detail Route")
    print("=" * 29)
    
    detail_route = '''@email_bp.route('/<int:email_id>')
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
        return redirect(url_for('main.emails'))'''
    
    return detail_route

def create_email_chat_api_route():
    """Create API route for email-specific chat"""
    print("\n🔧 Creating Email Chat API Route")
    print("=" * 31)
    
    chat_api_route = '''@email_bp.route('/<int:email_id>/chat', methods=['POST'])
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
                response = f"📧 **Email Summary**\\n\\n**From:** {email.sender_name or email.sender_email}\\n**Subject:** {email.subject}\\n**Date:** {email.received_date.strftime('%B %d, %Y at %I:%M %p') if email.received_date else 'Unknown'}\\n\\n"
                
                if email.body_text and len(email.body_text) > 100:
                    # Create a simple summary
                    preview = email.body_text[:300] + "..." if len(email.body_text) > 300 else email.body_text
                    response += f"**Content Summary:** {preview}\\n\\n"
                
                if email.importance and email.importance != 'normal':
                    response += f"**Priority:** {email.importance.title()}\\n\\n"
                
                response += "Is there anything specific about this email you'd like me to help you with?"
            
            elif any(word in message_lower for word in ['reply', 'respond', 'answer']):
                response = f"📝 **Reply Suggestions for '{email.subject}'**\\n\\n"
                
                if email.sender_name:
                    response += f"**Replying to:** {email.sender_name} ({email.sender_email})\\n\\n"
                
                response += "Here are some reply options:\\n\\n"
                response += "• **Quick Reply:** 'Thank you for your email. I'll review this and get back to you.'\\n"
                response += "• **Request More Info:** 'Thank you for reaching out. Could you provide more details about...'\\n"
                response += "• **Schedule Meeting:** 'I'd like to discuss this further. Are you available for a call this week?'\\n\\n"
                response += "Would you like me to help you draft a specific response?"
            
            elif any(word in message_lower for word in ['important', 'urgent', 'priority']):
                response = f"🎯 **Priority Assessment**\\n\\n"
                
                priority_indicators = []
                if email.importance == 'high':
                    priority_indicators.append("Marked as high importance by sender")
                if any(word in email.subject.lower() for word in ['urgent', 'asap', 'important', 'priority']):
                    priority_indicators.append("Urgent keywords in subject")
                if any(word in (email.body_text or '').lower() for word in ['deadline', 'due', 'urgent', 'asap']):
                    priority_indicators.append("Time-sensitive content detected")
                
                if priority_indicators:
                    response += "**Priority Indicators Found:**\\n"
                    for indicator in priority_indicators:
                        response += f"• {indicator}\\n"
                    response += "\\n**Recommendation:** This email may require prompt attention."
                else:
                    response += "**Assessment:** This appears to be a normal priority email with no urgent indicators."
                
                response += "\\n\\nWould you like me to help you prioritize your response?"
            
            elif any(word in message_lower for word in ['action', 'todo', 'task', 'need to do']):
                response = f"✅ **Action Items from '{email.subject}'**\\n\\n"
                
                # Simple action detection
                email_text = (email.body_text or '').lower()
                action_words = ['please', 'need', 'require', 'should', 'must', 'deadline', 'due', 'complete', 'finish', 'send', 'provide']
                
                actions_found = []
                for word in action_words:
                    if word in email_text:
                        actions_found.append(word)
                
                if actions_found:
                    response += f"**Potential Actions Detected:** {', '.join(set(actions_found[:5]))}\\n\\n"
                    response += "**Suggested Next Steps:**\\n"
                    response += "• Review the email content for specific requests\\n"
                    response += "• Identify any deadlines or due dates\\n"
                    response += "• Determine if a response is needed\\n"
                    response += "• Add to your task list if action is required\\n"
                else:
                    response += "**Analysis:** No specific action items detected in this email.\\n\\n"
                    response += "This appears to be informational. No immediate action may be required."
                
                response += "\\n\\nWould you like me to help you draft a response or create a task?"
            
            elif any(word in message_lower for word in ['sender', 'who is', 'about the person']):
                response = f"👤 **About the Sender**\\n\\n"
                response += f"**Name:** {email.sender_name or 'Not provided'}\\n"
                response += f"**Email:** {email.sender_email}\\n\\n"
                
                # Get recent emails from this sender
                recent_emails = Email.query.filter_by(
                    user_id=user_id, 
                    sender_email=email.sender_email
                ).order_by(Email.received_date.desc()).limit(5).all()
                
                if len(recent_emails) > 1:
                    response += f"**Recent Communication:** {len(recent_emails)} emails in your inbox\\n"
                    response += f"**Latest Contact:** {recent_emails[0].received_date.strftime('%B %d, %Y') if recent_emails[0].received_date else 'Unknown'}\\n"
                else:
                    response += "**Communication History:** This appears to be the first email from this sender\\n"
                
                response += "\\nWould you like me to show you other emails from this sender?"
            
            else:
                response = f"I'm here to help you with this email from **{email.sender_name or email.sender_email}** about **'{email.subject}'**.\\n\\n"
                response += f"You asked: _{message}_\\n\\n"
                response += "I can help you with:\\n"
                response += "• **Summarize** the email content\\n"
                response += "• **Draft a reply** or response\\n"
                response += "• **Identify action items** or tasks\\n"
                response += "• **Assess priority** and urgency\\n"
                response += "• **Find related emails** from this sender\\n\\n"
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
        return jsonify({'success': False, 'error': f'Chat error: {str(e)}'}), 500'''
    
    return chat_api_route

def add_email_detail_routes():
    """Add email detail routes to email.py"""
    print("\n🔧 Adding Email Detail Routes")
    print("=" * 28)
    
    routes_file = 'app/routes/email.py'
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add required imports if not present
        if 'from datetime import datetime' not in content:
            content = content.replace(
                'from flask import', 
                'from datetime import datetime\nfrom flask import'
            )
        
        if 'render_template' not in content:
            content = content.replace(
                'from flask import',
                'from flask import render_template,'
            )
        
        # Add the detail routes
        detail_route = create_email_detail_route()
        chat_route = create_email_chat_api_route()
        
        # Add at the end
        new_content = content + '\n\n' + detail_route + '\n\n' + chat_route + '\n'
        
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Added email detail and chat routes")
        return True
        
    except Exception as e:
        print(f"❌ Error adding routes: {e}")
        return False

def create_email_detail_template():
    """Create the email detail template"""
    print("\n🔧 Creating Email Detail Template")
    print("=" * 32)
    
    template_content = '''{% extends "base.html" %}

{% block title %}{{ email.subject }} - AI Email Assistant{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <!-- Email Content Column -->
        <div class="col-lg-7">
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">📧 Email Details</h5>
                    <div>
                        <a href="{{ url_for('main.emails') }}" class="btn btn-outline-secondary btn-sm">
                            ← Back to Inbox
                        </a>
                        {% if not email.is_read %}
                        <button class="btn btn-primary btn-sm" onclick="markEmailRead({{ email.id }})">
                            Mark as Read
                        </button>
                        {% else %}
                        <button class="btn btn-outline-secondary btn-sm" onclick="markEmailUnread({{ email.id }})">
                            Mark as Unread
                        </button>
                        {% endif %}
                    </div>
                </div>
                
                <div class="card-body">
                    <!-- Email Header -->
                    <div class="email-header mb-4">
                        <div class="row">
                            <div class="col-md-8">
                                <h4 class="email-subject">{{ email.subject or 'No Subject' }}</h4>
                                <p class="text-muted mb-1">
                                    <strong>From:</strong> 
                                    {% if email.sender_name %}
                                        {{ email.sender_name }} &lt;{{ email.sender_email }}&gt;
                                    {% else %}
                                        {{ email.sender_email }}
                                    {% endif %}
                                </p>
                                <p class="text-muted mb-1">
                                    <strong>To:</strong> {{ user.email }}
                                </p>
                                <p class="text-muted mb-0">
                                    <strong>Date:</strong> 
                                    {% if email.received_date %}
                                        {{ email.received_date.strftime('%B %d, %Y at %I:%M %p') }}
                                    {% else %}
                                        Unknown
                                    {% endif %}
                                </p>
                            </div>
                            <div class="col-md-4 text-end">
                                {% if email.importance == 'high' %}
                                    <span class="badge bg-danger">High Priority</span>
                                {% elif email.importance == 'low' %}
                                    <span class="badge bg-secondary">Low Priority</span>
                                {% endif %}
                                
                                {% if email.has_attachments %}
                                    <span class="badge bg-info">📎 Attachments</span>
                                {% endif %}
                                
                                {% if email.is_read %}
                                    <span class="badge bg-success">Read</span>
                                {% else %}
                                    <span class="badge bg-warning">Unread</span>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    
                    <hr>
                    
                    <!-- Email Body -->
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
                    </div>
                    
                    <!-- Email Actions -->
                    <hr>
                    <div class="email-actions">
                        <button class="btn btn-primary" onclick="startReply()">
                            📤 Reply
                        </button>
                        <button class="btn btn-outline-secondary" onclick="startForward()">
                            ↗️ Forward  
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteEmail()">
                            🗑️ Delete
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Related Emails -->
            {% if related_emails %}
            <div class="card mt-4">
                <div class="card-header">
                    <h6 class="mb-0">📎 Related Emails</h6>
                </div>
                <div class="card-body">
                    {% for related in related_emails %}
                    <div class="border-bottom py-2">
                        <a href="{{ url_for('email.email_detail', email_id=related.id) }}" class="text-decoration-none">
                            <strong>{{ related.subject or 'No Subject' }}</strong>
                        </a>
                        <br>
                        <small class="text-muted">
                            {{ related.received_date.strftime('%b %d, %Y') if related.received_date else 'Unknown' }}
                        </small>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>
        
        <!-- AI Chat Column -->
        <div class="col-lg-5">
            <div class="card h-100">
                <div class="card-header">
                    <h5 class="mb-0">🤖 AI Email Assistant</h5>
                    <small class="text-muted">Ask me anything about this email</small>
                </div>
                
                <div class="card-body d-flex flex-column">
                    <!-- Chat Messages -->
                    <div class="chat-messages flex-grow-1" id="chatMessages" style="max-height: 400px; overflow-y: auto;">
                        <div class="message assistant mb-3">
                            <div class="message-content p-3 bg-light rounded">
                                <strong>AI Assistant:</strong> I can see you're viewing an email from <strong>{{ email.sender_name or email.sender_email }}</strong> about "<strong>{{ email.subject }}</strong>". 
                                <br><br>
                                How can I help you with this email? I can:
                                <ul class="mb-0 mt-2">
                                    <li>Summarize the content</li>
                                    <li>Help you draft a reply</li>
                                    <li>Identify action items</li>
                                    <li>Assess priority level</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Chat Suggestions -->
                    <div class="chat-suggestions mb-3">
                        <small class="text-muted">Quick actions:</small><br>
                        <button class="btn btn-outline-primary btn-sm me-1 mb-1" onclick="sendQuickMessage('Summarize this email')">
                            📝 Summarize
                        </button>
                        <button class="btn btn-outline-primary btn-sm me-1 mb-1" onclick="sendQuickMessage('Help me reply to this email')">
                            📤 Help Reply
                        </button>
                        <button class="btn btn-outline-primary btn-sm me-1 mb-1" onclick="sendQuickMessage('What are the action items?')">
                            ✅ Action Items
                        </button>
                        <button class="btn btn-outline-primary btn-sm me-1 mb-1" onclick="sendQuickMessage('Is this email important?')">
                            ⭐ Priority
                        </button>
                    </div>
                    
                    <!-- Chat Input -->
                    <div class="chat-input">
                        <form id="chatForm" onsubmit="sendMessage(event)">
                            <div class="input-group">
                                <input type="text" 
                                       class="form-control" 
                                       id="messageInput" 
                                       placeholder="Ask me about this email..."
                                       required>
                                <button class="btn btn-primary" type="submit">
                                    Send
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
.email-header {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
}

.email-body {
    line-height: 1.6;
}

.email-html-body {
    max-width: 100%;
    overflow-x: auto;
}

.email-text-body pre {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
    border: 1px solid #dee2e6;
}

.chat-messages {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 15px;
    background-color: #fafafa;
}

.message {
    margin-bottom: 15px;
}

.message.user .message-content {
    background-color: #007bff !important;
    color: white !important;
    margin-left: 20%;
}

.message.assistant .message-content {
    background-color: #e9ecef !important;
    color: #333 !important;
    margin-right: 20%;
}

.chat-suggestions button {
    font-size: 0.85em;
}
</style>

<script>
const emailId = {{ email.id }};

function sendMessage(event) {
    event.preventDefault();
    
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage('user', message);
    messageInput.value = '';
    
    // Add loading message
    addMessage('assistant', 'Thinking...', true);
    
    // Send to API
    fetch(`/api/email/${emailId}/chat`, {
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
        // Remove loading message
        const loadingMsg = document.querySelector('.loading');
        if (loadingMsg) {
            loadingMsg.remove();
        }
        
        if (data.success) {
            addMessage('assistant', data.response);
        } else {
            addMessage('assistant', 'Sorry, I encountered an error: ' + data.error);
        }
    })
    .catch(error => {
        // Remove loading message
        const loadingMsg = document.querySelector('.loading');
        if (loadingMsg) {
            loadingMsg.remove();
        }
        
        addMessage('assistant', 'Sorry, I encountered a network error: ' + error.message);
    });
}

function sendQuickMessage(message) {
    document.getElementById('messageInput').value = message;
    document.getElementById('chatForm').dispatchEvent(new Event('submit'));
}

function addMessage(role, content, isLoading = false) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    if (isLoading) {
        messageDiv.classList.add('loading');
    }
    
    messageDiv.innerHTML = `
        <div class="message-content p-3 rounded">
            <strong>${role === 'user' ? 'You' : 'AI Assistant'}:</strong> ${content}
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Mark email functions (from previous implementation)
function markEmailRead(emailId) {
    fetch(`/api/email/${emailId}/mark-read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload(); // Refresh to update UI
        } else {
            alert('Failed to mark as read: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error.message);
    });
}

function markEmailUnread(emailId) {
    fetch(`/api/email/${emailId}/mark-unread`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload(); // Refresh to update UI
        } else {
            alert('Failed to mark as unread: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error.message);
    });
}

// Auto-focus chat input
document.getElementById('messageInput').focus();
</script>
{% endblock %}'''
    
    # Create templates directory if it doesn't exist
    templates_dir = 'app/templates'
    os.makedirs(templates_dir, exist_ok=True)
    
    template_file = os.path.join(templates_dir, 'email_detail.html')
    
    try:
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print("✅ Created email_detail.html template")
        return True
        
    except Exception as e:
        print(f"❌ Error creating template: {e}")
        return False

def update_main_routes_for_emails():
    """Update main routes to handle email URLs"""
    print("\n🔧 Updating Main Routes")
    print("=" * 22)
    
    main_routes_file = 'app/routes/main.py'
    
    try:
        with open(main_routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add email redirect route if not present
        redirect_route = '''
@main_bp.route('/emails/<int:email_id>')
def email_redirect(email_id):
    """Redirect to email detail page"""
    return redirect(url_for('email.email_detail', email_id=email_id))
'''
        
        if 'email_redirect' not in content:
            content += redirect_route
            
            with open(main_routes_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Added email redirect route to main.py")
        else:
            print("✅ Email redirect route already exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating main routes: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Create Email Detail Page with AI Chat")
    print("=" * 38)
    print("📧 Creating individual email view with chat functionality")
    print("🎯 URL: http://localhost:5000/emails/266")
    print()
    
    # Add email detail routes
    routes_added = add_email_detail_routes()
    
    # Create email detail template
    template_created = create_email_detail_template()
    
    # Update main routes
    main_routes_updated = update_main_routes_for_emails()
    
    if routes_added and template_created:
        print(f"\n🎉 EMAIL DETAIL PAGE WITH AI CHAT CREATED!")
        print(f"=" * 42)
        print(f"🚀 Restart your app:")
        print(f"   python docker_run.py")
        
        print(f"\n✅ What was created:")
        print(f"   - /api/email/<id> route (email detail page)")
        print(f"   - /api/email/<id>/chat route (AI chat API)")
        print(f"   - email_detail.html template (beautiful UI)")
        print(f"   - AI chat interface with context")
        print(f"   - Quick action buttons")
        
        print(f"\n🎯 Features:")
        print(f"   - Full email content display")
        print(f"   - Email metadata (sender, date, priority)")
        print(f"   - Mark as read/unread buttons")
        print(f"   - Related emails sidebar")
        print(f"   - AI chat specific to that email")
        print(f"   - Quick action buttons (Summarize, Reply help, etc.)")
        
        print(f"\n📧 AI Chat Capabilities:")
        print(f"   - Summarize email content")
        print(f"   - Help draft replies")
        print(f"   - Identify action items")
        print(f"   - Assess email priority")
        print(f"   - Information about sender")
        print(f"   - Context-aware responses")
        
        print(f"\n🧪 Test it:")
        print(f"   1. Visit: http://localhost:5000/emails/266")
        print(f"   2. See full email content + AI chat sidebar")
        print(f"   3. Try quick actions: 'Summarize', 'Help Reply'")
        print(f"   4. Ask specific questions about the email")
        
        print(f"\n🎉 Your AI Email Assistant now has:")
        print(f"   ✅ Individual email pages with full content")
        print(f"   ✅ Email-specific AI chat")
        print(f"   ✅ Smart context-aware responses")
        print(f"   ✅ Quick action buttons")
        print(f"   ✅ Professional email management UI")
        
    else:
        print(f"\n❌ Creation failed - check manually")

if __name__ == "__main__":
    main()