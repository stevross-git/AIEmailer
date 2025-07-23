#!/usr/bin/env python3
"""
Quick Test for create_app
"""
import os
import sys

def test():
    print("Testing create_app import")
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("1. Importing create_app...")
        from app import create_app
        print("SUCCESS: create_app imported")
        
        print("2. Creating app...")
        app = create_app()
        print("SUCCESS: App created")
        
        print("3. Testing app...")
        if app and hasattr(app, 'config'):
            print("SUCCESS: App is valid")
            print("Ready to start with: python docker_run.py")
            return True
        else:
            print("ERROR: App is invalid")
            return False
            
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test()
