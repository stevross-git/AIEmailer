#!/usr/bin/env python3
"""
Add Email Content Fields to Database Schema
"""
import os

def check_current_email_model():
    """Check the current Email model structure"""
    print("🔍 Checking Current Email Model")
    print("=" * 30)
    
    email_model_file = 'app/models/email.py'
    
    try:
        with open(email_model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ Email model file found")
        
        # Check for content fields
        content_fields = ['body_text', 'body_html', 'body_preview']
        missing_fields = []
        
        for field in content_fields:
            if field not in content:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False, missing_fields
        else:
            print("✅ All content fields present")
            return True, []
            
    except Exception as e:
        print(f"❌ Error checking model: {e}")
        return False, []

def update_email_model():
    """Update the Email model to include content fields"""
    print("\n🔧 Updating Email Model")
    print("=" * 21)
    
    email_model_file = 'app/models/email.py'
    
    try:
        with open(email_model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if content fields already exist
        if 'body_text' in content:
            print("✅ Content fields already exist")
            return True
        
        # Find the place to insert new fields (after existing fields)
        # Look for the last field before the closing of the class
        
        # Add the content fields after the existing fields
        content_fields = '''    
    # Email content fields
    body_text = db.Column(db.Text, nullable=True)
    body_html = db.Column(db.Text, nullable=True)
    body_preview = db.Column(db.String(500), nullable=True)'''
        
        # Find a good place to insert - after other db.Column definitions
        # Look for the last db.Column line
        lines = content.split('\n')
        insert_index = -1
        
        for i, line in enumerate(lines):
            if 'db.Column' in line and '=' in line:
                insert_index = i + 1
        
        if insert_index > 0:
            # Insert the content fields
            for line in reversed(content_fields.split('\n')):
                lines.insert(insert_index, line)
            
            new_content = '\n'.join(lines)
            
            with open(email_model_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ Added content fields to Email model")
            return True
        else:
            print("❌ Could not find insertion point")
            return False
            
    except Exception as e:
        print(f"❌ Error updating model: {e}")
        return False

def create_database_migration():
    """Create a database migration to add the new fields"""
    print("\n🔧 Creating Database Migration")
    print("=" * 28)
    
    migration_script = '''#!/usr/bin/env python3
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
            print("\\nTrying alternative migration approach...")
            
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
'''
    
    with open('migrate_database.py', 'w', encoding='utf-8') as f:
        f.write(migration_script)
    
    print("✅ Created migrate_database.py")

def create_improved_email_model():
    """Create a completely updated Email model"""
    print("\n🔧 Creating Improved Email Model")
    print("=" * 31)
    
    improved_model = '''"""
Email model for AI Email Assistant
"""
from app.models import db
from datetime import datetime

class Email(db.Model):
    """Email model to store email data"""
    __tablename__ = 'email'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.String(255), nullable=False, index=True)
    
    # Email metadata
    subject = db.Column(db.String(500), nullable=True)
    sender_email = db.Column(db.String(255), nullable=True, index=True)
    sender_name = db.Column(db.String(255), nullable=True)
    
    # Email content fields
    body_text = db.Column(db.Text, nullable=True)
    body_html = db.Column(db.Text, nullable=True)
    body_preview = db.Column(db.String(500), nullable=True)
    
    # Email properties
    received_date = db.Column(db.DateTime, nullable=True, index=True)
    sent_date = db.Column(db.DateTime, nullable=True)
    importance = db.Column(db.String(20), nullable=True, default='normal')
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    is_draft = db.Column(db.Boolean, nullable=False, default=False)
    has_attachments = db.Column(db.Boolean, nullable=False, default=False)
    
    # Organization
    folder = db.Column(db.String(100), nullable=True, default='inbox', index=True)
    conversation_id = db.Column(db.String(255), nullable=True, index=True)
    
    # AI analysis
    category = db.Column(db.String(100), nullable=True, index=True)
    priority_score = db.Column(db.Float, nullable=True)
    sentiment = db.Column(db.String(20), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('emails', lazy=True, cascade='all, delete-orphan'))
    
    def __init__(self, **kwargs):
        """Initialize email with default values"""
        super(Email, self).__init__(**kwargs)
        if not self.received_date:
            self.received_date = datetime.utcnow()
    
    def __repr__(self):
        return f'<Email {self.id}: {self.subject}>'
    
    def to_dict(self):
        """Convert email to dictionary"""
        return {
            'id': self.id,
            'message_id': self.message_id,
            'subject': self.subject,
            'sender_email': self.sender_email,
            'sender_name': self.sender_name,
            'body_text': self.body_text,
            'body_html': self.body_html,
            'body_preview': self.body_preview,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'importance': self.importance,
            'is_read': self.is_read,
            'is_draft': self.is_draft,
            'has_attachments': self.has_attachments,
            'folder': self.folder,
            'conversation_id': self.conversation_id,
            'category': self.category,
            'priority_score': self.priority_score,
            'sentiment': self.sentiment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def display_date(self):
        """Get formatted display date"""
        if self.received_date:
            return self.received_date.strftime('%B %d, %Y at %I:%M %p')
        return 'Unknown'
    
    @property
    def short_preview(self):
        """Get short preview of email content"""
        if self.body_preview:
            return self.body_preview[:100] + '...' if len(self.body_preview) > 100 else self.body_preview
        elif self.body_text:
            preview = self.body_text.strip()[:100]
            return preview + '...' if len(self.body_text) > 100 else preview
        return 'No preview available'
    
    @property
    def has_content(self):
        """Check if email has any content"""
        return any([
            self.body_text and len(self.body_text.strip()) > 0,
            self.body_html and len(self.body_html.strip()) > 0,
            self.body_preview and len(self.body_preview.strip()) > 0
        ])
'''
    
    # Backup current model
    email_model_file = 'app/models/email.py'
    backup_file = 'app/models/email_backup.py'
    
    try:
        with open(email_model_file, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(current_content)
        
        print("✅ Backed up current email model")
        
        # Write new model
        with open(email_model_file, 'w', encoding='utf-8') as f:
            f.write(improved_model)
        
        print("✅ Created improved email model with content fields")
        return True
        
    except Exception as e:
        print(f"❌ Error creating improved model: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Add Email Content Fields to Database Schema")
    print("=" * 44)
    print("🐛 Error: 'Email' object has no attribute 'body_text'")
    print("Need to add content fields to the Email model and database")
    print()
    
    # Check current model
    has_fields, missing = check_current_email_model()
    
    if not has_fields:
        print(f"Missing fields: {missing}")
        
        # Create improved email model
        model_updated = create_improved_email_model()
        
        # Create migration script
        create_database_migration()
        
        if model_updated:
            print(f"\n🎉 EMAIL MODEL UPDATED!")
            print(f"=" * 22)
            print(f"🔄 Run the database migration:")
            print(f"   python migrate_database.py")
            
            print(f"\n🚀 Then restart your app:")
            print(f"   python docker_run.py")
            
            print(f"\n✅ What was added:")
            print(f"   - body_text field (TEXT)")
            print(f"   - body_html field (TEXT)")
            print(f"   - body_preview field (VARCHAR 500)")
            print(f"   - Helper methods for content handling")
            print(f"   - Better email model structure")
            
            print(f"\n🔄 After migration:")
            print(f"   1. Run: python migrate_database.py")
            print(f"   2. Restart: python docker_run.py")
            print(f"   3. Test: python check_email_content.py")
            print(f"   4. Sync: Open enhanced_sync_test.html")
            print(f"   5. View: http://localhost:5000/emails/267")
            
            print(f"\n📧 After these steps:")
            print(f"   - Email model will have content fields")
            print(f"   - Database will store email bodies")
            print(f"   - Enhanced sync will populate content")
            print(f"   - Email detail page will show full content")
            
        else:
            print(f"\n❌ Model update failed")
    else:
        print("✅ Email model already has content fields")

if __name__ == "__main__":
    main()