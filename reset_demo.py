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
        
        print("🔄 Resetting database...")
        
        app = create_app()
        
        with app.app_context():
            # Import all models to ensure they're registered
            from app.models import User, Email, ChatMessage
            
            print("📦 Importing models...")
            print(f"   - User: {User}")
            print(f"   - Email: {Email}")
            print(f"   - ChatMessage: {ChatMessage}")
            
            # Drop and recreate all tables
            print("🗑️ Dropping existing tables...")
            db.drop_all()
            
            print("🏗️ Creating new tables...")
            db.create_all()
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✅ Created tables: {tables}")
            
            print("✅ Database reset successfully")
            print("🚀 You can now run: python docker_run.py")
            
    except Exception as e:
        print(f"❌ Reset error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_demo()