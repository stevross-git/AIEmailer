#!/usr/bin/env python3
"""
Simple Database Recreation with Content Fields
"""
import os
import sys
import sqlite3

def recreate_database():
    """Recreate database with new schema"""
    print("🔄 Recreating Database with Content Fields")
    print("=" * 40)
    
    # Database file path
    db_file = 'instance/app.db'
    
    try:
        # Create instance directory if it doesn't exist
        os.makedirs('instance', exist_ok=True)
        
        # Connect to database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        print("📊 Checking current schema...")
        
        # Check if email table exists and what columns it has
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email';")
        email_table_exists = cursor.fetchone() is not None
        
        if email_table_exists:
            cursor.execute("PRAGMA table_info(email);")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Current email columns: {columns}")
            
            # Check if content fields exist
            content_fields = ['body_text', 'body_html', 'body_preview']
            missing_fields = [field for field in content_fields if field not in columns]
            
            if missing_fields:
                print(f"Missing fields: {missing_fields}")
                
                # Add missing columns one by one
                for field in missing_fields:
                    if field in ['body_text', 'body_html']:
                        sql = f"ALTER TABLE email ADD COLUMN {field} TEXT;"
                    else:  # body_preview
                        sql = f"ALTER TABLE email ADD COLUMN {field} VARCHAR(500);"
                    
                    try:
                        print(f"Adding column: {field}")
                        cursor.execute(sql)
                        print(f"✅ Added {field}")
                    except sqlite3.Error as e:
                        if "duplicate column name" in str(e).lower():
                            print(f"✅ {field} already exists")
                        else:
                            print(f"❌ Error adding {field}: {e}")
                
                conn.commit()
                print("✅ Database schema updated!")
            else:
                print("✅ All content fields already exist!")
        else:
            print("ℹ️ Email table doesn't exist - will be created by Flask app")
        
        # Verify the updated schema
        if email_table_exists:
            cursor.execute("PRAGMA table_info(email);")
            new_columns = [col[1] for col in cursor.fetchall()]
            print(f"Updated email columns: {new_columns}")
        
        conn.close()
        print("✅ Database migration completed!")
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

if __name__ == "__main__":
    recreate_database()
