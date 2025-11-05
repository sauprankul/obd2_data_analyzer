#!/usr/bin/env python3
"""
Test for duplicate component IDs in the layout
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer

def find_all_component_ids(component, id_list=None, depth=0):
    """Recursively find all component IDs in the layout."""
    if id_list is None:
        id_list = []
    
    if depth > 20:  # Prevent infinite recursion
        return id_list
    
    # Check if component has an ID
    if hasattr(component, 'id') and component.id is not None:
        id_list.append(component.id)
    
    # Check children
    if hasattr(component, 'children') and component.children:
        if isinstance(component.children, list):
            for child in component.children:
                find_all_component_ids(child, id_list, depth + 1)
        else:
            find_all_component_ids(component.children, id_list, depth + 1)
    
    return id_list

def test_duplicate_ids():
    """Test for duplicate component IDs."""
    print("=" * 60)
    print("TEST: Duplicate Component IDs")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    layout = viewer.app.layout
    
    # Find all IDs
    all_ids = find_all_component_ids(layout)
    
    print(f"✅ Total components found: {len(all_ids)}")
    
    # Check for duplicates
    id_counts = {}
    duplicates = []
    
    for component_id in all_ids:
        # Convert to string for dict key
        id_str = str(component_id)
        if id_str in id_counts:
            id_counts[id_str] += 1
            if id_counts[id_str] == 2:  # First time we found a duplicate
                duplicates.append(id_str)
        else:
            id_counts[id_str] = 1
    
    print(f"✅ Unique IDs: {len(id_counts)}")
    
    if duplicates:
        print(f"❌ Found {len(duplicates)} duplicate IDs:")
        for dup_id in duplicates:
            print(f"  - {dup_id} (appears {id_counts[dup_id]} times)")
    else:
        print("✅ No duplicate IDs found")
    
    return len(duplicates) == 0

def test_checkbox_ids():
    """Specifically test checkbox IDs."""
    print("=" * 60)
    print("TEST: Checkbox IDs")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    layout = viewer.app.layout
    
    # Find all checkbox-related IDs
    all_ids = find_all_component_ids(layout)
    
    checkbox_ids = []
    for component_id in all_ids:
        id_str = str(component_id)
        if 'checkbox' in id_str.lower():
            checkbox_ids.append(component_id)
    
    print(f"✅ Found {len(checkbox_ids)} checkbox-related IDs:")
    for checkbox_id in checkbox_ids:
        print(f"  - {checkbox_id}")
    
    # Check for duplicates in checkbox IDs
    checkbox_strs = [str(cid) for cid in checkbox_ids]
    unique_checkbox_strs = set(checkbox_strs)
    
    if len(checkbox_strs) != len(unique_checkbox_strs):
        print(f"❌ Found duplicate checkbox IDs!")
        duplicates = []
        for cid in checkbox_strs:
            if checkbox_strs.count(cid) > 1 and cid not in duplicates:
                duplicates.append(cid)
                print(f"  - Duplicate: {cid} (appears {checkbox_strs.count(cid)} times)")
    else:
        print("✅ No duplicate checkbox IDs found")
    
    return len(checkbox_strs) == len(unique_checkbox_strs)

def test_layout_structure():
    """Test the overall layout structure for issues."""
    print("=" * 60)
    print("TEST: Layout Structure")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    print("🔍 Checking layout creation...")
    
    # Test PID controls creation
    try:
        pid_controls = viewer.create_pid_controls()
        print(f"✅ PID controls created: {len(pid_controls)} elements")
        
        # Check IDs in PID controls
        control_ids = find_all_component_ids(pid_controls)
        print(f"✅ PID controls have {len(control_ids)} IDs")
        
        # Check for duplicates in PID controls
        control_strs = [str(cid) for cid in control_ids]
        unique_control_strs = set(control_strs)
        
        if len(control_strs) != len(unique_control_strs):
            print(f"❌ PID controls have duplicate IDs!")
            for cid in control_strs:
                if control_strs.count(cid) > 1:
                    print(f"  - Duplicate in controls: {cid}")
        else:
            print("✅ PID controls have unique IDs")
        
    except Exception as e:
        print(f"❌ Error creating PID controls: {e}")
        return False
    
    # Test app layout
    try:
        layout = viewer.app.layout
        print(f"✅ App layout created successfully")
        
        layout_ids = find_all_component_ids(layout)
        print(f"✅ App layout has {len(layout_ids)} total IDs")
        
    except Exception as e:
        print(f"❌ Error creating app layout: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 DUPLICATE ID DEBUG TESTS")
    print("=" * 60)
    
    try:
        # Run tests
        test1 = test_duplicate_ids()
        test2 = test_checkbox_ids()
        test3 = test_layout_structure()
        
        print("\n" + "=" * 60)
        print("🔍 DEBUG ANALYSIS:")
        print("=" * 60)
        
        if not test1:
            print("❌ DUPLICATE IDs FOUND - Need to fix layout structure")
        
        if not test2:
            print("❌ DUPLICATE CHECKBOX IDs - Check checkbox creation")
        
        if test3:
            print("✅ Layout structure is correct")
        else:
            print("❌ Layout structure has issues")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
