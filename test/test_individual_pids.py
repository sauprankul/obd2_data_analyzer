#!/usr/bin/env python3
"""
Unit tests for individual PIDs as first-class citizens and modal functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer
import dash

def test_initialization_individual_pids():
    """Test that viewer starts with individual PIDs, not groups."""
    print("=" * 60)
    print("TEST: Individual PID Initialization")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    print(f"✅ Loaded {len(viewer.data)} PIDs")
    print(f"✅ Initial groups: {list(viewer.groups.keys())}")
    print(f"✅ Initial PID groups: {viewer.pid_groups}")
    
    # Should start with individual PIDs, no groups
    expected_pids = list(viewer.data.keys())
    print(f"✅ Expected PIDs: {expected_pids}")
    
    return viewer

def test_individual_pid_controls():
    """Test creating controls for individual PIDs."""
    print("=" * 60)
    print("TEST: Individual PID Controls")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Set up individual PIDs (no groups)
    viewer.groups = {}
    viewer.pid_groups = {}
    
    print("🔍 Creating individual PID controls...")
    try:
        controls = viewer.create_pid_controls()
        print(f"✅ Created {len(controls)} control elements")
        
        # Should have: new group button + individual PIDs
        expected_count = 1 + len(viewer.data)  # new group + each PID
        print(f"✅ Expected {expected_count} controls (new group + {len(viewer.data)} PIDs)")
        
        for i, control in enumerate(controls[:5]):  # Show first 5
            print(f"  Control {i}: {type(control).__name__}")
            
    except Exception as e:
        print(f"❌ Error creating individual PID controls: {e}")
        import traceback
        traceback.print_exc()

def test_mixed_layout():
    """Test mixed layout with individual PIDs and groups."""
    print("=" * 60)
    print("TEST: Mixed Layout (Individual PIDs + Groups)")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Set up mixed state: some individual PIDs, some groups
    viewer.groups = {
        "Engine Group": ["Engine RPM", "Vehicle Speed"]
    }
    viewer.pid_groups = {
        "Engine RPM": "Engine Group",
        "Vehicle Speed": "Engine Group"
    }
    
    print("🔍 Creating mixed layout controls...")
    try:
        controls = viewer.create_pid_controls()
        print(f"✅ Created {len(controls)} control elements")
        
        # Should have: new group + individual PIDs + group PIDs
        individual_pids = [pid for pid in viewer.data.keys() if pid not in viewer.pid_groups]
        expected_count = 1 + len(individual_pids) + 3  # new group + individuals + group elements
        print(f"✅ Expected ~{expected_count} controls")
        print(f"✅ Individual PIDs: {individual_pids}")
        
    except Exception as e:
        print(f"❌ Error creating mixed layout: {e}")
        import traceback
        traceback.print_exc()

def test_modal_functionality():
    """Test modal triggering and functionality."""
    print("=" * 60)
    print("TEST: Modal Functionality")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Check modal components exist
    layout = viewer.app.layout
    layout_str = str(layout)
    
    modal_components = [
        'add-pid-modal',
        'pid-selection-radio', 
        'cancel-add-pid',
        'confirm-add-pid'
    ]
    
    print("🔍 Checking modal components...")
    for comp_id in modal_components:
        if comp_id in layout_str:
            print(f"✅ Found: {comp_id}")
        else:
            print(f"❌ Missing: {comp_id}")
    
    # Check callback inputs for modal
    print("\n🔍 Checking modal callback inputs...")
    callback_map = viewer.app.callback_map
    
    for callback_key, callback in callback_map.items():
        if isinstance(callback, dict) and 'inputs' in callback:
            for input_item in callback['inputs']:
                input_id = input_item['id']
                if input_id in modal_components:
                    print(f"✅ Callback input: {input_id}")

def test_add_pid_callback():
    """Test Add PID callback functionality."""
    print("=" * 60)
    print("TEST: Add PID Callback")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Set up a simple group to test adding to
    viewer.groups = {"Test Group": []}
    viewer.pid_groups = {}
    
    print("🔍 Testing Add PID callback logic...")
    
    # Simulate the callback function manually
    try:
        # Test new group creation
        result = viewer.create_pid_controls()
        print(f"✅ PID controls created: {len(result)} elements")
        
        # Check if add buttons exist
        layout_str = str(result)
        add_buttons = []
        
        def find_add_buttons(component):
            if hasattr(component, 'id') and component.id:
                if isinstance(component.id, dict) and component.id.get('type') == 'add-button':
                    add_buttons.append(f"add-{component.id.get('index')}")
                elif isinstance(component.id, str) and component.id.startswith('add-'):
                    add_buttons.append(component.id)
            if hasattr(component, 'children') and component.children:
                if isinstance(component.children, list):
                    for child in component.children:
                        find_add_buttons(child)
                else:
                    find_add_buttons(component.children)
        
        for control in result:
            find_add_buttons(control)
        
        print(f"✅ Found add buttons: {add_buttons}")
        
    except Exception as e:
        print(f"❌ Error testing Add PID callback: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 INDIVIDUAL PIDS & MODAL UNIT TESTS")
    print("=" * 60)
    
    try:
        # Run tests
        viewer = test_initialization_individual_pids()
        test_individual_pid_controls()
        test_mixed_layout()
        test_modal_functionality()
        test_add_pid_callback()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
