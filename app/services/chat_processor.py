"""
Chat Processing Service for AI Email Assistant
"""
import re
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from flask import current_app
from app.models.user import User
from app.models.email import Email, EmailThread
from app.models.chat import ChatMessage
from app.services.ollama_engine import OllamaService
from app.services.email_processor import EmailProcessor
from app import db

class ChatProcessor:
    """Service for processing chat messages and generating AI responses"""
    
    def __init__(self):
        self.ollama_service = OllamaService()
        self.email_processor = EmailProcessor()
    
    def process_message(self, user_id: int, message: str, context_type: str = 'general', 
                       context_data: Dict = None, session_id: str = None) -> Dict:
        """Process a chat message and generate AI response"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'text': 'User not found', 'error': 'User not found'}
            
            # Analyze message intent
            intent = self._analyze_message_intent(message)
            
            # Get relevant context based on intent and user's emails
            context = self._get_relevant_context(user_id, message, intent, context_data)
            
            # Build system prompt based on intent
            system_prompt = self._build_system_prompt(intent, user)
            
            # Generate response
            response = self._generate_ai_response(message, context, system_prompt)
            
            # Add suggestions and related emails
            suggestions = self._generate_suggestions(intent, user_id)
            related_emails = self._find_related_emails(user_id, message, intent)
            
            return {
                'text': response['text'],
                'model_used': response.get('model_used'),
                'token_count': response.get('token_count'),
                'intent': intent,
                'context': {
                    'type': context_type,
                    'data': context_data or {},
                    'email_context': bool(context)
                },
                'suggestions': suggestions,
                'related_emails': [email.to_dict() for email in related_emails[:5]],
                'response_time_ms': response.get('response_time_ms')
            }
        
        except Exception as e:
            current_app.logger.error(f"Error processing chat message: {e}")
            return {
                'text': "I'm sorry, I encountered an error while processing your request. Please try again.",
                'error': str(e)
            }
    
    def _analyze_message_intent(self, message: str) -> str:
        """Analyze the intent of the user's message"""
        message_lower = message.lower()
        
        # Email management intents
        if any(word in message_lower for word in ['summarize', 'summary', 'overview']):
            if any(word in message_lower for word in ['unread', 'inbox', 'emails']):
                return 'summarize_emails'
            elif any(word in message_lower for word in ['thread', 'conversation']):
                return 'summarize_thread'
            else:
                return 'summarize_emails'
        
        elif any(word in message_lower for word in ['find', 'search', 'look for', 'show me']):
            return 'search_emails'
        
        elif any(word in message_lower for word in ['draft', 'write', 'compose', 'create email']):
            return 'draft_email'
        
        elif any(word in message_lower for word in ['reply', 'respond to', 'answer']):
            return 'suggest_reply'
        
        elif any(word in message_lower for word in ['organize', 'sort', 'categorize', 'clean up']):
            return 'organize_emails'
        
        elif any(word in message_lower for word in ['follow up', 'followup', 'remind']):
            return 'follow_up'
        
        elif any(word in message_lower for word in ['statistics', 'stats', 'analytics', 'patterns']):
            return 'email_analytics'
        
        elif any(word in message_lower for word in ['important', 'priority', 'urgent']):
            return 'priority_emails'
        
        elif any(word in message_lower for word in ['schedule', 'calendar', 'meeting']):
            return 'calendar_related'
        
        else:
            return 'general_query'
    
    def _get_relevant_context(self, user_id: int, message: str, intent: str, context_data: Dict = None) -> str:
        """Get relevant context for the user's message"""
        try:
            context_parts = []
            
            # Add specific context based on intent
            if intent in ['summarize_emails', 'search_emails', 'priority_emails']:
                # Get recent emails context
                if hasattr(current_app, 'vector_service'):
                    email_context = current_app.vector_service.get_user_email_context(
                        user_id=user_id,
                        query=message,
                        limit=5
                    )
                    if email_context:
                        context_parts.append(f"Relevant emails:\n{email_context}")
            
            elif intent == 'summarize_thread' and context_data and context_data.get('thread_id'):
                # Get specific thread context
                thread_id = context_data['thread_id']
                thread_emails = Email.query.filter_by(
                    user_id=user_id,
                    thread_id=thread_id
                ).order_by(Email.received_date).all()
                
                if thread_emails:
                    thread_context = []
                    for email in thread_emails:
                        thread_context.append(f"From: {email.sender_name}\nSubject: {email.subject}\nContent: {email.body_preview[:200]}")
                    context_parts.append(f"Thread emails:\n{'---'.join(thread_context)}")
            
            elif intent == 'suggest_reply' and context_data and context_data.get('email_id'):
                # Get specific email context for reply
                email_id = context_data['email_id']
                email = Email.query.filter_by(id=email_id, user_id=user_id).first()
                if email:
                    context_parts.append(f"Original email to reply to:\nFrom: {email.sender_name}\nSubject: {email.subject}\nContent: {email.body_preview}")
            
            # Add general user context
            user = User.query.get(user_id)
            if user:
                user_context = f"User: {user.display_name} ({user.email})"
                if user.job_title:
                    user_context += f", {user.job_title}"
                context_parts.append(user_context)
            
            return '\n\n'.join(context_parts)
        
        except Exception as e:
            current_app.logger.error(f"Error getting relevant context: {e}")
            return ""
    
    def _build_system_prompt(self, intent: str, user: User) -> str:
        """Build system prompt based on message intent"""
        base_prompt = f"""You are an AI assistant helping {user.display_name} manage their emails. 
        You have access to their email data and can help with various email-related tasks.
        Be helpful, professional, and concise in your responses."""
        
        intent_prompts = {
            'summarize_emails': f"{base_prompt} Focus on providing clear, organized summaries of emails. Highlight key information, action items, and important dates.",
            
            'search_emails': f"{base_prompt} Help find relevant emails based on the user's search criteria. Provide specific matches and explain why they're relevant.",
            
            'draft_email': f"{base_prompt} Help compose professional emails. Consider the recipient, purpose, and appropriate tone. Provide a complete draft with proper structure.",
            
            'suggest_reply': f"{base_prompt} Suggest appropriate email replies. Consider the original message context and maintain professional communication style.",
            
            'organize_emails': f"{base_prompt} Provide suggestions for organizing emails efficiently. Consider folder structures, rules, and best practices.",
            
            'follow_up': f"{base_prompt} Help with follow-up strategies. Identify emails that need responses and suggest appropriate follow-up actions.",
            
            'email_analytics': f"{base_prompt} Provide insights into email patterns, productivity metrics, and communication analytics. Present data in a clear, actionable format.",
            
            'priority_emails': f"{base_prompt} Help identify and prioritize important emails. Focus on urgency, sender importance, and content relevance.",
            
            'calendar_related': f"{base_prompt} Help with calendar and meeting-related email tasks. Consider scheduling, invitations, and time management.",
            
            'general_query': f"{base_prompt} Answer general questions about email management and provide helpful advice."
        }
        
        return intent_prompts.get(intent, base_prompt)
    
    def _generate_ai_response(self, message: str, context: str, system_prompt: str) -> Dict:
        """Generate AI response using Ollama"""
        try:
            # Build full prompt with context
            full_message = message
            if context:
                full_message = f"Context:\n{context}\n\nUser question: {message}"
            
            response = self.ollama_service.generate_response(
                prompt=full_message,
                system_prompt=system_prompt
            )
            
            return response
        
        except Exception as e:
            current_app.logger.error(f"Error generating AI response: {e}")
            return {
                'text': "I'm sorry, I'm having trouble generating a response right now. Please try again.",
                'error': str(e)
            }
    
    def _generate_suggestions(self, intent: str, user_id: int) -> List[str]:
        """Generate follow-up suggestions based on intent"""
        try:
            suggestions = []
            
            if intent == 'summarize_emails':
                suggestions = [
                    "Show me the most urgent emails",
                    "Find emails from last week",
                    "Help me organize my inbox"
                ]
            
            elif intent == 'search_emails':
                suggestions = [
                    "Search for emails about projects",
                    "Find emails from specific people",
                    "Show me emails with attachments"
                ]
            
            elif intent == 'draft_email':
                suggestions = [
                    "Help me write a follow-up email",
                    "Draft a meeting request",
                    "Compose a professional introduction"
                ]
            
            elif intent == 'suggest_reply':
                suggestions = [
                    "Draft a different tone reply",
                    "Suggest a meeting time",
                    "Help with a polite decline"
                ]
            
            elif intent == 'email_analytics':
                suggestions = [
                    "Show me my top email contacts",
                    "Analyze my response time patterns",
                    "Compare this month to last month"
                ]
            
            else:
                # Get recent unread emails for general suggestions
                unread_count = Email.query.filter_by(user_id=user_id, is_read=False).count()
                if unread_count > 0:
                    suggestions.append(f"You have {unread_count} unread emails")
                
                suggestions.extend([
                    "Summarize my recent emails",
                    "Help me organize my inbox",
                    "Find important emails I might have missed"
                ])
            
            return suggestions[:3]  # Limit to 3 suggestions
        
        except Exception as e:
            current_app.logger.error(f"Error generating suggestions: {e}")
            return []
    
    def _find_related_emails(self, user_id: int, message: str, intent: str) -> List[Email]:
        """Find emails related to the user's message"""
        try:
            if intent in ['general_query', 'draft_email']:
                return []
            
            # Use vector search if available
            if hasattr(current_app, 'vector_service'):
                search_results = current_app.vector_service.search_emails(
                    user_id=user_id,
                    query=message,
                    limit=10
                )
                
                if search_results:
                    email_ids = [result['email_id'] for result in search_results if result.get('email_id')]
                    emails = Email.query.filter(
                        Email.id.in_(email_ids),
                        Email.user_id == user_id
                    ).all()
                    return emails
            
            # Fallback to basic text search
            return Email.search_emails(user_id, message, limit=5)
        
        except Exception as e:
            current_app.logger.error(f"Error finding related emails: {e}")
            return []
    
    def handle_email_command(self, user_id: int, command: str, email_id: int = None, **kwargs) -> Dict:
        """Handle specific email commands"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            if command == 'summarize_email' and email_id:
                email = Email.query.filter_by(id=email_id, user_id=user_id).first()
                if not email:
                    return {'success': False, 'error': 'Email not found'}
                
                system_prompt = "Provide a concise summary of this email, highlighting key points and any action items."
                response = self.ollama_service.generate_response(
                    prompt=f"Email from {email.sender_name}: {email.subject}\n\n{email.body_preview}",
                    system_prompt=system_prompt
                )
                
                return {
                    'success': True,
                    'summary': response.get('text', 'Could not generate summary'),
                    'email': email.to_dict()
                }
            
            elif command == 'suggest_reply' and email_id:
                email = Email.query.filter_by(id=email_id, user_id=user_id).first()
                if not email:
                    return {'success': False, 'error': 'Email not found'}
                
                reply_suggestion = self.email_processor.suggest_email_reply(email)
                
                return {
                    'success': True,
                    'reply_suggestion': reply_suggestion,
                    'original_email': email.to_dict()
                }
            
            elif command == 'draft_email':
                recipient = kwargs.get('recipient', '')
                purpose = kwargs.get('purpose', '')
                context = kwargs.get('context', '')
                tone = kwargs.get('tone', 'professional')
                
                draft = self.email_processor.generate_email_draft(
                    context=context,
                    recipient=recipient,
                    purpose=purpose,
                    tone=tone
                )
                
                return {
                    'success': True,
                    'draft': draft,
                    'parameters': {
                        'recipient': recipient,
                        'purpose': purpose,
                        'tone': tone
                    }
                }
            
            elif command == 'analyze_patterns':
                days = kwargs.get('days', 30)
                analysis = self.email_processor.analyze_email_patterns(user_id, days)
                
                return {
                    'success': True,
                    'analysis': analysis
                }
            
            else:
                return {'success': False, 'error': f'Unknown command: {command}'}
        
        except Exception as e:
            current_app.logger.error(f"Error handling email command: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_conversation_context(self, session_id: str, limit: int = 5) -> str:
        """Get conversation context from previous messages"""
        try:
            messages = ChatMessage.get_session_messages(session_id)
            recent_messages = messages[-limit:] if messages else []
            
            context_parts = []
            for msg in recent_messages:
                if msg.message and msg.response:
                    context_parts.append(f"User: {msg.message}")
                    context_parts.append(f"Assistant: {msg.response}")
            
            return '\n'.join(context_parts) if context_parts else ""
        
        except Exception as e:
            current_app.logger.error(f"Error getting conversation context: {e}")
            return ""