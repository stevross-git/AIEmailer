#!/usr/bin/env python3
"""
Fix Chat Syntax Error
"""
import os

def create_clean_chat_routes():
    """Create a clean chat routes file without syntax errors"""
    print("🔧 Creating Clean Chat Routes")
    print("=" * 28)
    
    clean_chat_routes = '''"""
Chat routes for AI Email Assistant
"""
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app, render_template
from app.models.chat import ChatSession, ChatMessage
from app.models.email import Email
from app.models.user import User
from app import db

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('/message', methods=['POST'])
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
            context_prompt = f"You are an AI email assistant helping {user.display_name or user.email}.\\n\\nRecent emails context (last 20 emails):\\n"
            
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
        }), 500

@chat_bp.route('/sessions', methods=['GET'])
def get_chat_sessions():
    """Get chat sessions for current user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.updated_at.desc()).all()
        
        session_list = []
        for s in sessions:
            session_list.append({
                'id': s.id,
                'title': s.title,
                'created_at': s.created_at.isoformat(),
                'updated_at': s.updated_at.isoformat(),
                'message_count': len(s.messages) if hasattr(s, 'messages') else 0
            })
        
        return jsonify({
            'success': True,
            'sessions': session_list
        })
        
    except Exception as e:
        current_app.logger.error(f"Get sessions error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@chat_bp.route('/sessions/<session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    """Get messages for a specific chat session"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        # Verify session belongs to user
        chat_session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
        if not chat_session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()
        
        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            })
        
        return jsonify({
            'success': True,
            'messages': message_list
        })
        
    except Exception as e:
        current_app.logger.error(f"Get messages error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@chat_bp.route('/suggestions', methods=['GET'])
def get_chat_suggestions():
    """Get suggested chat prompts based on user's emails"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        # Get user's recent emails
        emails = Email.query.filter_by(user_id=user_id).order_by(Email.received_date.desc()).limit(10).all()
        
        suggestions = [
            "Summarize my unread emails",
            "What emails need my immediate attention?",
            "Show me emails from this week",
            "Help me prioritize my inbox"
        ]
        
        # Add dynamic suggestions based on emails
        if emails:
            unread_count = sum(1 for email in emails if not email.is_read)
            if unread_count > 0:
                suggestions.insert(0, f"I have {unread_count} unread emails - what should I focus on?")
            
            # Add sender-specific suggestions
            common_senders = {}
            for email in emails:
                sender = email.sender_email
                if sender:
                    common_senders[sender] = common_senders.get(sender, 0) + 1
            
            if common_senders:
                top_sender = max(common_senders.items(), key=lambda x: x[1])[0]
                suggestions.append(f"Show me emails from {top_sender}")
        
        return jsonify({
            'success': True,
            'suggestions': suggestions[:5]  # Limit to 5 suggestions
        })
        
    except Exception as e:
        current_app.logger.error(f"Get suggestions error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@chat_bp.route('/stats', methods=['GET'])
def get_chat_stats():
    """Get chat statistics for current user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Please sign in first'}), 401
        
        session_count = ChatSession.query.filter_by(user_id=user_id).count()
        message_count = ChatMessage.query.join(ChatSession).filter(ChatSession.user_id == user_id).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_sessions': session_count,
                'total_messages': message_count
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Get stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
'''
    
    # Write the clean chat routes
    chat_file = 'app/routes/chat.py'
    
    try:
        with open(chat_file, 'w', encoding='utf-8') as f:
            f.write(clean_chat_routes)
        
        print("✅ Created clean chat routes without syntax errors")
        return True
        
    except Exception as e:
        print(f"❌ Error creating clean chat routes: {e}")
        return False

def verify_chat_file():
    """Verify the chat file has no syntax errors"""
    print("\n🔍 Verifying Chat File Syntax")
    print("=" * 29)
    
    chat_file = 'app/routes/chat.py'
    
    try:
        with open(chat_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to compile the code to check for syntax errors
        compile(content, chat_file, 'exec')
        print("✅ Chat file has valid Python syntax")
        
        # Check for required routes
        required_routes = ['/message', '/sessions', '/suggestions', '/stats']
        found_routes = []
        
        for route in required_routes:
            if f"'{route}'" in content:
                found_routes.append(route)
                print(f"✅ Route {route} found")
            else:
                print(f"❌ Route {route} missing")
        
        return len(found_routes) == len(required_routes)
        
    except SyntaxError as e:
        print(f"❌ Syntax error in chat.py: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Error verifying chat file: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Fix Chat Syntax Error")
    print("=" * 22)
    
    # Create clean chat routes
    routes_created = create_clean_chat_routes()
    
    # Verify the file
    if routes_created:
        file_valid = verify_chat_file()
        
        if file_valid:
            print(f"\n🎉 CHAT SYNTAX FIXED!")
            print(f"=" * 19)
            print(f"🚀 Restart your app:")
            print(f"   python docker_run.py")
            
            print(f"\n✅ Chat routes created:")
            print(f"   - /api/chat/message - Send chat messages")
            print(f"   - /api/chat/sessions - Get chat sessions")
            print(f"   - /api/chat/suggestions - Get chat suggestions")
            print(f"   - /api/chat/stats - Get chat statistics")
            
            print(f"\n🎯 After restart:")
            print(f"   - Chat will work without JSON errors")
            print(f"   - No more syntax errors")
            print(f"   - AI responses about your emails")
            print(f"   - Full chat functionality")
            
        else:
            print(f"\n⚠️ File created but has issues - check manually")
    else:
        print(f"\n❌ Could not create clean chat routes")

if __name__ == "__main__":
    main()