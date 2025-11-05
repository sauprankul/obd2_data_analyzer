#!/usr/bin/env python3
"""
Simple launcher for the OBD Data Viewer
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies if not already installed."""
    try:
        import matplotlib
        import pandas
        import numpy
        print("All dependencies are already installed.")
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def main():
    """Main launcher function."""
    print("OBD Data Viewer Launcher")
    print("=" * 30)
    
    # Install dependencies if needed
    install_dependencies()
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Launch the viewer
    print("Launching OBD Data Viewer...")
    try:
        from obd_data_viewer import main as viewer_main
        viewer_main()
    except Exception as e:
        print(f"Error launching viewer: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
