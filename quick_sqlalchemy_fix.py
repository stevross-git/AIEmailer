#!/usr/bin/env python3
"""
Quick SQLAlchemy Initialization Fix
"""
import os

def fix_models_init_sqlalchemy():
    """Fix SQLAlchemy initialization in models/__init__.py"""
    print("🔧 Fixing SQLAlchemy Initialization")
    print("=" * 33)
    
    init_file = 'app/models/__init__.py'
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("Current content:")
        print(content)
        
        # Create a better __init__.py
        better_init = '''"""
Models package for AI Email Assistant
"""
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Import models after db is defined
from .user import User
from .email import Email
from .chat import ChatMessage

__all__ = ['db', 'User', 'Email', 'ChatMessage']
'''
        
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(better_init)
        
        print("✅ Fixed models/__init__.py")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing models init: {e}")
        return False

def fix_app_init_db():
    """Ensure app/__init__.py properly initializes database"""
    print("\n🔧 Checking App Database Initialization")
    print("=" * 38)
    
    app_init_file = 'app/__init__.py'
    
    try:
        with open(app_init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if db.init_app is called
        if 'db.init_app(app)' not in content:
            print("❌ db.init_app(app) not found")
            
            # Find where to add it
            lines = content.split('\n')
            new_lines = []
            added = False
            
            for line in lines:
                new_lines.append(line)
                
                # Add db.init_app after db import
                if 'from app.models import db' in line and not added:
                    new_lines.append('    db.init_app(app)')
                    added = True
                    print("✅ Added db.init_app(app)")
            
            if added:
                new_content = '\n'.join(new_lines)
                with open(app_init_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print("✅ Fixed app database initialization")
        else:
            print("✅ db.init_app(app) already present")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing app init: {e}")
        return False

def create_simple_start_test():
    """Create a simple test just to verify app starts"""
    print("\n🧪 Creating Simple Start Test")
    print("=" * 27)
    
    test_script = '''#!/usr/bin/env python3
"""
Simple App Start Test
"""
import os
import sys

def test_simple_start():
    """Just test if app starts"""
    print("🧪 Simple App Start Test")
    print("=" * 21)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("Importing app...")
        from app import create_app
        
        print("Creating app...")
        app = create_app()
        
        print("Testing app...")
        if app:
            print("✅ SUCCESS: App created successfully!")
            print("\\n🚀 Try starting with: python docker_run.py")
            return True
        else:
            print("❌ App creation returned None")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_start()
'''
    
    with open('test_simple_start.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ Created test_simple_start.py")

def main():
    """Main function"""
    print("🔧 Quick SQLAlchemy Fix")
    print("=" * 20)
    print("The app can be created but has SQLAlchemy init issue")
    print("Let's try to fix this quickly")
    print()
    
    # Fix models init
    models_fixed = fix_models_init_sqlalchemy()
    
    # Fix app init
    app_fixed = fix_app_init_db()
    
    # Create simple test
    create_simple_start_test()
    
    print(f"\n🎯 Quick Fix Applied!")
    print(f"=" * 19)
    
    print(f"\n🧪 Test with simple test:")
    print(f"   python test_simple_start.py")
    
    print(f"\n🚀 Or try starting directly:")
    print(f"   python docker_run.py")
    
    print(f"\n✅ If app starts:")
    print(f"   1. Go to http://localhost:5000")
    print(f"   2. Open enhanced_sync_test.html")
    print(f"   3. Run enhanced sync")
    print(f"   4. Visit http://localhost:5000/emails/267")
    print(f"   5. Should show email content!")

if __name__ == "__main__":
    main()