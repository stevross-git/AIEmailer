#!/usr/bin/env python3
"""
Reset Demo Database
"""
import os
from dotenv import load_dotenv

load_dotenv()

def reset_demo():
    """Reset the demo database"""
    try:
        # Set environment to use Docker config
        os.environ['USE_DOCKER_CONFIG'] = 'true'
        
        from app import create_app, db
        from app.models.user import User
        
        app = create_app()
        
        with app.app_context():
            # Drop and recreate all tables
            db.drop_all()
            db.create_all()
            
            print("✅ Database reset successfully")
            print("🚀 You can now run: python docker_run.py")
            
    except Exception as e:
        print(f"❌ Reset error: {e}")

if __name__ == "__main__":
    reset_demo()