"""
Email Processing Service for AI Email Assistant
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import re
from bs4 import BeautifulSoup
from flask import current_app
from app.models.email import Email, EmailThread
from app.models.user import User
from app.services.ms_graph import GraphService
from app.services.ollama_engine import OllamaService
from app import db

class EmailProcessor:
    """Service for processing and analyzing emails"""
    
    def __init__(self):
        self.ollama_service = OllamaService()
    
    def sync_user_emails(self, user: User, graph_service: GraphService, access_token: str, 
                        folder: str = 'inbox', limit: int = 50, force_refresh: bool = False) -> Dict:
        """Sync emails from Microsoft Graph for a user"""
        try:
            result = {
                'synced_count': 0,
                'new_count': 0,
                'updated_count': 0,
                'errors': []
            }
            
            # Get emails from Microsoft Graph
            emails_data = graph_service.get_emails(
                access_token=access_token,
                folder=folder,
                limit=limit
            )
            
            if not emails_data or 'value' not in emails_data:
                current_app.logger.warning(f"No emails retrieved for user {user.id}")
                return result
            
            emails_to_embed = []  # For batch vector database operations
            
            for email_data in emails_data['value']:
                try:
                    # Process individual email
                    email, is_new = self._process_email_data(user, email_data, folder, force_refresh)
                    
                    if email:
                        result['synced_count'] += 1
                        if is_new:
                            result['new_count'] += 1
                            # Add to embedding queue if it's a sent item or configured for indexing
                            if (email.is_sent_item and current_app.config.get('INDEX_SENT_ITEMS', True)) or \
                               (not email.is_sent_item and current_app.config.get('INDEX_INBOX', True)):
                                emails_to_embed.append((email.id, email.to_dict(include_body=True), user.id))
                        else:
                            result['updated_count'] += 1
                
                except Exception as e:
                    current_app.logger.error(f"Error processing email {email_data.get('id', 'unknown')}: {e}")
                    result['errors'].append(str(e))
            
            # Batch add to vector database
            if emails_to_embed and hasattr(current_app, 'vector_service'):
                try:
                    embedded_count = current_app.vector_service.batch_add_emails(emails_to_embed)
                    current_app.logger.info(f"Added {embedded_count} emails to vector database")
                except Exception as e:
                    current_app.logger.error(f"Error adding emails to vector database: {e}")
            
            # Update email threads
            self._update_email_threads(user.id)
            
            return result
        
        except Exception as e:
            current_app.logger.error(f"Email sync error for user {user.id}: {e}")
            return {'synced_count': 0, 'new_count': 0, 'updated_count': 0, 'errors': [str(e)]}
    
    def _process_email_data(self, user: User, email_data: Dict, folder: str, force_refresh: bool = False) -> Tuple[Optional[Email], bool]:
        """Process individual email data from Microsoft Graph"""
        try:
            message_id = email_data.get('id')
            if not message_id:
                return None, False
            
            # Check if email already exists
            existing_email = Email.find_by_message_id(message_id)
            is_new = existing_email is None
            
            if existing_email and not force_refresh:
                return existing_email, False
            
            # Parse email data
            email_info = self._parse_email_data(email_data, folder)
            
            if is_new:
                # Create new email
                email = Email(
                    message_id=message_id,
                    user_id=user.id,
                    **email_info
                )
                db.session.add(email)
            else:
                # Update existing email
                for key, value in email_info.items():
                    setattr(existing_email, key, value)
                email = existing_email
            
            db.session.commit()
            
            # Generate AI analysis for new emails
            if is_new:
                self._analyze_email_with_ai(email)
            
            return email, is_new
        
        except Exception as e:
            current_app.logger.error(f"Error processing email data: {e}")
            db.session.rollback()
            return None, False
    
    def _parse_email_data(self, email_data: Dict, folder: str) -> Dict:
        """Parse email data from Microsoft Graph API response"""
        # Parse sender information
        sender = email_data.get('sender', {}).get('emailAddress', {})
        sender_email = sender.get('address', '')
        sender_name = sender.get('name', '')
        
        # Parse recipients
        def parse_recipients(recipients_data):
            if not recipients_data:
                return []
            return [{
                'emailAddress': {
                    'address': r.get('emailAddress', {}).get('address', ''),
                    'name': r.get('emailAddress', {}).get('name', '')
                }
            } for r in recipients_data]
        
        to_recipients = parse_recipients(email_data.get('toRecipients', []))
        cc_recipients = parse_recipients(email_data.get('ccRecipients', []))
        bcc_recipients = parse_recipients(email_data.get('bccRecipients', []))
        
        # Parse dates
        received_date = self._parse_date(email_data.get('receivedDateTime'))
        sent_date = self._parse_date(email_data.get('sentDateTime'))
        
        # Parse body content
        body = email_data.get('body', {})
        body_content = body.get('content', '')
        body_content_type = body.get('contentType', 'html').lower()
        
        # Clean body content if HTML
        if body_content_type == 'html':
            body_preview = self._extract_text_from_html(body_content)[:500]
        else:
            body_preview = body_content[:500]
        
        # Determine if this is a sent item
        is_sent_item = folder.lower() in ['sent', 'sentitems', 'sent items']
        
        return {
            'conversation_id': email_data.get('conversationId', ''),
            'subject': email_data.get('subject', ''),
            'sender_email': sender_email,
            'sender_name': sender_name,
            'to_recipients': to_recipients,
            'cc_recipients': cc_recipients,
            'bcc_recipients': bcc_recipients,
            'body_preview': body_preview,
            'body_content': body_content,
            'body_content_type': body_content_type,
            'received_date': received_date,
            'sent_date': sent_date,
            'importance': email_data.get('importance', 'normal').lower(),
            'is_read': email_data.get('isRead', False),
            'is_draft': email_data.get('isDraft', False),
            'is_sent_item': is_sent_item,
            'has_attachments': email_data.get('hasAttachments', False),
            'categories': email_data.get('categories', []),
            'folder_id': email_data.get('parentFolderId', ''),
            'folder_name': folder
        }
    
    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse date string from Microsoft Graph API"""
        if not date_string:
            return None
        
        try:
            # Parse ISO 8601 format
            if date_string.endswith('Z'):
                return datetime.fromisoformat(date_string[:-1]).replace(tzinfo=timezone.utc)
            else:
                return datetime.fromisoformat(date_string)
        except ValueError:
            current_app.logger.warning(f"Could not parse date: {date_string}")
            return None
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract plain text from HTML content"""
        try:
            if not html_content:
                return ""
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it up
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        
        except Exception as e:
            current_app.logger.error(f"Error extracting text from HTML: {e}")
            return html_content[:1000]  # Fallback to raw content
    
    def _analyze_email_with_ai(self, email: Email):
        """Analyze email with AI to generate tags, summary, and sentiment"""
        try:
            # Create analysis prompt
            email_text = f"""
            Subject: {email.subject}
            From: {email.sender_name} ({email.sender_email})
            Date: {email.received_date}
            Content: {email.body_preview}
            """
            
            system_prompt = """You are an AI assistant that analyzes emails. For each email, provide:
            1. A brief summary (1-2 sentences)
            2. 3-5 relevant tags/keywords
            3. Sentiment (positive, negative, or neutral)
            4. Priority score (1-10, where 10 is most urgent)
            
            Format your response as JSON with keys: summary, tags, sentiment, priority_score"""
            
            # Get AI analysis
            response = self.ollama_service.generate_response(
                prompt=f"Analyze this email:\n\n{email_text}",
                system_prompt=system_prompt
            )
            
            if response and 'text' in response:
                try:
                    # Try to parse JSON response
                    import json
                    analysis = json.loads(response['text'])
                    
                    # Update email with AI analysis
                    email.update_ai_analysis(
                        summary=analysis.get('summary'),
                        tags=analysis.get('tags', []),
                        sentiment=analysis.get('sentiment'),
                        priority_score=analysis.get('priority_score')
                    )
                    
                except json.JSONDecodeError:
                    # Fallback to basic analysis
                    self._basic_email_analysis(email, response['text'])
        
        except Exception as e:
            current_app.logger.error(f"Error analyzing email with AI: {e}")
            # Fallback to basic analysis
            self._basic_email_analysis(email)
    
    def _basic_email_analysis(self, email: Email, ai_response: str = None):
        """Basic email analysis without AI parsing"""
        try:
            # Simple keyword extraction
            text = f"{email.subject} {email.body_preview}".lower()
            
            # Basic tags based on keywords
            tags = []
            if any(word in text for word in ['urgent', 'asap', 'immediately', 'critical']):
                tags.append('urgent')
            if any(word in text for word in ['meeting', 'call', 'schedule', 'calendar']):
                tags.append('meeting')
            if any(word in text for word in ['project', 'task', 'deadline', 'deliverable']):
                tags.append('project')
            if any(word in text for word in ['invoice', 'payment', 'bill', 'cost']):
                tags.append('financial')
            if any(word in text for word in ['report', 'analysis', 'data', 'results']):
                tags.append('report')
            
            # Basic sentiment analysis
            sentiment = 'neutral'
            if any(word in text for word in ['thank', 'great', 'excellent', 'good', 'happy']):
                sentiment = 'positive'
            elif any(word in text for word in ['problem', 'issue', 'error', 'wrong', 'bad']):
                sentiment = 'negative'
            
            # Basic priority scoring
            priority_score = 5  # Default medium priority
            if any(word in text for word in ['urgent', 'asap', 'critical', 'immediate']):
                priority_score = 8
            elif any(word in text for word in ['fyi', 'info', 'notification']):
                priority_score = 3
            
            # Use AI response as summary if available
            summary = ai_response[:200] if ai_response else f"Email from {email.sender_name} about {email.subject}"
            
            email.update_ai_analysis(
                summary=summary,
                tags=tags,
                sentiment=sentiment,
                priority_score=priority_score
            )
        
        except Exception as e:
            current_app.logger.error(f"Error in basic email analysis: {e}")
    
    def _update_email_threads(self, user_id: int):
        """Update email threads for a user"""
        try:
            # Get all emails without thread assignment
            unthreaded_emails = Email.query.filter_by(
                user_id=user_id,
                thread_id=None
            ).filter(Email.conversation_id.isnot(None)).all()
            
            for email in unthreaded_emails:
                if not email.conversation_id:
                    continue
                
                # Find or create thread
                thread = EmailThread.find_by_conversation_id(email.conversation_id)
                
                if not thread:
                    # Create new thread
                    thread = EmailThread(
                        conversation_id=email.conversation_id,
                        subject=email.subject
                    )
                    db.session.add(thread)
                    db.session.flush()  # Get thread ID
                
                # Assign email to thread
                email.thread_id = thread.id
            
            db.session.commit()
            
            # Update thread statistics
            threads_to_update = EmailThread.query.join(Email).filter(
                Email.user_id == user_id
            ).distinct().all()
            
            for thread in threads_to_update:
                thread.update_thread_stats()
        
        except Exception as e:
            current_app.logger.error(f"Error updating email threads: {e}")
            db.session.rollback()
    
    def generate_email_draft(self, context: str, recipient: str, purpose: str, tone: str = 'professional') -> str:
        """Generate email draft using AI"""
        try:
            system_prompt = f"""You are an AI assistant that helps draft professional emails. 
            Generate a well-structured email with appropriate greeting, body, and closing.
            Tone should be {tone}. Do not include subject line."""
            
            prompt = f"""
            Draft an email for the following:
            Recipient: {recipient}
            Purpose: {purpose}
            Context: {context}
            
            Please write a complete email body.
            """
            
            response = self.ollama_service.generate_response(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            if response and 'text' in response:
                return response['text'].strip()
            else:
                return "I'm sorry, I couldn't generate an email draft at this time."
        
        except Exception as e:
            current_app.logger.error(f"Error generating email draft: {e}")
            return "Error generating email draft. Please try again."
    
    def suggest_email_reply(self, original_email: Email, reply_type: str = 'standard') -> str:
        """Suggest a reply to an email"""
        try:
            # Create context from original email
            context = f"""
            Original Email:
            From: {original_email.sender_name} ({original_email.sender_email})
            Subject: {original_email.subject}
            Content: {original_email.body_preview}
            Date: {original_email.received_date}
            """
            
            system_prompt = f"""You are an AI assistant that helps draft email replies. 
            Generate an appropriate reply based on the original email content.
            Reply type: {reply_type}
            Keep the response professional and concise."""
            
            prompt = f"Generate a suitable reply to this email:\n\n{context}"
            
            response = self.ollama_service.generate_response(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            if response and 'text' in response:
                return response['text'].strip()
            else:
                return "Thank you for your email. I'll get back to you soon."
        
        except Exception as e:
            current_app.logger.error(f"Error suggesting email reply: {e}")
            return "Thank you for your email. I'll review it and respond accordingly."
    
    def analyze_email_patterns(self, user_id: int, days: int = 30) -> Dict:
        """Analyze email patterns for a user"""
        try:
            from datetime import timedelta
            
            # Get emails from the last N days
            since_date = datetime.utcnow() - timedelta(days=days)
            
            emails = Email.query.filter(
                Email.user_id == user_id,
                Email.received_date >= since_date
            ).all()
            
            if not emails:
                return {'error': 'No emails found for analysis'}
            
            # Basic statistics
            total_emails = len(emails)
            unread_emails = sum(1 for email in emails if not email.is_read)
            sent_emails = sum(1 for email in emails if email.is_sent_item)
            
            # Top senders
            sender_counts = {}
            for email in emails:
                if not email.is_sent_item:  # Only count received emails
                    sender = email.sender_email
                    sender_counts[sender] = sender_counts.get(sender, 0) + 1
            
            top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Sentiment distribution
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
            for email in emails:
                sentiment = email.ai_sentiment or 'neutral'
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            
            # Priority distribution
            priority_scores = [email.ai_priority_score for email in emails if email.ai_priority_score]
            avg_priority = sum(priority_scores) / len(priority_scores) if priority_scores else 5
            
            return {
                'period_days': days,
                'total_emails': total_emails,
                'unread_emails': unread_emails,
                'sent_emails': sent_emails,
                'received_emails': total_emails - sent_emails,
                'unread_percentage': (unread_emails / total_emails * 100) if total_emails > 0 else 0,
                'top_senders': top_senders,
                'sentiment_distribution': sentiment_counts,
                'average_priority': round(avg_priority, 2),
                'emails_per_day': round(total_emails / days, 2)
            }
        
        except Exception as e:
            current_app.logger.error(f"Error analyzing email patterns: {e}")
            return {'error': str(e)}