#!/usr/bin/env python3
"""
OBD Data Viewer using Plotly for better interactive plotting
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import pandas as pd
import numpy as np
import os
from pathlib import Path
import glob
from collections import defaultdict
import colorsys
import sys
from PIL import Image, ImageTk
import io
import threading
import webbrowser
import tempfile

# Configure Plotly to use a static renderer that works well with Tkinter
pio.kaleido.scope.mathjax = None

class PlotlyOBDViewer:
    """OBD Data Viewer using Plotly for better interactive experience."""
    
    def __init__(self, root, csv_folder_path=None, auto_load=True):
        """
        Initialize the viewer.
        
        Args:
            root: Tkinter root window
            csv_folder_path: Path to folder containing CSV files
            auto_load: Whether to auto-load data on initialization
        """
        self.root = root
        self.root.title("OBD Data Viewer - Plotly Edition")
        self.root.geometry("1400x900")
        
        self.csv_folder_path = csv_folder_path
        self.auto_load = auto_load
        
        # Data storage
        self.data = {}
        self.units = {}
        self.unit_groups = defaultdict(list)
        self.visible_plots = set()
        self.colors = {}
        self.color_index = 0
        
        # Time navigation
        self.min_time = 0
        self.max_time = 0
        self.current_start = 0
        self.current_end = 0
        self.zoom_level = 1.0
        
        # Global zoom for graph height
        self.global_zoom_level = 1.0
        
        # Setup UI
        self.setup_ui()
        
        # Load data if auto_load is enabled
        if self.auto_load and self.csv_folder_path:
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
        
        # Bottom navigation
        self.setup_navigation()
        
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
        
        # Load button
        self.load_btn = ttk.Button(sidebar_frame, text="Load CSV Folder", command=self.prompt_and_load_folder)
        self.load_btn.pack(pady=5)
        
        # Scrollable frame for checkboxes
        self.sidebar_canvas = tk.Canvas(sidebar_frame, width=200)
        self.sidebar_scrollbar = ttk.Scrollbar(sidebar_frame, orient="vertical", command=self.sidebar_canvas.yview)
        self.scrollable_sidebar = ttk.Frame(self.sidebar_canvas)
        
        self.scrollable_sidebar.bind(
            "<Configure>",
            lambda e: self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all"))
        )
        
        self.sidebar_canvas.create_window((0, 0), window=self.scrollable_sidebar, anchor="nw")
        self.sidebar_canvas.configure(yscrollcommand=self.sidebar_scrollbar.set)
        
        self.sidebar_canvas.pack(side="left", fill="both", expand=True)
        self.sidebar_scrollbar.pack(side="right", fill="y")
        
        self.pid_checkboxes = {}
        self.pid_vars = {}
        self.pid_labels = {}
        
    def setup_plot_area(self, parent):
        """Setup the plot area using a web browser or embedded view."""
        plot_container = ttk.Frame(parent)
        plot_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Global zoom controls
        zoom_frame = ttk.Frame(plot_container)
        zoom_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(zoom_frame, text="Graph Height:").pack(side=tk.LEFT)
        ttk.Button(zoom_frame, text="Zoom In", command=self.global_zoom_in).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Zoom Out", command=self.global_zoom_out).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Reset", command=self.global_zoom_reset).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Open in Browser", command=self.open_in_browser).pack(side=tk.LEFT, padx=10)
        
        # Create a text widget to show the plot as HTML or use a simple image display
        self.plot_frame = ttk.Frame(plot_container)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a label to display the plot image
        self.plot_label = ttk.Label(self.plot_frame, text="Load data to see plots", anchor="center")
        self.plot_label.pack(expand=True)
        
        # Store current plot
        self.current_plot_html = None
        
    def setup_navigation(self):
        """Setup time navigation controls."""
        nav_frame = ttk.Frame(self.root)
        nav_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Left navigation buttons
        left_frame = ttk.Frame(nav_frame)
        left_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(left_frame, text="←", font=("Arial", 12, "bold")).pack()
        
        self.left_buttons = {}
        left_times = [-1800, -60, -30, -10, -5, -3, -1]  # Reversed order: -30m, -1m, -30s, -10s, -5s, -3s, -1s
        
        for seconds in left_times:
            if seconds >= 60:
                label = f"-{abs(seconds)//60}m"
            else:
                label = f"-{abs(seconds)}s"
            
            btn = ttk.Button(
                left_frame, 
                text=label, 
                width=4,
                command=lambda s=seconds: self.shift_time(s)
            )
            btn.pack(side=tk.LEFT, padx=1)
            self.left_buttons[seconds] = btn
        
        # Center time entry
        center_frame = ttk.Frame(nav_frame)
        center_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(center_frame, text="Center Time:").pack()
        self.center_time_var = tk.StringVar()
        self.center_time_entry = ttk.Entry(
            center_frame, 
            textvariable=self.center_time_var, 
            width=10
        )
        self.center_time_entry.pack()
        self.center_time_entry.bind('<Return>', self.on_center_time_change)
        self.center_time_entry.bind('<FocusOut>', self.on_center_time_change)
        
        # Right navigation buttons
        right_frame = ttk.Frame(nav_frame)
        right_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(right_frame, text="→", font=("Arial", 12, "bold")).pack()
        
        self.right_buttons = {}
        right_times = [1, 3, 5, 10, 30, 60, 1800]  # seconds
        
        for seconds in right_times:
            if seconds >= 60:
                label = f"+{seconds//60}m"
            else:
                label = f"+{seconds}s"
            
            btn = ttk.Button(
                right_frame, 
                text=label, 
                width=4,
                command=lambda s=seconds: self.shift_time(s)
            )
            btn.pack(side=tk.LEFT, padx=1)
            self.right_buttons[seconds] = btn
        
        # Time range text boxes
        range_frame = ttk.Frame(nav_frame)
        range_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(range_frame, text="Time Range:").pack()
        
        range_entry_frame = ttk.Frame(range_frame)
        range_entry_frame.pack()
        
        ttk.Label(range_entry_frame, text="Start:").pack(side=tk.LEFT)
        self.start_time_var = tk.StringVar()
        self.start_time_entry = ttk.Entry(
            range_entry_frame, 
            textvariable=self.start_time_var, 
            width=8
        )
        self.start_time_entry.pack(side=tk.LEFT, padx=2)
        self.start_time_entry.bind('<Return>', self.on_time_range_change)
        self.start_time_entry.bind('<FocusOut>', self.on_time_range_change)
        
        ttk.Label(range_entry_frame, text="End:").pack(side=tk.LEFT, padx=(10, 0))
        self.end_time_var = tk.StringVar()
        self.end_time_entry = ttk.Entry(
            range_entry_frame, 
            textvariable=self.end_time_var, 
            width=8
        )
        self.end_time_entry.pack(side=tk.LEFT, padx=2)
        self.end_time_entry.bind('<Return>', self.on_time_range_change)
        self.end_time_entry.bind('<FocusOut>', self.on_time_range_change)
        
    def load_data(self, folder_path=None):
        """Load data from specified folder."""
        if folder_path:
            target_folder = Path(folder_path)
        elif self.csv_folder_path:
            target_folder = Path(self.csv_folder_path)
        else:
            return False
            
        if not target_folder.exists():
            messagebox.showerror("Error", f"Folder not found: {target_folder}")
            return False
            
        # Clear existing data
        self.clear_data()
        
        # Find all CSV files
        csv_files = list(target_folder.glob("*.csv"))
        
        if not csv_files:
            messagebox.showwarning("Warning", f"No CSV files found in {target_folder}")
            return False
            
        # Load each CSV file
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, delimiter=';')
                
                # Check if required columns exist
                if all(col in df.columns for col in ['SECONDS', 'PID', 'VALUE', 'UNITS']):
                    pid = df['PID'].iloc[0]
                    unit = df['UNITS'].iloc[0]
                    
                    self.data[pid] = df
                    self.units[pid] = unit
                    self.unit_groups[unit].append(pid)
                    self.visible_plots.add(pid)
                    
                    # Assign color
                    self.colors[pid] = self.get_next_color()
                    
                    print(f"Loaded {csv_file.name}: {len(df)} rows, unit: {unit}")
                    
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
                
        if self.data:
            self.setup_pid_checkboxes()
            self.update_time_range()
            self.refresh_plot()
            return True
        else:
            messagebox.showerror("Error", "No valid data loaded")
            return False
            
    def get_next_color(self):
        """Get next color in sequence."""
        hue = (self.color_index * 0.618033988749895) % 1  # Golden ratio
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.8)
        color = '#%02x%02x%02x' % tuple(int(c * 255) for c in rgb)
        self.color_index += 1
        return color
        
    def setup_pid_checkboxes(self):
        """Setup checkboxes for PIDs in scrollable sidebar."""
        for unit, pids in self.unit_groups.items():
            unit_label = ttk.Label(
                self.scrollable_sidebar, 
                text=f"Unit: {unit}", 
                font=("Arial", 10, "bold")
            )
            unit_label.pack(pady=(10, 2), anchor="w")
            
            for pid in pids:
                self.create_draggable_checkbox(self.scrollable_sidebar, pid, unit)
                
    def create_draggable_checkbox(self, parent, pid, unit):
        """Create a draggable checkbox for PID."""
        frame = ttk.Frame(parent, relief="raised", borderwidth=1)
        frame.pack(fill=tk.X, pady=2, padx=5)
        
        # Store original position for drag detection
        frame.pid = pid
        frame.original_y = 0
        
        # Make the entire frame draggable
        frame.bind("<Button-1>", self.on_drag_start)
        frame.bind("<B1-Motion>", self.on_drag_motion)
        frame.bind("<ButtonRelease-1>", self.on_drag_end)
        
        # Add cursor change on hover
        frame.bind("<Enter>", lambda e: frame.config(cursor="hand2"))
        frame.bind("<Leave>", lambda e: frame.config(cursor=""))
        
        # Checkbox and label
        var = tk.BooleanVar(value=True)
        checkbox = ttk.Checkbutton(frame, text=pid, variable=var, 
                                  command=lambda: self.toggle_pid(pid))
        checkbox.pack(side=tk.LEFT, padx=5)
        
        # Unit label
        unit_label = ttk.Label(frame, text=f"({unit})", font=("Arial", 8))
        unit_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Drag handle indicator
        drag_label = ttk.Label(frame, text="⋮⋮", font=("Arial", 8))
        drag_label.pack(side=tk.RIGHT, padx=2)
        
        self.pid_checkboxes[pid] = checkbox
        self.pid_vars[pid] = var
        self.pid_labels[pid] = unit_label
        
        return frame
        
    def on_drag_start(self, event):
        """Start dragging a PID."""
        widget = event.widget
        # Find the frame that contains the PID
        while widget and not hasattr(widget, 'pid'):
            widget = widget.master
        
        if widget and hasattr(widget, 'pid'):
            self.drag_data = {"pid": widget.pid, "widget": widget, "y": event.y_root}
            widget.config(relief="sunken")
        
    def on_drag_motion(self, event):
        """Handle drag motion with visual feedback."""
        if hasattr(self, 'drag_data'):
            # Move the widget visually during drag
            y_diff = event.y_root - self.drag_data["y"]
            # For now, just provide visual feedback
            pass
        
    def on_drag_end(self, event):
        """End dragging and reorder PIDs."""
        if hasattr(self, 'drag_data'):
            widget = self.drag_data["widget"]
            widget.config(relief="raised")
            
            # Find drop target based on mouse position
            drop_y = event.y_root
            target_widget = event.widget.winfo_containing(drop_y, drop_y)
            
            # Find the target frame
            while target_widget and not hasattr(target_widget, 'pid'):
                target_widget = target_widget.master
            
            if target_widget and target_widget != widget:
                # Simple reordering - move the widget
                widget.pack_forget()
                widget.pack(before=target_widget, fill=tk.X, pady=2, padx=5)
            
            del self.drag_data
            
    def toggle_pid(self, pid):
        """Toggle PID visibility."""
        if pid in self.pid_vars:
            if self.pid_vars[pid].get():
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
        
    def clear_data(self):
        """Clear all data."""
        self.data.clear()
        self.units.clear()
        self.unit_groups.clear()
        self.visible_plots.clear()
        self.colors.clear()
        self.color_index = 0
        
        self.clear_checkboxes()
        
    def clear_checkboxes(self):
        """Clear existing checkboxes."""
        if hasattr(self, 'scrollable_sidebar'):
            for widget in self.scrollable_sidebar.winfo_children():
                widget.destroy()
        if hasattr(self, 'pid_checkboxes'):
            self.pid_checkboxes.clear()
        if hasattr(self, 'pid_vars'):
            self.pid_vars.clear()
        if hasattr(self, 'pid_labels'):
            self.pid_labels.clear()
            
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
            
            self.update_time_display()
            self.update_center_time()
            self.update_nav_buttons()
            
    def update_time_display(self):
        """Update time range display."""
        self.start_time_var.set(f"{int(round(self.current_start))}")
        self.end_time_var.set(f"{int(round(self.current_end))}")
        
    def update_center_time(self):
        """Update center time display."""
        if self.data:
            center = (self.current_start + self.current_end) / 2
            self.center_time_var.set(f"{int(round(center))}")
            
    def on_time_range_change(self, event=None):
        """Handle time range entry change."""
        if not self.data:
            return
            
        try:
            new_start = int(self.start_time_var.get())
            new_end = int(self.end_time_var.get())
            
            # Validate range
            if new_start >= new_end:
                # Invalid range, reset to current
                self.update_time_display()
                return
                
            # Keep within bounds (round bounds to int)
            min_int = int(round(self.min_time))
            max_int = int(round(self.max_time))
            
            if new_start < min_int:
                new_start = min_int
            if new_end > max_int:
                new_end = max_int
                
            self.current_start = new_start
            self.current_end = new_end
            
            self.update_time_display()
            self.update_center_time()
            self.update_nav_buttons()
            self.refresh_plot()
            
        except ValueError:
            # Invalid input, reset to current values
            self.update_time_display()
            
    def on_center_time_change(self, event=None):
        """Handle center time entry change."""
        if not self.data:
            return
            
        try:
            new_center = int(self.center_time_var.get())
            window_size = self.current_end - self.current_start
            
            # Calculate new start/end based on center
            self.current_start = new_center - window_size / 2
            self.current_end = new_center + window_size / 2
            
            # Keep within bounds (round bounds to int)
            min_int = int(round(self.min_time))
            max_int = int(round(self.max_time))
            
            if self.current_start < min_int:
                self.current_start = min_int
                self.current_end = min_int + window_size
            elif self.current_end > max_int:
                self.current_end = max_int
                self.current_start = max_int - window_size
                
            self.update_time_display()
            self.update_center_time()
            self.update_nav_buttons()
            self.refresh_plot()
            
        except ValueError:
            # Invalid input, reset to current center
            self.update_center_time()
            
    def shift_time(self, seconds):
        """Shift time window by specified seconds."""
        if not self.data:
            return
            
        window_size = self.current_end - self.current_start
        
        # Calculate new center
        current_center = (self.current_start + self.current_end) / 2
        new_center = current_center + seconds
        
        # Calculate new window bounds
        self.current_start = new_center - window_size / 2
        self.current_end = new_center + window_size / 2
        
        # Keep within bounds
        if self.current_start < self.min_time:
            self.current_start = self.min_time
            self.current_end = self.min_time + window_size
        elif self.current_end > self.max_time:
            self.current_end = self.max_time
            self.current_start = self.max_time - window_size
            
        self.update_time_display()
        self.update_center_time()
        self.update_nav_buttons()
        self.refresh_plot()
        
    def update_nav_buttons(self):
        """Update navigation button states."""
        if not self.data:
            for btn in self.left_buttons.values():
                btn.config(state='disabled')
            for btn in self.right_buttons.values():
                btn.config(state='disabled')
            return
            
        current_center = (self.current_start + self.current_end) / 2
        window_size = self.current_end - self.current_start
        
        # Update left buttons (can't go past min_time)
        for seconds, btn in self.left_buttons.items():
            min_center = self.min_time + window_size / 2
            if current_center - abs(seconds) < min_center:
                btn.config(state='disabled')
            else:
                btn.config(state='normal')
                
        # Update right buttons (can't go past max_time)
        for seconds, btn in self.right_buttons.items():
            max_center = self.max_time - window_size / 2
            if current_center + seconds > max_center:
                btn.config(state='disabled')
            else:
                btn.config(state='normal')
                
    def global_zoom_in(self):
        """Global zoom in - make graphs taller."""
        if self.global_zoom_level < 3.0:
            self.global_zoom_level *= 1.2
            self.refresh_plot()
            
    def global_zoom_out(self):
        """Global zoom out - make graphs shorter."""
        if self.global_zoom_level > 0.5:
            self.global_zoom_level /= 1.2
            self.refresh_plot()
            
    def global_zoom_reset(self):
        """Reset global zoom."""
        self.global_zoom_level = 1.0
        self.refresh_plot()
        
    def refresh_plot(self):
        """Refresh the plot using Plotly."""
        if not self.data or not self.visible_plots:
            self.plot_label.config(text="No data to display\nLoad CSV files to see data")
            return
            
        # Group visible PIDs by unit
        visible_by_unit = defaultdict(list)
        for pid in self.visible_plots:
            if pid in self.units:
                visible_by_unit[self.units[pid]].append(pid)
                
        if not visible_by_unit:
            self.plot_label.config(text="No PIDs selected")
            return
            
        # Calculate subplot layout
        n_units = len(visible_by_unit)
        
        # Create subplots with shared x-axis
        fig = make_subplots(
            rows=n_units, 
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05 / self.global_zoom_level,
            subplot_titles=[', '.join(pids) for pids in visible_by_unit.values()]
        )
        
        # Add traces for each PID
        for i, (unit, pids) in enumerate(visible_by_unit.items()):
            for pid in pids:
                if pid in self.data:
                    df = self.data[pid]
                    
                    # Filter data for current time range
                    mask = (df['SECONDS'] >= self.current_start) & (df['SECONDS'] <= self.current_end)
                    filtered_df = df[mask]
                    
                    if not filtered_df.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=filtered_df['SECONDS'],
                                y=filtered_df['VALUE'],
                                mode='lines+markers',
                                name=pid,
                                line=dict(color=self.colors.get(pid, 'blue'), width=2),
                                marker=dict(size=4)
                            ),
                            row=i+1, col=1
                        )
                        
            # Update y-axis label
            fig.update_yaxes(title_text=unit, row=i+1, col=1)
            
        # Update layout
        fig.update_layout(
            title="OBD Data Viewer",
            height=300 * n_units * self.global_zoom_level,
            showlegend=True,
            hovermode='x unified',
            dragmode='zoom'
        )
        
        # Update x-axis
        fig.update_xaxes(title_text="Time (seconds)", row=n_units, col=1)
        
        # Convert to HTML and display
        self.current_plot_html = pio.to_html(fig, include_plotlyjs='cdn')
        
        # Create a temporary HTML file and open in browser
        self.display_plot_in_browser()
        
    def display_plot_in_browser(self):
        """Display the plot in a web browser."""
        if self.current_plot_html:
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(self.current_plot_html)
                temp_path = f.name
                
            # Open in browser
            webbrowser.open(f'file://{temp_path}')
            
            # Update label
            self.plot_label.config(text="Plot opened in browser\nClick 'Open in Browser' to refresh")
            
    def open_in_browser(self):
        """Open current plot in browser."""
        self.refresh_plot()
        
    def prompt_and_load_folder(self):
        """Prompt user to select folder and load data."""
        folder = filedialog.askdirectory(title="Select folder with CSV files")
        if folder:
            self.load_data(folder)

def main():
    """Main function."""
    root = tk.Tk()
    
    # Use test data folder for demo
    test_folder = Path(__file__).parent.parent / "test"
    
    app = PlotlyOBDViewer(
        root, 
        csv_folder_path=test_folder,
        auto_load=True
    )
    
    root.mainloop()

if __name__ == "__main__":
    main()
