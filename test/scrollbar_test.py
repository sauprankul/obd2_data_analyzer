#!/usr/bin/env python3
"""
Test scrollbar configuration
"""

import tkinter as tk
from tkinter import ttk

def test_scrollbar():
    root = tk.Tk()
    
    # Create scrollbar
    scrollbar = ttk.Scrollbar(root, orient=tk.HORIZONTAL)
    scrollbar.pack()
    
    # Test different config methods
    try:
        print("Testing config with 'from_' and 'to'...")
        scrollbar.config(from_=0, to=100)
        print("✓ from_/to works")
    except Exception as e:
        print(f"✗ from_/to failed: {e}")
    
    # Test getting values
    try:
        scrollbar.set(0, 100)
        print(f"Scrollbar value: {scrollbar.get()}")
    except Exception as e:
        print(f"Set failed: {e}")
    
    root.destroy()

if __name__ == "__main__":
    test_scrollbar()
