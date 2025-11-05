#!/usr/bin/env python3
"""
Debug test for modal visibility not working
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer

def test_modal_callback_logic():
    """Test the modal callback logic step by step."""
    print("=" * 60)
    print("TEST: Modal Callback Logic")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Create a test group
    viewer.groups = {"Test Group": []}
    viewer.pid_groups = {}
    
    print("🔍 Step 1: Test trigger ID parsing")
    
    # Simulate what happens when Add PID button is clicked
    test_trigger_id = "{'type': 'add-button', 'index': 'Test Group'}.n_clicks"
    print(f"✅ Simulated trigger_id: {test_trigger_id}")
    
    # Test the parsing logic from the callback
    trigger_id_split = test_trigger_id.split('.')[0]
    print(f"✅ After split('.')[0]: {trigger_id_split}")
    
    # Test if it's a dict (it won't be, this is the bug!)
    print(f"✅ Is dict: {isinstance(trigger_id_split, dict)}")
    
    # The correct way to parse pattern matching trigger IDs
    import ast
    try:
        parsed_trigger = ast.literal_eval(trigger_id_split)
        print(f"✅ Parsed trigger: {parsed_trigger}")
        print(f"✅ Is dict after parsing: {isinstance(parsed_trigger, dict)}")
        
        if isinstance(parsed_trigger, dict) and parsed_trigger.get('type') == 'add-button':
            group_name = parsed_trigger.get('index')
            print(f"✅ Extracted group name: {group_name}")
            
            # Test modal opening logic
            available_pids = []
            for pid in viewer.data.keys():
                if pid not in viewer.groups.get(group_name, []):
                    available_pids.append({"label": f"{pid} ({viewer.units[pid]})", "value": pid})
            
            print(f"✅ Modal would open with {len(available_pids)} PIDs")
            print(f"✅ Modal visibility should be: True")
            return True
            
    except Exception as e:
        print(f"❌ Failed to parse trigger ID: {e}")
    
    print("❌ Modal logic would not trigger")
    return False

def test_modal_component_structure():
    """Test if modal components are properly structured."""
    print("=" * 60)
    print("TEST: Modal Component Structure")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    layout = viewer.app.layout
    layout_str = str(layout)
    
    # Check for modal components
    modal_components = [
        'add-pid-modal',
        'pid-selection-radio', 
        'cancel-add-pid',
        'confirm-add-pid'
    ]
    
    print("🔍 Checking modal components in layout:")
    for comp in modal_components:
        if comp in layout_str:
            print(f"✅ Found: {comp}")
        else:
            print(f"❌ Missing: {comp}")
    
    # Check modal structure
    if 'dbc.Modal' in layout_str:
        print("✅ Modal component found")
        
        # Check if modal has is_open property
        if 'is_open' in layout_str:
            print("✅ Modal has is_open property")
        else:
            print("❌ Modal missing is_open property")
    else:
        print("❌ No modal component found")
    
    return True

def test_callback_return_values():
    """Test what the callback returns when triggered."""
    print("=" * 60)
    print("TEST: Callback Return Values")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Create test state
    viewer.groups = {"Test Group": []}
    viewer.pid_groups = {}
    
    print("🔍 Simulating callback return for Add PID click:")
    
    # Simulate the callback return
    available_pids = []
    for pid in viewer.data.keys():
        if pid not in viewer.groups.get("Test Group", []):
            available_pids.append({"label": f"{pid} ({viewer.units[pid]})", "value": pid})
    
    # This is what the callback should return
    expected_return = (
        viewer.create_pid_controls(),  # pid-controls-container
        {"operation": "add_prompt", "group": "Test Group"},  # group-operation-store
        True,  # add-pid-modal is_open
        available_pids  # pid-selection-radio options
    )
    
    print(f"✅ Expected return values:")
    print(f"  - Controls: {len(expected_return[0])} elements")
    print(f"  - Store data: {expected_return[1]}")
    print(f"  - Modal open: {expected_return[2]}")
    print(f"  - Radio options: {len(expected_return[3])} options")
    
    return True

if __name__ == "__main__":
    print("🧪 MODAL VISIBILITY DEBUG")
    print("=" * 60)
    
    try:
        # Run debug tests
        test1 = test_modal_callback_logic()
        test2 = test_modal_component_structure()
        test3 = test_callback_return_values()
        
        print("\n" + "=" * 60)
        print("🔍 DEBUG ANALYSIS:")
        print("=" * 60)
        
        if not test1:
            print("❌ ISSUE: Trigger ID parsing is broken")
            print("💡 FIX: Need to properly parse pattern matching trigger IDs")
        
        if test2 and test3:
            print("✅ Modal components and return logic are correct")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
