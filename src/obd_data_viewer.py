#!/usr/bin/env python3
"""
OBD Data Viewer
A rich GUI application for plotting and analyzing OBD data from CSV files.
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


class OBDDDataViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("OBD Data Viewer")
        self.root.geometry("1400x900")
        
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
        
        self.setup_ui()
        self.load_default_data()
        
    def setup_ui(self):
        """Setup the main UI components."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left sidebar for PID selection
        self.setup_sidebar(main_frame)
        
        # Right side for plots
        self.setup_plot_area(main_frame)
        
        # Bottom scrollbar
        self.setup_scrollbar()
        
    def setup_sidebar(self, parent):
        """Setup the left sidebar with PID checkboxes."""
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
        
        # Load CSV button
        self.load_btn = ttk.Button(sidebar_frame, text="Load CSV Files", command=self.load_csv_files)
        self.load_btn.pack(pady=2)
        
        # Alternative: Load individual files button
        self.load_files_btn = ttk.Button(sidebar_frame, text="Load Individual CSVs", command=self.load_individual_files)
        self.load_files_btn.pack(pady=2)
        
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
        self.pid_vars = {}  # Dictionary to store checkbox variables
        
    def setup_plot_area(self, parent):
        """Setup the main plotting area."""
        plot_frame = ttk.Frame(parent)
        plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 8), dpi=80)
        self.figure.patch.set_facecolor('white')
        
        # Create subplot
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('Time (seconds)', fontsize=10)
        self.ax.set_ylabel('Value', fontsize=10)
        self.ax.set_title('OBD Data', fontsize=12, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        
        # Create canvas
        self.canvas_plot = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas_plot.draw()
        self.canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add matplotlib toolbar for additional functionality
        toolbar_frame = ttk.Frame(plot_frame)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.toolbar = NavigationToolbar2Tk(self.canvas_plot, toolbar_frame)
        self.toolbar.update()
        
        # Zoom buttons
        zoom_frame = ttk.Frame(toolbar_frame)
        zoom_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(zoom_frame, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Reset Zoom", command=self.reset_zoom).pack(side=tk.LEFT, padx=2)
        
    def setup_scrollbar(self):
        """Setup the time scrollbar at the bottom."""
        scrollbar_frame = ttk.Frame(self.root)
        scrollbar_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Time scrollbar
        self.time_scrollbar = ttk.Scrollbar(
            scrollbar_frame, 
            orient=tk.HORIZONTAL,
            command=self.on_scrollbar_change
        )
        self.time_scrollbar.pack(fill=tk.X)
        
        # Time range labels
        self.time_label = ttk.Label(scrollbar_frame, text="Time Range: 0.00 - 0.00")
        self.time_label.pack()
        
    def load_csv_files(self):
        """Load CSV files from a directory."""
        # Start from the current directory or the default data directory
        initial_dir = Path(__file__).parent
        
        # Try to start from the Car_scanner_nov_4 directory if it exists
        default_dir = initial_dir / "Car_scanner_nov_4"
        if default_dir.exists():
            initial_dir = default_dir
        
        directory = filedialog.askdirectory(
            title="Select directory with CSV files",
            initialdir=str(initial_dir)
        )
        if not directory:
            return
            
        self.clear_data()
        
        # Find all CSV files in the directory
        csv_files = glob.glob(os.path.join(directory, "*.csv"))
        
        if not csv_files:
            messagebox.showwarning("No Files", f"No CSV files found in:\n{directory}\n\nMake sure the directory contains CSV files.")
            return
            
        # Load each CSV file
        for csv_file in csv_files:
            self.load_csv_file(csv_file)
            
        self.setup_pid_checkboxes()
        self.update_time_range()
        self.update_plots()
        
        # Show success message
        messagebox.showinfo("Success", f"Loaded {len(csv_files)} CSV files successfully!")
        
    def load_individual_files(self):
        """Load individual CSV files using file selection dialog."""
        # Start from the current directory or the default data directory
        initial_dir = Path(__file__).parent
        
        # Try to start from the Car_scanner_nov_4 directory if it exists
        default_dir = initial_dir / "Car_scanner_nov_4"
        if default_dir.exists():
            initial_dir = default_dir
        
        file_paths = filedialog.askopenfilenames(
            title="Select CSV files to load",
            initialdir=str(initial_dir),
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if not file_paths:
            return
            
        # Clear existing data
        self.clear_data()
        
        # Load each selected file
        for file_path in file_paths:
            self.load_csv_file(file_path)
            
        self.setup_pid_checkboxes()
        self.update_time_range()
        self.update_plots()
        
        # Show success message
        messagebox.showinfo("Success", f"Loaded {len(file_paths)} CSV files successfully!")
        
    def load_default_data(self):
        """Load data from the default Car_scanner_nov_4 directory."""
        default_dir = Path(__file__).parent / "Car_scanner_nov_4"
        
        if default_dir.exists():
            csv_files = glob.glob(os.path.join(default_dir, "*.csv"))
            
            for csv_file in csv_files:
                self.load_csv_file(csv_file)
                
            self.setup_pid_checkboxes()
            self.update_time_range()
            self.update_plots()
            
    def load_csv_file(self, csv_file):
        """Load a single CSV file."""
        try:
            # Read CSV with semicolon delimiter, no quoting
            df = pd.read_csv(csv_file, delimiter=';', quoting=3)  # quoting=3 = QUOTE_NONE
            
            # Extract PID name from filename
            pid_name = Path(csv_file).stem
            
            # Skip if no data
            if df.empty:
                print(f"No data in {csv_file}")
                return
                
            print(f"Loading {pid_name}: {len(df)} rows")
            print(f"Columns: {list(df.columns)}")
            print(f"Sample data: {df.head(2).to_dict()}")
                
            # Convert time to numeric and sort
            df['SECONDS'] = pd.to_numeric(df['SECONDS'], errors='coerce')
            df['VALUE'] = pd.to_numeric(df['VALUE'], errors='coerce')
            df = df.dropna()
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
                
                print(f"Successfully loaded {pid_name} with unit {unit}")
            else:
                print(f"No valid data after cleaning {csv_file}")
                
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
            import traceback
            traceback.print_exc()
            
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
        
        # Clear checkboxes
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        self.pid_vars.clear()
        
    def setup_pid_checkboxes(self):
        """Setup checkboxes for each PID."""
        # Group PIDs by unit
        for unit, pids in self.unit_groups.items():
            # Unit label
            unit_label = ttk.Label(
                self.checkbox_frame, 
                text=f"Unit: {unit}", 
                font=("Arial", 10, "bold")
            )
            unit_label.pack(pady=(10, 2), anchor="w")
            
            # PID checkboxes
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
                self.visible_plots.add(pid)
                
    def toggle_pid(self, pid, is_visible):
        """Toggle visibility of a PID plot."""
        if is_visible:
            self.visible_plots.add(pid)
        else:
            self.visible_plots.discard(pid)
        self.update_plots()
        
    def show_all_plots(self):
        """Show all PID plots."""
        for pid, var in self.pid_vars.items():
            var.set(True)
            self.visible_plots.add(pid)
        self.update_plots()
        
    def hide_all_plots(self):
        """Hide all PID plots."""
        for pid, var in self.pid_vars.items():
            var.set(False)
            self.visible_plots.clear()
        self.update_plots()
        
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
            
            # Update scrollbar
            self.time_scrollbar.config(to=self.max_time - self.min_time)
            self.time_scrollbar.set(0, self.max_time - self.min_time)
            
            self.update_time_label()
            
    def update_time_label(self):
        """Update the time range label."""
        self.time_label.config(
            text=f"Time Range: {self.current_start:.2f} - {self.current_end:.2f}"
        )
        
    def on_scrollbar_change(self, *args):
        """Handle scrollbar change."""
        if not self.data:
            return
            
        # Get scrollbar position
        start_pos = self.time_scrollbar.get()[0]
        window_size = (self.max_time - self.min_time) / self.zoom_level
        
        self.current_start = self.min_time + start_pos
        self.current_end = self.current_start + window_size
        
        # Ensure we don't go beyond bounds
        if self.current_end > self.max_time:
            self.current_end = self.max_time
            self.current_start = self.max_time - window_size
            
        self.update_time_label()
        self.update_plots()
        
    def zoom_in(self):
        """Zoom in on the time axis."""
        if self.zoom_level < 10:
            self.zoom_level *= 1.5
            self.apply_zoom()
            
    def zoom_out(self):
        """Zoom out on the time axis."""
        if self.zoom_level > 1:
            self.zoom_level /= 1.5
            self.apply_zoom()
            
    def reset_zoom(self):
        """Reset zoom to default."""
        self.zoom_level = 1.0
        self.current_start = self.min_time
        self.current_end = self.max_time
        self.time_scrollbar.set(0, self.max_time - self.min_time)
        self.update_time_label()
        self.update_plots()
        
    def apply_zoom(self):
        """Apply the current zoom level."""
        if not self.data:
            return
            
        window_size = (self.max_time - self.min_time) / self.zoom_level
        
        # Center the zoom window on current view
        current_center = (self.current_start + self.current_end) / 2
        self.current_start = current_center - window_size / 2
        self.current_end = current_center + window_size / 2
        
        # Ensure we don't go beyond bounds
        if self.current_start < self.min_time:
            self.current_start = self.min_time
            self.current_end = self.min_time + window_size
        elif self.current_end > self.max_time:
            self.current_end = self.max_time
            self.current_start = self.max_time - window_size
            
        # Update scrollbar
        scroll_pos = self.current_start - self.min_time
        self.time_scrollbar.set(scroll_pos, scroll_pos + window_size)
        
        self.update_time_label()
        self.update_plots()
        
    def update_plots(self):
        """Update all plots based on current settings."""
        print(f"Updating plots - visible PIDs: {len(self.visible_plots)}, total data: {len(self.data)}")
        
        # Clear the entire figure
        self.figure.clear()
        
        if not self.data or not self.visible_plots:
            print("No data or no visible plots")
            # Create a single empty subplot
            ax = self.figure.add_subplot(111)
            ax.set_xlabel('Time (seconds)', fontsize=10)
            ax.set_ylabel('Value', fontsize=10)
            ax.set_title('OBD Data - No Data Selected', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            self.canvas_plot.draw()
            return
            
        # Group visible PIDs by unit
        visible_by_unit = defaultdict(list)
        for pid in self.visible_plots:
            if pid in self.units:
                visible_by_unit[self.units[pid]].append(pid)
                
        print(f"Visible by unit: {dict(visible_by_unit)}")
        
        # Create separate plots for each unit group
        if visible_by_unit:
            n_units = len(visible_by_unit)
            
            for i, (unit, pids) in enumerate(visible_by_unit.items()):
                ax = self.figure.add_subplot(n_units, 1, i + 1)
                
                print(f"Plotting unit {unit} with PIDs: {pids}")
                
                # Plot each PID in this unit group
                for pid in pids:
                    if pid in self.data:
                        df = self.data[pid]
                        
                        # Filter data by current time range
                        mask = (df['SECONDS'] >= self.current_start) & (df['SECONDS'] <= self.current_end)
                        filtered_df = df[mask]
                        
                        print(f"  {pid}: {len(filtered_df)} points in range")
                        
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
                ax.set_title(f'{unit} - {len(pids)} parameter(s)', fontsize=11, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
                # Set y-axis limits based on all data in this unit group
                self.set_y_axis_limits(ax, pids)
                
                # Add legend
                if len(pids) > 1:
                    ax.legend(loc='upper right', fontsize=8)
                    
                # Format x-axis
                ax.tick_params(axis='x', labelsize=8)
                ax.tick_params(axis='y', labelsize=8)
                
            self.figure.tight_layout()
            
        self.canvas_plot.draw()
        print("Plots updated and drawn")
        
        # Update the main ax reference for toolbar compatibility
        if hasattr(self, 'ax') and len(self.figure.axes) > 0:
            self.ax = self.figure.axes[0]
        
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


def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = OBDDDataViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
