#!/usr/bin/env python3
"""
Test rename callback functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer

def test_rename_callback_structure():
    """Test the rename callback structure."""
    print("=" * 60)
    print("TEST: Rename Callback Structure")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    callback_map = viewer.app.callback_map
    
    # Find the main group management callback
    group_callback = None
    for callback_key, callback in callback_map.items():
        if 'group-operation-store' in callback_key:
            group_callback = callback
            print(f"✅ Found group management callback: {callback_key}")
            break
    
    if not group_callback:
        print("❌ Group management callback not found")
        return False
    
    # Check callback inputs
    inputs = group_callback.get('inputs', [])
    print(f"✅ Callback has {len(inputs)} inputs")
    
    # Check for rename-related inputs
    rename_inputs = []
    for input_item in inputs:
        input_id = input_item.get('id', '')
        if 'rename' in input_id.lower():
            rename_inputs.append(input_item)
            print(f"✅ Found rename input: {input_item}")
    
    # Check for confirm-rename-group specifically
    confirm_rename_input = None
    for input_item in inputs:
        input_id = input_item.get('id', '')
        if input_id == 'confirm-rename-group':
            confirm_rename_input = input_item
            print(f"✅ Found confirm rename input: {input_item}")
    
    if not confirm_rename_input:
        print("❌ confirm-rename-group input not found")
        print("🔍 All inputs:")
        for i, input_item in enumerate(inputs):
            print(f"  Input {i}: {input_item}")
        return False
    
    # Check states
    states = group_callback.get('state', [])
    print(f"✅ Callback has {len(states)} states")
    
    # Check for rename input state
    rename_input_state = None
    for state_item in states:
        state_id = state_item.get('id', '')
        if state_id == 'group-name-input':
            rename_input_state = state_item
            print(f"✅ Found rename input state: {state_item}")
    
    if not rename_input_state:
        print("❌ group-name-input state not found")
        return False
    
    return True

def test_rename_modal_structure():
    """Test the rename modal structure in layout."""
    print("=" * 60)
    print("TEST: Rename Modal Structure")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    layout = viewer.app.layout
    
    # Find rename modal components
    modal_components = []
    
    def find_modal_components(component, depth=0):
        if depth > 10:  # Prevent infinite recursion
            return
        
        if hasattr(component, 'id') and component.id:
            component_id = str(component.id)
            if 'rename' in component_id.lower():
                modal_components.append((component_id, component))
        
        if hasattr(component, 'children') and component.children:
            if isinstance(component.children, list):
                for child in component.children:
                    find_modal_components(child, depth + 1)
            else:
                find_modal_components(component.children, depth + 1)
    
    find_modal_components(layout)
    
    print(f"✅ Found {len(modal_components)} rename-related components:")
    for comp_id, comp in modal_components:
        print(f"  - {comp_id}")
    
    # Check for specific required components
    required_ids = ['rename-group-modal', 'group-name-input', 'confirm-rename-group', 'cancel-rename-group']
    found_ids = [comp_id for comp_id, _ in modal_components]
    
    missing_ids = []
    for req_id in required_ids:
        if req_id in found_ids:
            print(f"✅ Found required component: {req_id}")
        else:
            print(f"❌ Missing required component: {req_id}")
            missing_ids.append(req_id)
    
    return len(missing_ids) == 0

def test_rename_logic_simulation():
    """Test the rename logic with simulated data."""
    print("=" * 60)
    print("TEST: Rename Logic Simulation")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Setup test scenario
    viewer.groups = {"Group 1": ["Engine RPM"]}
    viewer.pid_groups = {"Engine RPM": "Group 1"}
    
    print(f"✅ Initial groups: {list(viewer.groups.keys())}")
    
    # Simulate rename operation
    old_name = "Group 1"
    new_name = "Engine Performance"
    
    # This is what the callback should do
    store_data = {"operation": "rename_prompt", "group": old_name}
    rename_input = new_name
    
    print(f"🔍 Simulating rename: '{old_name}' -> '{new_name}'")
    
    # Check conditions
    if store_data and 'group' in store_data and rename_input:
        old_name = store_data['group']
        new_name = rename_input.strip()
        
        if new_name and old_name != new_name:
            if new_name in viewer.groups:
                print(f"❌ Would fail: Group '{new_name}' already exists")
                return False
            
            # Perform the rename
            pids = viewer.groups.pop(old_name)
            viewer.groups[new_name] = pids
            
            # Update PID mappings
            for pid in pids:
                viewer.pid_groups[pid] = new_name
            
            print(f"✅ Rename successful: '{old_name}' -> '{new_name}'")
            print(f"✅ Updated groups: {list(viewer.groups.keys())}")
            print(f"✅ Updated PID mappings: {viewer.pid_groups}")
            return True
        else:
            print(f"❌ Would fail: Invalid name '{new_name}'")
            return False
    
    return False

if __name__ == "__main__":
    print("🧪 RENAME CALLBACK DEBUG TESTS")
    print("=" * 60)
    
    try:
        # Run tests
        test1 = test_rename_callback_structure()
        test2 = test_rename_modal_structure()
        test3 = test_rename_logic_simulation()
        
        print("\n" + "=" * 60)
        print("🔍 DEBUG ANALYSIS:")
        print("=" * 60)
        
        if all([test1, test2, test3]):
            print("✅ All rename callback tests passed")
            print("💡 Issue might be in callback execution order or trigger detection")
        else:
            print("❌ Some tests failed - check callback structure")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
