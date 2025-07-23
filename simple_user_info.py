#!/usr/bin/env python3
"""
Show Current User Info
"""
import os
import sys

def show_user_info():
    """Show current user information"""
    print("Current User Information")
    print("=" * 25)
    
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        from app import create_app, db
        from app.models.user import User
        
        app = create_app()
        
        with app.app_context():
            users = User.query.all()
            
            if not users:
                print("No users found in database")
                return
            
            for user in users:
                print(f"\nUser: {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Azure ID: {user.azure_id}")
                print(f"   Name: {user.display_name}")
                print(f"   Active: {user.is_active}")
                print(f"   Has Tokens: {user.access_token_hash is not None}")
                print(f"   Last Sync: {user.last_sync}")
                
                is_real = user.azure_id and user.azure_id != 'demo-user-123'
                print(f"   Type: {'Real Microsoft User' if is_real else 'Demo User'}")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    show_user_info()