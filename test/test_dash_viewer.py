#!/usr/bin/env python3
"""
Unit tests for Dash OBD Viewer
"""

import unittest
import sys
import os
from pathlib import Path
import pandas as pd
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dash_viewer import DashOBDViewer

class TestDashOBDViewer(unittest.TestCase):
    """Test cases for DashOBDViewer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create test CSV files
        self.create_test_csv_files()
        
        # Initialize viewer with test directory
        self.viewer = DashOBDViewer(csv_folder_path=self.test_dir)
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
        
    def create_test_csv_files(self):
        """Create test CSV files for testing."""
        # Test data
        test_data = [
            {
                'filename': 'test_rpm.csv',
                'data': {
                    'SECONDS': [0, 1, 2, 3, 4, 5],
                    'PID': ['Engine RPM'] * 6,
                    'VALUE': [800, 1200, 1500, 1800, 2000, 2200],
                    'UNITS': ['rpm'] * 6
                }
            },
            {
                'filename': 'test_speed.csv',
                'data': {
                    'SECONDS': [0, 1, 2, 3, 4, 5],
                    'PID': ['Vehicle Speed'] * 6,
                    'VALUE': [0, 10, 20, 30, 40, 45],
                    'UNITS': ['mph'] * 6
                }
            },
            {
                'filename': 'test_temp.csv',
                'data': {
                    'SECONDS': [0, 1, 2, 3, 4, 5],
                    'PID': ['Coolant Temperature'] * 6,
                    'VALUE': [180, 185, 190, 195, 200, 205],
                    'UNITS': ['°F'] * 6
                }
            }
        ]
        
        # Write CSV files
        for file_info in test_data:
            filepath = Path(self.test_dir) / file_info['filename']
            df = pd.DataFrame(file_info['data'])
            df.to_csv(filepath, sep=';', index=False)
            
    def test_initialization(self):
        """Test viewer initialization."""
        # Test that viewer initializes without crashing
        self.assertIsNotNone(self.viewer)
        self.assertIsInstance(self.viewer.data, dict)
        self.assertIsInstance(self.viewer.units, dict)
        self.assertIsInstance(self.viewer.unit_groups, dict)
        
    def test_data_loading(self):
        """Test CSV data loading."""
        # Check that data was loaded
        self.assertEqual(len(self.viewer.data), 3)
        
        # Check specific PIDs
        self.assertIn('Engine RPM', self.viewer.data)
        self.assertIn('Vehicle Speed', self.viewer.data)
        self.assertIn('Coolant Temperature', self.viewer.data)
        
        # Check units
        self.assertEqual(self.viewer.units['Engine RPM'], 'rpm')
        self.assertEqual(self.viewer.units['Vehicle Speed'], 'mph')
        self.assertEqual(self.viewer.units['Coolant Temperature'], '°F')
        
        # Check unit groups
        self.assertIn('rpm', self.viewer.unit_groups)
        self.assertIn('mph', self.viewer.unit_groups)
        self.assertIn('°F', self.viewer.unit_groups)
        
        # Check dataframes
        rpm_df = self.viewer.data['Engine RPM']
        self.assertEqual(len(rpm_df), 6)
        self.assertEqual(rpm_df['VALUE'].iloc[0], 800)
        self.assertEqual(rpm_df['VALUE'].iloc[-1], 2200)
        
    def test_time_range_calculation(self):
        """Test time range calculation."""
        # Check that time range was calculated
        self.assertEqual(self.viewer.min_time, 0)
        self.assertEqual(self.viewer.max_time, 5)
        self.assertEqual(self.viewer.current_start, 0)
        self.assertEqual(self.viewer.current_end, 5)
        
    def test_color_generation(self):
        """Test color generation for PIDs."""
        # Check that colors were assigned
        self.assertEqual(len(self.viewer.colors), 3)
        
        # Check that each PID has a color
        for pid in self.viewer.data.keys():
            self.assertIn(pid, self.viewer.colors)
            self.assertIsInstance(self.viewer.colors[pid], str)
            self.assertTrue(self.viewer.colors[pid].startswith('#'))
            
    def test_figure_creation(self):
        """Test figure creation with different parameters."""
        # Test with all PIDs visible
        visible_pids = list(self.viewer.data.keys())
        fig = self.viewer.create_figure(visible_pids, 0, 5, 1.0)
        
        # Check that figure was created
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 3)  # 3 traces
        
        # Test with subset of PIDs
        visible_pids = ['Engine RPM', 'Vehicle Speed']
        fig = self.viewer.create_figure(visible_pids, 0, 5, 1.0)
        
        self.assertEqual(len(fig.data), 2)  # 2 traces
        
        # Test with no PIDs
        visible_pids = []
        fig = self.viewer.create_figure(visible_pids, 0, 5, 1.0)
        
        # Should have annotation but no data traces
        self.assertEqual(len(fig.data), 0)
        
    def test_figure_layout(self):
        """Test figure layout properties."""
        visible_pids = list(self.viewer.data.keys())
        fig = self.viewer.create_figure(visible_pids, 0, 5, 1.0)
        
        # Check layout properties
        self.assertEqual(fig.layout.title.text, "OBD Data Viewer")
        self.assertEqual(fig.layout.height, 300 * 3 * 1.0)  # 3 units * 1.0 zoom
        self.assertTrue(fig.layout.showlegend)
        
        # Test with different zoom levels
        fig_zoomed = self.viewer.create_figure(visible_pids, 0, 5, 2.0)
        self.assertEqual(fig_zoomed.layout.height, 300 * 3 * 2.0)  # 3 units * 2.0 zoom
        
    def test_time_filtering(self):
        """Test that data is properly filtered by time range."""
        visible_pids = ['Engine RPM']
        
        # Test full range
        fig = self.viewer.create_figure(visible_pids, 0, 5, 1.0)
        trace = fig.data[0]
        self.assertEqual(len(trace.x), 6)  # All 6 points
        
        # Test partial range
        fig = self.viewer.create_figure(visible_pids, 1, 3, 1.0)
        trace = fig.data[0]
        self.assertEqual(len(trace.x), 3)  # Points at 1, 2, 3
        
        # Test narrow range
        fig = self.viewer.create_figure(visible_pids, 2, 2, 1.0)
        trace = fig.data[0]
        self.assertEqual(len(trace.x), 1)  # Only point at 2
        
    def test_app_creation(self):
        """Test Dash app creation."""
        # Check that app was created
        self.assertIsNotNone(self.viewer.app)
        
        # Check that layout was set
        self.assertIsNotNone(self.viewer.app.layout)
        
    def test_invalid_folder(self):
        """Test handling of invalid folder."""
        # Test with non-existent folder
        viewer = DashOBDViewer(csv_folder_path="/non/existent/path")
        
        # Should not crash
        self.assertIsNotNone(viewer)
        self.assertEqual(len(viewer.data), 0)
        
    def test_empty_folder(self):
        """Test handling of empty folder."""
        # Create empty temporary directory
        empty_dir = tempfile.mkdtemp()
        
        try:
            viewer = DashOBDViewer(csv_folder_path=empty_dir)
            
            # Should not crash
            self.assertIsNotNone(viewer)
            self.assertEqual(len(viewer.data), 0)
            
        finally:
            shutil.rmtree(empty_dir)
            
    def test_malformed_csv(self):
        """Test handling of malformed CSV files."""
        # Create malformed CSV file
        malformed_file = Path(self.test_dir) / 'malformed.csv'
        with open(malformed_file, 'w') as f:
            f.write('invalid,csv,data\n')
            f.write('no,proper,columns\n')
            
        # Reload viewer
        viewer = DashOBDViewer(csv_folder_path=self.test_dir)
        
        # Should still load valid files and ignore invalid ones
        self.assertEqual(len(viewer.data), 3)  # Only the 3 valid files
        
    def test_callback_setup(self):
        """Test that callbacks are properly set up."""
        # Check that app has callbacks
        self.assertIsNotNone(self.viewer.app.callback_map)
        
        # The main graph callback should be registered
        self.assertIn('main-graph', self.viewer.app.callback_map)
        
class TestDataProcessing(unittest.TestCase):
    """Test data processing utilities."""
    
    def test_csv_parsing(self):
        """Test CSV parsing with semicolon delimiter."""
        # Create test CSV with semicolon delimiter
        csv_content = "SECONDS;PID;VALUE;UNITS\n0;Test PID;100;test\n1;Test PID;200;test\n"
        
        # Parse with pandas
        from io import StringIO
        df = pd.read_csv(StringIO(csv_content), delimiter=';')
        
        # Verify parsing
        self.assertEqual(len(df), 2)
        self.assertEqual(df['SECONDS'].iloc[0], 0)
        self.assertEqual(df['PID'].iloc[0], 'Test PID')
        self.assertEqual(df['VALUE'].iloc[0], 100)
        self.assertEqual(df['UNITS'].iloc[0], 'test')
        
    def test_time_range_bounds(self):
        """Test time range boundary handling."""
        viewer = DashOBDViewer(csv_folder_path=tempfile.mkdtemp())
        
        # Test with no data
        self.assertEqual(viewer.min_time, 0)
        self.assertEqual(viewer.max_time, 0)
        
class TestColorGeneration(unittest.TestCase):
    """Test color generation utilities."""
    
    def test_color_sequence(self):
        """Test that color sequence generates different colors."""
        viewer = DashOBDViewer(csv_folder_path=tempfile.mkdtemp())
        
        colors = []
        for i in range(10):
            color = viewer.get_next_color()
            colors.append(color)
            
        # Check that colors are valid hex colors
        for color in colors:
            self.assertTrue(color.startswith('#'))
            self.assertEqual(len(color), 7)  # #RRGGBB format
            
        # Check that colors are different (at least some)
        unique_colors = set(colors)
        self.assertGreater(len(unique_colors), 5)  # Should have variety
        
if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
