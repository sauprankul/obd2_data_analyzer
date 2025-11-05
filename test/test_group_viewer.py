#!/usr/bin/env python3
"""
Unit tests for group management viewer to debug callback issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer
import dash

def test_initialization():
    """Test viewer initialization and data loading."""
    print("=" * 60)
    print("TEST: Initialization")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    print(f"✅ Loaded {len(viewer.data)} PIDs")
    print(f"✅ Groups initialized: {list(viewer.groups.keys())}")
    print(f"✅ PID groups: {viewer.pid_groups}")
    
    return viewer

def test_layout_creation():
    """Test layout creation and component IDs."""
    print("=" * 60)
    print("TEST: Layout Creation")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    layout = viewer.app.layout
    
    print("🔍 Layout structure:")
    print_layout_structure(layout, indent=0)
    
    # Check for specific components
    layout_str = str(layout)
    component_ids = []
    
    def extract_component_ids(component, depth=0):
        if hasattr(component, 'id') and component.id:
            component_ids.append(component.id)
        if hasattr(component, 'children') and component.children:
            if isinstance(component.children, list):
                for child in component.children:
                    extract_component_ids(child, depth + 1)
            else:
                extract_component_ids(component.children, depth + 1)
    
    extract_component_ids(layout)
    
    print(f"\n✅ Found {len(component_ids)} component IDs:")
    for comp_id in sorted(component_ids):
        print(f"  - {comp_id}")
    
    return component_ids

def test_callback_registration():
    """Test callback registration and inputs."""
    print("=" * 60)
    print("TEST: Callback Registration")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    print("🔍 Registered callbacks:")
    callback_map = viewer.app.callback_map
    print(f"Found {len(callback_map)} callbacks")
    
    for callback_key, callback in callback_map.items():
        print(f"\nCallback: {callback_key}")
        if isinstance(callback, dict):
            print(f"  Outputs: {callback.get('outputs', 'N/A')}")
            print(f"  Inputs: {callback.get('inputs', 'N/A')}")
        else:
            print(f"  Type: {type(callback)}")
    
    # Check for problematic inputs
    print("\n🔍 Checking for problematic inputs...")
    layout_str = str(viewer.app.layout)
    
    for callback_key, callback in callback_map.items():
        if isinstance(callback, dict) and 'inputs' in callback:
            for input_item in callback['inputs']:
                input_id = input_item['id']
                if input_id not in layout_str:
                    print(f"❌ MISSING COMPONENT: {input_id}")
                else:
                    print(f"✅ Found: {input_id}")

def test_pid_controls_creation():
    """Test PID controls creation."""
    print("=" * 60)
    print("TEST: PID Controls Creation")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Test initial PID controls (should be just new group button)
    print("🔍 Creating initial PID controls...")
    try:
        controls = viewer.create_pid_controls()
        print(f"✅ Created {len(controls)} control elements")
        
        for i, control in enumerate(controls):
            print(f"  Control {i}: {type(control).__name__}")
            if hasattr(control, 'children'):
                print(f"    Children: {len(control.children) if control.children else 0}")
        
        # Test with a group
        print("\n🔍 Testing with a group...")
        viewer.groups["Test Group"] = ["Engine RPM", "Vehicle Speed"]
        viewer.pid_groups["Engine RPM"] = "Test Group"
        viewer.pid_groups["Vehicle Speed"] = "Test Group"
        
        controls_with_group = viewer.create_pid_controls()
        print(f"✅ Created {len(controls_with_group)} control elements with group")
        
    except Exception as e:
        print(f"❌ Error creating PID controls: {e}")
        import traceback
        traceback.print_exc()

def print_layout_structure(component, indent=0):
    """Recursively print layout structure."""
    indent_str = "  " * indent
    comp_name = type(component).__name__
    comp_id = getattr(component, 'id', 'no-id')
    
    print(f"{indent_str}{comp_name} (id: {comp_id})")
    
    if hasattr(component, 'children') and component.children:
        if isinstance(component.children, list):
            for i, child in enumerate(component.children):
                print(f"{indent_str}  Child {i}:")
                print_layout_structure(child, indent + 2)
        else:
            print(f"{indent_str}  Child:")
            print_layout_structure(component.children, indent + 1)

if __name__ == "__main__":
    print("🧪 GROUP VIEWER UNIT TESTS")
    print("=" * 60)
    
    try:
        # Run tests
        viewer = test_initialization()
        component_ids = test_layout_creation()
        test_callback_registration()
        test_pid_controls_creation()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
