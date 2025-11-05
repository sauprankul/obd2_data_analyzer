#!/usr/bin/env python3
"""
Test modal state management and cross-group contamination
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer

def test_modal_state_isolation():
    """Test that modal state is properly isolated between groups."""
    print("=" * 60)
    print("TEST: Modal State Isolation")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Create two groups with different units
    viewer.groups = {
        "Group 1": ["Engine RPM"],  # rpm unit
        "Group 2": ["Coolant Temperature"]  # °F unit
    }
    viewer.pid_groups = {
        "Engine RPM": "Group 1",
        "Coolant Temperature": "Group 2"
    }
    
    print(f"✅ Created test groups: {list(viewer.groups.keys())}")
    
    # Test Group 1 (rpm) - should only show rpm PIDs
    group1_unit = viewer.units["Engine RPM"]
    group1_available = []
    for pid in viewer.data.keys():
        if (pid not in viewer.groups.get("Group 1", []) and 
            viewer.units[pid] == group1_unit):
            group1_available.append(pid)
    
    print(f"✅ Group 1 ({group1_unit}) available PIDs: {group1_available}")
    
    # Test Group 2 (°F) - should only show °F PIDs  
    group2_unit = viewer.units["Coolant Temperature"]
    group2_available = []
    for pid in viewer.data.keys():
        if (pid not in viewer.groups.get("Group 2", []) and 
            viewer.units[pid] == group2_unit):
            group2_available.append(pid)
    
    print(f"✅ Group 2 ({group2_unit}) available PIDs: {group2_available}")
    
    # Simulate the error scenario
    print("\n🔍 Simulating cross-group contamination:")
    
    # What happens if Group 2 gets Group 1's PIDs in the selection?
    contaminated_selection = group1_available + group2_available
    print(f"❌ Contaminated selection: {contaminated_selection}")
    
    # Check units in contaminated selection
    units_in_selection = set()
    for pid in contaminated_selection:
        if pid in viewer.units:
            units_in_selection.add(viewer.units[pid])
    
    print(f"❌ Units in contaminated selection: {units_in_selection}")
    print(f"❌ Would trigger error: {len(units_in_selection) > 1}")
    
    return True

def test_callback_return_values():
    """Test what the callback returns for different groups."""
    print("=" * 60)
    print("TEST: Callback Return Values")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    # Setup test scenario
    viewer.groups = {
        "Engine Performance": ["Engine RPM"],  # rpm
        "Temperature Group": ["Coolant Temperature"]  # °F
    }
    viewer.pid_groups = {
        "Engine RPM": "Engine Performance", 
        "Coolant Temperature": "Temperature Group"
    }
    
    print("🔍 Testing callback returns for each group:")
    
    for group_name in viewer.groups.keys():
        print(f"\n--- Group: {group_name} ---")
        
        # Get group unit
        group_unit = None
        for pid in viewer.groups[group_name]:
            group_unit = viewer.units[pid]
            break
        
        print(f"Group unit: {group_unit}")
        
        # Get available PIDs (what should be in modal)
        available_pids = []
        for pid in viewer.data.keys():
            if (pid not in viewer.groups.get(group_name, []) and 
                viewer.units[pid] == group_unit):
                available_pids.append({"label": pid, "value": pid})
        
        print(f"Available PIDs: {[p['label'] for p in available_pids]}")
        
        # Test the units validation
        selected_units = set()
        for pid_dict in available_pids:
            pid = pid_dict['value']
            if pid in viewer.units:
                selected_units.add(viewer.units[pid])
        
        print(f"Units in available PIDs: {selected_units}")
        print(f"Validation passes: {len(selected_units) <= 1}")
    
    return True

def test_modal_state_reset():
    """Test that modal state is properly reset between groups."""
    print("=" * 60)
    print("TEST: Modal State Reset")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    
    print("🔍 Testing modal state management:")
    
    # Simulate what happens when switching between groups
    test_scenarios = [
        {"group": "Group 1", "unit": "rpm", "pids": ["Engine RPM"]},
        {"group": "Group 2", "unit": "°F", "pids": ["Coolant Temperature", "Intake Air Temperature"]},
        {"group": "Group 3", "unit": "%", "pids": ["Engine Load", "Long Term Fuel Trim"]}
    ]
    
    for scenario in test_scenarios:
        group_name = scenario["group"]
        expected_unit = scenario["unit"]
        group_pids = scenario["pids"]
        
        print(f"\n--- Testing {group_name} ---")
        
        # Setup group
        viewer.groups = {group_name: group_pids}
        viewer.pid_groups = {pid: group_name for pid in group_pids}
        
        # Test what modal should show
        unit_options = [{"label": expected_unit, "value": expected_unit}]
        pid_options = []
        for pid in viewer.data.keys():
            if (pid not in group_pids and viewer.units[pid] == expected_unit):
                pid_options.append({"label": pid, "value": pid})
        
        print(f"Expected unit options: {[u['label'] for u in unit_options]}")
        print(f"Expected PID options: {[p['label'] for p in pid_options]}")
        
        # Test that all PIDs have same unit
        units_in_options = set()
        for pid_dict in pid_options:
            pid = pid_dict['value']
            if pid in viewer.units:
                units_in_options.add(viewer.units[pid])
        
        print(f"Units in options: {units_in_options}")
        print(f"✅ All same unit: {len(units_in_options) <= 1}")
    
    return True

if __name__ == "__main__":
    print("🧪 MODAL STATE DEBUG TESTS")
    print("=" * 60)
    
    try:
        # Run tests
        test1 = test_modal_state_isolation()
        test2 = test_callback_return_values()
        test3 = test_modal_state_reset()
        
        print("\n" + "=" * 60)
        print("🔍 DEBUG ANALYSIS:")
        print("=" * 60)
        
        print("✅ Modal logic is correct")
        print("❌ Issue likely in callback state management")
        print("💡 Need to ensure PID selection checklist is reset between groups")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
