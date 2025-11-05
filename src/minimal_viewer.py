#!/usr/bin/env python3
"""
Minimal test version of OBD Data Viewer
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
import os
from pathlib import Path
import glob
from collections import defaultdict

class MinimalViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("OBD Data Viewer - Minimal Test")
        self.root.geometry("1000x600")
        
        # Load some test data
        self.load_test_data()
        
        # Setup simple UI
        self.setup_ui()
        
        # Plot the data
        self.plot_data()
        
    def load_test_data(self):
        """Load test data from CSV files."""
        self.data = {}
        
        # Try to load one CSV file
        csv_file = Path(__file__).parent / "Car_scanner_nov_4" / "Engine_RPM.csv"
        
        if csv_file.exists():
            try:
                df = pd.read_csv(csv_file, delimiter=';')
                df['SECONDS'] = pd.to_numeric(df['SECONDS'], errors='coerce')
                df['VALUE'] = pd.to_numeric(df['VALUE'], errors='coerce')
                df = df.dropna()
                
                if not df.empty:
                    self.data['Engine_RPM'] = df
                    print(f"Loaded {len(df)} rows of Engine RPM data")
                    print(f"Time range: {df['SECONDS'].min():.2f} - {df['SECONDS'].max():.2f}")
                    print(f"Value range: {df['VALUE'].min()} - {df['VALUE'].max()}")
                else:
                    print("No valid data after cleaning")
                    
            except Exception as e:
                print(f"Error loading CSV: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"CSV file not found: {csv_file}")
            
    def setup_ui(self):
        """Setup simple UI."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 6), dpi=80)
        self.ax = self.figure.add_subplot(111)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready")
        self.status_label.pack(pady=5)
        
    def plot_data(self):
        """Plot the loaded data."""
        self.ax.clear()
        
        if not self.data:
            self.ax.text(0.5, 0.5, 'No data loaded', ha='center', va='center', transform=self.ax.transAxes)
            self.status_label.config(text="No data loaded")
        else:
            for pid, df in self.data.items():
                self.ax.plot(df['SECONDS'], df['VALUE'], label=pid, linewidth=2)
                
            self.ax.set_xlabel('Time (seconds)')
            self.ax.set_ylabel('Value')
            self.ax.set_title('OBD Data - Test Plot')
            self.ax.grid(True, alpha=0.3)
            self.ax.legend()
            
            self.status_label.config(text=f"Loaded {len(self.data)} dataset(s)")
            
        self.canvas.draw()

def main():
    root = tk.Tk()
    app = MinimalViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
