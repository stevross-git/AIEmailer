#!/usr/bin/env python3
"""
Fix Circular Import Issue in Models
"""
import os

def check_models_init():
    """Check the current models/__init__.py file"""
    print("🔍 Checking Models __init__.py")
    print("=" * 28)
    
    init_file = 'app/models/__init__.py'
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ Found models/__init__.py")
        print(f"Content length: {len(content)} characters")
        print("Current content:")
        print("-" * 40)
        print(content)
        print("-" * 40)
        
        return True, content
        
    except Exception as e:
        print(f"❌ Error reading __init__.py: {e}")
        return False, ""

def create_fixed_models_init():
    """Create a fixed models/__init__.py file"""
    print("\n🔧 Creating Fixed Models __init__.py")
    print("=" * 34)
    
    # Simple, clean __init__.py that avoids circular imports
    fixed_init = '''"""
Models package for AI Email Assistant
"""
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Import models after db is initialized to avoid circular imports
def init_models():
    """Initialize all models - call this after app is created"""
    from . import user
    from . import email
    return user, email
'''
    
    init_file = 'app/models/__init__.py'
    backup_file = 'app/models/__init___backup.py'
    
    try:
        # Backup current file
        if os.path.exists(init_file):
            with open(init_file, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(current_content)
            
            print("✅ Backed up current __init__.py")
        
        # Write fixed version
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(fixed_init)
        
        print("✅ Created fixed __init__.py")
        return True
        
    except Exception as e:
        print(f"❌ Error creating fixed __init__.py: {e}")
        return False

def fix_user_model():
    """Ensure user model imports correctly"""
    print("\n🔧 Checking User Model")
    print("=" * 20)
    
    user_file = 'app/models/user.py'
    
    try:
        with open(user_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Make sure it imports db correctly
        if 'from app.models import db' not in content and 'from . import db' not in content:
            # Fix the import
            if 'from app.models' in content:
                content = content.replace('from app.models', 'from . import db\nfrom app.models')
            else:
                content = 'from . import db\n' + content
            
            with open(user_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Fixed user model imports")
        else:
            print("✅ User model imports are correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing user model: {e}")
        return False

def fix_email_model():
    """Ensure email model imports correctly"""
    print("\n🔧 Checking Email Model")
    print("=" * 21)
    
    email_file = 'app/models/email.py'
    
    try:
        with open(email_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Make sure it imports db correctly and doesn't have circular imports
        lines = content.split('\n')
        
        # Remove any problematic imports
        fixed_lines = []
        for line in lines:
            if 'from app.models import db' in line:
                fixed_lines.append('from . import db')
            elif 'from app.models.user import User' in line:
                # Remove this to avoid circular import - we'll use string reference
                continue
            else:
                fixed_lines.append(line)
        
        # Ensure db import is at the top
        if 'from . import db' not in fixed_lines[0:5]:
            fixed_lines.insert(1, 'from . import db')
        
        fixed_content = '\n'.join(fixed_lines)
        
        with open(email_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("✅ Fixed email model imports")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing email model: {e}")
        return False

def create_simple_app_test():
    """Create a simple test to verify app can start"""
    print("\n🧪 Creating App Start Test")
    print("=" * 24)
    
    test_script = '''#!/usr/bin/env python3
"""
Test App Startup
"""
import os
import sys

def test_app_start():
    """Test if the app can start without circular import errors"""
    print("🧪 Testing App Startup")
    print("=" * 19)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("1. Importing Flask...")
        from flask import Flask
        print("✅ Flask imported")
        
        print("2. Importing models...")
        from app.models import db
        print("✅ Models imported")
        
        print("3. Creating app...")
        from app import create_app
        app = create_app()
        print("✅ App created")
        
        print("4. Testing app context...")
        with app.app_context():
            print("✅ App context works")
            
            print("5. Creating database tables...")
            db.create_all()
            print("✅ Database tables created")
            
            print("6. Testing models...")
            from app.models.user import User
            from app.models.email import Email
            print("✅ Models can be imported")
        
        print("\\n🎉 SUCCESS: App can start without circular import errors!")
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
    
    with open('test_app_start.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ Created test_app_start.py")

def main():
    """Main function"""
    print("🔧 Fix Circular Import Issue in Models")
    print("=" * 36)
    print("🐛 Error: cannot import name 'db' from partially initialized module")
    print("This is a circular import problem in app/models/__init__.py")
    print()
    
    # Check current models init
    has_init, current_content = check_models_init()
    
    if has_init:
        # Fix models init
        init_fixed = create_fixed_models_init()
        
        # Fix user model
        user_fixed = fix_user_model()
        
        # Fix email model  
        email_fixed = fix_email_model()
        
        # Create test
        create_simple_app_test()
        
        if init_fixed and user_fixed and email_fixed:
            print(f"\n🎉 CIRCULAR IMPORT ISSUE FIXED!")
            print(f"=" * 32)
            
            print(f"\n🧪 Test the fix:")
            print(f"   python test_app_start.py")
            
            print(f"\n🚀 If test passes, restart app:")
            print(f"   python docker_run.py")
            
            print(f"\n✅ What was fixed:")
            print(f"   - Clean models/__init__.py (no circular imports)")
            print(f"   - Proper db import in user.py")
            print(f"   - Proper db import in email.py")
            print(f"   - Removed circular references")
            
            print(f"\n🔄 After app starts:")
            print(f"   1. Database will be created with new schema")
            print(f"   2. Open enhanced_sync_test.html")
            print(f"   3. Run enhanced sync to get emails with content")
            print(f"   4. Visit http://localhost:5000/emails/267")
            print(f"   5. Should show full email content!")
            
        else:
            print(f"\n❌ Some fixes failed - check manually")
    else:
        print(f"\n❌ Could not find models/__init__.py")

if __name__ == "__main__":
    main()