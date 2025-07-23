#!/usr/bin/env python3
"""
Fix Email Sync Issue
"""
import os
import sys
sys.path.append('.')
os.environ['USE_DOCKER_CONFIG'] = 'true'

from app import create_app, db
from app.models.user import User
from app.models.email import Email
from datetime import datetime
import uuid

def fix_email_sync():
    """Fix email sync by ensuring demo emails exist"""
    print("🔧 Fixing Email Sync...")
    
    app = create_app()
    
    with app.app_context():
        # Get demo user
        user = User.query.filter_by(azure_id='demo-user-123').first()
        
        if not user:
            print("❌ Demo user not found")
            return False
        
        print(f"✅ Found user: {user.display_name} (ID: {user.id})")
        
        # Check existing emails
        existing_emails = Email.query.filter_by(user_id=user.id).count()
        print(f"📧 Current emails: {existing_emails}")
        
        if existing_emails == 0:
            print("📝 Creating demo emails...")
            
            demo_emails = [
                {
                    'subject': 'Welcome to AI Email Assistant',
                    'sender_email': 'welcome@aiassistant.com',
                    'sender_name': 'AI Assistant Team',
                    'body_text': 'Welcome to your AI-powered email assistant! We\'re excited to help you manage your emails more efficiently.',
                    'is_read': False,
                    'importance': 'normal'
                },
                {
                    'subject': 'Configure Microsoft 365 Integration',
                    'sender_email': 'admin@aiassistant.com',
                    'sender_name': 'Admin',
                    'body_text': 'To sync real emails from Microsoft 365/Outlook, configure your Azure AD settings. See AZURE_SETUP.md for instructions.',
                    'is_read': False,
                    'importance': 'high'
                },
                {
                    'subject': 'Getting Started Guide',
                    'sender_email': 'help@aiassistant.com',
                    'sender_name': 'Help Center',
                    'body_text': 'Here are some tips to get started with your email assistant: 1) Sync your emails, 2) Use AI chat for help, 3) Organize your inbox.',
                    'is_read': True,
                    'importance': 'normal'
                },
                {
                    'subject': 'Weekly Productivity Report',
                    'sender_email': 'reports@aiassistant.com',
                    'sender_name': 'Productivity Bot',
                    'body_text': 'Your weekly email productivity summary: 25 emails processed, 3 hours saved, 12 priority items identified.',
                    'is_read': False,
                    'importance': 'normal'
                },
                {
                    'subject': 'Meeting Reminder: Team Standup',
                    'sender_email': 'calendar@company.com',
                    'sender_name': 'Calendar System',
                    'body_text': 'Reminder: Team standup meeting today at 10:00 AM. Agenda: Sprint progress, blockers, and next steps.',
                    'is_read': False,
                    'importance': 'high'
                }
            ]
            
            for i, email_data in enumerate(demo_emails):
                email = Email(
                    user_id=user.id,
                    message_id=f'demo-{uuid.uuid4()}',
                    subject=email_data['subject'],
                    sender_email=email_data['sender_email'],
                    sender_name=email_data['sender_name'],
                    body_text=email_data['body_text'],
                    body_html=f"<p>{email_data['body_text']}</p>",
                    received_date=datetime.utcnow() - timedelta(hours=i),
                    is_read=email_data['is_read'],
                    importance=email_data['importance'],
                    folder='inbox',
                    has_attachments=False
                )
                db.session.add(email)
            
            db.session.commit()
            print(f"✅ Created {len(demo_emails)} demo emails")
        else:
            print(f"✅ Found {existing_emails} existing emails")
        
        # Update user's last sync time
        user.last_sync = datetime.utcnow()
        db.session.commit()
        print("✅ Updated last sync time")
        
        # Verify emails were created
        final_count = Email.query.filter_by(user_id=user.id).count()
        print(f"📧 Final email count: {final_count}")
        
        return True

def main():
    """Main function"""
    print("🔧 AI Email Assistant - Email Sync Fix")
    print("=" * 40)
    
    try:
        from datetime import timedelta
        
        if fix_email_sync():
            print("\n✅ Email sync fixed successfully!")
            print("🚀 You can now:")
            print("   1. Restart the app: python docker_run.py")
            print("   2. Try email sync from the dashboard")
            print("   3. Check the emails page")
        else:
            print("\n❌ Failed to fix email sync")
            print("💡 Try the no-database demo instead:")
            print("   python no_db_run.py")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Try the no-database demo:")
        print("   python no_db_run.py")

if __name__ == "__main__":
    main()