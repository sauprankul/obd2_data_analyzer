#!/usr/bin/env python3
"""
Test grouped PID graphing functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer

def test_group_graphing_logic():
    """Test the graph callback logic for grouped PIDs."""
    print("=" * 60)
    print("TEST: Group Graphing Logic")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Create test groups
    viewer.groups = {
        "Engine Performance": ["Engine RPM", "Vehicle Speed"],  # Both rpm/mph but different units
        "Temperature Group": ["Coolant Temperature", "Intake Air Temperature"]  # Both °F
    }
    viewer.pid_groups = {
        "Engine RPM": "Engine Performance",
        "Vehicle Speed": "Engine Performance", 
        "Coolant Temperature": "Temperature Group",
        "Intake Air Temperature": "Temperature Group"
    }
    
    print(f"✅ Created test groups: {list(viewer.groups.keys())}")
    print(f"✅ Group contents: {viewer.groups}")
    
    # Test what the graph callback sees
    print("\n🔍 Testing graph callback inputs:")
    
    # Simulate checkbox states (all checked)
    checkbox_states = {}
    for pid in viewer.data.keys():
        checkbox_states[f'hidden-checkbox-{pid}'] = [pid]  # All checked
    
    print(f"✅ Hidden checkbox states: {len(checkbox_states)} PIDs")
    
    # Test the visible_groups logic from the graph callback
    visible_groups = {}
    for group_name, pids in viewer.groups.items():
        # Check if any PID in group is checked
        group_visible = False
        for pid in pids:
            if pid in checkbox_states and checkbox_states[pid]:
                group_visible = True
                break
        
        if group_visible:
            visible_groups[group_name] = pids
    
    print(f"✅ Visible groups: {list(visible_groups.keys())}")
    print(f"✅ Visible group contents: {visible_groups}")
    
    # Check individual PIDs
    individual_pids = []
    for pid in viewer.data.keys():
        if pid not in viewer.pid_groups:
            if pid in checkbox_states and checkbox_states[pid]:
                individual_pids.append(pid)
    
    print(f"✅ Individual PIDs: {individual_pids}")
    
    return True

def test_checkbox_synchronization():
    """Test if hidden and visible checkboxes are synchronized."""
    print("=" * 60)
    print("TEST: Checkbox Synchronization")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Create a test group
    viewer.groups = {"Test Group": ["Engine RPM"]}
    viewer.pid_groups = {"Engine RPM": "Test Group"}
    
    print("🔍 Testing checkbox ID patterns:")
    
    # Hidden checkbox IDs (what graph callback listens to)
    hidden_ids = [f'hidden-checkbox-{pid}' for pid in viewer.data.keys()]
    print(f"✅ Hidden checkbox IDs: {len(hidden_ids)}")
    print(f"  Sample: {hidden_ids[:3]}")
    
    # Visible checkbox IDs (what users interact with)
    visible_ids = []
    for pid in viewer.data.keys():
        if pid not in viewer.pid_groups:
            visible_ids.append(f'checkbox-{pid}')
    
    print(f"✅ Individual visible checkbox IDs: {len(visible_ids)}")
    print(f"  Sample: {visible_ids[:3]}")
    
    # The problem: graph callback only listens to hidden checkboxes
    # but users interact with visible checkboxes in groups
    
    print("\n❌ PROBLEM IDENTIFIED:")
    print("  - Graph callback listens to: hidden-checkbox-{pid}")
    print("  - Users interact with: checkbox-{pid} (in groups)")
    print("  - No synchronization between them!")
    
    return True

def test_graph_callback_inputs():
    """Test what inputs the graph callback is actually listening to."""
    print("=" * 60)
    print("TEST: Graph Callback Inputs")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    callback_map = viewer.app.callback_map
    
    # Find the graph callback
    graph_callback = None
    for callback_key, callback in callback_map.items():
        if 'main-graph' in callback_key:
            graph_callback = callback
            print(f"✅ Found graph callback: {callback_key}")
            break
    
    if not graph_callback:
        print("❌ Graph callback not found")
        return False
    
    # Check callback inputs
    inputs = graph_callback.get('inputs', [])
    print(f"✅ Graph callback has {len(inputs)} inputs")
    
    checkbox_inputs = []
    for input_item in inputs:
        input_id = input_item.get('id', '')
        if 'checkbox' in input_id:
            checkbox_inputs.append(input_id)
    
    print(f"✅ Checkbox inputs: {len(checkbox_inputs)}")
    for checkbox_id in checkbox_inputs[:5]:  # Show first 5
        print(f"  - {checkbox_id}")
    
    # Check if they're hidden or visible
    hidden_count = sum(1 for cid in checkbox_inputs if 'hidden-checkbox' in cid)
    visible_count = sum(1 for cid in checkbox_inputs if cid.startswith('checkbox-') and 'hidden' not in cid)
    
    print(f"✅ Hidden checkbox inputs: {hidden_count}")
    print(f"✅ Visible checkbox inputs: {visible_count}")
    
    if hidden_count > 0 and visible_count == 0:
        print("❌ Graph callback only listens to hidden checkboxes!")
        print("💡 Need to sync visible checkboxes to hidden ones")
    
    return True

if __name__ == "__main__":
    print("🧪 GROUP GRAPHING DEBUG TESTS")
    print("=" * 60)
    
    try:
        # Run tests
        test1 = test_group_graphing_logic()
        test2 = test_checkbox_synchronization()
        test3 = test_graph_callback_inputs()
        
        print("\n" + "=" * 60)
        print("🔍 DEBUG ANALYSIS:")
        print("=" * 60)
        
        print("❌ ROOT CAUSE IDENTIFIED:")
        print("  - Graph callback listens to hidden-checkbox-{pid}")
        print("  - Users interact with visible checkbox-{pid} in groups")
        print("  - No synchronization between visible and hidden checkboxes")
        print("  - Grouped PIDs appear unchecked to graph callback")
        
        print("\n💡 SOLUTION NEEDED:")
        print("  - Add callbacks to sync visible checkboxes to hidden ones")
        print("  - OR modify graph callback to listen to visible checkboxes")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
