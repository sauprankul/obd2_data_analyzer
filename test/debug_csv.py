#!/usr/bin/env python3
"""
Debug script to check CSV files
"""

import pandas as pd
from pathlib import Path

def debug_csv():
    csv_file = Path(__file__).parent / "test_data_engine_rpm.csv"
    
    print(f"Reading: {csv_file}")
    
    # Read raw
    with open(csv_file, 'r') as f:
        lines = f.readlines()
        print(f"Raw lines: {len(lines)}")
        for i, line in enumerate(lines):
            print(f"  {i}: {repr(line)}")
    
    # Read with pandas
    df = pd.read_csv(csv_file, delimiter=';')
    print(f"\nPandas DataFrame:")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"Data:\n{df}")
    
    # Convert
    df['SECONDS'] = pd.to_numeric(df['SECONDS'], errors='coerce')
    df['VALUE'] = pd.to_numeric(df['VALUE'], errors='coerce')
    print(f"\nAfter conversion:")
    print(f"SECONDS dtype: {df['SECONDS'].dtype}")
    print(f"VALUE dtype: {df['VALUE'].dtype}")
    print(f"Data:\n{df}")
    
    # Drop NaN
    df_clean = df.dropna()
    print(f"\nAfter dropping NaN:")
    print(f"Shape: {df_clean.shape}")
    print(f"Data:\n{df_clean}")

if __name__ == "__main__":
    debug_csv()
