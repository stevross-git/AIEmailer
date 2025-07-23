#!/usr/bin/env python3
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
            print("\n🚀 Try starting with: python docker_run.py")
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
