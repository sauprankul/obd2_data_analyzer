#!/usr/bin/env python3
"""
Simple test to check callback registration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from working_viewer import WorkingOBDViewer

def test_simple_callback():
    """Test simple callback registration."""
    print("=" * 60)
    print("TEST: Simple Callback Registration")
    print("=" * 60)
    
    viewer = WorkingOBDViewer()
    callback_map = viewer.app.callback_map
    
    print(f"✅ Total callbacks found: {len(callback_map)}")
    
    for callback_key, callback in callback_map.items():
        print(f"\n🔍 Callback: {callback_key}")
        
        if isinstance(callback, dict):
            inputs = callback.get('inputs', [])
            outputs = callback.get('outputs', [])
            print(f"  Inputs: {len(inputs)}")
            print(f"  Outputs: {len(outputs)}")
            
            if outputs:
                print("  ✅ Has outputs")
                for i, output in enumerate(outputs):
                    print(f"    Output {i}: {output}")
            else:
                print("  ❌ No outputs")
        else:
            print(f"  Type: {type(callback)}")
            print(f"  Value: {callback}")

if __name__ == "__main__":
    test_simple_callback()
