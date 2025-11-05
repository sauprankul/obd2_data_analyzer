#!/usr/bin/env python3
"""
Full-featured OBD Data Viewer with all requested features
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
import os
from pathlib import Path
import glob
from collections import defaultdict
import colorsys

class FullFeaturedOBDViewer:
    """Full-featured OBD Data Viewer."""
    
    def __init__(self, root, csv_folder_path=None, auto_load=True):
        self.root = root
        self.root.title("OBD Data Viewer - Full Featured")
        self.root.geometry("1400x900")
        
        # Data storage
        self.data = {}
        self.units = {}
        self.unit_groups = defaultdict(list)
        self.visible_plots = set()
        
        # Time range variables
        self.min_time = 0
        self.max_time = 1
        self.current_start = 0
        self.current_end = 1
        self.zoom_level = 1.0
        
        # Colors
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
        
        # Left sidebar
        self.setup_sidebar(main_frame)
        
        # Right plot area
        self.setup_plot_area(main_frame)
        
        # Bottom scrollbar
        self.setup_scrollbar()
        
    def setup_sidebar(self, parent):
        """Setup the left sidebar."""
        sidebar_frame = ttk.Frame(parent, width=300)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        sidebar_frame.pack_propagate(False)
        
        # Title
        title_label = ttk.Label(sidebar_frame, text="PID Selection", font=("Arial", 12, "bold"))
        title_label.pack(pady=5)
        
        # Show All / Hide All buttons
        button_frame = ttk.Frame(sidebar_frame)
        button_frame.pack(pady=5)
        
        self.show_all_btn = ttk.Button(button_frame, text="Show All", command=self.show_all_plots)
        self.show_all_btn.pack(side=tk.LEFT, padx=2)
        
        self.hide_all_btn = ttk.Button(button_frame, text="Hide All", command=self.hide_all_plots)
        self.hide_all_btn.pack(side=tk.LEFT, padx=2)
        
        # Load button
        self.load_btn = ttk.Button(sidebar_frame, text="Load CSV Folder", command=self.prompt_and_load_folder)
        self.load_btn.pack(pady=5)
        
        # Scrollable frame for checkboxes
        canvas = tk.Canvas(sidebar_frame)
        scrollbar = ttk.Scrollbar(sidebar_frame, orient="vertical", command=canvas.yview)
        self.checkbox_frame = ttk.Frame(canvas)
        
        self.checkbox_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.canvas = canvas
        self.pid_vars = {}
        
    def setup_plot_area(self, parent):
        """Setup the main plotting area."""
        plot_frame = ttk.Frame(parent)
        plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 8), dpi=80)
        self.figure.patch.set_facecolor('white')
        
        # Create canvas
        self.canvas_plot = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas_plot.draw()
        self.canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Toolbar with zoom controls
        toolbar_frame = ttk.Frame(plot_frame)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.toolbar = NavigationToolbar2Tk(self.canvas_plot, toolbar_frame)
        self.toolbar.update()
        
        # Custom zoom buttons
        zoom_frame = ttk.Frame(toolbar_frame)
        zoom_frame.pack(side=tk.RIGHT, padx=5)
        
        self.zoom_in_btn = ttk.Button(zoom_frame, text="Zoom In", command=self.zoom_in)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        self.zoom_out_btn = ttk.Button(zoom_frame, text="Zoom Out", command=self.zoom_out)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        self.reset_zoom_btn = ttk.Button(zoom_frame, text="Reset Zoom", command=self.reset_zoom)
        self.reset_zoom_btn.pack(side=tk.LEFT, padx=2)
        
    def setup_scrollbar(self):
        """Setup the time scrollbar."""
        scrollbar_frame = ttk.Frame(self.root)
        scrollbar_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Use Scale widget instead of Scrollbar for better control
        self.time_scrollbar = ttk.Scale(
            scrollbar_frame, 
            orient=tk.HORIZONTAL,
            from_=0,
            to=100,
            command=self.on_scrollbar_change
        )
        self.time_scrollbar.pack(fill=tk.X)
        
        self.time_label = ttk.Label(scrollbar_frame, text="Time Range: 0.00 - 0.00")
        self.time_label.pack()
        
    def load_data(self, folder_path=None):
        """Load data from specified folder."""
        if folder_path:
            target_folder = Path(folder_path)
        elif self.csv_folder_path:
            target_folder = Path(self.csv_folder_path)
        else:
            return False
            
        if not target_folder.exists():
            return False
            
        self.clear_data()
        
        csv_files = glob.glob(os.path.join(target_folder, "*.csv"))
        
        for csv_file in csv_files:
            self.load_csv_file(csv_file)
            
        if self.data:
            self.setup_pid_checkboxes()
            self.update_time_range()
            self.refresh_plot()
            return True
        return False
            
    def load_csv_file(self, csv_file):
        """Load a single CSV file."""
        try:
            df = pd.read_csv(csv_file, delimiter=';')
            pid_name = Path(csv_file).stem
            
            if df.empty:
                return False
                
            df['SECONDS'] = pd.to_numeric(df['SECONDS'], errors='coerce')
            df['VALUE'] = pd.to_numeric(df['VALUE'], errors='coerce')
            df = df.dropna(subset=['SECONDS', 'VALUE'])
            df = df.sort_values('SECONDS')
            
            if not df.empty:
                self.data[pid_name] = df
                
                if 'UNITS' in df.columns and not df['UNITS'].empty:
                    unit = df['UNITS'].iloc[0]
                    self.units[pid_name] = unit
                    self.unit_groups[unit].append(pid_name)
                else:
                    self.units[pid_name] = "Unknown"
                    self.unit_groups["Unknown"].append(pid_name)
                    
                self.colors[pid_name] = self.get_next_color()
                self.visible_plots.add(pid_name)
                
                return True
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
            return False
            
    def get_next_color(self):
        """Generate next color."""
        hue = (self.color_index * 0.618033988749895) % 1
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        color = '#%02x%02x%02x' % tuple(int(c * 255) for c in rgb)
        self.color_index += 1
        return color
        
    def clear_data(self):
        """Clear all data."""
        self.data.clear()
        self.units.clear()
        self.unit_groups.clear()
        self.visible_plots.clear()
        self.colors.clear()
        self.color_index = 0
        
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        self.pid_vars.clear()
        
    def setup_pid_checkboxes(self):
        """Setup checkboxes for PIDs."""
        for unit, pids in self.unit_groups.items():
            unit_label = ttk.Label(
                self.checkbox_frame, 
                text=f"Unit: {unit}", 
                font=("Arial", 10, "bold")
            )
            unit_label.pack(pady=(10, 2), anchor="w")
            
            for pid in pids:
                var = tk.BooleanVar(value=True)
                checkbox = ttk.Checkbutton(
                    self.checkbox_frame,
                    text=pid,
                    variable=var,
                    command=lambda p=pid, v=var: self.toggle_pid(p, v.get())
                )
                checkbox.pack(anchor="w", padx=(20, 0))
                self.pid_vars[pid] = var
                
    def toggle_pid(self, pid, is_visible):
        """Toggle PID visibility."""
        if is_visible:
            self.visible_plots.add(pid)
        else:
            self.visible_plots.discard(pid)
        self.refresh_plot()
        
    def show_all_plots(self):
        """Show all plots."""
        for pid, var in self.pid_vars.items():
            var.set(True)
            self.visible_plots.add(pid)
        self.refresh_plot()
        
    def hide_all_plots(self):
        """Hide all plots."""
        for pid, var in self.pid_vars.items():
            var.set(False)
        self.visible_plots.clear()
        self.refresh_plot()
        
    def update_time_range(self):
        """Update time range."""
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
            self.zoom_level = 1.0
            
            # Initialize scale
            self.time_scrollbar.config(from_=0, to=100)
            self.time_scrollbar.set(0)
            
            self.update_time_label()
            self.update_zoom_buttons()
            
    def update_time_label(self):
        """Update time label."""
        self.time_label.config(
            text=f"Time Range: {self.current_start:.2f} - {self.current_end:.2f}"
        )
        
    def on_scrollbar_change(self, value):
        """Handle scrollbar change."""
        if not self.data:
            return
            
        # Scale widget passes value as string
        scroll_pos = float(value)
        
        # Calculate window size based on zoom
        total_range = self.max_time - self.min_time
        window_size = total_range / self.zoom_level
        
        # Calculate new time range
        max_scroll_pos = 100 - (window_size / total_range * 100)
        actual_pos = min(scroll_pos, max_scroll_pos)
        
        self.current_start = self.min_time + (actual_pos / 100.0) * total_range
        self.current_end = self.current_start + window_size
        
        self.update_time_label()
        self.update_zoom_buttons()
        self.refresh_plot()
        
    def update_zoom_buttons(self):
        """Update zoom button states based on current zoom level."""
        if not self.data:
            self.zoom_in_btn.config(state='disabled')
            self.zoom_out_btn.config(state='disabled')
            return
            
        # Calculate current time window
        window_size = self.current_end - self.current_start
        
        # Check if ticks are > 1s apart (for zoom in)
        # We need enough data points to make zooming meaningful
        min_window_size = 2.0  # Minimum 2 second window
        
        # Check if we're already at full range (for zoom out)
        total_range = self.max_time - self.min_time
        
        # Update button states
        if window_size <= min_window_size:
            self.zoom_in_btn.config(state='disabled')
        else:
            self.zoom_in_btn.config(state='normal')
            
        if abs(window_size - total_range) < 0.01:  # Already at full range
            self.zoom_out_btn.config(state='disabled')
        else:
            self.zoom_out_btn.config(state='normal')
            
    def zoom_in(self):
        """Zoom in with better logic."""
        if not self.data:
            return
            
        # Calculate current window size
        window_size = self.current_end - self.current_start
        min_window_size = 2.0  # Minimum 2 second window
        
        if window_size <= min_window_size:
            return  # Can't zoom in further
            
        # Zoom in by 25% (more conservative than 50%)
        self.zoom_level *= 1.25
        
        # Limit maximum zoom to prevent issues
        max_zoom = (self.max_time - self.min_time) / min_window_size
        if self.zoom_level > max_zoom:
            self.zoom_level = max_zoom
            
        self.apply_zoom()
        
    def zoom_out(self):
        """Zoom out with better logic."""
        if not self.data:
            return
            
        total_range = self.max_time - self.min_time
        current_window = self.current_end - self.current_start
        
        if abs(current_window - total_range) < 0.01:
            return  # Already at full range
            
        # Zoom out by 25%
        self.zoom_level /= 1.25
        
        # Ensure we don't go below 1x zoom
        if self.zoom_level < 1.0:
            self.zoom_level = 1.0
            
        self.apply_zoom()
            
    def reset_zoom(self):
        """Reset zoom."""
        self.zoom_level = 1.0
        self.current_start = self.min_time
        self.current_end = self.max_time
        self.time_scrollbar.set(0)
        self.update_time_label()
        self.update_zoom_buttons()
        self.refresh_plot()
        
    def apply_zoom(self):
        """Apply zoom with better bounds checking."""
        if not self.data:
            return
            
        total_range = self.max_time - self.min_time
        window_size = total_range / self.zoom_level
        
        # Ensure window size is reasonable
        min_window_size = 2.0
        if window_size < min_window_size:
            window_size = min_window_size
            self.zoom_level = total_range / min_window_size
            
        current_center = (self.current_start + self.current_end) / 2
        self.current_start = current_center - window_size / 2
        self.current_end = current_center + window_size / 2
        
        # Keep within bounds
        if self.current_start < self.min_time:
            self.current_start = self.min_time
            self.current_end = self.min_time + window_size
        elif self.current_end > self.max_time:
            self.current_end = self.max_time
            self.current_start = self.max_time - window_size
            
        # Update scale position
        scroll_pos = ((self.current_start - self.min_time) / total_range) * 100
        self.time_scrollbar.set(scroll_pos)
        
        self.update_time_label()
        self.update_zoom_buttons()
        self.refresh_plot()
        
    def refresh_plot(self):
        """Refresh the plot."""
        self.figure.clear()
        
        if not self.data or not self.visible_plots:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No data to display\nLoad CSV files to see data', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_xlabel('Time (seconds)', fontsize=10)
            ax.set_ylabel('Value', fontsize=10)
            ax.set_title('OBD Data - No Data', fontsize=12, fontweight='bold')
        else:
            visible_by_unit = defaultdict(list)
            for pid in self.visible_plots:
                if pid in self.units:
                    visible_by_unit[self.units[pid]].append(pid)
                    
            if visible_by_unit:
                n_units = len(visible_by_unit)
                
                for i, (unit, pids) in enumerate(visible_by_unit.items()):
                    ax = self.figure.add_subplot(n_units, 1, i + 1)
                    
                    for pid in pids:
                        if pid in self.data:
                            df = self.data[pid]
                            
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
                    
                    ax.set_xlabel('Time (seconds)', fontsize=10)
                    ax.set_ylabel(f'{unit}', fontsize=10)
                    
                    # Comma-separated PID names in title
                    pid_names = ', '.join(pids)
                    ax.set_title(pid_names, fontsize=11, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    
                    self.set_y_axis_limits(ax, pids)
                    
                    if len(pids) > 1:
                        ax.legend(loc='upper right', fontsize=8)
                        
                    ax.tick_params(axis='x', labelsize=8)
                    ax.tick_params(axis='y', labelsize=8)
                    
                self.figure.tight_layout()
                
        self.canvas_plot.draw()
        
    def set_y_axis_limits(self, ax, pids):
        """Set y-axis limits."""
        all_values = []
        
        for pid in pids:
            if pid in self.data:
                df = self.data[pid]
                all_values.extend(df['VALUE'].values)
                
        if all_values:
            y_min = min(all_values)
            y_max = max(all_values)
            
            padding = (y_max - y_min) * 0.05
            if padding == 0:
                padding = 1
                
            ax.set_ylim(y_min - padding, y_max + padding)
            
    def prompt_and_load_folder(self):
        """Prompt for folder and load."""
        folder = filedialog.askdirectory(title="Select folder with CSV files")
        if folder:
            self.load_data(folder)


def main():
    """Main function."""
    root = tk.Tk()
    
    # Use test data folder for demo
    test_folder = Path(__file__).parent / "test"
    
    app = FullFeaturedOBDViewer(
        root, 
        csv_folder_path=test_folder,
        auto_load=True
    )
    
    root.mainloop()


if __name__ == "__main__":
    main()
