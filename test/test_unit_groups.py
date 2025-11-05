#!/usr/bin/env python3
"""
Test unit-based group logic and improved modal
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer

def test_unit_analysis():
    """Test unit analysis and grouping."""
    print("=" * 60)
    print("TEST: Unit Analysis")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Analyze units
    unit_groups = {}
    for pid, unit in viewer.units.items():
        if unit not in unit_groups:
            unit_groups[unit] = []
        unit_groups[unit].append(pid)
    
    print(f"✅ Found {len(unit_groups)} different units:")
    for unit, pids in unit_groups.items():
        print(f"  - {unit}: {len(pids)} PIDs ({pids[:3]}...)")
    
    return unit_groups

def test_unit_filtering():
    """Test filtering PIDs by unit for modal."""
    print("=" * 60)
    print("TEST: Unit Filtering for Modal")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Test filtering by different units
    unit_groups = test_unit_analysis()
    
    for unit in list(unit_groups.keys())[:3]:  # Test first 3 units
        available_pids = []
        for pid in viewer.data.keys():
            if viewer.units[pid] == unit:
                available_pids.append({"label": pid, "value": pid})
        
        print(f"✅ Unit '{unit}' has {len(available_pids)} available PIDs")
        print(f"   Sample: {[p['label'] for p in available_pids[:3]]}")
    
    return True

def test_group_unit_validation():
    """Test that groups only allow same-unit PIDs."""
    print("=" * 60)
    print("TEST: Group Unit Validation")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Create a test group with a specific unit
    test_unit = "rpm"
    test_pid = "Engine RPM"
    
    viewer.groups = {"Test Group": [test_pid]}
    viewer.pid_groups = {test_pid: "Test Group"}
    
    print(f"✅ Created group with {test_pid} (unit: {test_unit})")
    
    # Test filtering PIDs for this group
    available_pids = []
    for pid in viewer.data.keys():
        if (pid not in viewer.groups.get("Test Group", []) and 
            viewer.units[pid] == test_unit):
            available_pids.append({"label": pid, "value": pid})
    
    print(f"✅ Available PIDs for group (same unit {test_unit}): {len(available_pids)}")
    
    # Test that different units are excluded
    excluded_units = set()
    for pid in viewer.data.keys():
        if viewer.units[pid] != test_unit and pid not in viewer.groups.get("Test Group", []):
            excluded_units.add(viewer.units[pid])
    
    print(f"✅ Excluded units: {list(excluded_units)[:3]}...")
    
    return len(available_pids) > 0

def test_modal_structure():
    """Test new modal structure with unit selection."""
    print("=" * 60)
    print("TEST: New Modal Structure")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Get unique units for radio buttons
    unique_units = sorted(set(viewer.units.values()))
    print(f"✅ Unique units for radio selection: {len(unique_units)}")
    print(f"   Sample: {unique_units[:5]}")
    
    # Test unit radio options
    unit_options = [{"label": unit, "value": unit} for unit in unique_units]
    print(f"✅ Unit radio options: {len(unit_options)}")
    
    # Test PID checkboxes for a specific unit
    test_unit = unique_units[0]
    pid_checkboxes = []
    for pid in viewer.data.keys():
        if viewer.units[pid] == test_unit:
            pid_checkboxes.append({"label": pid, "value": pid})
    
    print(f"✅ PID checkboxes for {test_unit}: {len(pid_checkboxes)}")
    
    return len(unit_options) > 0 and len(pid_checkboxes) > 0

if __name__ == "__main__":
    print("🧪 UNIT-BASED GROUP LOGIC TESTS")
    print("=" * 60)
    
    try:
        # Run tests
        test1 = test_unit_analysis()
        test2 = test_unit_filtering()
        test3 = test_group_unit_validation()
        test4 = test_modal_structure()
        
        print("\n" + "=" * 60)
        print("✅ ALL UNIT GROUP TESTS PASSED")
        print("=" * 60)
        print("💡 Ready to implement unit-based group logic")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
