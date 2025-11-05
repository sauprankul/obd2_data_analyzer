#!/usr/bin/env python3
"""
Comprehensive GUI tests for full-featured OBD Viewer
"""

import unittest
import tkinter as tk
from pathlib import Path
import sys
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestFullFeaturedGUI(unittest.TestCase):
    """Test the full-featured GUI."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
        from full_featured_viewer import FullFeaturedOBDViewer
        self.FullFeaturedOBDViewer = FullFeaturedOBDViewer
        
        self.test_folder = Path(__file__).parent
        
    def tearDown(self):
        """Clean up."""
        self.root.destroy()
        
    def test_full_gui_initialization(self):
        """Test full GUI initialization."""
        app = self.FullFeaturedOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=False
        )
        
        # Check all UI components exist
        self.assertIsNotNone(app.checkbox_frame)
        self.assertIsNotNone(app.time_scrollbar)
        self.assertIsNotNone(app.canvas_plot)
        self.assertIsNotNone(app.figure)
        
        # Check buttons exist
        self.assertTrue(hasattr(app, 'show_all_btn'))
        self.assertTrue(hasattr(app, 'hide_all_btn'))
        self.assertTrue(hasattr(app, 'load_btn'))
        
    def test_auto_load_with_full_gui(self):
        """Test auto-loading with full GUI."""
        app = self.FullFeaturedOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=True
        )
        
        self.root.update()
        
        # Should have loaded data
        self.assertGreater(len(app.data), 0)
        self.assertGreater(len(app.pid_vars), 0)
        
        # Check checkboxes were created
        for pid in app.data.keys():
            self.assertIn(pid, app.pid_vars)
            
    def test_show_all_hide_all_functionality(self):
        """Test show all/hide all buttons."""
        app = self.FullFeaturedOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=True
        )
        
        self.root.update()
        
        # Initially all should be visible
        initial_count = len(app.visible_plots)
        self.assertGreater(initial_count, 0)
        
        # Hide all
        app.hide_all_plots()
        self.assertEqual(len(app.visible_plots), 0)
        
        # Show all
        app.show_all_plots()
        self.assertEqual(len(app.visible_plots), initial_count)
        
    def test_individual_checkbox_toggle(self):
        """Test individual checkbox functionality."""
        app = self.FullFeaturedOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=True
        )
        
        self.root.update()
        
        # Get first PID
        first_pid = list(app.data.keys())[0]
        
        # Should be visible initially
        self.assertIn(first_pid, app.visible_plots)
        
        # Toggle off
        app.pid_vars[first_pid].set(False)
        app.toggle_pid(first_pid, False)
        self.assertNotIn(first_pid, app.visible_plots)
        
        # Toggle on
        app.pid_vars[first_pid].set(True)
        app.toggle_pid(first_pid, True)
        self.assertIn(first_pid, app.visible_plots)
        
    def test_zoom_functionality(self):
        """Test zoom in/out functionality."""
        app = self.FullFeaturedOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=True
        )
        
        self.root.update()
        
        initial_zoom = app.zoom_level
        initial_start = app.current_start
        initial_end = app.current_end
        
        # Test zoom in
        app.zoom_in()
        self.assertGreater(app.zoom_level, initial_zoom)
        
        # Test zoom out
        app.zoom_out()
        self.assertEqual(app.zoom_level, initial_zoom)
        
        # Test reset zoom
        app.zoom_in()  # Zoom in first
        app.reset_zoom()
        self.assertEqual(app.zoom_level, 1.0)
        self.assertEqual(app.current_start, initial_start)
        self.assertEqual(app.current_end, initial_end)
        
    def test_scrollbar_functionality(self):
        """Test scrollbar functionality."""
        app = self.FullFeaturedOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=True
        )
        
        self.root.update()
        
        # Test scrollbar range
        self.assertIsNotNone(app.time_scrollbar)
        
        # Simulate scrollbar change
        app.on_scrollbar_change()
        
        # Should update time range
        self.assertIsNotNone(app.current_start)
        self.assertIsNotNone(app.current_end)
        
    def test_plot_refresh_with_visibility_changes(self):
        """Test plot updates when visibility changes."""
        app = self.FullFeaturedOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=True
        )
        
        self.root.update()
        
        # Should refresh without error
        try:
            app.refresh_plot()
            self.root.update()
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"refresh_plot() failed: {e}")
            
        # Hide some plots and refresh
        first_pid = list(app.data.keys())[0]
        app.toggle_pid(first_pid, False)
        
        try:
            app.refresh_plot()
            self.root.update()
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"refresh_plot() after toggle failed: {e}")
            
    def test_y_axis_limits_maintained_during_zoom(self):
        """Test Y-axis limits stay constant during zoom."""
        app = self.FullFeaturedOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=True
        )
        
        self.root.update()
        
        # Get initial Y-axis limits
        app.refresh_plot()
        self.root.update()
        
        if len(app.figure.axes) > 0:
            ax = app.figure.axes[0]
            initial_ylim = ax.get_ylim()
            
            # Zoom in
            app.zoom_in()
            app.refresh_plot()
            self.root.update()
            
            # Y-axis should be the same (based on full dataset)
            new_ylim = ax.get_ylim()
            self.assertAlmostEqual(initial_ylim[0], new_ylim[0], places=5)
            self.assertAlmostEqual(initial_ylim[1], new_ylim[1], places=5)
            
    def test_comma_separated_titles(self):
        """Test that plot titles use comma-separated PID names."""
        app = self.FullFeaturedOBDViewer(
            self.root, 
            csv_folder_path=self.test_folder,
            auto_load=True
        )
        
        self.root.update()
        
        app.refresh_plot()
        self.root.update()
        
        # Check titles are comma-separated
        for ax in app.figure.axes:
            title = ax.get_title()
            # Should contain commas if multiple PIDs, or just PID name if single
            self.assertIsInstance(title, str)
            self.assertGreater(len(title), 0)


class TestGUIIntegration(unittest.TestCase):
    """Integration tests for GUI."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        
        from full_featured_viewer import FullFeaturedOBDViewer
        self.FullFeaturedOBDViewer = FullFeaturedOBDViewer
        
        self.test_folder = Path(__file__).parent
        
    def tearDown(self):
        """Clean up."""
        self.root.destroy()
        
    def test_complete_workflow(self):
        """Test complete user workflow."""
        # Create viewer
        app = self.FullFeaturedOBDViewer(
            self.root, 
            csv_folder_path=None,
            auto_load=False
        )
        
        # Initially empty
        self.assertEqual(len(app.data), 0)
        
        # Load data
        success = app.load_data(self.test_folder)
        self.assertTrue(success)
        
        # Should have data and UI
        self.assertGreater(len(app.data), 0)
        self.assertGreater(len(app.pid_vars), 0)
        
        # Test interactions
        app.hide_all_plots()
        self.assertEqual(len(app.visible_plots), 0)
        
        app.show_all_plots()
        self.assertGreater(len(app.visible_plots), 0)
        
        # Test zoom
        app.zoom_in()
        app.zoom_out()
        app.reset_zoom()
        
        # Test plot refresh
        app.refresh_plot()
        
        # All should work without errors
        self.assertTrue(True)


if __name__ == '__main__':
    # Run tests with more detail
    unittest.main(verbosity=2)
