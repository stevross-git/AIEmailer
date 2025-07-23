#!/usr/bin/env python3
"""
Check Email Content in Database
"""
import os
import sys

def check_email_content():
    """Check email content in database"""
    print("🔍 Checking Email Content in Database")
    print("=" * 35)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        from app import create_app
        from app.models.email import Email
        
        app = create_app()
        
        with app.app_context():
            # Get email 267
            email = Email.query.filter_by(id=267).first()
            
            if email:
                print(f"✅ Found email {email.id}")
                print(f"Subject: {email.subject}")
                print(f"Sender: {email.sender_email}")
                print(f"Body Text: {repr(email.body_text)}")
                print(f"Body HTML: {repr(email.body_html)}")
                print(f"Body Preview: {repr(email.body_preview)}")
                print(f"Message ID: {email.message_id}")
                
                # Check if any content exists
                has_content = any([
                    email.body_text and len(email.body_text.strip()) > 0,
                    email.body_html and len(email.body_html.strip()) > 0,
                    email.body_preview and len(email.body_preview.strip()) > 0
                ])
                
                print(f"\nHas Content: {has_content}")
                
                if not has_content:
                    print("\n❌ No email content found!")
                    print("The email sync is not capturing email body content.")
                    print("We need to fix the Microsoft Graph email fetching.")
                else:
                    print("\n✅ Email content exists in database!")
                    
            else:
                print("❌ Email 267 not found")
                
                # Check what emails we do have
                emails = Email.query.limit(5).all()
                print(f"\nFound {len(emails)} emails:")
                for e in emails:
                    print(f"  {e.id}: {e.subject} (body_text: {len(e.body_text or '')} chars)")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_email_content()
