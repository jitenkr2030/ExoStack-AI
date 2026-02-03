#!/usr/bin/env python3
"""
ExoStack Startup Script
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import redis
        import psutil
        import aiohttp
        print("✓ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def start_hub():
    """Start the ExoStack Hub."""
    print("🚀 Starting ExoStack Hub...")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "exo_hub.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ])
        
        # Wait for hub to start
        time.sleep(5)
        
        # Check if hub is running
        try:
            response = requests.get("http://localhost:8000/")
            if response.status_code == 200:
                print("✓ Hub started successfully at http://localhost:8000")
                return process
        except:
            pass
            
        print("❌ Failed to start hub")
        return None
        
    except Exception as e:
        print(f"❌ Error starting hub: {e}")
        return None

def start_agent():
    """Start an ExoStack Agent."""
    print("🤖 Starting ExoStack Agent...")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "exo_agent.agent"
        ])
        
        time.sleep(3)
        print("✓ Agent started successfully")
        return process
        
    except Exception as e:
        print(f"❌ Error starting agent: {e}")
        return None

def main():
    print("🚀 ExoStack Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start hub
    hub_process = start_hub()
    if not hub_process:
        sys.exit(1)
    
    # Start agent
    agent_process = start_agent()
    if not agent_process:
        hub_process.terminate()
        sys.exit(1)
    
    print("\n✅ ExoStack is running!")
    print("Hub: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop...")
    
    try:
        # Keep processes running
        hub_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down ExoStack...")
        hub_process.terminate()
        agent_process.terminate()
        print("✓ ExoStack stopped")

if __name__ == "__main__":
    main()