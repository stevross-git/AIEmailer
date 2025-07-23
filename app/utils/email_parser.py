"""
Email Parsing Utilities for AI Email Assistant
"""
import re
import html
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
from email.utils import parseaddr, getaddresses
import markdownify

class EmailParser:
    """Utility class for parsing and processing email content"""
    
    @staticmethod
    def clean_html_content(html_content: str) -> str:
        """Clean HTML content and extract readable text"""
        if not html_content:
            return ""
        
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'meta', 'link', 'head']):
                element.decompose()
            
            # Convert to plain text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
            
            return clean_text
        
        except Exception as e:
            # Fallback: use raw content with HTML tags stripped
            return re.sub(r'<[^>]+>', '', html_content)
    
    @staticmethod
    def html_to_markdown(html_content: str) -> str:
        """Convert HTML email content to Markdown"""
        if not html_content:
            return ""
        
        try:
            # Use markdownify to convert HTML to Markdown
            markdown_content = markdownify.markdownify(
                html_content,
                heading_style="ATX",
                bullets="-",
                strip=['script', 'style']
            )
            
            # Clean up extra whitespace
            markdown_content = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_content)
            return markdown_content.strip()
        
        except Exception as e:
            # Fallback to plain text
            return EmailParser.clean_html_content(html_content)
    
    @staticmethod
    def extract_email_addresses(text: str) -> List[str]:
        """Extract email addresses from text"""
        if not text:
            return []
        
        # Email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Remove duplicates and return
        return list(set(emails))
    
    @staticmethod
    def parse_recipient_string(recipient_string: str) -> List[Dict[str, str]]:
        """Parse recipient string into structured format"""
        if not recipient_string:
            return []
        
        try:
            # Use email.utils to parse addresses
            addresses = getaddresses([recipient_string])
            
            recipients = []
            for name, email in addresses:
                if email:  # Only add if email is present
                    recipients.append({
                        'name': name.strip() if name else '',
                        'email': email.strip(),
                        'display': f"{name} <{email}>" if name else email
                    })
            
            return recipients
        
        except Exception as e:
            # Fallback: try to extract emails directly
            emails = EmailParser.extract_email_addresses(recipient_string)
            return [{'name': '', 'email': email, 'display': email} for email in emails]
    
    @staticmethod
    def extract_quoted_text(email_body: str) -> Tuple[str, str]:
        """Separate new content from quoted/forwarded content"""
        if not email_body:
            return "", ""
        
        # Common patterns for quoted text
        quote_patterns = [
            r'(?i)^\s*>.*$',  # Lines starting with >
            r'(?i)^On .* wrote:.*$',  # "On ... wrote:" pattern
            r'(?i)^From:.*$',  # Forward headers
            r'(?i)^-+\s*Original Message\s*-+.*$',  # Outlook forward
            r'(?i)^_{5,}.*$',  # Underline separators
        ]
        
        lines = email_body.split('\n')
        new_content_lines = []
        quoted_content_lines = []
        in_quoted_section = False
        
        for line in lines:
            # Check if this line starts a quoted section
            if not in_quoted_section:
                for pattern in quote_patterns:
                    if re.match(pattern, line):
                        in_quoted_section = True
                        break
            
            if in_quoted_section:
                quoted_content_lines.append(line)
            else:
                new_content_lines.append(line)
        
        new_content = '\n'.join(new_content_lines).strip()
        quoted_content = '\n'.join(quoted_content_lines).strip()
        
        return new_content, quoted_content
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from email content"""
        if not text:
            return []
        
        # URL regex pattern
        url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
        urls = re.findall(url_pattern, text)
        
        return list(set(urls))  # Remove duplicates
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """Extract phone numbers from email content"""
        if not text:
            return []
        
        # Phone number patterns
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
            r'\b\(\d{3}\)\s?\d{3}[-.]?\d{4}\b',  # (xxx) xxx-xxxx
            r'\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'  # International
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        
        return list(set(phones))  # Remove duplicates
    
    @staticmethod
    def extract_dates(text: str) -> List[str]:
        """Extract date mentions from email content"""
        if not text:
            return []
        
        # Date patterns
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # MM/DD/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',  # MM-DD-YYYY
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b',  # Month DD, YYYY
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b'  # DD Month YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return list(set(dates))  # Remove duplicates
    
    @staticmethod
    def detect_language(text: str) -> str:
        """Detect the language of email content (basic detection)"""
        if not text:
            return "unknown"
        
        # Simple language detection based on common words
        text_lower = text.lower()
        
        # English indicators
        english_words = ['the', 'and', 'you', 'that', 'was', 'for', 'are', 'with', 'his', 'they']
        english_count = sum(1 for word in english_words if word in text_lower)
        
        # Spanish indicators
        spanish_words = ['que', 'por', 'con', 'una', 'los', 'del', 'las', 'para', 'por', 'como']
        spanish_count = sum(1 for word in spanish_words if word in text_lower)
        
        # French indicators
        french_words = ['que', 'dans', 'pour', 'avec', 'sur', 'par', 'mais', 'ses', 'vous', 'comme']
        french_count = sum(1 for word in french_words if word in text_lower)
        
        # German indicators
        german_words = ['der', 'und', 'die', 'von', 'den', 'mit', 'auf', 'für', 'ist', 'das']
        german_count = sum(1 for word in german_words if word in text_lower)
        
        # Determine language based on highest count
        counts = {
            'english': english_count,
            'spanish': spanish_count,
            'french': french_count,
            'german': german_count
        }
        
        detected_language = max(counts, key=counts.get)
        return detected_language if counts[detected_language] > 0 else "unknown"
    
    @staticmethod
    def extract_signatures(email_body: str) -> Tuple[str, str]:
        """Separate email body from signature"""
        if not email_body:
            return "", ""
        
        # Common signature separators
        signature_patterns = [
            r'^\s*--\s*$',  # Standard -- separator
            r'^\s*_{3,}\s*$',  # Underline separator
            r'^\s*Best regards?\s*,?\s*$',  # Best regards
            r'^\s*Sincerely\s*,?\s*$',  # Sincerely
            r'^\s*Thanks?\s*,?\s*$',  # Thanks
            r'^\s*Sent from my .*$',  # Mobile signatures
        ]
        
        lines = email_body.split('\n')
        body_lines = []
        signature_lines = []
        signature_started = False
        
        for i, line in enumerate(lines):
            if not signature_started:
                # Check if this line starts a signature
                for pattern in signature_patterns:
                    if re.match(pattern, line, re.IGNORECASE):
                        signature_started = True
                        signature_lines.append(line)
                        break
                
                if not signature_started:
                    body_lines.append(line)
            else:
                signature_lines.append(line)
        
        body = '\n'.join(body_lines).strip()
        signature = '\n'.join(signature_lines).strip()
        
        return body, signature
    
    @staticmethod
    def calculate_reading_time(text: str) -> int:
        """Calculate estimated reading time in minutes"""
        if not text:
            return 0
        
        # Average reading speed: 200-250 words per minute
        words = len(text.split())
        reading_time = max(1, round(words / 225))  # Round up, minimum 1 minute
        
        return reading_time
    
    @staticmethod
    def get_text_stats(text: str) -> Dict[str, int]:
        """Get statistics about text content"""
        if not text:
            return {
                'characters': 0,
                'words': 0,
                'sentences': 0,
                'paragraphs': 0,
                'reading_time_minutes': 0
            }
        
        # Character count
        char_count = len(text)
        
        # Word count
        words = text.split()
        word_count = len(words)
        
        # Sentence count (approximate)
        sentence_count = len(re.findall(r'[.!?]+', text))
        
        # Paragraph count
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # Reading time
        reading_time = EmailParser.calculate_reading_time(text)
        
        return {
            'characters': char_count,
            'words': word_count,
            'sentences': sentence_count,
            'paragraphs': paragraph_count,
            'reading_time_minutes': reading_time
        }