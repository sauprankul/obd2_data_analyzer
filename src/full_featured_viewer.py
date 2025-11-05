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
        """Setup the plot area with vertical scrolling and proper scaling."""
        plot_container = ttk.Frame(parent)
        plot_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Global zoom controls
        zoom_frame = ttk.Frame(plot_container)
        zoom_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(zoom_frame, text="Graph Height:").pack(side=tk.LEFT)
        ttk.Button(zoom_frame, text="Zoom In", command=self.global_zoom_in).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Zoom Out", command=self.global_zoom_out).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Reset", command=self.global_zoom_reset).pack(side=tk.LEFT, padx=2)
        
        # Main plot frame that will contain the canvas and scrollbar
        main_plot_frame = ttk.Frame(plot_container)
        main_plot_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable plot area with proper scaling
        self.plot_canvas = tk.Canvas(main_plot_frame, bg='white')
        self.plot_scrollbar = ttk.Scrollbar(main_plot_frame, orient="vertical", command=self.plot_canvas.yview)
        self.scrollable_plot = ttk.Frame(self.plot_canvas)
        
        # Make canvas expand with window
        self.plot_canvas.create_window((0, 0), window=self.scrollable_plot, anchor="nw")
        self.plot_canvas.configure(yscrollcommand=self.plot_scrollbar.set)
        
        # Pack canvas to expand - this is the key fix
        self.plot_canvas.pack(side="left", fill="both", expand=True)
        self.plot_scrollbar.pack(side="right", fill="y")
        
        # Create matplotlib figure with dynamic size
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas_plot = FigureCanvasTkAgg(self.figure, master=self.scrollable_plot)
        self.canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Bind window resize to update figure size
        self.scrollable_plot.bind("<Configure>", self.on_plot_resize)
        
        # Navigation toolbar
        toolbar_frame = ttk.Frame(self.scrollable_plot)
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
        
        # Initialize global zoom level
        self.global_zoom_level = 1.0
        self.subplot_heights = {}  # Store individual subplot heights
        
    def update_canvas_scroll_region(self):
        """Update the canvas scroll region to match the actual content size."""
        # Update canvas scroll region after a short delay to ensure layout is complete
        self.root.after(100, self._update_scroll_region)
        
    def _update_scroll_region(self):
        """Internal method to update scroll region."""
        try:
            # Get the actual size of the scrollable content
            self.scrollable_plot.update_idletasks()
            bbox = self.scrollable_plot.bbox("all")
            if bbox:
                # Add some padding to the bottom
                self.plot_canvas.configure(scrollregion=(bbox[0], bbox[1], bbox[2], bbox[3] + 50))
        except:
            pass
        
    def on_plot_resize(self, event):
        """Handle plot area resize - only update width, preserve zoom-controlled height."""
        # Update figure width based on canvas size, but keep height controlled by zoom
        canvas_width = event.width
        
        if canvas_width > 100:
            # Calculate new figure width (in inches)
            dpi = self.figure.get_dpi()
            width_in = canvas_width / dpi
            
            # Keep current height (controlled by zoom)
            current_height = self.figure.get_figheight()
            
            self.figure.set_size_inches(width_in, current_height)
            self.figure.tight_layout()
            self.canvas_plot.draw()
            # Update scroll region after resize
            self.update_canvas_scroll_region()
        
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
        
        # Make checkbox also draggable
        checkbox.bind("<Button-1>", lambda e: self.on_drag_start(pid, e))
        checkbox.bind("<B1-Motion>", lambda e: self.on_drag_motion(pid, e))
        checkbox.bind("<ButtonRelease-1>", lambda e: self.on_drag_end(pid, e))
        
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
            
    def setup_scrollbar(self):
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
        
    def setup_pid_checkboxes(self):
        """Setup draggable checkboxes for PIDs in scrollable sidebar."""
        for unit, pids in self.unit_groups.items():
            unit_label = ttk.Label(
                self.scrollable_sidebar, 
                text=f"Unit: {unit}", 
                font=("Arial", 10, "bold")
            )
            unit_label.pack(pady=(10, 2), anchor="w")
            
            for pid in pids:
                self.create_draggable_checkbox(self.scrollable_sidebar, pid, unit)
                
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
            self.update_zoom_buttons()
            
    def update_time_display(self):
        """Update time range display."""
        self.start_time_var.set(f"{int(round(self.current_start))}")
        self.end_time_var.set(f"{int(round(self.current_end))}")
        
    def update_center_time(self):
        """Update center time display."""
        if self.data:
            center = (self.current_start + self.current_end) / 2
            self.center_time_var.set(f"{int(round(center))}")
            
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
            
            # Update zoom level based on new window size
            total_range = self.max_time - self.min_time
            window_size = new_end - new_start
            if window_size > 0:
                self.zoom_level = total_range / window_size
            
            self.update_time_display()
            self.update_center_time()
            self.update_nav_buttons()
            self.update_zoom_buttons()
            self.refresh_plot()
            
        except ValueError:
            # Invalid input, reset to current values
            self.update_time_display()
            
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
        self.update_time_display()
        self.update_center_time()
        self.update_nav_buttons()
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
            
        self.update_time_display()
        self.update_center_time()
        self.update_nav_buttons()
        self.update_zoom_buttons()
        self.refresh_plot()
        
    def refresh_plot(self):
        """Refresh the plot with improved spacing and global zoom."""
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
                
                # Calculate the total figure height based on global zoom
                # Each graph gets more vertical space when zoomed in
                base_height_per_graph = 2.0  # inches per graph at 1x zoom
                zoomed_height_per_graph = base_height_per_graph * self.global_zoom_level
                
                # Total figure height = (height per graph * number of graphs) + spacing
                total_figure_height = (zoomed_height_per_graph * n_units) + (n_units * 0.5)
                
                # Width stays responsive to window, height is controlled by zoom
                current_width = self.figure.get_figwidth()
                self.figure.set_size_inches(current_width, total_figure_height)
                
                # Use gridspec with fixed row heights based on zoom
                # Each row gets equal height based on the zoom level
                gs = self.figure.add_gridspec(n_units, 1, height_ratios=[1]*n_units, hspace=0.3)
                
                for i, (unit, pids) in enumerate(visible_by_unit.items()):
                    ax = self.figure.add_subplot(gs[i])
                    
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
                    
                    # Comma-separated PID names in title with fixed padding
                    pid_names = ', '.join(pids)
                    ax.set_title(pid_names, fontsize=11, fontweight='bold', pad=10)
                    ax.grid(True, alpha=0.3)
                    
                    self.set_y_axis_limits(ax, pids)
                    
                    if len(pids) > 1:
                        ax.legend(loc='upper right', fontsize=8)
                        
                    ax.tick_params(axis='x', labelsize=8)
                    ax.tick_params(axis='y', labelsize=8)
                
                # Apply tight layout
                self.figure.tight_layout()
                
        # Draw and update scroll region
        self.canvas_plot.draw()
        self.update_canvas_scroll_region()
        
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
    test_folder = Path(__file__).parent.parent / "test"
    
    app = FullFeaturedOBDViewer(
        root, 
        csv_folder_path=test_folder,
        auto_load=True
    )
    
    root.mainloop()


if __name__ == "__main__":
    main()
