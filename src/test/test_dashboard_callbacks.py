#!/usr/bin/env python3
"""
Test dashboard callback functionality
"""

import unittest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from obd2_viewer.core.data_loader import OBDDataLoader
from obd2_viewer.visualization.dashboard import OBD2Dashboard


class TestDashboardCallbacks(unittest.TestCase):
    """Test dashboard callback behavior."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_csv = Path(__file__).parent / "nov_4_test_data.csv"
        
        # Load test data
        self.loader = OBDDataLoader(self.test_csv.parent)
        self.channels_data, self.units = self.loader.load_csv_files()
        
        # Create display names
        self.display_names = {}
        for channel in self.channels_data.keys():
            self.display_names[channel] = channel.replace('_', ' ').title()
    
    def test_initial_figure_creation(self):
        """Test that figure is created correctly on initialization."""
        dashboard = OBD2Dashboard(self.channels_data, self.units, self.display_names)
        
        # Test that initial figure has data
        all_channels = list(self.channels_data.keys())
        fig = dashboard.create_figure(all_channels, dashboard.min_time, dashboard.max_time, 1.0)
        
        self.assertGreater(len(fig.data), 0, "Initial figure should have traces")
        self.assertEqual(len(fig.data), len(all_channels), "Should have trace for each channel")
        
        # Verify each trace has data
        for i, trace in enumerate(fig.data):
            self.assertGreater(len(trace.x), 0, f"Trace {i} should have x data")
            self.assertGreater(len(trace.y), 0, f"Trace {i} should have y data")
        
        print(f"✅ Initial figure created with {len(fig.data)} data traces")
    
    def test_channel_controls_initialization(self):
        """Test that channel controls are properly initialized."""
        dashboard = OBD2Dashboard(self.channels_data, self.units, self.display_names)
        
        # Test channel controls creation
        controls = dashboard.create_channel_controls()
        
        self.assertEqual(len(controls), len(self.channels_data), 
                        "Should have control for each channel")
        
        # Test that all controls are checked by default
        controls_checked = dashboard.create_channel_controls(all_checked=True)
        controls_unchecked = dashboard.create_channel_controls(all_checked=False)
        
        self.assertEqual(len(controls_checked), len(controls_unchecked))
        
        print(f"✅ Channel controls initialized: {len(controls)} items")
    
    def test_show_hide_all_functionality(self):
        """Test Show All/Hide All button functionality."""
        dashboard = OBD2Dashboard(self.channels_data, self.units, self.display_names)
        
        # Test Show All
        all_channels = list(self.channels_data.keys())
        fig_all = dashboard.create_figure(all_channels, dashboard.min_time, dashboard.max_time, 1.0)
        self.assertEqual(len(fig_all.data), len(all_channels))
        
        # Test Hide All
        fig_empty = dashboard.create_figure([], dashboard.min_time, dashboard.max_time, 1.0)
        self.assertEqual(len(fig_empty.data), 0)
        
        print("✅ Show All/Hide All functionality working")
    
    def test_time_range_functionality(self):
        """Test time range functionality."""
        dashboard = OBD2Dashboard(self.channels_data, self.units, self.display_names)
        
        # Test with full time range
        all_channels = list(self.channels_data.keys())
        fig_full = dashboard.create_figure(all_channels, dashboard.min_time, dashboard.max_time, 1.0)
        self.assertEqual(len(fig_full.data), len(all_channels))
        
        # Test with partial time range
        duration = dashboard.max_time - dashboard.min_time
        mid_point = dashboard.min_time + duration / 2
        quarter_duration = duration / 4
        
        fig_partial = dashboard.create_figure(
            all_channels, 
            mid_point - quarter_duration, 
            mid_point + quarter_duration, 
            1.0
        )
        self.assertEqual(len(fig_partial.data), len(all_channels))
        
        print("✅ Time range functionality working")
    
    def test_layout_components(self):
        """Test that layout contains all required components."""
        dashboard = OBD2Dashboard(self.channels_data, self.units, self.display_names)
        
        layout = dashboard.app.layout
        layout_str = str(layout)
        
        # Check for essential components
        required_components = [
            "main-graph",
            "channel-controls-container", 
            "btn-show-all",
            "btn-hide-all",
            "initial-trigger",
            "visible-channels-store",
            "Interval"  # Interval component for initial trigger
        ]
        
        for component in required_components:
            self.assertIn(component, layout_str, 
                          f"Layout should contain {component}")
        
        print("✅ All required layout components present")
    
    def test_interval_trigger(self):
        """Test that the interval trigger is properly configured."""
        dashboard = OBD2Dashboard(self.channels_data, self.units, self.display_names)
        
        layout = dashboard.app.layout
        layout_str = str(layout)
        
        # Check for interval component with correct settings
        self.assertIn('Interval', layout_str, "Should have Interval component")
        self.assertIn("id='initial-trigger'", layout_str, "Interval should have correct ID")
        self.assertIn('interval=1000', layout_str, "Interval should be 1000ms")
        self.assertIn('n_intervals=0', layout_str, "Should start at 0 intervals")
        
        print("✅ Interval trigger properly configured")


if __name__ == '__main__':
    unittest.main(verbosity=2)
