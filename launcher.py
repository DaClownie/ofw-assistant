#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def main():
    # Change to the app directory
    app_dir = Path(__file__).parent
    os.chdir(app_dir)
    
    # Start Streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", "8501",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    print("Starting OFW Assistant...")
    process = subprocess.Popen(cmd)
    
    # Wait a moment for server to start
    time.sleep(3)
    
    # Open browser
    webbrowser.open("http://localhost:8501")
    
    # Keep the process running
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()

if __name__ == "__main__":
    main()
