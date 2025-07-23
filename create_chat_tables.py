#!/usr/bin/env python3
"""
Create Chat Tables Migration
"""
import os
import sys

def create_chat_tables():
    """Create chat tables in the database"""
    print("🗄️ Creating Chat Tables")
    print("=" * 21)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        from app import create_app, db
        from app.models.chat import ChatSession, ChatMessage
        from app.models.user import User
        from app.models.email import Email
        
        app = create_app()
        
        with app.app_context():
            # Create all tables
            db.create_all()
            
            print("✅ Chat tables created successfully")
            
            # Verify tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['chat_sessions', 'chat_messages']
            for table in required_tables:
                if table in tables:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' missing")
            
            return True
    
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    create_chat_tables()
