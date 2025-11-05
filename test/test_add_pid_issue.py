#!/usr/bin/env python3
"""
Debug tests for Add PID button not working and individual PIDs not plotting
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer

def test_add_pid_button_structure():
    """Test if Add PID buttons have correct structure."""
    print("=" * 60)
    print("TEST: Add PID Button Structure")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Create a test group
    viewer.groups = {"Test Group": []}
    viewer.pid_groups = {}
    
    # Create controls
    controls = viewer.create_pid_controls()
    layout_str = str(controls)
    
    print("🔍 Looking for Add PID buttons...")
    
    # Check for pattern matching button IDs
    add_buttons_found = []
    
    def find_add_buttons(component, depth=0):
        if hasattr(component, 'id') and component.id:
            if isinstance(component.id, dict) and component.id.get('type') == 'add-button':
                add_buttons_found.append(component.id)
                print(f"✅ Found Add PID button: {component.id}")
            elif isinstance(component.id, str) and component.id.startswith('add-'):
                add_buttons_found.append(component.id)
                print(f"✅ Found Add PID button (old style): {component.id}")
        
        if hasattr(component, 'children') and component.children:
            if isinstance(component.children, list):
                for child in component.children:
                    find_add_buttons(child, depth + 1)
            else:
                find_add_buttons(component.children, depth + 1)
    
    for control in controls:
        find_add_buttons(control)
    
    print(f"✅ Total Add PID buttons found: {len(add_buttons_found)}")
    
    # Check if buttons have correct dict structure
    for button_id in add_buttons_found:
        if isinstance(button_id, dict):
            print(f"✅ Pattern matching button: {button_id}")
        else:
            print(f"❌ Old style button (won't work): {button_id}")
    
    return len(add_buttons_found) > 0

def test_callback_inputs():
    """Test if callback inputs match button structure."""
    print("=" * 60)
    print("TEST: Callback Input Structure")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    callback_map = viewer.app.callback_map
    
    # Find the group management callback
    group_callback = None
    for callback_key, callback in callback_map.items():
        if 'group-operation-store' in callback_key:
            group_callback = callback
            print(f"✅ Found callback: {callback_key}")
            break
    
    if group_callback and isinstance(group_callback, dict):
        print("✅ Found group management callback")
        
        inputs = group_callback.get('inputs', [])
        print(f"✅ Callback has {len(inputs)} inputs")
        
        # Check for pattern matching input
        pattern_input_found = False
        for input_item in inputs:
            input_id = input_item.get('id', {})
            print(f"🔍 Input: {input_id}")
            if isinstance(input_id, dict) and input_id.get('type') == 'add-button':
                print(f"✅ Pattern matching input found: {input_id}")
                pattern_input_found = True
            elif 'ALL' in str(input_id):
                print(f"✅ ALL input found: {input_id}")
                pattern_input_found = True
        
        if not pattern_input_found:
            print("❌ No pattern matching input found in callback")
    else:
        print("❌ Group management callback not found")
        print("🔍 Available callbacks:")
        for key in callback_map.keys():
            print(f"  - {key}")

def test_individual_pid_graphing():
    """Test why individual PIDs are not being plotted."""
    print("=" * 60)
    print("TEST: Individual PID Graphing")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Test with individual PIDs (no groups)
    viewer.groups = {}
    viewer.pid_groups = {}
    
    print(f"✅ Current state: {len(viewer.groups)} groups, {len(viewer.pid_groups)} PID mappings")
    
    # Test the graph callback logic manually
    print("🔍 Testing graph callback logic...")
    
    # Simulate checkbox values (all checked)
    checkbox_values = [[] for _ in viewer.data.keys()]
    for i in range(len(checkbox_values)):
        checkbox_values[i] = [list(viewer.data.keys())[i]]
    
    # Get visible groups (should be empty since no groups)
    visible_groups = {}
    for group_name in viewer.groups.keys():
        group_pids = []
        for pid in viewer.groups[group_name]:
            pid_index = list(viewer.data.keys()).index(pid)
            if checkbox_values[pid_index]:
                group_pids.append(pid)
        if group_pids:
            visible_groups[group_name] = group_pids
    
    print(f"✅ Visible groups: {list(visible_groups.keys())}")
    
    # Check individual PIDs
    individual_pids = [pid for pid in viewer.data.keys() if pid not in viewer.pid_groups]
    visible_individual_pids = []
    
    for pid in individual_pids:
        pid_index = list(viewer.data.keys()).index(pid)
        if checkbox_values[pid_index]:
            visible_individual_pids.append(pid)
    
    print(f"✅ Visible individual PIDs: {visible_individual_pids}")
    
    if not visible_groups and not visible_individual_pids:
        print("❌ No PIDs would be plotted - this is the bug!")
        print("💡 Need to handle individual PIDs in graph callback")
    else:
        print("✅ PIDs would be plotted correctly")

def test_graph_callback_structure():
    """Test the actual graph callback structure."""
    print("=" * 60)
    print("TEST: Graph Callback Structure")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    callback_map = viewer.app.callback_map
    
    # Find graph callback
    graph_callback = None
    for callback_key, callback in callback_map.items():
        if 'main-graph.figure' in callback_key:
            graph_callback = callback
            break
    
    if graph_callback and isinstance(graph_callback, dict):
        print("✅ Found graph callback")
        
        inputs = graph_callback.get('inputs', [])
        print(f"✅ Graph callback has {len(inputs)} inputs")
        
        # Check if it only looks at groups
        print("🔍 Graph callback inputs:")
        for input_item in inputs:
            input_id = input_item.get('id', 'unknown')
            print(f"  - {input_id}")
    else:
        print("❌ Graph callback not found")

if __name__ == "__main__":
    print("🧪 ADD PID & INDIVIDUAL PID GRAPHING DEBUG")
    print("=" * 60)
    
    try:
        # Run debug tests
        test1 = test_add_pid_button_structure()
        test2 = test_callback_inputs()
        test3 = test_individual_pid_graphing()
        test4 = test_graph_callback_structure()
        
        print("\n" + "=" * 60)
        print("🔍 DEBUG ANALYSIS COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
