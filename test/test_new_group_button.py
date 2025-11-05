#!/usr/bin/env python3
"""
Debug test for new group button failure
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer

def test_new_group_callback():
    """Test the new group button callback structure."""
    print("=" * 60)
    print("TEST: New Group Button Callback")
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
    
    # Check for btn-new-group input
    new_group_input = None
    for input_item in inputs:
        input_id = input_item.get('id', '')
        if input_id == 'btn-new-group':
            new_group_input = input_item
            print(f"✅ Found new group button input: {input_item}")
    
    if not new_group_input:
        print("❌ btn-new-group input not found in callback")
        print("🔍 All inputs:")
        for i, input_item in enumerate(inputs):
            print(f"  Input {i}: {input_item}")
        return False
    
    # Check callback outputs
    outputs = group_callback.get('outputs', [])
    print(f"✅ Callback has {len(outputs)} outputs")
    
    # Check for required outputs
    required_outputs = ['pid-controls-container', 'group-operation-store', 'add-pid-modal', 'rename-group-modal']
    found_outputs = []
    
    for output_item in outputs:
        output_id = output_item.get('id', '')
        for required in required_outputs:
            if required in output_id:
                found_outputs.append(required)
                print(f"✅ Found output: {output_item}")
    
    print(f"✅ Found {len(found_outputs)}/{len(required_outputs)} required outputs")
    
    return True

def test_new_group_logic():
    """Test the new group creation logic."""
    print("=" * 60)
    print("TEST: New Group Creation Logic")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    print(f"✅ Initial groups: {list(viewer.groups.keys())}")
    print(f"✅ Initial PID mappings: {len(viewer.pid_groups)}")
    
    # Simulate new group creation
    initial_count = len(viewer.groups)
    group_name = f"Group {initial_count + 1}"
    
    # This is what the callback should do
    viewer.groups[group_name] = []
    
    print(f"✅ Created new group: {group_name}")
    print(f"✅ Updated groups: {list(viewer.groups.keys())}")
    print(f"✅ Group count: {len(viewer.groups)} (was {initial_count})")
    
    # Test creating PID controls with new group
    controls = viewer.create_pid_controls()
    print(f"✅ PID controls created: {len(controls)} elements")
    
    # Check if new group appears in controls
    layout_str = str(controls)
    if group_name in layout_str:
        print(f"✅ New group '{group_name}' found in controls")
    else:
        print(f"❌ New group '{group_name}' not found in controls")
    
    return True

def test_callback_signature():
    """Test if callback signature matches the inputs/outputs."""
    print("=" * 60)
    print("TEST: Callback Signature")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    callback_map = viewer.app.callback_map
    
    # Find the main callback
    for callback_key, callback in callback_map.items():
        if 'group-operation-store' in callback_key:
            print(f"✅ Callback key: {callback_key}")
            
            # Count inputs and outputs
            inputs = callback.get('inputs', [])
            outputs = callback.get('outputs', [])
            
            print(f"✅ Inputs: {len(inputs)}")
            print(f"✅ Outputs: {len(outputs)}")
            
            # Expected counts
            expected_inputs = 9  # btn-new-group, cancel-add-pid, confirm-add-pid, add-button, unit-selection, group-name, cancel-rename, confirm-rename + states
            expected_outputs = 9  # pid-controls, store, add-modal, unit-options, pid-options, selection-info, rename-modal, name-input, rename-info
            
            print(f"✅ Expected inputs: {expected_inputs}, actual: {len(inputs)}")
            print(f"✅ Expected outputs: {expected_outputs}, actual: {len(outputs)}")
            
            if len(inputs) == expected_inputs and len(outputs) == expected_outputs:
                print("✅ Callback signature matches expected")
            else:
                print("❌ Callback signature mismatch")
                print("🔍 Input details:")
                for i, inp in enumerate(inputs):
                    print(f"  {i}: {inp}")
                print("🔍 Output details:")
                for i, out in enumerate(outputs):
                    print(f"  {i}: {out}")
            
            break
    
    return True

if __name__ == "__main__":
    print("🧪 NEW GROUP BUTTON DEBUG")
    print("=" * 60)
    
    try:
        # Run debug tests
        test1 = test_new_group_callback()
        test2 = test_new_group_logic()
        test3 = test_callback_signature()
        
        print("\n" + "=" * 60)
        print("🔍 DEBUG ANALYSIS:")
        print("=" * 60)
        
        if all([test1, test2, test3]):
            print("✅ All new group button tests passed")
            print("💡 Issue might be in callback execution or browser")
        else:
            print("❌ Some tests failed - check callback structure")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
