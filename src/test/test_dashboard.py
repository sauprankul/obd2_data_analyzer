#!/usr/bin/env python3
"""
Permanent tests for OBD2 Dashboard
"""

import unittest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from obd2_viewer.core.data_loader import OBDDataLoader
from obd2_viewer.visualization.dashboard import OBD2Dashboard


class TestOBD2Dashboard(unittest.TestCase):
    """Test the OBD2 dashboard functionality."""
    
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
    
    def test_dashboard_creation(self):
        """Test dashboard creation with test data."""
        dashboard = OBD2Dashboard(self.channels_data, self.units, self.display_names)
        
        # Verify dashboard attributes
        self.assertEqual(len(dashboard.channels_data), len(self.channels_data))
        self.assertEqual(len(dashboard.units), len(self.units))
        self.assertEqual(len(dashboard.colors), len(self.channels_data))
        
        # Verify time range
        self.assertLess(dashboard.min_time, dashboard.max_time)
        
        print(f"✅ Dashboard created with {len(dashboard.channels_data)} channels")
    
    def test_figure_creation_all_channels(self):
        """Test figure creation with all channels."""
        dashboard = OBD2Dashboard(self.channels_data, self.units, self.display_names)
        
        all_channels = list(self.channels_data.keys())
        # Use the actual time range from the data
        fig = dashboard.create_figure(all_channels, dashboard.min_time, dashboard.max_time, 1.0)
        
        # Verify figure structure
        self.assertIsNotNone(fig, "Figure should be created")
        self.assertEqual(len(fig.data), len(all_channels), "Should have trace for each channel")
        
        # Verify trace data
        for i, trace in enumerate(fig.data):
            self.assertIsNotNone(trace.x, f"Trace {i} should have x data")
            self.assertIsNotNone(trace.y, f"Trace {i} should have y data")
            self.assertGreater(len(trace.x), 0, f"Trace {i} should have data points")
        
        print(f"✅ Figure created with {len(fig.data)} traces")
    
    def test_figure_creation_subset(self):
        """Test figure creation with subset of channels."""
        dashboard = OBD2Dashboard(self.channels_data, self.units, self.display_names)
        
        # Test with first 3 channels
        subset_channels = list(self.channels_data.keys())[:3]
        fig = dashboard.create_figure(subset_channels, dashboard.min_time, dashboard.max_time, 1.0)
        
        self.assertEqual(len(fig.data), len(subset_channels), 
                        "Should have trace for each selected channel")
        
        print(f"✅ Subset figure created with {len(fig.data)} traces")
    
    def test_figure_creation_empty(self):
        """Test figure creation with no channels."""
        dashboard = OBD2Dashboard(self.channels_data, self.units, self.display_names)
        
        fig = dashboard.create_figure([], 0, 100, 1.0)
        
        self.assertEqual(len(fig.data), 0, "Empty figure should have no traces")
        
        print("✅ Empty figure created correctly")
    
    def test_channel_controls_creation(self):
        """Test channel controls creation."""
        dashboard = OBD2Dashboard(self.channels_data, self.units, self.display_names)
        
        controls = dashboard.create_channel_controls()
        
        self.assertEqual(len(controls), len(self.channels_data), 
                        "Should have control for each channel")
        
        # Test with different checked states
        controls_all_checked = dashboard.create_channel_controls(all_checked=True)
        controls_all_unchecked = dashboard.create_channel_controls(all_checked=False)
        
        self.assertEqual(len(controls_all_checked), len(controls_all_unchecked))
        
        print(f"✅ Channel controls created: {len(controls)} items")
    
    def test_time_navigation(self):
        """Test time navigation functionality."""
        dashboard = OBD2Dashboard(self.channels_data, self.units, self.display_names)
        
        # Test time range
        min_time, max_time = dashboard.min_time, dashboard.max_time
        duration = max_time - min_time
        
        self.assertGreater(duration, 0, "Should have positive duration")
        
        # Test figure creation with different time ranges
        visible_channels = list(self.channels_data.keys())[:3]
        
        # Full range
        fig_full = dashboard.create_figure(visible_channels, min_time, max_time, 1.0)
        self.assertIsNotNone(fig_full)
        
        # Partial range
        mid_point = min_time + duration / 2
        fig_partial = dashboard.create_figure(
            visible_channels, 
            mid_point - 10, 
            mid_point + 10, 
            1.0
        )
        self.assertIsNotNone(fig_partial)
        
        # Zoomed
        fig_zoomed = dashboard.create_figure(visible_channels, min_time, max_time, 1.5)
        self.assertIsNotNone(fig_zoomed)
        
        print(f"✅ Time navigation working: duration {duration:.1f}s")
    
    def test_layout_creation(self):
        """Test dashboard layout creation."""
        dashboard = OBD2Dashboard(self.channels_data, self.units, self.display_names)
        
        layout = dashboard.app.layout
        self.assertIsNotNone(layout, "Layout should be created")
        
        layout_str = str(layout)
        
        # Check for key components
        self.assertIn("main-graph", layout_str, "Layout should contain main graph")
        self.assertIn("channel-controls-container", layout_str, 
                      "Layout should contain channel controls")
        self.assertIn("btn-show-all", layout_str, "Layout should contain show all button")
        self.assertIn("btn-hide-all", layout_str, "Layout should contain hide all button")
        
        print("✅ Layout created with all required components")


if __name__ == '__main__':
    unittest.main(verbosity=2)
