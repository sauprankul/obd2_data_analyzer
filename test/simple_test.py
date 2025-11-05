#!/usr/bin/env python3
"""
Simple test to verify layout rendering
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_dash_viewer import EnhancedDashOBDViewer

def simple_test():
    """Simple test of layout creation."""
    print("=== SIMPLE LAYOUT TEST ===")
    
    # Create viewer
    test_folder = Path(__file__).parent.parent / "test"
    viewer = EnhancedDashOBDViewer(csv_folder_path=test_folder)
    
    # Test the layout creation methods directly
    print("Testing create_initial_groups_display...")
    groups_display = viewer.create_initial_groups_display()
    print(f"Groups display type: {type(groups_display)}")
    print(f"Groups display length: {len(groups_display)}")
    
    print("\nTesting create_initial_pid_checkboxes...")
    pid_checkboxes = viewer.create_initial_pid_checkboxes()
    print(f"PID checkboxes type: {type(pid_checkboxes)}")
    print(f"PID checkboxes length: {len(pid_checkboxes)}")
    
    # Check if they contain actual content
    groups_str = str(groups_display)
    pid_str = str(pid_checkboxes)
    
    print(f"\n=== CONTENT CHECK ===")
    print(f"Groups contain 'Default': {'Default' in groups_str}")
    print(f"Groups contain '13 PIDs': {'13 PIDs' in groups_str}")
    print(f"PID contain 'Engine RPM': {'Engine RPM' in pid_str}")
    print(f"PID contain 'Checklist': {'Checklist' in pid_str}")
    
    # Test the full layout
    print(f"\n=== FULL LAYOUT ===")
    layout = viewer.app.layout
    layout_str = str(layout)
    
    print(f"Full layout contains 'CardBody': {'CardBody' in layout_str}")
    print(f"Full layout contains 'Engine RPM': {'Engine RPM' in layout_str}")
    print(f"Full layout contains 'btn-add-group': {'btn-add-group' in layout_str}")
    
    print("\n=== SAMPLE CONTENT ===")
    # Find and print a sample of the controls section
    if 'CardBody' in layout_str:
        start = layout_str.find('CardBody')
        sample = layout_str[start:start+500]
        print(sample)
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    simple_test()
