#!/usr/bin/env python3
"""
File utilities for OBD2 data processing.
"""

import os
import csv
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FileUtils:
    """Utility class for file operations."""
    
    @staticmethod
    def split_obd_csv(csv_file_path: str, output_directory: Optional[str] = None) -> bool:
        """
        Split OBD CSV file into separate files by PID.
        
        Args:
            csv_file_path: Path to the input CSV file
            output_directory: Directory to save split files (optional)
            
        Returns:
            True if splitting was successful
        """
        if not os.path.exists(csv_file_path):
            logger.error(f"File not found: {csv_file_path}")
            return False
        
        try:
            # Determine output directory
            if output_directory:
                out_dir = Path(output_directory)
            else:
                base_name = Path(csv_file_path).stem
                parent_dir = Path(csv_file_path).parent
                out_dir = parent_dir / base_name
            
            # Create output directory
            os.makedirs(out_dir, exist_ok=True)
            logger.info(f"Created output directory: {out_dir}")
            
            # Dictionary to store data for each PID
            pid_data = {}
            
            # Read the CSV file
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter=';')
                
                # Read header
                header = next(reader)
                
                # Read data rows and group by PID
                for row_num, row in enumerate(reader, start=2):
                    if len(row) >= 2:  # Ensure we have at least SECONDS and PID
                        pid = row[1]  # PID is in the second column
                        if pid not in pid_data:
                            pid_data[pid] = [header]  # Add header to new PID
                        pid_data[pid].append(row)
            
            # Write separate files for each PID
            for pid, data_rows in pid_data.items():
                # Sanitize PID name for filename
                safe_pid = FileUtils.sanitize_filename(pid)
                output_file = out_dir / f"{safe_pid}.csv"
                
                with open(output_file, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, delimiter=';')
                    writer.writerows(data_rows)
                
                logger.info(f"Created {output_file} with {len(data_rows)-1} data rows")
            
            logger.info(f"Successfully split {csv_file_path} into {len(pid_data)} files")
            return True
            
        except Exception as e:
            logger.error(f"Error splitting CSV file: {e}")
            return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe file system usage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace problematic characters
        sanitized = filename.replace(' ', '_')
        sanitized = sanitized.replace('-', '_')
        sanitized = sanitized.replace('.', '_')
        sanitized = sanitized.replace('/', '_')
        sanitized = sanitized.replace('\\', '_')
        
        # Remove any characters that aren't alphanumeric or underscores
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '_')
        
        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:97] + '...'
        
        return sanitized
    
    @staticmethod
    def validate_csv_structure(file_path: str, required_columns: List[str]) -> tuple[bool, str]:
        """
        Validate that CSV file has the required structure.
        
        Args:
            file_path: Path to CSV file
            required_columns: List of required column names
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter=';')
                header = next(reader)
                
                missing_columns = [col for col in required_columns if col not in header]
                
                if missing_columns:
                    return False, f"Missing required columns: {missing_columns}"
                
                return True, "CSV structure is valid"
                
        except Exception as e:
            return False, f"Error reading CSV file: {e}"
    
    @staticmethod
    def get_csv_info(file_path: str) -> Dict[str, any]:
        """
        Get information about a CSV file.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Dictionary with file information
        """
        info = {
            'file_path': file_path,
            'file_size': 0,
            'row_count': 0,
            'column_count': 0,
            'columns': [],
            'has_header': False
        }
        
        try:
            file_path_obj = Path(file_path)
            info['file_size'] = file_path_obj.stat().st_size
            
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter=';')
                
                # Try to read header
                try:
                    header = next(reader)
                    info['columns'] = header
                    info['column_count'] = len(header)
                    info['has_header'] = True
                    
                    # Count remaining rows
                    row_count = sum(1 for row in reader)
                    info['row_count'] = row_count + 1  # Include header
                    
                except StopIteration:
                    # Empty file
                    info['row_count'] = 0
                    info['column_count'] = 0
                    
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    @staticmethod
    def clean_temp_directory(temp_dir: str) -> bool:
        """
        Clean up temporary directory.
        
        Args:
            temp_dir: Path to temporary directory
            
        Returns:
            True if cleanup was successful
        """
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up temporary directory: {e}")
            return False
