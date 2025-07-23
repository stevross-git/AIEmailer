#!/usr/bin/env python3
"""
Restart ChromaDB and fix connection issues
"""
import subprocess
import time
import requests

def restart_chromadb():
    """Restart ChromaDB container"""
    print("🔄 Restarting ChromaDB...")
    
    try:
        # Restart ChromaDB container
        result = subprocess.run(['docker', 'restart', 'ai_email_chromadb'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ ChromaDB container restarted")
        else:
            print(f"❌ Failed to restart ChromaDB: {result.stderr}")
            return False
        
        # Wait for it to start
        print("⏳ Waiting for ChromaDB to start...")
        time.sleep(15)
        
        # Test connection
        for attempt in range(10):
            try:
                response = requests.get('http://localhost:8000/api/v1/heartbeat', timeout=5)
                if response.status_code == 200:
                    print("✅ ChromaDB is responding")
                    return True
            except:
                print(f"⏳ Attempt {attempt + 1}/10...")
                time.sleep(3)
        
        print("⚠️ ChromaDB is not responding to HTTP requests")
        print("💡 The container is running but HTTP API may take longer to start")
        return True  # Container is running, even if HTTP isn't ready
        
    except FileNotFoundError:
        print("❌ Docker not found. Make sure Docker is installed and running")
        return False
    except Exception as e:
        print(f"❌ Error restarting ChromaDB: {e}")
        return False

def check_all_containers():
    """Check status of all containers"""
    print("\n🔍 Checking all containers...")
    
    try:
        result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}'], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        
        # Check if our containers are running
        containers = ['ai_email_db', 'ai_email_redis', 'ai_email_chromadb']
        running_containers = []
        
        for container in containers:
            if container in result.stdout:
                running_containers.append(container)
        
        print(f"\n✅ Running containers: {', '.join(running_containers)}")
        
        if len(running_containers) == len(containers):
            print("🎉 All containers are running!")
            return True
        else:
            missing = set(containers) - set(running_containers)
            print(f"⚠️ Missing containers: {', '.join(missing)}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking containers: {e}")
        return False

def restart_all_services():
    """Restart all database services"""
    print("\n🔄 Restarting all database services...")
    
    try:
        result = subprocess.run(['docker', 'compose', 'restart'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All services restarted")
            time.sleep(20)  # Give more time for all services
            return True
        else:
            print(f"❌ Failed to restart services: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error restarting services: {e}")
        return False

def main():
    """Main function"""
    print("🔧 ChromaDB Connection Fix")
    print("=" * 30)
    
    # Check current status
    all_running = check_all_containers()
    
    if not all_running:
        print("\n🔄 Some containers are missing. Restarting all services...")
        if restart_all_services():
            check_all_containers()
    else:
        # Just restart ChromaDB
        restart_chromadb()
    
    print("\n" + "=" * 30)
    print("🏁 Next Steps:")
    print("1. Run: python fix_email_sync.py")
    print("2. Start app: python docker_run.py")
    print("3. Try email sync from dashboard")
    
    print("\n💡 If issues persist:")
    print("Use the no-database demo: python no_db_run.py")

if __name__ == "__main__":
    main()