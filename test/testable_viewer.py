#!/usr/bin/env python3
"""
Testable OBD Data Viewer - Parameterizable version for testing
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
import os
from pathlib import Path
import glob
from collections import defaultdict
import colorsys
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class TestableOBDViewer:
    """Testable OBD Data Viewer that can be parameterized."""
    
    def __init__(self, root, csv_folder_path=None, auto_load=True):
        """
        Initialize the viewer.
        
        Args:
            root: Tkinter root window
            csv_folder_path: Path to CSV folder (if None, will prompt user)
            auto_load: Whether to auto-load data on startup
        """
        self.root = root
        self.root.title("Testable OBD Data Viewer")
        self.root.geometry("1200x800")
        
        # Data storage
        self.data = {}  # Dictionary to store DataFrames by PID
        self.units = {}  # Dictionary to store units for each PID
        self.unit_groups = defaultdict(list)  # PIDs grouped by units
        self.visible_plots = set()  # Set of currently visible PIDs
        
        # Time range variables
        self.min_time = 0
        self.max_time = 1
        self.current_start = 0
        self.current_end = 1
        self.zoom_level = 1.0
        
        # Colors for plots
        self.colors = {}
        self.color_index = 0
        
        # Configuration
        self.csv_folder_path = csv_folder_path
        self.auto_load = auto_load
        
        self.setup_ui()
        
        if self.auto_load:
            self.load_data()
            
    def setup_ui(self):
        """Setup the main UI components."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control panel
        self.setup_control_panel(main_frame)
        
        # Plot area
        self.setup_plot_area(main_frame)
        
    def setup_control_panel(self, parent):
        """Setup the control panel."""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Load button
        self.load_btn = ttk.Button(
            control_frame, 
            text="Load CSV Folder", 
            command=self.prompt_and_load_folder
        )
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        self.refresh_btn = ttk.Button(
            control_frame, 
            text="Refresh Plot", 
            command=self.refresh_plot
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(
            control_frame, 
            text="Ready" + (f" (Auto-loaded from {self.csv_folder_path})" if self.csv_folder_path else "")
        )
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Data info
        self.info_label = ttk.Label(control_frame, text="")
        self.info_label.pack(side=tk.RIGHT, padx=5)
        
    def setup_plot_area(self, parent):
        """Setup the main plotting area."""
        plot_frame = ttk.Frame(parent)
        plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(12, 8), dpi=80)
        self.figure.patch.set_facecolor('white')
        
        # Create initial subplot
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('Time (seconds)', fontsize=10)
        self.ax.set_ylabel('Value', fontsize=10)
        self.ax.set_title('OBD Data', fontsize=12, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def load_data(self, folder_path=None):
        """Load data from specified folder or default path."""
        if folder_path:
            target_folder = Path(folder_path)
        elif self.csv_folder_path:
            target_folder = Path(self.csv_folder_path)
        else:
            return False
            
        if not target_folder.exists():
            print(f"Folder not found: {target_folder}")
            return False
            
        self.clear_data()
        
        # Find all CSV files
        csv_files = glob.glob(os.path.join(target_folder, "*.csv"))
        
        if not csv_files:
            print(f"No CSV files found in {target_folder}")
            return False
            
        # Load each CSV file
        loaded_count = 0
        for csv_file in csv_files:
            if self.load_csv_file(csv_file):
                loaded_count += 1
                
        if loaded_count > 0:
            self.update_time_range()
            self.refresh_plot()
            self.status_label.config(text=f"Loaded {loaded_count} files from {target_folder.name}")
            return True
        else:
            self.status_label.config(text="No valid data loaded")
            return False
            
    def load_csv_file(self, csv_file):
        """Load a single CSV file."""
        try:
            # Read CSV with semicolon delimiter
            df = pd.read_csv(csv_file, delimiter=';')
            
            # Extract PID name from filename
            pid_name = Path(csv_file).stem
            
            # Skip if no data
            if df.empty:
                print(f"No data in {csv_file}")
                return False
                
            # Convert time to numeric and sort
            df['SECONDS'] = pd.to_numeric(df['SECONDS'], errors='coerce')
            df['VALUE'] = pd.to_numeric(df['VALUE'], errors='coerce')
            # Only drop NaN from SECONDS and VALUE columns
            df = df.dropna(subset=['SECONDS', 'VALUE'])
            df = df.sort_values('SECONDS')
            
            if not df.empty:
                self.data[pid_name] = df
                
                # Extract unit
                if 'UNITS' in df.columns and not df['UNITS'].empty:
                    unit = df['UNITS'].iloc[0]
                    self.units[pid_name] = unit
                    self.unit_groups[unit].append(pid_name)
                else:
                    self.units[pid_name] = "Unknown"
                    self.unit_groups["Unknown"].append(pid_name)
                    
                # Assign color
                self.colors[pid_name] = self.get_next_color()
                
                # Initially make all plots visible
                self.visible_plots.add(pid_name)
                
                print(f"Loaded {pid_name}: {len(df)} rows, unit: {self.units[pid_name]}")
                return True
            else:
                print(f"No valid data after cleaning {csv_file}")
                return False
                
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
            return False
            
    def get_next_color(self):
        """Generate the next color for plotting."""
        hue = (self.color_index * 0.618033988749895) % 1  # Golden ratio
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        color = '#%02x%02x%02x' % tuple(int(c * 255) for c in rgb)
        self.color_index += 1
        return color
        
    def clear_data(self):
        """Clear all loaded data."""
        self.data.clear()
        self.units.clear()
        self.unit_groups.clear()
        self.visible_plots.clear()
        self.colors.clear()
        self.color_index = 0
        
    def update_time_range(self):
        """Update the global time range based on loaded data."""
        if not self.data:
            return
            
        all_times = []
        for df in self.data.values():
            all_times.extend(df['SECONDS'].values)
            
        if all_times:
            self.min_time = min(all_times)
            self.max_time = max(all_times)
            self.current_start = self.min_time
            self.current_end = self.max_time
            
    def refresh_plot(self):
        """Refresh the plot with current data."""
        self.figure.clear()
        
        if not self.data or not self.visible_plots:
            # Create empty plot
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No data to display\nLoad CSV files to see data', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_xlabel('Time (seconds)', fontsize=10)
            ax.set_ylabel('Value', fontsize=10)
            ax.set_title('OBD Data - No Data', fontsize=12, fontweight='bold')
            self.info_label.config(text="No data")
        else:
            # Group visible PIDs by unit
            visible_by_unit = defaultdict(list)
            for pid in self.visible_plots:
                if pid in self.units:
                    visible_by_unit[self.units[pid]].append(pid)
                    
            # Create separate plots for each unit group
            if visible_by_unit:
                n_units = len(visible_by_unit)
                
                for i, (unit, pids) in enumerate(visible_by_unit.items()):
                    ax = self.figure.add_subplot(n_units, 1, i + 1)
                    
                    # Plot each PID in this unit group
                    for pid in pids:
                        if pid in self.data:
                            df = self.data[pid]
                            
                            # Filter data by current time range
                            mask = (df['SECONDS'] >= self.current_start) & (df['SECONDS'] <= self.current_end)
                            filtered_df = df[mask]
                            
                            if not filtered_df.empty:
                                ax.plot(
                                    filtered_df['SECONDS'], 
                                    filtered_df['VALUE'],
                                    label=pid,
                                    color=self.colors.get(pid, 'blue'),
                                    linewidth=1.5
                                )
                    
                    # Set labels and title
                    ax.set_xlabel('Time (seconds)', fontsize=10)
                    ax.set_ylabel(f'{unit}', fontsize=10)
                    
                    # Create comma-separated list of PID names for title
                    pid_names = ', '.join(pids)
                    ax.set_title(pid_names, fontsize=11, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    
                    # Set y-axis limits based on all data in this unit group
                    self.set_y_axis_limits(ax, pids)
                    
                    # Add legend
                    if len(pids) > 1:
                        ax.legend(loc='upper right', fontsize=8)
                        
                    # Format axes
                    ax.tick_params(axis='x', labelsize=8)
                    ax.tick_params(axis='y', labelsize=8)
                    
                self.figure.tight_layout()
                
                # Update info
                total_points = sum(len(df) for df in self.data.values())
                self.info_label.config(text=f"{len(self.data)} datasets, {total_points} points")
                
        self.canvas.draw()
        
    def set_y_axis_limits(self, ax, pids):
        """Set y-axis limits based on min/max values of all PIDs in the group."""
        all_values = []
        
        for pid in pids:
            if pid in self.data:
                df = self.data[pid]
                # Use all data (not just current view) for y-axis limits
                all_values.extend(df['VALUE'].values)
                
        if all_values:
            y_min = min(all_values)
            y_max = max(all_values)
            
            # Add 5% padding
            padding = (y_max - y_min) * 0.05
            if padding == 0:  # Handle case where all values are the same
                padding = 1
                
            ax.set_ylim(y_min - padding, y_max + padding)
            
    def prompt_and_load_folder(self):
        """Prompt user to select folder and load data."""
        folder = filedialog.askdirectory(title="Select folder with CSV files")
        if folder:
            self.load_data(folder)
            
    def get_data_summary(self):
        """Get summary of loaded data."""
        if not self.data:
            return "No data loaded"
            
        summary = f"Loaded {len(self.data)} datasets:\n"
        for pid, df in self.data.items():
            unit = self.units.get(pid, 'Unknown')
            summary += f"  {pid}: {len(df)} points, unit: {unit}\n"
            
        return summary


def main():
    """Main function for standalone testing."""
    root = tk.Tk()
    
    # Example usage with test data
    test_folder = Path(__file__).parent
    
    app = TestableOBDViewer(
        root, 
        csv_folder_path=test_folder,
        auto_load=True
    )
    
    root.mainloop()


if __name__ == "__main__":
    main()
