#!/usr/bin/env python3
"""
Simple Database Schema Fix - Recreate with Content Fields
"""
import os
import shutil

def backup_database():
    """Backup the current database"""
    print("💾 Backing Up Current Database")
    print("=" * 29)
    
    db_file = 'instance/app.db'
    backup_file = 'instance/app_backup.db'
    
    try:
        if os.path.exists(db_file):
            shutil.copy2(db_file, backup_file)
            print("✅ Database backed up to app_backup.db")
            return True
        else:
            print("ℹ️ No existing database to backup")
            return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def create_simple_migration_script():
    """Create a simple migration script that works"""
    print("\n🔧 Creating Simple Migration Script")
    print("=" * 32)
    
    migration_script = '''#!/usr/bin/env python3
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
'''
    
    with open('simple_migrate.py', 'w', encoding='utf-8') as f:
        f.write(migration_script)
    
    print("✅ Created simple_migrate.py")

def create_test_database_content():
    """Create a test script to verify database content"""
    print("\n🧪 Creating Database Test Script")
    print("=" * 31)
    
    test_script = '''#!/usr/bin/env python3
"""
Test Database Content Fields
"""
import os
import sys
import sqlite3

def test_database():
    """Test if database has content fields"""
    print("🧪 Testing Database Content Fields")
    print("=" * 32)
    
    db_file = 'instance/app.db'
    
    try:
        if not os.path.exists(db_file):
            print("❌ Database file doesn't exist")
            return False
        
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check email table schema
        cursor.execute("PRAGMA table_info(email);")
        columns = cursor.fetchall()
        
        print("📊 Email table schema:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check if content fields exist
        column_names = [col[1] for col in columns]
        content_fields = ['body_text', 'body_html', 'body_preview']
        
        print("\\n🔍 Content fields check:")
        for field in content_fields:
            if field in column_names:
                print(f"  ✅ {field} - EXISTS")
            else:
                print(f"  ❌ {field} - MISSING")
        
        # Count emails
        cursor.execute("SELECT COUNT(*) FROM email;")
        count = cursor.fetchone()[0]
        print(f"\\n📧 Total emails in database: {count}")
        
        # Check sample email
        if count > 0:
            cursor.execute("SELECT id, subject, sender_email, body_text, body_html, body_preview FROM email LIMIT 1;")
            sample = cursor.fetchone()
            print(f"\\n📮 Sample email (ID {sample[0]}):")
            print(f"  Subject: {sample[1]}")
            print(f"  Sender: {sample[2]}")
            print(f"  Body Text: {len(sample[3] or '')} chars")
            print(f"  Body HTML: {len(sample[4] or '')} chars") 
            print(f"  Body Preview: {len(sample[5] or '')} chars")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    test_database()
'''
    
    with open('test_database.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ Created test_database.py")

def create_force_recreate_script():
    """Create script to force recreate database if needed"""
    print("\n🔧 Creating Force Recreate Script")
    print("=" * 32)
    
    recreate_script = '''#!/usr/bin/env python3
"""
Force Recreate Database with Proper Schema
"""
import os
import sys

def force_recreate():
    """Force recreate database by deleting and letting Flask recreate"""
    print("🔄 Force Recreating Database")
    print("=" * 27)
    
    db_file = 'instance/app.db'
    backup_file = 'instance/app_backup.db'
    
    try:
        # Backup if exists
        if os.path.exists(db_file):
            if os.path.exists(backup_file):
                os.remove(backup_file)
            os.rename(db_file, backup_file)
            print(f"✅ Moved {db_file} to {backup_file}")
        
        print("🗑️ Database removed - Flask will recreate with new schema")
        print("\\n🚀 Next steps:")
        print("1. Restart your Flask app: python docker_run.py")
        print("2. The app will create a new database with content fields")
        print("3. Re-sync your emails with enhanced sync")
        print("4. Your email content will be properly stored")
        
        return True
        
    except Exception as e:
        print(f"❌ Force recreate error: {e}")
        return False

if __name__ == "__main__":
    force_recreate()
'''
    
    with open('force_recreate_db.py', 'w', encoding='utf-8') as f:
        f.write(recreate_script)
    
    print("✅ Created force_recreate_db.py")

def main():
    """Main function"""
    print("🔧 Simple Database Schema Fix")
    print("=" * 27)
    print("🐛 Circular import issue with migration")
    print("Creating simple SQLite-based migration")
    print()
    
    # Backup database
    backup_success = backup_database()
    
    # Create simple migration
    create_simple_migration_script()
    
    # Create test script
    create_test_database_content()
    
    # Create force recreate option
    create_force_recreate_script()
    
    if backup_success:
        print(f"\n🎉 SIMPLE MIGRATION CREATED!")
        print(f"=" * 27)
        
        print(f"\n🔄 Option 1 - Try Simple Migration:")
        print(f"   python simple_migrate.py")
        print(f"   python test_database.py")
        print(f"   python docker_run.py")
        
        print(f"\n🔄 Option 2 - Force Recreate (if migration fails):")
        print(f"   python force_recreate_db.py")
        print(f"   python docker_run.py")
        print(f"   Open enhanced_sync_test.html")
        print(f"   Run enhanced sync to populate emails")
        
        print(f"\n✅ What these do:")
        print(f"   - simple_migrate.py: Adds content fields to existing table")
        print(f"   - test_database.py: Verifies the database schema")
        print(f"   - force_recreate_db.py: Deletes DB for fresh start")
        
        print(f"\n🎯 Goal:")
        print(f"   - Get email table with body_text, body_html, body_preview")
        print(f"   - Keep your existing 20 emails if possible")
        print(f"   - Enable full email content display")
        
        print(f"\n💡 Recommendation:")
        print(f"   Try Option 1 first (simple migration)")
        print(f"   If that fails, use Option 2 (force recreate)")
    
    else:
        print(f"\n❌ Backup failed - check manually")

if __name__ == "__main__":
    main()