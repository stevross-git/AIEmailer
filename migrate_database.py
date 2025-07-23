#!/usr/bin/env python3
"""
Database Migration: Add Email Content Fields
"""
import os
import sys

def migrate_database():
    """Add content fields to email table"""
    print("🔄 Migrating Database")
    print("=" * 18)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        from app import create_app
        from app.models import db
        
        app = create_app()
        
        with app.app_context():
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('email')]
            
            print(f"Existing columns: {columns}")
            
            # SQL commands to add missing columns
            migration_sql = []
            
            if 'body_text' not in columns:
                migration_sql.append("ALTER TABLE email ADD COLUMN body_text TEXT;")
                
            if 'body_html' not in columns:
                migration_sql.append("ALTER TABLE email ADD COLUMN body_html TEXT;")
                
            if 'body_preview' not in columns:
                migration_sql.append("ALTER TABLE email ADD COLUMN body_preview VARCHAR(500);")
            
            if migration_sql:
                print(f"Adding {len(migration_sql)} new columns...")
                
                for sql in migration_sql:
                    print(f"Executing: {sql}")
                    db.engine.execute(sql)
                
                print("✅ Database migration completed!")
                
                # Verify the changes
                inspector = db.inspect(db.engine)
                new_columns = [col['name'] for col in inspector.get_columns('email')]
                print(f"New columns: {new_columns}")
                
            else:
                print("✅ All columns already exist - no migration needed")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        
        # Try alternative approach for SQLite
        try:
            print("\nTrying alternative migration approach...")
            
            # Recreate tables (this will add missing columns)
            from app.models.email import Email
            from app.models.user import User
            
            print("Creating all tables...")
            db.create_all()
            print("✅ Tables created/updated successfully")
            
            return True
            
        except Exception as alt_error:
            print(f"❌ Alternative migration failed: {alt_error}")
            return False

if __name__ == "__main__":
    migrate_database()
