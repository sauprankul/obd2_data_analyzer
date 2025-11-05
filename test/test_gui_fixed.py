#!/usr/bin/env python3
"""
GUI tests for the OBD Data Viewer - Fixed version
"""

import unittest
import tkinter as tk
from pathlib import Path
import sys
import time

# Add current directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

class TestOBDViewerGUI(unittest.TestCase):
    """Test the GUI components of the OBD Viewer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
        
        # Import here to avoid issues with display
        from testable_viewer import TestableOBDViewer
        
        # Store for use in tests
        self.TestableOBDViewer = TestableOBDViewer
        
        # Use test data folder
        self.test_folder = Path(__file__).parent
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
        
    def test_viewer_initialization(self):
        """Test that the viewer initializes correctly."""
        app = self.TestableOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=False  # Don't auto-load for this test
        )
        
        # Check basic attributes
        self.assertIsNotNone(app.data)
        self.assertIsNotNone(app.units)
        self.assertIsNotNone(app.unit_groups)
        self.assertIsNotNone(app.visible_plots)
        
        # Should be empty initially
        self.assertEqual(len(app.data), 0)
        self.assertEqual(len(app.visible_plots), 0)
        
    def test_auto_load_data(self):
        """Test auto-loading of data."""
        app = self.TestableOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=True
        )
        
        # Give it a moment to load
        self.root.update()
        
        # Should have loaded data
        self.assertGreater(len(app.data), 0)
        self.assertGreater(len(app.visible_plots), 0)
        
        # Check specific test data
        self.assertIn('test_data_engine_rpm', app.data)
        self.assertIn('test_data_vehicle_speed', app.data)
        self.assertIn('test_data_coolant_temp', app.data)
        
        # Check units
        self.assertEqual(app.units['test_data_engine_rpm'], 'rpm')
        self.assertEqual(app.units['test_data_vehicle_speed'], 'mph')
        self.assertEqual(app.units['test_data_coolant_temp'], 'F')
        
    def test_data_loading_method(self):
        """Test the data loading method directly."""
        app = self.TestableOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=False
        )
        
        # Load data
        success = app.load_data(self.test_folder)
        
        self.assertTrue(success)
        self.assertEqual(len(app.data), 3)
        
        # Check data content
        for pid, df in app.data.items():
            self.assertGreater(len(df), 0)
            self.assertIn('SECONDS', df.columns)
            self.assertIn('VALUE', df.columns)
            
    def test_time_range_calculation(self):
        """Test time range calculation."""
        app = self.TestableOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=True
        )
        
        self.root.update()
        
        # Should have calculated time range
        self.assertEqual(app.min_time, 1000.0)
        self.assertEqual(app.max_time, 1009.0)
        self.assertEqual(app.current_start, 1000.0)
        self.assertEqual(app.current_end, 1009.0)
        
    def test_data_summary(self):
        """Test data summary functionality."""
        app = self.TestableOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=True
        )
        
        self.root.update()
        
        summary = app.get_data_summary()
        
        self.assertIn("Loaded 3 datasets", summary)
        self.assertIn("test_data_engine_rpm", summary)
        self.assertIn("test_data_vehicle_speed", summary)
        self.assertIn("test_data_coolant_temp", summary)
        self.assertIn("unit: rpm", summary)
        self.assertIn("unit: mph", summary)
        self.assertIn("unit: F", summary)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
