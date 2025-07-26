"""
Email routes for AI Email Assistant
"""
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app, render_template
from app.models import db
from app.models.user import User
from app.models.email import Email
from app.models.chat import ChatMessage
from app.utils.auth_helpers import login_required

email_bp = Blueprint('email', __name__)

@email_bp.route('/sync', methods=['POST', 'GET'])
@login_required
def sync_emails():
    """Sync emails from Microsoft 365"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # For demo purposes, create some sample emails
        sample_emails = [
            {
                'graph_id': f'demo-email-{i}',
                'subject': f'Demo Email {i}: Important Business Matter',
                'sender_email': f'sender{i}@example.com',
                'sender_name': f'Demo Sender {i}',
                'body_text': f'This is the body content of demo email {i}. It contains important information about business matters and requires your attention.',
                'body_preview': f'Demo email {i} preview...',
                'importance': 'normal' if i % 3 != 0 else 'high',
                'is_read': i % 4 == 0,
                'received_date': datetime.utcnow()
            }
            for i in range(1, 21)  # Create 20 demo emails
        ]
        
        synced_count = 0
        
        for email_data in sample_emails:
            # Check if email already exists
            existing_email = Email.find_by_graph_id(email_data['graph_id'])
            if not existing_email:
                # Create new email
                new_email = Email(
                    user_id=user.id,
                    graph_id=email_data['graph_id'],
                    subject=email_data['subject'],
                    sender_email=email_data['sender_email'],
                    sender_name=email_data['sender_name'],
                    body_text=email_data['body_text'],
                    body_preview=email_data['body_preview'],
                    importance=email_data['importance'],
                    is_read=email_data['is_read'],
                    received_date=email_data['received_date']
                )
                db.session.add(new_email)
                synced_count += 1
        
        # Commit all new emails
        db.session.commit()
        
        # Update user sync info
        user.update_sync_info()
        
        current_app.logger.info(f"Synced {synced_count} emails for user {user.email}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully synced {synced_count} emails',
            'synced_count': synced_count,
            'total_emails': user.get_email_count()
        })
        
    except Exception as e:
        current_app.logger.error(f"Email sync error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/list', methods=['GET'])
@login_required
def list_emails():
    """Get list of user's emails"""
    try:
        user_id = session.get('user_id')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get emails
        emails = Email.get_user_emails(
            user_id=user_id,
            limit=per_page,
            offset=offset,
            unread_only=unread_only
        )
        
        # Convert to dict format
        email_list = [email.to_dict() for email in emails]
        
        return jsonify({
            'success': True,
            'emails': email_list,
            'page': page,
            'per_page': per_page,
            'total_emails': len(email_list)
        })
        
    except Exception as e:
        current_app.logger.error(f"List emails error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/<int:email_id>', methods=['GET'])
@login_required
def get_email(email_id):
    """Get specific email details"""
    try:
        user_id = session.get('user_id')
        
        # Get email and verify ownership
        email = Email.query.filter_by(id=email_id, user_id=user_id).first()
        if not email:
            return jsonify({'error': 'Email not found'}), 404
        
        # Get related emails
        related_emails = email.get_related_emails(limit=5)
        
        return jsonify({
            'success': True,
            'email': email.to_dict(include_body=True),
            'related_emails': [e.to_dict() for e in related_emails]
        })
        
    except Exception as e:
        current_app.logger.error(f"Get email error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/<int:email_id>/detail', methods=['GET'])
@login_required
def email_detail(email_id):
    """Show email detail page with chat interface"""
    try:
        user_id = session.get('user_id')
        
        # Get email and verify ownership
        email = Email.query.filter_by(id=email_id, user_id=user_id).first()
        if not email:
            return render_template('errors/404.html'), 404
        
        # Get user
        user = User.query.get(user_id)
        
        # Get related emails
        related_emails = email.get_related_emails(limit=5)
        
        # Get email-specific chat history
        chat_history = ChatMessage.get_email_specific_chat(user_id, email_id, limit=10)
        
        return render_template('email_detail.html',
                             email=email.to_dict(include_body=True),
                             user=user.to_dict(),
                             related_emails=[e.to_dict() for e in related_emails],
                             chat_history=[c.to_dict() for c in chat_history])
        
    except Exception as e:
        current_app.logger.error(f"Email detail page error: {e}")
        return render_template('errors/500.html'), 500

@email_bp.route('/<int:email_id>/mark-read', methods=['POST'])
@login_required
def mark_email_read(email_id):
    """Mark email as read"""
    try:
        user_id = session.get('user_id')
        
        # Get email and verify ownership
        email = Email.query.filter_by(id=email_id, user_id=user_id).first()
        if not email:
            return jsonify({'success': False, 'error': 'Email not found'}), 404
        
        # Mark as read
        email.mark_as_read()
        
        current_app.logger.info(f"Email {email_id} marked as read by user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Email marked as read',
            'email_id': email_id,
            'is_read': True
        })
        
    except Exception as e:
        current_app.logger.error(f"Mark read error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/<int:email_id>/mark-unread', methods=['POST'])
@login_required
def mark_email_unread(email_id):
    """Mark email as unread"""
    try:
        user_id = session.get('user_id')
        
        # Get email and verify ownership
        email = Email.query.filter_by(id=email_id, user_id=user_id).first()
        if not email:
            return jsonify({'success': False, 'error': 'Email not found'}), 404
        
        # Mark as unread
        email.mark_as_unread()
        
        current_app.logger.info(f"Email {email_id} marked as unread by user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Email marked as unread',
            'email_id': email_id,
            'is_read': False
        })
        
    except Exception as e:
        current_app.logger.error(f"Mark unread error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/<int:email_id>/chat', methods=['POST'])
@login_required
def email_chat(email_id):
    """Handle chat about specific email"""
    try:
        user_id = session.get('user_id')
        
        # Get email and verify ownership
        email = Email.query.filter_by(id=email_id, user_id=user_id).first()
        if not email:
            return jsonify({'success': False, 'error': 'Email not found'}), 404
        
        # Get user
        user = User.query.get(user_id)
        
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
        
        current_app.logger.info(f"Email chat for email {email_id}: {message[:50]}...")
        
        # Create email-specific AI response
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['summary', 'summarize', 'what is this about']):
            response = f"📧 **Email Summary**\n\n**From:** {email.sender_name or email.sender_email}\n**Subject:** {email.subject}\n**Date:** {email.received_date.strftime('%B %d, %Y at %I:%M %p') if email.received_date else 'Unknown'}\n\n"
            
            if email.body_text and len(email.body_text) > 100:
                preview = email.body_text[:300] + "..." if len(email.body_text) > 300 else email.body_text
                response += f"**Content Preview:** {preview}\n\n"
            
            if email.importance and email.importance != 'normal':
                response += f"**Priority:** {email.importance.title()}\n\n"
            
            response += "Is there anything specific about this email you'd like me to help you with?"
        
        elif any(word in message_lower for word in ['reply', 'respond', 'answer']):
            response = f"📝 **Reply Suggestions for '{email.subject}'**\n\n"
            response += f"**Replying to:** {email.sender_name} ({email.sender_email})\n\n"
            response += "Here are some reply options:\n\n"
            response += "• **Quick Reply:** 'Thank you for your email. I'll review this and get back to you.'\n"
            response += "• **Request More Info:** 'Thank you for reaching out. Could you provide more details about...'\n"
            response += "• **Schedule Meeting:** 'I'd like to discuss this further. Are you available for a call this week?'\n\n"
            response += "Would you like me to help you draft a specific response?"
        
        elif any(word in message_lower for word in ['action', 'todo', 'task', 'follow up']):
            response = f"📋 **Action Items from '{email.subject}'**\n\n"
            response += "Based on this email, here are potential action items:\n\n"
            response += "• Review the email content thoroughly\n"
            response += "• Respond to the sender within 24-48 hours\n"
            response += "• Follow up on any requests or questions mentioned\n"
            
            if email.importance == 'high':
                response += "• **HIGH PRIORITY** - This email was marked as important\n"
            
            response += "\nWould you like me to help you prioritize these tasks or draft a response?"
        
        elif any(word in message_lower for word in ['urgent', 'priority', 'important']):
            priority_level = "Normal"
            if email.importance == 'high':
                priority_level = "High"
            elif email.importance == 'low':
                priority_level = "Low"
            
            response = f"🎯 **Priority Assessment**\n\n"
            response += f"**Current Priority Level:** {priority_level}\n"
            response += f"**Received:** {email.received_date.strftime('%B %d, %Y at %I:%M %p') if email.received_date else 'Unknown'}\n"
            response += f"**Read Status:** {'Read' if email.is_read else 'Unread'}\n\n"
            
            if email.importance == 'high':
                response += "⚠️ This email was flagged as **high importance** by the sender.\n\n"
            
            response += "Based on the content and timing, I recommend reviewing this email and responding appropriately."
        
        else:
            response = f"I can help you with this email from {email.sender_name}. I can:\n\n"
            response += "• **Summarize** the email content\n"
            response += "• **Help you reply** with suggested responses\n"
            response += "• **Identify action items** that need follow-up\n"
            response += "• **Assess priority** and urgency\n"
            response += "• **Answer questions** about the sender or content\n\n"
            response += "What would you like me to help you with regarding this email?"
        
        # Create chat message record
        chat_message = ChatMessage.create_message(
            user_id=user_id,
            message=message,
            context_type='email',
            context_id=email_id,
            message_type='email_specific'
        )
        
        # Update with response
        chat_message.update_response(
            response=response,
            ai_model='email_assistant_v1',
            processing_time=0.1
        )
        
        return jsonify({
            'success': True,
            'response': response,
            'message_id': chat_message.id,
            'context': {
                'email_id': email_id,
                'email_subject': email.subject,
                'sender': email.sender_name or email.sender_email
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Email chat error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/search', methods=['GET'])
@login_required
def search_emails():
    """Search user's emails"""
    try:
        user_id = session.get('user_id')
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query required'}), 400
        
        # Simple search in subject and body text
        emails = Email.query.filter_by(user_id=user_id).filter(
            db.or_(
                Email.subject.contains(query),
                Email.body_text.contains(query),
                Email.sender_email.contains(query),
                Email.sender_name.contains(query)
            )
        ).order_by(Email.received_date.desc()).limit(limit).all()
        
        email_list = [email.to_dict() for email in emails]
        
        return jsonify({
            'success': True,
            'query': query,
            'results': len(email_list),
            'emails': email_list
        })
        
    except Exception as e:
        current_app.logger.error(f"Search emails error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/send', methods=['POST'])
@login_required
def send_email():
    """Send email (Demo version)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('to_recipients') or not data.get('subject'):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # For demo purposes, just return success
        current_app.logger.info(f"Demo email send: {data.get('subject')} to {data.get('to_recipients')}")
        
        return jsonify({
            'success': True,
            'message': 'Email sent successfully (Demo mode)',
            'message_id': f'demo-sent-{uuid.uuid4()}'
        })
        
    except Exception as e:
        current_app.logger.error(f"Send email error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/stats', methods=['GET'])
@login_required
def email_stats():
    """Get email statistics for user"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Calculate statistics
        total_emails = user.get_email_count()
        unread_emails = user.get_unread_email_count()
        
        # Get recent activity
        recent_emails = Email.get_user_emails(user_id, limit=5)
        
        stats = {
            'total_emails': total_emails,
            'unread_emails': unread_emails,
            'read_emails': total_emails - unread_emails,
            'last_sync': user.last_email_sync.isoformat() if user.last_email_sync else None,
            'recent_emails': [email.to_dict() for email in recent_emails]
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Email stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500