#!/usr/bin/env python3
"""
OBD Data Splitter
Splits OBD CSV data into separate files by PID.
"""

import csv
import os
import sys
from collections import defaultdict
from pathlib import Path


def split_obd_csv(csv_file_path):
    """
    Split OBD CSV file into separate files by PID.
    
    Args:
        csv_file_path (str): Path to the input CSV file
    """
    # Validate input file exists
    if not os.path.exists(csv_file_path):
        print(f"Error: File {csv_file_path} not found")
        return
    
    # Get the base name without extension for folder creation
    base_name = Path(csv_file_path).stem
    parent_dir = Path(csv_file_path).parent
    output_dir = parent_dir / base_name
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")
    
    # Dictionary to store data for each PID
    pid_data = defaultdict(list)
    
    # Read the CSV file
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=';')
            
            # Read header
            header = next(reader)
            pid_data['header'] = header
            
            # Read data rows
            for row_num, row in enumerate(reader, start=2):
                if len(row) >= 2:  # Ensure we have at least SECONDS and PID
                    pid = row[1]  # PID is in the second column
                    pid_data[pid].append(row)
                else:
                    print(f"Warning: Skipping malformed row {row_num}: {row}")
    
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Write separate files for each PID
    header_row = pid_data['header']
    pids_written = 0
    
    for pid, data_rows in pid_data.items():
        if pid == 'header':
            continue  # Skip the header entry
            
        # Create safe filename from PID
        safe_pid = pid.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        safe_pid = safe_pid.replace(' ', '_').replace('-', '_')
        
        output_file = output_dir / f"{safe_pid}.csv"
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                
                # Write header
                writer.writerow(header_row)
                
                # Write data rows
                for row in data_rows:
                    writer.writerow(row)
                
                print(f"Created {output_file} with {len(data_rows)} data points")
                pids_written += 1
                
        except Exception as e:
            print(f"Error writing file {output_file}: {e}")
    
    print(f"\nSummary: Split {len(pid_data) - 1} unique PIDs into {pids_written} files in {output_dir}")


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 2:
        print("Usage: python split_obd_data.py <csv_file_path>")
        print("Example: python split_obd_data.py Car_scanner_nov_4.csv")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    split_obd_csv(csv_file_path)


if __name__ == "__main__":
    main()
