#!/usr/bin/env python3
"""
Test script to check CSV loading
"""

import pandas as pd
from pathlib import Path

def test_csv_loading():
    csv_file = Path(__file__).parent / "Car_scanner_nov_4" / "Engine_RPM.csv"
    
    print(f"Testing: {csv_file}")
    print(f"File exists: {csv_file.exists()}")
    
    try:
        # Try different reading methods
        print("\n--- Method 1: Default ---")
        df1 = pd.read_csv(csv_file)
        print(f"Shape: {df1.shape}")
        print(f"Columns: {list(df1.columns)}")
        print(f"Head:\n{df1.head()}")
        
        print("\n--- Method 2: Semicolon delimiter ---")
        df2 = pd.read_csv(csv_file, delimiter=';')
        print(f"Shape: {df2.shape}")
        print(f"Columns: {list(df2.columns)}")
        print(f"Head:\n{df2.head()}")
        
        print("\n--- Method 3: Semicolon + no quoting ---")
        df3 = pd.read_csv(csv_file, delimiter=';', quoting=3)
        print(f"Shape: {df3.shape}")
        print(f"Columns: {list(df3.columns)}")
        print(f"Head:\n{df3.head()}")
        
        # Check data types
        print(f"\nData types: {df3.dtypes}")
        
        # Convert to numeric
        df3['SECONDS'] = pd.to_numeric(df3['SECONDS'], errors='coerce')
        df3['VALUE'] = pd.to_numeric(df3['VALUE'], errors='coerce')
        print(f"\nAfter conversion:")
        print(f"Data types: {df3.dtypes}")
        print(f"Non-null counts: {df3.count()}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_csv_loading()
