#!/usr/bin/env python3
"""
Simple Docker Run - Fixed Version
"""
import os
import sys

def main():
    """Start the application"""
    print("Starting AI Email Assistant")
    print("=" * 27)
    
    try:
        # Set environment
        os.environ['USE_DOCKER_CONFIG'] = 'true'
        
        # Import app
        from app import app
        
        print("App imported successfully")
        print()
        print("AI Email Assistant Ready!")
        print("=" * 26) 
        print("Visit: http://localhost:5000")
        print()
        
        # Start the app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
