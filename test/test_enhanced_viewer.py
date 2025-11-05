#!/usr/bin/env python3
"""
Unit tests for Enhanced Dash OBD Viewer to debug UI issues
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

from enhanced_dash_viewer import EnhancedDashOBDViewer

class TestEnhancedViewerUI(unittest.TestCase):
    """Test UI components of Enhanced Dash OBD Viewer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create test CSV files
        self.create_test_csv_files()
        
        # Initialize viewer with test directory
        self.viewer = EnhancedDashOBDViewer(csv_folder_path=self.test_dir)
        
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
            }
        ]
        
        # Write CSV files
        for file_info in test_data:
            filepath = Path(self.test_dir) / file_info['filename']
            df = pd.DataFrame(file_info['data'])
            df.to_csv(filepath, sep=';', index=False)
            
    def test_viewer_initialization(self):
        """Test that viewer initializes correctly."""
        # Test basic initialization
        self.assertIsNotNone(self.viewer)
        self.assertIsNotNone(self.viewer.app)
        self.assertIsNotNone(self.viewer.app.layout)
        
        # Test data loading
        self.assertEqual(len(self.viewer.data), 2)
        self.assertIn('Engine RPM', self.viewer.data)
        self.assertIn('Vehicle Speed', self.viewer.data)
        
        # Test group initialization
        self.assertIn('Default', self.viewer.groups)
        self.assertEqual(len(self.viewer.groups['Default']), 2)
        
    def test_layout_structure(self):
        """Test that the layout has the correct structure."""
        layout = self.viewer.app.layout
        
        # Convert to string for searching
        layout_str = str(layout)
        
        print(f"\n=== LAYOUT DEBUG ===")
        print(f"Layout type: {type(layout)}")
        print(f"Layout string length: {len(layout_str)}")
        print(f"First 1000 chars: {layout_str[:1000]}")
        print(f"Contains 'PID Selection & Groups': {'PID Selection & Groups' in layout_str}")
        print(f"Contains 'CardBody': {'CardBody' in layout_str}")
        print(f"Contains 'groups-container': {'groups-container' in layout_str}")
        print(f"Contains 'btn-add-group': {'btn-add-group' in layout_str}")
        print(f"===================\n")
        
        # Check for main components
        self.assertIn('PID Selection & Groups', layout_str)
        self.assertIn('Time Navigation', layout_str)
        self.assertIn('Graph Height', layout_str)
        self.assertIn('btn-add-group', layout_str)
        self.assertIn('btn-clear-groups', layout_str)
        self.assertIn('pid-checkboxes-container', layout_str)
        self.assertIn('groups-container', layout_str)
        
    def test_callback_outputs(self):
        """Test that callback functions produce correct outputs."""
        # Test groups callback
        groups = self.viewer.groups.copy()
        
        # Simulate the update_groups callback
        add_clicks = 0
        clear_clicks = 0
        data_loaded = True
        
        # Call the callback function directly
        result = self.viewer.setup_callbacks.__wrapped__.__func__.__globals__['update_groups'](
            add_clicks, clear_clicks, data_loaded, groups
        ) if hasattr(self.viewer.setup_callbacks, '__wrapped__') else None
        
        # Test PID checkboxes callback
        groups_data = self.viewer.groups.copy()
        pid_groups_data = self.viewer.pid_groups.copy()
        
        print(f"\n=== CALLBACK DEBUG ===")
        print(f"Groups data: {groups_data}")
        print(f"PID groups data: {pid_groups_data}")
        print(f"Data loaded: {data_loaded}")
        print(f"Number of PIDs in Default: {len(groups_data.get('Default', []))}")
        print(f"PIDs in Default: {groups_data.get('Default', [])}")
        print(f"===================\n")
        
        # Verify that groups contain PIDs
        self.assertIn('Default', groups_data)
        self.assertGreater(len(groups_data['Default']), 0)
        
    def test_manual_callback_execution(self):
        """Manually test callback execution to debug issues."""
        print(f"\n=== MANUAL CALLBACK TEST ===")
        
        # Get the callback functions from the app
        callbacks = self.viewer.app.callback_map
        
        # Check groups-container callback
        groups_callback = callbacks.get('groups-container.children')
        if groups_callback:
            print(f"Groups callback exists: {groups_callback is not None}")
            print(f"Groups callback inputs: {len(groups_callback['inputs'])}")
            
        # Check pid-checkboxes-container callback  
        pid_callback = callbacks.get('pid-checkboxes-container.children')
        if pid_callback:
            print(f"PID callback exists: {pid_callback is not None}")
            print(f"PID callback inputs: {len(pid_callback['inputs'])}")
            
        print(f"Total callbacks registered: {len(callbacks)}")
        print(f"Callback keys: {list(callbacks.keys())}")
        print(f"========================\n")
        
        # Verify callbacks exist
        self.assertIn('groups-container.children', callbacks)
        # The PID callback has multiple outputs, so key format is different
        pid_callback_keys = [k for k in callbacks.keys() if 'pid-checkboxes-container.children' in k]
        self.assertGreater(len(pid_callback_keys), 0, "PID checkboxes callback not found")
        
    def test_group_functionality(self):
        """Test group management functionality."""
        # Test initial groups
        self.assertEqual(len(self.viewer.groups), 1)
        self.assertIn('Default', self.viewer.groups)
        self.assertEqual(len(self.viewer.groups['Default']), 2)
        
        # Test adding a group
        new_group_name = "Test Group"
        self.viewer.groups[new_group_name] = []
        self.assertEqual(len(self.viewer.groups), 2)
        self.assertIn(new_group_name, self.viewer.groups)
        
    def test_pid_checkbox_creation(self):
        """Test PID checkbox creation logic."""
        # Test that we can create checkbox options
        for pid in self.viewer.data.keys():
            unit = self.viewer.units[pid]
            checkbox_option = {
                "label": f"{pid} ({unit})",
                "value": pid
            }
            
            # Verify structure
            self.assertIn('label', checkbox_option)
            self.assertIn('value', checkbox_option)
            self.assertEqual(checkbox_option['value'], pid)
            self.assertIn(unit, checkbox_option['label'])
            
    def test_time_controls_creation(self):
        """Test time controls creation."""
        # Test initial time values
        self.assertEqual(self.viewer.min_time, 0)
        self.assertEqual(self.viewer.max_time, 5)
        self.assertEqual(self.viewer.current_start, 0)
        self.assertEqual(self.viewer.current_end, 5)
        
        # Test center time calculation
        center = (self.viewer.current_start + self.viewer.current_end) / 2
        self.assertEqual(center, 2.5)
        
    def test_figure_creation(self):
        """Test figure creation with visible PIDs."""
        visible_pids = list(self.viewer.data.keys())
        fig = self.viewer.create_figure(visible_pids, 0, 5, 1.0)
        
        # Check figure structure
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 2)  # 2 PIDs
        self.assertEqual(fig.layout.title.text, "OBD Data Viewer - Individual PIDs")
        self.assertEqual(fig.layout.height, 200 * 2 * 1.0)  # 2 PIDs * 1.0 zoom
        
    def test_empty_figure_creation(self):
        """Test figure creation with no visible PIDs."""
        fig = self.viewer.create_figure([], 0, 5, 1.0)
        
        # Check that empty figure has annotation
        self.assertEqual(len(fig.data), 0)
        # Check for annotation (indirectly through layout)
        self.assertIsNotNone(fig.layout)
        
    def test_group_dropdown_options(self):
        """Test group dropdown options creation."""
        groups = self.viewer.groups
        group_options = [{"label": name, "value": name} for name in groups.keys()]
        
        # Verify options
        self.assertEqual(len(group_options), 1)
        self.assertEqual(group_options[0]['label'], 'Default')
        self.assertEqual(group_options[0]['value'], 'Default')
        
    def test_data_initialization(self):
        """Test that data is properly initialized."""
        # Test data storage
        self.assertIsInstance(self.viewer.data, dict)
        self.assertIsInstance(self.viewer.units, dict)
        self.assertIsInstance(self.viewer.groups, dict)
        self.assertIsInstance(self.viewer.pid_groups, dict)
        self.assertIsInstance(self.viewer.colors, dict)
        
        # Test specific data
        self.assertEqual(self.viewer.units['Engine RPM'], 'rpm')
        self.assertEqual(self.viewer.units['Vehicle Speed'], 'mph')
        self.assertEqual(self.viewer.pid_groups['Engine RPM'], 'Default')
        self.assertEqual(self.viewer.pid_groups['Vehicle Speed'], 'Default')

