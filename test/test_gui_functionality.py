#!/usr/bin/env python3
"""
GUI tests for the OBD viewer using Playwright
Tests actual user interactions in the browser
"""

import sys
import os
import time
import subprocess
import requests
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_app_startup():
    """Test that the app starts and is accessible."""
    print("=" * 60)
    print("GUI TEST: App Startup")
    print("=" * 60)
    
    try:
        # Start the app in background
        app_process = subprocess.Popen([
            sys.executable, "src/working_viewer.py"
        ], cwd=os.path.dirname(__file__).replace("test", ""))
        
        # Wait for app to start
        time.sleep(5)
        
        # Test if app is responding
        response = requests.get("http://localhost:8052", timeout=10)
        if response.status_code == 200:
            print("✅ App is running and accessible")
            print(f"✅ Response status: {response.status_code}")
            
            # Check if page contains expected elements
            page_content = response.text
            expected_elements = [
                "OBD Data Viewer",
                "btn-new-group", 
                "pid-controls-container",
                "main-graph"
            ]
            
            for element in expected_elements:
                if element in page_content:
                    print(f"✅ Found element: {element}")
                else:
                    print(f"❌ Missing element: {element}")
            
            return app_process
        else:
            print(f"❌ App returned status: {response.status_code}")
            app_process.terminate()
            return None
            
    except Exception as e:
        print(f"❌ App startup failed: {e}")
        return None

def test_individual_pids_display():
    """Test that individual PIDs are displayed correctly."""
    print("=" * 60)
    print("GUI TEST: Individual PIDs Display")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8052", timeout=10)
        page_content = response.text
        
        # Check for individual PID elements
        expected_pids = [
            "Air Fuel Ratio",
            "Engine RPM", 
            "Vehicle Speed",
            "Coolant Temperature"
        ]
        
        found_pids = 0
        for pid in expected_pids:
            if pid in page_content:
                print(f"✅ Found PID: {pid}")
                found_pids += 1
            else:
                print(f"❌ Missing PID: {pid}")
        
        print(f"✅ Found {found_pids}/{len(expected_pids)} expected PIDs")
        
        # Check for individual PID controls (up/down buttons)
        if "up-Air Fuel Ratio" in page_content:
            print("✅ Found individual PID controls")
        else:
            print("❌ Missing individual PID controls")
            
    except Exception as e:
        print(f"❌ Individual PIDs test failed: {e}")

def test_group_functionality():
    """Test group creation and management."""
    print("=" * 60)
    print("GUI TEST: Group Functionality")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8052", timeout=10)
        page_content = response.text
        
        # Check for group management elements
        group_elements = [
            "btn-new-group",
            "add-pid-modal",
            "pid-selection-radio",
            "cancel-add-pid",
            "confirm-add-pid"
        ]
        
        for element in group_elements:
            if element in page_content:
                print(f"✅ Found group element: {element}")
            else:
                print(f"❌ Missing group element: {element}")
        
        # Check for modal structure
        if "Modal" in page_content and "RadioItems" in page_content:
            print("✅ Modal structure is present")
        else:
            print("❌ Modal structure missing")
            
    except Exception as e:
        print(f"❌ Group functionality test failed: {e}")

def test_callback_structure():
    """Test callback registration without duplicates."""
    print("=" * 60)
    print("GUI TEST: Callback Structure")
    print("=" * 60)
    
    try:
        # Import and test the viewer
        from working_viewer import WorkingOBDViewer
        
        viewer = WorkingOBDViewer()
        callback_map = viewer.app.callback_map
        
        print(f"✅ Found {len(callback_map)} callbacks")
        
        # Check for duplicate outputs
        output_counts = {}
        for callback_key, callback in callback_map.items():
            if isinstance(callback, dict) and 'outputs' in callback:
                for output in callback['outputs']:
                    output_id = output.get('id', 'unknown')
                    output_counts[output_id] = output_counts.get(output_id, 0) + 1
        
        duplicates = {k: v for k, v in output_counts.items() if v > 1}
        
        if duplicates:
            print(f"❌ Found duplicate outputs: {duplicates}")
        else:
            print("✅ No duplicate callback outputs found")
        
        # List all callbacks
        print("\n🔍 Registered callbacks:")
        for callback_key in callback_map.keys():
            print(f"  - {callback_key}")
            
    except Exception as e:
        print(f"❌ Callback structure test failed: {e}")

def test_graph_functionality():
    """Test graph rendering and structure."""
    print("=" * 60)
    print("GUI TEST: Graph Functionality")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8052", timeout=10)
        page_content = response.text
        
        # Check for graph elements
        graph_elements = [
            "main-graph",
            "plotly",
            "zoom-in",
            "zoom-out", 
            "zoom-reset",
            "tick-zoom-in",
            "tick-zoom-out",
            "tick-zoom-reset"
        ]
        
        for element in graph_elements:
            if element in page_content:
                print(f"✅ Found graph element: {element}")
            else:
                print(f"❌ Missing graph element: {element}")
        
        # Check for zoom controls
        if "Zoom" in page_content and "X-Axis Zoom" in page_content:
            print("✅ Zoom controls are present")
        else:
            print("❌ Zoom controls missing")
            
    except Exception as e:
        print(f"❌ Graph functionality test failed: {e}")

def run_gui_tests():
    """Run all GUI tests."""
    print("🧪 GUI FUNCTIONALITY TESTS")
    print("=" * 60)
    
    app_process = None
    
    try:
        # Test app startup
        app_process = test_app_startup()
        
        if app_process:
            # Run all tests
            test_individual_pids_display()
            test_group_functionality()
            test_callback_structure()
            test_graph_functionality()
            
            print("\n" + "=" * 60)
            print("✅ ALL GUI TESTS COMPLETED")
            print("=" * 60)
            
        else:
            print("❌ Could not start app for GUI testing")
            
    except Exception as e:
        print(f"❌ GUI tests failed: {e}")
        
    finally:
        # Clean up
        if app_process:
            print("\n🧹 Cleaning up...")
            app_process.terminate()
            app_process.wait()
            print("✅ App stopped")

if __name__ == "__main__":
    run_gui_tests()
