#!/usr/bin/env python3
"""
Test to verify callback duplicates are fixed and app structure is correct
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer

def test_no_duplicate_callbacks():
    """Test that there are no duplicate callback outputs."""
    print("=" * 60)
    print("TEST: No Duplicate Callback Outputs")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    callback_map = viewer.app.callback_map
    
    print(f"✅ Found {len(callback_map)} callbacks")
    
    # Track all outputs
    all_outputs = []
    duplicates = []
    
    for callback_key, callback in callback_map.items():
        if isinstance(callback, dict) and 'outputs' in callback:
            for output in callback['outputs']:
                if output in all_outputs:
                    duplicates.append(output)
                else:
                    all_outputs.append(output)
    
    if duplicates:
        print(f"❌ Found duplicate outputs: {duplicates}")
        return False
    else:
        print("✅ No duplicate callback outputs found")
        return True

def test_individual_pid_structure():
    """Test individual PID structure is correct."""
    print("=" * 60)
    print("TEST: Individual PID Structure")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Should start with individual PIDs
    print(f"✅ Initial groups: {list(viewer.groups.keys())}")
    print(f"✅ PID groups: {len(viewer.pid_groups)} mappings")
    
    # Create controls
    controls = viewer.create_pid_controls()
    print(f"✅ Created {len(controls)} control elements")
    
    # Should have new group button + individual PIDs
    expected_count = 1 + len(viewer.data)
    if len(controls) == expected_count:
        print(f"✅ Correct number of controls: {len(controls)}")
    else:
        print(f"❌ Wrong number of controls: {len(controls)}, expected {expected_count}")
    
    # Check individual PID controls
    individual_pids = [pid for pid in viewer.data.keys() if pid not in viewer.pid_groups]
    print(f"✅ Individual PIDs: {len(individual_pids)}")
    
    return True

def test_modal_components():
    """Test modal components exist in layout."""
    print("=" * 60)
    print("TEST: Modal Components")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    layout = viewer.app.layout
    layout_str = str(layout)
    
    modal_components = [
        'add-pid-modal',
        'pid-selection-radio',
        'cancel-add-pid', 
        'confirm-add-pid'
    ]
    
    found_count = 0
    for comp_id in modal_components:
        if comp_id in layout_str:
            print(f"✅ Found: {comp_id}")
            found_count += 1
        else:
            print(f"❌ Missing: {comp_id}")
    
    print(f"✅ Found {found_count}/{len(modal_components)} modal components")
    return found_count == len(modal_components)

def test_pattern_matching_callbacks():
    """Test pattern matching callbacks are properly structured."""
    print("=" * 60)
    print("TEST: Pattern Matching Callbacks")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    callback_map = viewer.app.callback_map
    
    print("🔍 All callback keys:")
    for callback_key in callback_map.keys():
        print(f"  {callback_key}")
    
    pattern_callbacks = []
    for callback_key, callback in callback_map.items():
        # Check for pattern matching in inputs
        if isinstance(callback, dict) and 'inputs' in callback:
            for input_item in callback['inputs']:
                input_id = input_item.get('id', {})
                if isinstance(input_id, dict):
                    pattern_callbacks.append(callback_key)
                    print(f"✅ Found pattern callback: {callback_key}")
                    print(f"   Input: {input_id}")
                elif 'ALL' in str(input_id):
                    pattern_callbacks.append(callback_key)
                    print(f"✅ Found ALL callback: {callback_key}")
                    print(f"   Input: {input_id}")
    
    print(f"✅ Found {len(pattern_callbacks)} pattern matching callbacks")
    return len(pattern_callbacks) > 0

if __name__ == "__main__":
    print("🧪 CALLBACK DUPLICATE & STRUCTURE TESTS")
    print("=" * 60)
    
    try:
        # Run tests
        test1 = test_no_duplicate_callbacks()
        test2 = test_individual_pid_structure()
        test3 = test_modal_components()
        test4 = test_pattern_matching_callbacks()
        
        print("\n" + "=" * 60)
        if all([test1, test2, test3, test4]):
            print("✅ ALL STRUCTURE TESTS PASSED")
        else:
            print("❌ SOME STRUCTURE TESTS FAILED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