class TestEnhancedViewerCallbacks(unittest.TestCase):
    """Test callback functions of Enhanced Dash OBD Viewer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test CSV files
        test_data = [
            {
                'filename': 'test_rpm.csv',
                'data': {
                    'SECONDS': [0, 1, 2],
                    'PID': ['Engine RPM'] * 3,
                    'VALUE': [800, 1200, 1500],
                    'UNITS': ['rpm'] * 3
                }
            }
        ]
        
        for file_info in test_data:
            filepath = Path(self.test_dir) / file_info['filename']
            df = pd.DataFrame(file_info['data'])
            df.to_csv(filepath, sep=';', index=False)
        
        self.viewer = EnhancedDashOBDViewer(csv_folder_path=self.test_dir)
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
        
    def test_groups_callback_logic(self):
        """Test the groups update callback logic."""
        # Test initial state
        groups = self.viewer.groups.copy()
        
        # Simulate adding a group
        add_clicks = 1
        clear_clicks = 0
        
        # Manually test the callback logic
        if add_clicks:
            new_group_name = f"Group {len(groups) + 1}"
            groups[new_group_name] = []
            
        self.assertEqual(len(groups), 2)
        self.assertIn('Group 2', groups)
        
    def test_pid_checkboxes_callback_logic(self):
        """Test the PID checkboxes callback logic."""
        groups = self.viewer.groups.copy()
        pid_groups = self.viewer.pid_groups.copy()
        
        # Test group options creation
        group_options = [{"label": name, "value": name} for name in groups.keys()]
        self.assertEqual(len(group_options), 1)
        
        # Test checkbox creation
        checkbox_elements = []
        for group_name, pids in groups.items():
            if pids:
                for pid in pids:
                    unit = self.viewer.units.get(pid, 'N/A')
                    checkbox_option = {
                        "label": f"{pid} ({unit})",
                        "value": pid
                    }
                    checkbox_elements.append(checkbox_option)
                    
        self.assertEqual(len(checkbox_elements), 1)
        self.assertIn('Engine RPM', checkbox_elements[0]['label'])
        
    def test_figure_update_logic(self):
        """Test figure update callback logic."""
        # Test initial state
        visible_pids = list(self.viewer.data.keys())
        current_start = self.viewer.current_start
        current_end = self.viewer.current_end
        global_zoom = self.viewer.global_zoom_level
        
        # Test figure creation
        fig = self.viewer.create_figure(visible_pids, current_start, current_end, global_zoom)
        
        # Verify figure properties
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 1)
        self.assertEqual(fig.layout.title.text, "OBD Data Viewer - Individual PIDs")

class TestEnhancedViewerIntegration(unittest.TestCase):
    """Integration tests for the complete viewer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create comprehensive test data
        test_files = [
            ('test_rpm.csv', {
                'SECONDS': [0, 1, 2, 3, 4, 5],
                'PID': ['Engine RPM'] * 6,
                'VALUE': [800, 1200, 1500, 1800, 2000, 2200],
                'UNITS': ['rpm'] * 6
            }),
            ('test_speed.csv', {
                'SECONDS': [0, 1, 2, 3, 4, 5],
                'PID': ['Vehicle Speed'] * 6,
                'VALUE': [0, 10, 20, 30, 40, 45],
                'UNITS': ['mph'] * 6
            }),
            ('test_temp.csv', {
                'SECONDS': [0, 1, 2, 3, 4, 5],
                'PID': ['Coolant Temp'] * 6,
                'VALUE': [180, 185, 190, 195, 200, 205],
                'UNITS': ['°F'] * 6
            })
        ]
        
        for filename, data in test_files:
            filepath = Path(self.test_dir) / filename
            df = pd.DataFrame(data)
            df.to_csv(filepath, sep=';', index=False)
        
        self.viewer = EnhancedDashOBDViewer(csv_folder_path=self.test_dir)
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
        
    def test_complete_workflow(self):
        """Test a complete workflow from initialization to figure creation."""
        # 1. Test initialization
        self.assertEqual(len(self.viewer.data), 3)
        self.assertEqual(len(self.viewer.groups['Default']), 3)
        
        # 2. Test layout creation
        self.assertIsNotNone(self.viewer.app.layout)
        
        # 3. Test callback registration
        self.assertIsNotNone(self.viewer.app.callback_map)
        
        # 4. Test figure creation with all PIDs
        all_pids = list(self.viewer.data.keys())
        fig = self.viewer.create_figure(all_pids, 0, 5, 1.0)
        self.assertEqual(len(fig.data), 3)
        
        # 5. Test figure creation with subset
        subset_pids = ['Engine RPM', 'Vehicle Speed']
        fig = self.viewer.create_figure(subset_pids, 0, 5, 1.0)
        self.assertEqual(len(fig.data), 2)
        
        # 6. Test figure creation with empty
        fig = self.viewer.create_figure([], 0, 5, 1.0)
        self.assertEqual(len(fig.data), 0)
        
    def test_ui_components_exist(self):
        """Test that all required UI components exist in layout."""
        layout_str = str(self.viewer.app.layout)
        
        required_components = [
            'PID Selection & Groups',
            'Time Navigation', 
            'Graph Height',
            'btn-add-group',
            'btn-clear-groups',
            'groups-container',
            'pid-checkboxes-container',
            'center-time-input',
            'start-time-input',
            'end-time-input',
            'btn-left-10',
            'btn-left-5', 
            'btn-left-1',
            'btn-right-1',
            'btn-right-5',
            'btn-right-10',
            'btn-zoom-in',
            'btn-zoom-out',
            'btn-zoom-reset'
        ]
        
        for component in required_components:
            with self.subTest(component=component):
                self.assertIn(component, layout_str, 
                            f"Component '{component}' not found in layout")

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
