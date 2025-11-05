#!/usr/bin/env python3
"""
Debug test for modal not opening when clicking Add PID
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer

def test_modal_callback_trigger():
    """Test if modal callback can be triggered properly."""
    print("=" * 60)
    print("TEST: Modal Callback Trigger")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Get the callback
    callback_map = viewer.app.callback_map
    group_callback = None
    
    for callback_key, callback in callback_map.items():
        if 'group-operation-store' in callback_key:
            group_callback = callback
            print(f"✅ Found callback: {callback_key}")
            break
    
    if not group_callback:
        print("❌ Group callback not found")
        return False
    
    # Test callback inputs
    inputs = group_callback.get('inputs', [])
    print(f"✅ Callback has {len(inputs)} inputs")
    
    print("🔍 All callback inputs:")
    for i, input_item in enumerate(inputs):
        input_id = input_item.get('id', {})
        print(f"  Input {i}: {input_id} (type: {type(input_id)})")
        
        # Check pattern matching input
        if isinstance(input_id, dict) and input_id.get('type') == 'add-button':
            print(f"✅ Pattern input found: {input_id}")
        elif 'ALL' in str(input_id):
            print(f"✅ ALL input found: {input_id}")
    
    # Test callback outputs
    outputs = group_callback.get('outputs', [])
    print(f"✅ Callback has {len(outputs)} outputs")
    
    print("🔍 All callback outputs:")
    for i, output_item in enumerate(outputs):
        output_id = output_item.get('id', '')
        print(f"  Output {i}: {output_item}")
    
    return True

def test_modal_button_creation():
    """Test if modal buttons are created correctly in layout."""
    print("=" * 60)
    print("TEST: Modal Button Creation")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Create a test group
    viewer.groups = {"Test Group": []}
    viewer.pid_groups = {}
    
    # Create controls
    controls = viewer.create_pid_controls()
    
    print("🔍 Searching for Add PID buttons in created controls...")
    
    add_buttons = []
    
    def find_add_buttons(component, depth=0):
        if hasattr(component, 'id') and component.id:
            if isinstance(component.id, dict) and component.id.get('type') == 'add-button':
                add_buttons.append(component.id)
                print(f"✅ Found Add PID button at depth {depth}: {component.id}")
        
        if hasattr(component, 'children') and component.children and depth < 10:
            if isinstance(component.children, list):
                for child in component.children:
                    find_add_buttons(child, depth + 1)
            else:
                find_add_buttons(component.children, depth + 1)
    
    for i, control in enumerate(controls):
        print(f"🔍 Checking control {i}...")
        find_add_buttons(control, 0)
    
    print(f"✅ Total Add PID buttons found: {len(add_buttons)}")
    
    # Check if buttons are in the actual app layout
    layout = viewer.app.layout
    layout_str = str(layout)
    
    layout_buttons = []
    if '"type": "add-button"' in layout_str:
        print("✅ Add PID buttons found in app layout")
        # Extract button info
        import re
        pattern = r'\{"type": "add-button", "index": "([^"]+)"\}'
        matches = re.findall(pattern, layout_str)
        layout_buttons = matches
        print(f"✅ Layout buttons: {layout_buttons}")
    else:
        print("❌ No Add PID buttons found in app layout")
    
    return len(add_buttons) > 0 and len(layout_buttons) > 0

def test_callback_context_simulation():
    """Test simulating callback context to see if logic works."""
    print("=" * 60)
    print("TEST: Callback Context Simulation")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Create test data
    viewer.groups = {"Test Group": []}
    viewer.pid_groups = {}
    
    print("🔍 Simulating callback trigger...")
    
    # Test the trigger ID parsing logic
    test_trigger_id = {"type": "add-button", "index": "Test Group"}
    
    print(f"✅ Test trigger ID: {test_trigger_id}")
    print(f"✅ Is dict: {isinstance(test_trigger_id, dict)}")
    print(f"✅ Has type: {test_trigger_id.get('type') == 'add-button'}")
    print(f"✅ Group name: {test_trigger_id.get('index')}")
    
    # Test available PIDs logic
    available_pids = []
    for pid in viewer.data.keys():
        if pid not in viewer.groups.get("Test Group", []):
            available_pids.append({"label": f"{pid} ({viewer.units[pid]})", "value": pid})
    
    print(f"✅ Available PIDs for Test Group: {len(available_pids)}")
    if available_pids:
        print(f"✅ First few: {available_pids[:3]}")
    
    return True

if __name__ == "__main__":
    print("🧪 MODAL DEBUG TESTS")
    print("=" * 60)
    
    try:
        # Run debug tests
        test1 = test_modal_callback_trigger()
        test2 = test_modal_button_creation()
        test3 = test_callback_context_simulation()
        
        print("\n" + "=" * 60)
        if all([test1, test2, test3]):
            print("✅ ALL MODAL DEBUG TESTS PASSED")
            print("💡 Modal should work - check browser console for errors")
        else:
            print("❌ SOME MODAL DEBUG TESTS FAILED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
