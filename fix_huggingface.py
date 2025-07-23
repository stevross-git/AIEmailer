#!/usr/bin/env python3
"""
Fix HuggingFace Hub compatibility issue
"""
import subprocess
import sys

def fix_huggingface_hub():
    """Fix the HuggingFace Hub version compatibility"""
    print("🔧 Fixing HuggingFace Hub compatibility...")
    
    try:
        # Downgrade to a compatible version
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "huggingface-hub==0.19.4", "--force-reinstall"
        ])
        print("✅ HuggingFace Hub downgraded to compatible version")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to fix HuggingFace Hub: {e}")
        return False

def main():
    """Main function"""
    print("🛠️ HuggingFace Hub Compatibility Fix")
    print("=" * 40)
    
    if fix_huggingface_hub():
        print("\n✅ Fix completed successfully!")
        print("You can now try running the application again.")
    else:
        print("\n❌ Fix failed. You can still use the no-database demo mode:")
        print("python no_db_run.py")

if __name__ == "__main__":
    main()