"""
Chat routes for AI Email Assistant
"""
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app
from app.models import db
from app.models.user import User
from app.models.email import Email
from app.models.chat import ChatMessage
from app.utils.auth_helpers import login_required

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/message', methods=['POST'])
@login_required
def chat_message():
    """Handle general chat message from user"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 401
        
        # Get message from request
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        current_app.logger.info(f"Chat message from user {user_id}: {message[:50]}...")
        
        # Generate AI response based on message content
        start_time = time.time()
        response = generate_ai_response(message, user)
        processing_time = time.time() - start_time
        
        # Create chat message record
        chat_message = ChatMessage.create_message(
            user_id=user_id,
            message=message,
            message_type='general'
        )
        
        # Update with response
        chat_message.update_response(
            response=response,
            ai_model='ai_email_assistant_v1',
            processing_time=processing_time
        )
        
        return jsonify({
            'success': True,
            'response': response,
            'message_id': chat_message.id,
            'processing_time': round(processing_time, 3)
        })
        
    except Exception as e:
        current_app.logger.error(f"Chat message error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@chat_bp.route('/history', methods=['GET'])
@login_required
def chat_history():
    """Get chat history for user"""
    try:
        user_id = session.get('user_id')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Get chat history
        messages = ChatMessage.get_user_chat_history(user_id, limit=limit, offset=offset)
        
        # Convert to dict format
        history = [message.to_dict() for message in messages]
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
        
    except Exception as e:
        current_app.logger.error(f"Chat history error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@chat_bp.route('/clear', methods=['POST'])
@login_required
def clear_chat():
    """Clear chat history for user"""
    try:
        user_id = session.get('user_id')
        
        # Delete all chat messages for user
        ChatMessage.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
        current_app.logger.info(f"Cleared chat history for user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Chat history cleared successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Clear chat error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_ai_response(message, user):
    """Generate AI response based on user message and context"""
    try:
        message_lower = message.lower()
        
        # Greeting responses
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return f"Hello {user.display_name or 'there'}! I'm your AI email assistant. I can help you manage your emails, analyze your inbox, prioritize tasks, and much more. What would you like me to help you with today?"
        
        # Email-related queries
        elif any(word in message_lower for word in ['email', 'emails', 'inbox']):
            email_count = user.get_email_count()
            unread_count = user.get_unread_email_count()
            
            response = f"📧 **Your Email Overview**\n\n"
            response += f"• **Total emails:** {email_count}\n"
            response += f"• **Unread emails:** {unread_count}\n"
            response += f"• **Last sync:** {user.last_email_sync.strftime('%B %d, %Y at %I:%M %p') if user.last_email_sync else 'Never'}\n\n"
            
            if unread_count > 0:
                response += f"You have {unread_count} unread emails that might need your attention. "
            
            response += "I can help you:\n"
            response += "• Analyze and prioritize your emails\n"
            response += "• Summarize important messages\n"
            response += "• Draft replies and responses\n"
            response += "• Find specific emails or information\n"
            response += "• Organize your inbox\n\n"
            response += "What would you like me to help you with regarding your emails?"
            
            return response
        
        # Urgent/priority queries
        elif any(word in message_lower for word in ['urgent', 'priority', 'important', 'critical']):
            # Get high priority emails
            high_priority_emails = Email.query.filter_by(
                user_id=user.id, 
                importance='high'
            ).order_by(Email.received_date.desc()).limit(5).all()
            
            response = "🚨 **Priority & Urgent Emails**\n\n"
            
            if high_priority_emails:
                response += f"I found {len(high_priority_emails)} high-priority emails:\n\n"
                for email in high_priority_emails:
                    status = "📭 Unread" if not email.is_read else "📬 Read"
                    response += f"• **{email.subject[:50]}...** from {email.sender_name or email.sender_email} {status}\n"
                
                response += "\nWould you like me to summarize any of these or help you prioritize your response?"
            else:
                response += "No high-priority emails found in your recent messages. "
                response += "However, I can help you review your unread emails to identify anything that might need immediate attention.\n\n"
                response += "Would you like me to analyze your unread emails for urgency?"
            
            return response
        
        # Summary queries
        elif any(word in message_lower for word in ['summary', 'summarize', 'overview', 'digest']):
            recent_emails = Email.get_user_emails(user.id, limit=10)
            unread_emails = [e for e in recent_emails if not e.is_read]
            
            response = "📊 **Email Summary & Digest**\n\n"
            response += f"**Recent Activity:**\n"
            response += f"• {len(recent_emails)} recent emails\n"
            response += f"• {len(unread_emails)} unread messages\n\n"
            
            if unread_emails:
                response += "**Unread Messages:**\n"
                for email in unread_emails[:5]:
                    priority_icon = "🔴" if email.importance == 'high' else "🟡" if email.importance == 'normal' else "🟢"
                    response += f"{priority_icon} **{email.subject[:40]}...** from {email.sender_name or email.sender_email}\n"
                
                if len(unread_emails) > 5:
                    response += f"... and {len(unread_emails) - 5} more unread emails\n"
            
            response += "\nWould you like me to provide detailed summaries of any specific emails or help you prioritize your responses?"
            
            return response
        
        # Unread emails query
        elif any(word in message_lower for word in ['unread', 'new messages', 'new emails']):
            unread_emails = Email.query.filter_by(
                user_id=user.id, 
                is_read=False
            ).order_by(Email.received_date.desc()).limit(10).all()
            
            response = "📬 **Unread Emails**\n\n"
            
            if unread_emails:
                response += f"You have {len(unread_emails)} unread emails:\n\n"
                for email in unread_emails:
                    priority_icon = "🔴" if email.importance == 'high' else "🟡"
                    date_str = email.received_date.strftime('%m/%d %I:%M %p') if email.received_date else 'Unknown'
                    response += f"{priority_icon} **{email.subject[:45]}...**\n"
                    response += f"   From: {email.sender_name or email.sender_email}\n"
                    response += f"   Date: {date_str}\n\n"
                
                response += "Would you like me to:\n"
                response += "• Summarize any of these emails\n"
                response += "• Help you prioritize which to read first\n"
                response += "• Draft responses to any messages\n"
                response += "• Mark some as read if they're not important"
            else:
                response += "Great news! You're all caught up - no unread emails. 🎉\n\n"
                response += "I can still help you with:\n"
                response += "• Organizing your existing emails\n"
                response += "• Finding specific messages\n"
                response += "• Drafting new emails\n"
                response += "• Setting up email management strategies"
            
            return response
        
        # Search/find queries
        elif any(word in message_lower for word in ['find', 'search', 'look for', 'locate']):
            response = "🔍 **Email Search & Discovery**\n\n"
            response += "I can help you find emails by:\n\n"
            response += "• **Sender:** Find emails from specific people\n"
            response += "• **Subject:** Search email subjects and titles\n"
            response += "• **Content:** Look through email body text\n"
            response += "• **Date range:** Find emails from specific time periods\n"
            response += "• **Keywords:** Search for specific terms or topics\n"
            response += "• **Attachments:** Find emails with files\n\n"
            response += "What are you looking for? You can say something like:\n"
            response += "• 'Find emails from John Smith'\n"
            response += "• 'Search for emails about project Alpha'\n"
            response += "• 'Show me emails from last week'"
            
            return response
        
        # Help/assistance queries
        elif any(word in message_lower for word in ['help', 'what can you do', 'assist', 'support']):
            response = "🤖 **AI Email Assistant Capabilities**\n\n"
            response += "I'm here to help you manage your emails efficiently! Here's what I can do:\n\n"
            
            response += "**📧 Email Management:**\n"
            response += "• Sync and organize your Microsoft 365 emails\n"
            response += "• Prioritize messages by importance and urgency\n"
            response += "• Mark emails as read/unread\n"
            response += "• Search and filter your inbox\n\n"
            
            response += "**🧠 AI Analysis:**\n"
            response += "• Summarize email content and key points\n"
            response += "• Identify action items and follow-ups\n"
            response += "• Analyze email sentiment and tone\n"
            response += "• Extract important information and contacts\n\n"
            
            response += "**✍️ Writing Assistance:**\n"
            response += "• Draft professional email responses\n"
            response += "• Suggest reply templates\n"
            response += "• Help with email composition\n"
            response += "• Improve email tone and clarity\n\n"
            
            response += "**📊 Productivity:**\n"
            response += "• Provide inbox overviews and statistics\n"
            response += "• Track email response times\n"
            response += "• Organize emails by categories\n"
            response += "• Create daily email digests\n\n"
            
            response += "Just ask me anything about your emails or type a specific request!"
            
            return response
        
        # Compose/write queries
        elif any(word in message_lower for word in ['compose', 'write', 'draft', 'create email']):
            response = "✍️ **Email Composition Assistant**\n\n"
            response += "I can help you write effective emails! Here's how:\n\n"
            
            response += "**📝 Email Types I Can Help With:**\n"
            response += "• Professional business emails\n"
            response += "• Follow-up messages\n"
            response += "• Meeting requests and invitations\n"
            response += "• Thank you and appreciation emails\n"
            response += "• Apology and clarification messages\n"
            response += "• Project updates and status reports\n\n"
            
            response += "**🎯 To get started, tell me:**\n"
            response += "• Who you're writing to\n"
            response += "• The purpose of the email\n"
            response += "• Key points you want to include\n"
            response += "• The tone you want (formal, casual, friendly)\n\n"
            
            response += "For example: 'Help me write a follow-up email to Sarah about the marketing project meeting'"
            
            return response
        
        # Generic/conversation responses
        else:
            response = f"I understand you're asking about: '{message[:50]}...'\n\n"
            response += "I'm your AI email assistant, and I specialize in helping with email-related tasks. I can:\n\n"
            response += "• 📧 **Manage your emails** - sync, organize, and prioritize\n"
            response += "• 🔍 **Search and find** specific messages or information\n"
            response += "• 📊 **Analyze and summarize** email content\n"
            response += "• ✍️ **Help write responses** and compose new emails\n"
            response += "• 🎯 **Prioritize tasks** and identify urgent messages\n\n"
            
            email_count = user.get_email_count()
            unread_count = user.get_unread_email_count()
            
            if email_count > 0:
                response += f"You currently have {email_count} emails with {unread_count} unread. "
            
            response += "How can I help you with your email management today?"
            
            return response
        
    except Exception as e:
        current_app.logger.error(f"AI response generation error: {e}")
        return "I apologize, but I encountered an error processing your request. Please try asking again, or let me know if you need help with a specific email task."

@chat_bp.route('/quick-actions', methods=['GET'])
@login_required  
def quick_actions():
    """Get quick action suggestions based on user's current email state"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        unread_count = user.get_unread_email_count()
        total_count = user.get_email_count()
        
        actions = []
        
        if unread_count > 0:
            actions.append({
                'action': 'summarize_unread',
                'title': f'Summarize {unread_count} unread emails',
                'description': 'Get a quick overview of your unread messages',
                'icon': '📬'
            })
            
        if unread_count > 5:
            actions.append({
                'action': 'prioritize_inbox',
                'title': 'Prioritize my inbox',
                'description': 'Identify which emails need attention first',
                'icon': '🎯'
            })
            
        actions.extend([
            {
                'action': 'find_urgent',
                'title': 'Find urgent emails',
                'description': 'Show me high-priority messages',
                'icon': '🚨'
            },
            {
                'action': 'compose_help',
                'title': 'Help me write an email',
                'description': 'Get assistance composing a new message',
                'icon': '✍️'
            },
            {
                'action': 'inbox_overview',
                'title': 'Inbox overview',
                'description': 'Get statistics and recent activity summary',
                'icon': '📊'
            }
        ])
        
        return jsonify({
            'success': True,
            'actions': actions,
            'user_stats': {
                'total_emails': total_count,
                'unread_emails': unread_count
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Quick actions error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500