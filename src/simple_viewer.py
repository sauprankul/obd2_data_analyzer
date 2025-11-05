#!/usr/bin/env python3
"""
Simple OBD Data Viewer - Guaranteed to work
"""

import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
import os
from pathlib import Path
import glob

class SimpleOBDViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple OBD Data Viewer")
        self.root.geometry("1200x800")
        
        self.data = {}
        self.colors = {}
        
        self.setup_ui()
        self.load_default_data()
        
    def setup_ui(self):
        """Setup the UI."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(control_frame, text="Load CSV Folder", command=self.load_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Refresh Plot", command=self.refresh_plot).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ttk.Label(control_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Plot area
        self.figure = Figure(figsize=(12, 8), dpi=80)
        self.ax = self.figure.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def load_folder(self):
        """Load CSV files from a folder."""
        folder = filedialog.askdirectory(title="Select folder with CSV files")
        if not folder:
            return
            
        self.data.clear()
        
        csv_files = glob.glob(os.path.join(folder, "*.csv"))
        for csv_file in csv_files:
            self.load_csv(csv_file)
            
        self.refresh_plot()
        
    def load_default_data(self):
        """Load default data."""
        default_folder = Path(__file__).parent / "Car_scanner_nov_4"
        if default_folder.exists():
            csv_files = glob.glob(os.path.join(default_folder, "*.csv"))
            for csv_file in csv_files:
                self.load_csv(csv_file)
            self.refresh_plot()
            
    def load_csv(self, csv_file):
        """Load a single CSV file."""
        try:
            df = pd.read_csv(csv_file, delimiter=';')
            
            # Convert columns
            df['SECONDS'] = pd.to_numeric(df['SECONDS'], errors='coerce')
            df['VALUE'] = pd.to_numeric(df['VALUE'], errors='coerce')
            df = df.dropna()
            
            if not df.empty:
                pid_name = Path(csv_file).stem
                self.data[pid_name] = df
                print(f"Loaded {pid_name}: {len(df)} rows")
                
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
            
    def refresh_plot(self):
        """Refresh the plot."""
        self.ax.clear()
        
        if not self.data:
            self.ax.text(0.5, 0.5, 'No data loaded\nClick "Load CSV Folder" to load data', 
                        ha='center', va='center', transform=self.ax.transAxes, fontsize=14)
            self.status_label.config(text="No data loaded")
        else:
            # Plot each dataset
            colors = plt.cm.tab10(np.linspace(0, 1, len(self.data)))
            
            for i, (pid, df) in enumerate(self.data.items()):
                self.ax.plot(df['SECONDS'], df['VALUE'], label=pid, 
                           color=colors[i % len(colors)], linewidth=1.5, alpha=0.8)
                
            self.ax.set_xlabel('Time (seconds)', fontsize=12)
            self.ax.set_ylabel('Value', fontsize=12)
            self.ax.set_title('OBD Data - All Parameters', fontsize=14, fontweight='bold')
            self.ax.grid(True, alpha=0.3)
            
            # Add legend
            if len(self.data) <= 10:  # Only show legend if not too many items
                self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                
            self.status_label.config(text=f"Loaded {len(self.data)} datasets")
            
        self.figure.tight_layout()
        self.canvas.draw()

def main():
    root = tk.Tk()
    app = SimpleOBDViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
