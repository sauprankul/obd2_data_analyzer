#!/usr/bin/env python3
"""
Debug script to check layout content
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enhanced_dash_viewer import EnhancedDashOBDViewer

def debug_layout():
    """Debug the layout content."""
    print("=== DEBUGGING LAYOUT ===")
    
    # Create viewer
    test_folder = Path(__file__).parent.parent / "test"
    viewer = EnhancedDashOBDViewer(csv_folder_path=test_folder)
    
    print(f"Data loaded: {len(viewer.data)} PIDs")
    print(f"Groups: {viewer.groups}")
    
    # Get layout
    layout = viewer.app.layout
    layout_str = str(layout)
    
    print(f"\n=== LAYOUT ANALYSIS ===")
    print(f"Layout type: {type(layout)}")
    print(f"Layout length: {len(layout_str)}")
    
    # Check for key components
    checks = [
        'PID Selection & Groups',
        'Engine RPM',
        'Vehicle Speed', 
        'groups-container',
        'pid-checkboxes-container',
        'btn-add-group',
        'Checklist'
    ]
    
    print(f"\n=== COMPONENT CHECKS ===")
    for check in checks:
        found = check in layout_str
        print(f"'{check}': {'✅ FOUND' if found else '❌ MISSING'}")
        
    # Look for actual content
    print(f"\n=== CONTENT SEARCH ===")
    if 'Engine RPM' in layout_str:
        print("✅ Engine RPM found in layout")
        # Find context around Engine RPM
        idx = layout_str.find('Engine RPM')
        context = layout_str[max(0, idx-100):idx+200]
        print(f"Context: {context}")
    else:
        print("❌ Engine RPM NOT found in layout")
        
    # Check if groups container has content
    if 'Default (' in layout_str:
        print("✅ Group content found")
        # Extract group info
        import re
        groups = re.findall(r'Default \((\d+) PIDs\)', layout_str)
        print(f"Groups found: {groups}")
    else:
        print("❌ No group content found")
        
    print(f"\n=== RAW LAYOUT SNIPPET ===")
    print(layout_str[:2000])
    print("...")

if __name__ == "__main__":
    debug_layout()
