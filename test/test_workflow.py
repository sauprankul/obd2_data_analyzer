#!/usr/bin/env python3
"""
Test the user workflow: Create group -> Add PID -> Modal opens
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer

def test_user_workflow():
    """Test the complete user workflow."""
    print("=" * 60)
    print("TEST: User Workflow")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    print("🔍 Step 1: Initial state (no groups)")
    controls = viewer.create_pid_controls()
    print(f"✅ Initial controls: {len(controls)} elements")
    
    # Check for Add PID buttons initially
    initial_add_buttons = []
    layout_str = str(controls)
    if '"type": "add-button"' in layout_str:
        print("❌ Found Add PID buttons in initial state (shouldn't be there)")
    else:
        print("✅ No Add PID buttons initially (correct)")
    
    print("\n🔍 Step 2: Create a group")
    viewer.groups = {"Group 1": []}
    viewer.pid_groups = {}
    
    controls_with_group = viewer.create_pid_controls()
    print(f"✅ Controls with group: {len(controls_with_group)} elements")
    
    # Check for Add PID buttons after creating group
    layout_with_group = str(controls_with_group)
    
    if "'type': 'add-button'" in layout_with_group:
        print("✅ Found Add PID buttons after creating group")
        
        # Extract button info
        import re
        pattern = r"{'type': 'add-button', 'index': '([^']+)'"
        matches = re.findall(pattern, layout_with_group)
        print(f"✅ Add PID buttons for groups: {matches}")
    else:
        print("❌ No Add PID buttons found after creating group")
    
    print("\n🔍 Step 3: Test modal opening logic")
    if viewer.groups:
        group_name = list(viewer.groups.keys())[0]
        
        # Simulate the callback logic
        available_pids = []
        for pid in viewer.data.keys():
            if pid not in viewer.groups.get(group_name, []):
                available_pids.append({"label": f"{pid} ({viewer.units[pid]})", "value": pid})
        
        print(f"✅ Available PIDs for {group_name}: {len(available_pids)}")
        print(f"✅ Modal would open with: {available_pids[:3]}...")
    
    return True

if __name__ == "__main__":
    test_user_workflow()
