#!/usr/bin/env python3
"""
Debug version of OBD Data Viewer with console output
"""

import subprocess
import sys
import os

def main():
    """Main launcher function."""
    print("Starting OBD Data Viewer with debug output...")
    print("=" * 50)
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Launch the viewer with output capture
    print("Launching viewer...")
    try:
        # Import and run directly to see console output
        from obd_data_viewer import OBDDDataViewer
        import tkinter as tk
        
        root = tk.Tk()
        app = OBDDDataViewer(root)
        
        print("GUI initialized. Check the application window.")
        print("Debug output will appear here when you interact with the GUI.")
        
        root.mainloop()
        
    except Exception as e:
        print(f"Error launching viewer: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
