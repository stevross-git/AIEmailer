#!/usr/bin/env python3
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
        print("\n🚀 Next steps:")
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
