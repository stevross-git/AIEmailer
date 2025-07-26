#!/usr/bin/env python3
"""
Simple database connection test
"""
import os
import sqlite3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

def test_database():
    """Test database connection"""
    print("Testing database connection...")
    
    # Test SQLite directly
    try:
        db_file = 'data/app.db'
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT sqlite_version()')
        version = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ SQLite {version} working directly")
        
        # Test Flask-SQLAlchemy
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy(app)
        
        with app.app_context():
            # Try new SQLAlchemy 2.0 syntax
            try:
                with db.engine.connect() as conn:
                    result = conn.execute(db.text('SELECT 1'))
                    result.fetchone()
                print("✅ SQLAlchemy 2.0 syntax working")
            except Exception as e:
                print(f"⚠️ SQLAlchemy 2.0 syntax failed: {e}")
                # Try old syntax
                try:
                    result = db.engine.execute('SELECT 1')
                    result.fetchone()
                    print("✅ SQLAlchemy 1.4 syntax working")
                except Exception as e2:
                    print(f"❌ Both SQLAlchemy syntaxes failed: {e2}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    test_database()
