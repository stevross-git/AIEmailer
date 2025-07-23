#!/usr/bin/env python3
"""
Simple Database Reset Script
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def reset_database():
    """Reset the PostgreSQL database"""
    try:
        # Set environment to use Docker config
        os.environ['USE_DOCKER_CONFIG'] = 'true'
        
        print("🔄 Resetting PostgreSQL database...")
        
        # Direct database connection using psycopg2
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Database connection parameters
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'ai_email_assistant',
            'user': 'ai_email_user',
            'password': 'ai_email_password123'
        }
        
        print("📡 Connecting to PostgreSQL...")
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Drop all tables if they exist
        tables_to_drop = ['chat_messages', 'emails', 'users']
        
        print("🗑️ Dropping existing tables...")
        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"   ✅ Dropped {table}")
            except Exception as e:
                print(f"   ⚠️ Could not drop {table}: {e}")
        
        # Create users table
        print("🏗️ Creating users table...")
        users_sql = '''
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            azure_id VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(320) UNIQUE NOT NULL,
            display_name VARCHAR(255),
            given_name VARCHAR(255),
            surname VARCHAR(255),
            job_title VARCHAR(255),
            office_location VARCHAR(255),
            preferred_language VARCHAR(10),
            access_token_hash TEXT,
            refresh_token_hash TEXT,
            token_expires_at TIMESTAMP,
            preferences TEXT,
            timezone VARCHAR(50) DEFAULT 'UTC',
            is_active BOOLEAN DEFAULT true,
            is_admin BOOLEAN DEFAULT false,
            last_login TIMESTAMP,
            last_sync TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        cursor.execute(users_sql)
        print("   ✅ Created users table")
        
        # Create emails table
        print("🏗️ Creating emails table...")
        emails_sql = '''
        CREATE TABLE emails (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            message_id VARCHAR(255) UNIQUE NOT NULL,
            conversation_id VARCHAR(255),
            internet_message_id VARCHAR(255),
            subject VARCHAR(998),
            sender_email VARCHAR(320),
            sender_name VARCHAR(255),
            body_text TEXT,
            body_html TEXT,
            received_date TIMESTAMP,
            sent_date TIMESTAMP,
            is_read BOOLEAN DEFAULT false,
            importance VARCHAR(20) DEFAULT 'normal',
            folder VARCHAR(50) DEFAULT 'inbox',
            has_attachments BOOLEAN DEFAULT false,
            is_flagged BOOLEAN DEFAULT false,
            categories TEXT,
            ai_summary TEXT,
            ai_priority_score INTEGER,
            ai_category VARCHAR(100),
            ai_sentiment VARCHAR(20),
            search_vector TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        cursor.execute(emails_sql)
        print("   ✅ Created emails table")
        
        # Create chat_messages table
        print("🏗️ Creating chat_messages table...")
        chat_sql = '''
        CREATE TABLE chat_messages (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            message TEXT NOT NULL,
            is_user BOOLEAN DEFAULT true,
            conversation_id VARCHAR(255),
            message_type VARCHAR(50) DEFAULT 'text',
            ai_model VARCHAR(100),
            processing_time INTEGER,
            confidence_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        cursor.execute(chat_sql)
        print("   ✅ Created chat_messages table")
        
        # Create indexes for better performance
        print("📈 Creating indexes...")
        indexes = [
            "CREATE INDEX idx_emails_user_id ON emails(user_id);",
            "CREATE INDEX idx_emails_received_date ON emails(received_date);",
            "CREATE INDEX idx_emails_is_read ON emails(is_read);",
            "CREATE INDEX idx_emails_folder ON emails(folder);",
            "CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id);",
            "CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"   ✅ Created index")
            except Exception as e:
                print(f"   ⚠️ Index creation warning: {e}")
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("\n✅ Database reset completed successfully!")
        print("🎯 Tables created:")
        print("   - users (with authentication and profile data)")
        print("   - emails (with full email metadata)")  
        print("   - chat_messages (for AI conversations)")
        print("   - All foreign keys and indexes created")
        
        print("\n🚀 Ready to start the application:")
        print("   python docker_run.py")
        
        return True
        
    except ImportError:
        print("❌ psycopg2 not installed. Run: python install_postgres.py")
        return False
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        print("💡 Make sure PostgreSQL is running: python start_docker_db.py")
        return False
    except Exception as e:
        print(f"❌ Reset error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    reset_database()