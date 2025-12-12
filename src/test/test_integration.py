#!/usr/bin/env python3
"""
Integration tests for the complete OBD2 workflow
"""

import unittest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from obd2_viewer.core.data_loader import OBDDataLoader
from obd2_viewer.visualization.dashboard import OBD2Dashboard
from obd2_viewer.app.main_application import OBD2ViewerApp


class TestIntegration(unittest.TestCase):
    """Test the complete integration workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_csv = Path(__file__).parent / "nov_4_test_data.csv"
    
    def test_complete_workflow(self):
        """Test the complete workflow from CSV to dashboard."""
        # Step 1: Load CSV data
        loader = OBDDataLoader(self.test_csv.parent)
        channels_data, units = loader.load_csv_files()
        
        self.assertGreater(len(channels_data), 0, "Should load channels")
        self.assertGreater(len(units), 0, "Should load units")
        
        # Step 2: Create dashboard
        display_names = {}
        for channel in channels_data.keys():
            display_names[channel] = channel.replace('_', ' ').title()
        
        dashboard = OBD2Dashboard(channels_data, units, display_names)
        
        self.assertIsNotNone(dashboard, "Dashboard should be created")
        
        # Step 3: Test figure creation
        all_channels = list(channels_data.keys())
        fig = dashboard.create_figure(all_channels, 0, 100, 1.0)
        
        self.assertEqual(len(fig.data), len(all_channels), 
                        "Figure should have all channels")
        
        # Step 4: Test channel controls
        controls = dashboard.create_channel_controls()
        self.assertEqual(len(controls), len(all_channels), 
                        "Should have controls for all channels")
        
        print(f"✅ Complete workflow: {len(channels_data)} channels -> dashboard -> visualization")
    
    def test_main_application_integration(self):
        """Test integration with main application."""
        import tempfile
        import shutil
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Copy test CSV to temp directory
            test_csv_copy = Path(temp_dir) / "test.csv"
            shutil.copy2(self.test_csv, test_csv_copy)
            
            # Create main application
            cache_file = Path(temp_dir) / "cache.json"
            app = OBD2ViewerApp(str(cache_file))
            
            # Test directory validation
            is_valid, message = app.validate_data_directory(temp_dir)
            self.assertTrue(is_valid, f"Directory should be valid: {message}")
            
            # Test dashboard creation
            app.create_dashboard_from_directory(temp_dir)
            self.assertIsNotNone(app.obd_dashboard, "Dashboard should be created")
            
            # Test viewer page creation
            viewer_page = app.create_viewer_page()
            viewer_str = str(viewer_page)
            
            self.assertIn("main-graph", viewer_str, "Viewer should contain main graph")
            self.assertIn("Channel Controls", viewer_str, "Viewer should contain controls")
            
            print("✅ Main application integration working")
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_data_consistency(self):
        """Test data consistency across components."""
        # Load data through loader
        loader = OBDDataLoader(self.test_csv.parent)
        channels_data, units = loader.load_csv_files()
        
        # Create dashboard
        display_names = {}
        for channel in channels_data.keys():
            display_names[channel] = channel.replace('_', ' ').title()
        
        dashboard = OBD2Dashboard(channels_data, units, display_names)
        
        # Verify consistency
        self.assertEqual(set(dashboard.channels_data.keys()), 
                        set(channels_data.keys()),
                        "Dashboard should have same channels as loader")
        
        self.assertEqual(set(dashboard.units.keys()), 
                        set(units.keys()),
                        "Dashboard should have same units as loader")
        
        # Test figure data consistency with correct time range
        all_channels = list(channels_data.keys())
        fig = dashboard.create_figure(all_channels, dashboard.min_time, dashboard.max_time, 1.0)
        
        for i, (channel, df) in enumerate(channels_data.items()):
            if i < len(fig.data):  # Check first few traces
                trace = fig.data[i]
                self.assertEqual(len(trace.x), len(df), 
                               f"Trace {i} should have same data points as DataFrame")
        
        print("✅ Data consistency verified across all components")
    
    def test_error_handling(self):
        """Test error handling in integration."""
        # Test with non-existent directory - should return empty data, not raise exception
        loader = OBDDataLoader("/non/existent/directory")
        channels_data, units = loader.load_csv_files()
        self.assertEqual(len(channels_data), 0, "Non-existent directory should return empty channels")
        self.assertEqual(len(units), 0, "Non-existent directory should return empty units")
        
        # Test with empty directory
        import tempfile
        empty_dir = tempfile.mkdtemp()
        try:
            loader = OBDDataLoader(empty_dir)
            channels_data, units = loader.load_csv_files()
            self.assertEqual(len(channels_data), 0, "Empty directory should return no channels")
        finally:
            import shutil
            shutil.rmtree(empty_dir, ignore_errors=True)
        
        print("✅ Error handling working correctly")


if __name__ == '__main__':
    unittest.main(verbosity=2)
