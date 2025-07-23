#!/usr/bin/env python3
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
        
        print("\n🔍 Content fields check:")
        for field in content_fields:
            if field in column_names:
                print(f"  ✅ {field} - EXISTS")
            else:
                print(f"  ❌ {field} - MISSING")
        
        # Count emails
        cursor.execute("SELECT COUNT(*) FROM email;")
        count = cursor.fetchone()[0]
        print(f"\n📧 Total emails in database: {count}")
        
        # Check sample email
        if count > 0:
            cursor.execute("SELECT id, subject, sender_email, body_text, body_html, body_preview FROM email LIMIT 1;")
            sample = cursor.fetchone()
            print(f"\n📮 Sample email (ID {sample[0]}):")
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
