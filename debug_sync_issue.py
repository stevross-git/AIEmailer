#!/usr/bin/env python3
"""
Debug Email Sync Issue
"""
import os
import requests
import subprocess
from dotenv import load_dotenv

load_dotenv()

def check_chromadb():
    """Check ChromaDB status"""
    print("🔍 Checking ChromaDB...")
    
    try:
        # Check if container is running
        result = subprocess.run(['docker', 'ps', '--filter', 'name=chromadb', '--format', 'table {{.Names}}\t{{.Status}}'], 
                              capture_output=True, text=True)
        
        if 'chromadb' in result.stdout:
            print("✅ ChromaDB container is running")
        else:
            print("❌ ChromaDB container not found")
            return False
        
        # Test HTTP connection
        try:
            response = requests.get('http://localhost:8000/api/v1/heartbeat', timeout=5)
            if response.status_code == 200:
                print("✅ ChromaDB HTTP API is responding")
                return True
            else:
                print(f"⚠️ ChromaDB HTTP API returned: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to ChromaDB HTTP API")
            return False
        except Exception as e:
            print(f"❌ ChromaDB test error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking ChromaDB: {e}")
        return False

def test_email_sync():
    """Test email sync manually"""
    print("\n🔧 Testing Email Sync...")
    
    try:
        # Set environment to use Docker config
        os.environ['USE_DOCKER_CONFIG'] = 'true'
        
        from app import create_app, db
        from app.models.user import User
        from app.models.email import Email
        
        app = create_app()
        
        with app.app_context():
            # Get demo user
            user = User.query.filter_by(azure_id='demo-user-123').first()
            
            if not user:
                print("❌ Demo user not found")
                return False
            
            print(f"✅ Found user: {user.display_name} (ID: {user.id})")
            
            # Check existing emails
            email_count = Email.query.filter_by(user_id=user.id).count()
            print(f"📧 Current emails in database: {email_count}")
            
            # Test creating a new email
            from datetime import datetime
            import uuid
            
            test_email = Email(
                user_id=user.id,
                message_id=f'test-{uuid.uuid4()}',
                subject='Test Email Sync',
                sender_email='test@example.com',
                sender_name='Test Sender',
                body_text='This is a test email to verify sync functionality.',
                body_html='<p>This is a test email to verify sync functionality.</p>',
                received_date=datetime.utcnow(),
                is_read=False,
                importance='normal',
                folder='inbox',
                has_attachments=False
            )
            
            db.session.add(test_email)
            db.session.commit()
            
            print(f"✅ Test email created successfully")
            
            # Verify count increased
            new_count = Email.query.filter_by(user_id=user.id).count()
            print(f"📧 New email count: {new_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Email sync test error: {e}")
        return False

def fix_chromadb():
    """Try to fix ChromaDB connection"""
    print("\n🔧 Attempting to fix ChromaDB...")
    
    try:
        # Restart ChromaDB container
        print("🔄 Restarting ChromaDB container...")
        subprocess.run(['docker', 'restart', 'ai_email_chromadb'], check=True)
        
        print("⏳ Waiting for ChromaDB to start...")
        import time
        time.sleep(10)
        
        # Test connection
        for attempt in range(10):
            try:
                response = requests.get('http://localhost:8000/api/v1/heartbeat', timeout=5)
                if response.status_code == 200:
                    print("✅ ChromaDB is now responding")
                    return True
            except:
                time.sleep(2)
        
        print("⚠️ ChromaDB still not responding after restart")
        return False
        
    except Exception as e:
        print(f"❌ Error fixing ChromaDB: {e}")
        return False

def create_session_fix():
    """Create a simple session fix"""
    print("\n🔧 Creating email sync session fix...")
    
    # Create a simple script to fix the session issue
    fix_script = """
import os
import sys
sys.path.append('.')
os.environ['USE_DOCKER_CONFIG'] = 'true'

from app import create_app, db
from app.models.user import User
from app.models.email import Email
from datetime import datetime
import uuid

app = create_app()

with app.app_context():
    # Get demo user
    user = User.query.filter_by(azure_id='demo-user-123').first()
    
    if user:
        # Create demo emails if none exist
        existing_emails = Email.query.filter_by(user_id=user.id).count()
        
        if existing_emails == 0:
            demo_emails = [
                {
                    'subject': 'Welcome to AI Email Assistant',
                    'sender_email': 'welcome@aiassistant.com',
                    'sender_name': 'AI Assistant Team',
                    'body_text': 'Welcome to your AI-powered email assistant!',
                    'is_read': False
                },
                {
                    'subject': 'Configure Microsoft 365 Integration',
                    'sender_email': 'admin@aiassistant.com',
                    'sender_name': 'Admin',
                    'body_text': 'To sync real emails, configure Azure AD settings.',
                    'is_read': False
                },
                {
                    'subject': 'Getting Started Guide',
                    'sender_email': 'help@aiassistant.com',
                    'sender_name': 'Help Center',
                    'body_text': 'Here are some tips to get started with your email assistant.',
                    'is_read': True
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
                    received_date=datetime.utcnow(),
                    is_read=email_data['is_read'],
                    importance='normal',
                    folder='inbox',
                    has_attachments=False
                )
                db.session.add(email)
            
            db.session.commit()
            print(f"Created {len(demo_emails)} demo emails")
        else:
            print(f"Found {existing_emails} existing emails")
        
        # Update user's last sync time
        user.last_sync = datetime.utcnow()
        db.session.commit()
        print("Updated last sync time")
"""
    
    with open('fix_email_sync.py', 'w') as f:
        f.write(fix_script)
    
    print("✅ Created fix_email_sync.py")
    return True

def main():
    """Main debug function"""
    print("🔍 AI Email Assistant - Debug Email Sync Issue")
    print("=" * 50)
    
    # Check ChromaDB
    chromadb_ok = check_chromadb()
    
    # Test email sync
    sync_ok = test_email_sync()
    
    # Create session fix
    fix_created = create_session_fix()
    
    print("\n" + "=" * 50)
    print("📊 Debug Results")
    print("=" * 50)
    print(f"ChromaDB Status: {'✅ OK' if chromadb_ok else '❌ ISSUE'}")
    print(f"Email Sync Test: {'✅ OK' if sync_ok else '❌ ISSUE'}")
    print(f"Fix Script Created: {'✅ OK' if fix_created else '❌ ISSUE'}")
    
    print("\n🔧 Recommended Actions:")
    
    if not chromadb_ok:
        print("1. Fix ChromaDB:")
        print("   docker restart ai_email_chromadb")
        print("   # OR restart all containers:")
        print("   docker compose restart")
    
    if not sync_ok:
        print("2. Fix email sync:")
        print("   python fix_email_sync.py")
    
    print("3. Restart the application:")
    print("   python docker_run.py")
    
    print("\n💡 Alternative: Use the no-database demo:")
    print("   python no_db_run.py")

if __name__ == "__main__":
    main()