#!/usr/bin/env python3
"""
Debug User Info with Better Error Handling
"""
import os
import sys

def show_user_info():
    """Show current user information with detailed debugging"""
    print("DEBUG: Starting user info check...")
    
    # Set environment
    os.environ['USE_DOCKER_CONFIG'] = 'true'
    sys.path.append('.')
    
    try:
        print("DEBUG: Importing modules...")
        from app import create_app, db
        from app.models.user import User
        
        print("DEBUG: Creating app...")
        app = create_app()
        
        print("DEBUG: Entering app context...")
        with app.app_context():
            print("DEBUG: Querying users...")
            
            try:
                users = User.query.all()
                print(f"DEBUG: Found {len(users)} users")
                
                if not users:
                    print("\n❌ NO USERS FOUND IN DATABASE")
                    print("This means no one has signed in yet.")
                    return
                
                print(f"\n📊 USERS IN DATABASE:")
                print("=" * 25)
                
                for i, user in enumerate(users, 1):
                    print(f"\n{i}. Email: {user.email}")
                    print(f"   ID: {user.id}")
                    print(f"   Azure ID: {user.azure_id}")
                    print(f"   Display Name: {user.display_name}")
                    print(f"   Active: {user.is_active}")
                    print(f"   Has Access Token: {'Yes' if user.access_token_hash else 'No'}")
                    print(f"   Has Refresh Token: {'Yes' if user.refresh_token_hash else 'No'}")
                    print(f"   Last Login: {user.last_login}")
                    print(f"   Last Sync: {user.last_sync}")
                    print(f"   Created: {user.created_at}")
                    
                    # Determine user type
                    if user.azure_id == 'demo-user-123':
                        print(f"   TYPE: 🎭 DEMO USER")
                    elif user.azure_id and user.azure_id != 'demo-user-123':
                        print(f"   TYPE: ✅ REAL MICROSOFT USER")
                        if user.access_token_hash:
                            print(f"   STATUS: 🔑 Has tokens for email sync")
                        else:
                            print(f"   STATUS: ⚠️ Missing tokens - needs re-authentication")
                    else:
                        print(f"   TYPE: ❓ UNKNOWN USER TYPE")
                
                # Show recommendations
                demo_users = [u for u in users if u.azure_id == 'demo-user-123']
                real_users = [u for u in users if u.azure_id and u.azure_id != 'demo-user-123']
                
                print(f"\n📈 SUMMARY:")
                print(f"Demo users: {len(demo_users)}")
                print(f"Real users: {len(real_users)}")
                
                if real_users:
                    real_user = real_users[0]
                    print(f"\n✅ REAL USER FOUND: {real_user.email}")
                    if real_user.access_token_hash:
                        print("🎉 Ready for real email sync!")
                    else:
                        print("⚠️ Need to sign in with Microsoft to get tokens")
                else:
                    print(f"\n❌ NO REAL MICROSOFT USER FOUND")
                    print("Need to sign in with Microsoft 365 first")
                
            except Exception as db_error:
                print(f"DEBUG: Database error: {db_error}")
                print("This might mean the database tables don't exist yet")
                
    except ImportError as ie:
        print(f"DEBUG: Import error: {ie}")
        print("Could not import app modules")
    except Exception as e:
        print(f"DEBUG: General error: {e}")
        import traceback
        traceback.print_exc()

def quick_fix_instructions():
    """Show quick fix instructions"""
    print(f"\n🚀 QUICK FIX INSTRUCTIONS:")
    print("=" * 25)
    print("1. Restart your app: python docker_run.py")
    print("2. Visit: http://localhost:5000")
    print("3. Look for 'Sign in with Microsoft' button")
    print("4. Sign in as: stephendavies@peoplesainetwork.com")
    print("5. Authorize the app")
    print("6. Try email sync again")
    
    print(f"\n💡 IF NO MICROSOFT BUTTON:")
    print("Run: python setup_real_microsoft_sync.py")
    print("This will add the Microsoft sign-in option")

if __name__ == "__main__":
    show_user_info()
    quick_fix_instructions()