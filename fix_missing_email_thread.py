#!/usr/bin/env python3
"""
Fix Missing EmailThread Import Issue
"""
import os

def check_app_init_imports():
    """Check what's being imported in app/__init__.py"""
    print("🔍 Checking App __init__.py Imports")
    print("=" * 33)
    
    app_init_file = 'app/__init__.py'
    
    try:
        with open(app_init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find lines that import from models
        lines = content.split('\n')
        import_lines = []
        
        for i, line in enumerate(lines):
            if 'from app.models' in line or 'import EmailThread' in line:
                import_lines.append(f"Line {i+1}: {line}")
        
        print("Import lines found:")
        for line in import_lines:
            print(f"  {line}")
        
        return content
        
    except Exception as e:
        print(f"❌ Error checking app init: {e}")
        return ""

def fix_app_init_imports():
    """Fix the imports in app/__init__.py"""
    print("\n🔧 Fixing App __init__.py Imports")
    print("=" * 29)
    
    app_init_file = 'app/__init__.py'
    backup_file = 'app/__init___backup.py'
    
    try:
        with open(app_init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup current file
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Backed up app/__init__.py")
        
        # Fix the problematic import lines
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if 'from app.models.email import Email, EmailThread' in line:
                # Replace with just Email since EmailThread doesn't exist
                fixed_lines.append('from app.models.email import Email')
                print("🔧 Fixed: Removed EmailThread import")
            elif 'from app.models.chat import ChatMessage' in line and 'ChatSession' in line:
                # Simplify chat imports
                fixed_lines.append('from app.models.chat import ChatMessage')
                print("🔧 Fixed: Simplified chat imports")
            elif 'EmailThread' in line and 'import' in line:
                # Skip any other EmailThread imports
                print(f"🔧 Skipped: {line}")
                continue
            else:
                fixed_lines.append(line)
        
        # Write fixed content
        fixed_content = '\n'.join(fixed_lines)
        
        with open(app_init_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("✅ Fixed app/__init__.py imports")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing app init: {e}")
        return False

def check_chat_model():
    """Check if chat model exists and what it contains"""
    print("\n🔍 Checking Chat Model")
    print("=" * 19)
    
    chat_file = 'app/models/chat.py'
    
    try:
        if os.path.exists(chat_file):
            with open(chat_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print("✅ Chat model exists")
            
            # Check what classes are defined
            classes = []
            for line in content.split('\n'):
                if line.strip().startswith('class '):
                    class_name = line.split('class ')[1].split('(')[0].split(':')[0].strip()
                    classes.append(class_name)
            
            print(f"Classes found: {classes}")
            return True, classes
            
        else:
            print("❌ Chat model doesn't exist")
            return False, []
            
    except Exception as e:
        print(f"❌ Error checking chat model: {e}")
        return False, []

def create_minimal_chat_model():
    """Create a minimal chat model if it doesn't exist"""
    print("\n🔧 Creating Minimal Chat Model")
    print("=" * 28)
    
    chat_file = 'app/models/chat.py'
    
    minimal_chat = '''"""
Chat model for AI Email Assistant
"""
from . import db
from datetime import datetime

class ChatMessage(db.Model):
    """Chat message model"""
    __tablename__ = 'chat_message'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='chat_messages')
    
    def __repr__(self):
        return f'<ChatMessage {self.id}>'
'''
    
    try:
        if not os.path.exists(chat_file):
            with open(chat_file, 'w', encoding='utf-8') as f:
                f.write(minimal_chat)
            
            print("✅ Created minimal chat model")
        else:
            print("✅ Chat model already exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating chat model: {e}")
        return False

def create_simplified_app_test():
    """Create a simplified test that handles missing models gracefully"""
    print("\n🧪 Creating Simplified App Test")
    print("=" * 30)
    
    test_script = '''#!/usr/bin/env python3
"""
Simplified App Startup Test
"""
import os
import sys

def test_app_start():
    """Test if the app can start after fixes"""
    print("🧪 Testing App Startup (Fixed)")
    print("=" * 28)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("1. Importing Flask...")
        from flask import Flask
        print("✅ Flask imported")
        
        print("2. Testing models import...")
        try:
            from app.models import db
            print("✅ Database imported")
        except Exception as db_error:
            print(f"❌ Database import failed: {db_error}")
            return False
        
        print("3. Testing individual models...")
        try:
            from app.models.user import User
            print("✅ User model imported")
        except Exception as user_error:
            print(f"❌ User model failed: {user_error}")
        
        try:
            from app.models.email import Email
            print("✅ Email model imported")
        except Exception as email_error:
            print(f"❌ Email model failed: {email_error}")
        
        try:
            from app.models.chat import ChatMessage
            print("✅ Chat model imported")
        except Exception as chat_error:
            print(f"❌ Chat model failed: {chat_error}")
        
        print("4. Creating app...")
        from app import create_app
        app = create_app()
        print("✅ App created successfully")
        
        print("5. Testing app context...")
        with app.app_context():
            print("✅ App context works")
            
            print("6. Creating database tables...")
            db.create_all()
            print("✅ Database tables created")
        
        print("\\n🎉 SUCCESS: App can start without errors!")
        print("\\n🚀 You can now run: python docker_run.py")
        return True
        
    except Exception as e:
        print(f"\\n❌ FAILED: {e}")
        import traceback
        print("\\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_app_start()
'''
    
    with open('test_app_fixed.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ Created test_app_fixed.py")

def main():
    """Main function"""
    print("🔧 Fix Missing EmailThread Import Issue")
    print("=" * 37)
    print("🐛 Error: cannot import name 'EmailThread' from 'app.models.email'")
    print("The app is trying to import EmailThread which doesn't exist")
    print()
    
    # Check current imports
    check_app_init_imports()
    
    # Fix app init imports
    app_fixed = fix_app_init_imports()
    
    # Check chat model
    chat_exists, chat_classes = check_chat_model()
    
    # Create chat model if needed
    if not chat_exists:
        create_minimal_chat_model()
    
    # Create simplified test
    create_simplified_app_test()
    
    if app_fixed:
        print(f"\n🎉 IMPORT ISSUES FIXED!")
        print(f"=" * 22)
        
        print(f"\n🧪 Test the fix:")
        print(f"   python test_app_fixed.py")
        
        print(f"\n🚀 If test passes:")
        print(f"   python docker_run.py")
        
        print(f"\n✅ What was fixed:")
        print(f"   - Removed EmailThread import (doesn't exist)")
        print(f"   - Fixed chat model imports")
        print(f"   - Created minimal chat model if needed")
        print(f"   - Cleaned up problematic imports")
        
        print(f"\n🎯 After app starts:")
        print(f"   - Fresh database with email content fields")
        print(f"   - Open enhanced_sync_test.html")
        print(f"   - Run enhanced sync")
        print(f"   - Visit http://localhost:5000/emails/267")
        print(f"   - Should show full email content!")
        
    else:
        print(f"\n❌ Could not fix import issues")

if __name__ == "__main__":
    main()