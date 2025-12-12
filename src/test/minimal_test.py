#!/usr/bin/env python3
"""
Minimal test to find the exact issue
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def minimal_dashboard_test():
    """Create the absolute minimal dashboard to test."""
    
    print("🔍 MINIMAL DASHBOARD TEST")
    print("=" * 40)
    
    try:
        import dash
        from dash import dcc, html, Input, Output
        import plotly.graph_objects as go
        
        # Create minimal Dash app
        app = dash.Dash(__name__)
        
        # Create simple figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 1, 2], name='Test Data'))
        
        app.layout = html.Div([
            html.H1("Minimal Test"),
            dcc.Graph(id='test-graph', figure=fig),
            html.Div(id='status')
        ])
        
        print("✅ Minimal app created successfully")
        
        # Now test the actual dashboard creation
        from obd2_viewer.core.data_loader import OBDDataLoader
        from obd2_viewer.visualization.dashboard import OBD2Dashboard
        
        test_csv = Path(__file__).parent / "src/test/nov_4_test_data.csv"
        
        # Load data
        loader = OBDDataLoader(test_csv.parent)
        channels_data, units = loader.load_csv_files()
        
        print(f"✅ Loaded {len(channels_data)} channels")
        
        # Create dashboard
        display_names = {}
        for channel in channels_data.keys():
            display_names[channel] = channel.replace('_', ' ').title()
        
        dashboard = OBD2Dashboard(channels_data, units, display_names)
        
        print(f"✅ Dashboard created")
        
        # Test figure creation directly
        all_channels = list(channels_data.keys())
        fig = dashboard.create_figure(all_channels, dashboard.min_time, dashboard.max_time, 1.0)
        
        print(f"✅ Figure created with {len(fig.data)} traces")
        
        # Check if figure has actual data
        if len(fig.data) > 0:
            for i, trace in enumerate(fig.data[:3]):
                print(f"   Trace {i+1}: {trace.name}")
                print(f"     Points: {len(trace.x)}")
                if len(trace.x) > 0:
                    print(f"     X range: {min(trace.x):.1f} - {max(trace.x):.1f}")
                    print(f"     Y range: {min(trace.y):.1f} - {max(trace.y):.1f}")
                else:
                    print("     ❌ NO DATA!")
        
        # Test the layout
        layout = dashboard.app.layout
        layout_str = str(layout)
        
        print(f"\n🔍 LAYOUT ANALYSIS:")
        print(f"   Length: {len(layout_str)} chars")
        
        # Check for key components
        checks = {
            "main-graph": "main-graph" in layout_str,
            "channel-controls": "channel-controls-container" in layout_str,
            "interval": "Interval" in layout_str,
            "initial-trigger": "initial-trigger" in layout_str,
            "show-all": "btn-show-all" in layout_str,
            "hide-all": "btn-hide-all" in layout_str
        }
        
        for component, found in checks.items():
            status = "✅" if found else "❌"
            print(f"   {status} {component}")
        
        # Test callback map
        if hasattr(dashboard.app, 'callback_map'):
            callbacks = list(dashboard.app.callback_map.keys())
            print(f"\n🔍 CALLBACK ANALYSIS:")
            print(f"   Total callbacks: {len(callbacks)}")
            
            for i, callback in enumerate(callbacks):
                print(f"   {i+1}. {callback}")
        
        print(f"\n🎯 ISSUE DIAGNOSIS:")
        if not all(checks.values()):
            missing = [k for k, v in checks.items() if not v]
            print(f"   ❌ Missing components: {missing}")
        else:
            print(f"   ✅ All components present")
        
        if len(fig.data) == 0:
            print(f"   ❌ Figure has no traces")
        else:
            print(f"   ✅ Figure has {len(fig.data)} traces")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = minimal_dashboard_test()
    if success:
        print("\n✅ Minimal test completed")
        print("📱 Check the analysis above for issues")
    else:
        print("\n❌ Minimal test failed")
