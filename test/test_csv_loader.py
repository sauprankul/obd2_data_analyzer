#!/usr/bin/env python3
"""
Unit tests for CSV loading functionality
"""

import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

class TestCSVLoader(unittest.TestCase):
    """Test CSV loading functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = Path(__file__).parent
        
    def test_load_engine_rpm_csv(self):
        """Test loading engine RPM CSV file."""
        csv_file = self.test_data_dir / "test_data_engine_rpm.csv"
        
        # Load CSV
        df = pd.read_csv(csv_file, delimiter=';')
        
        # Basic checks
        self.assertEqual(len(df), 10)
        self.assertIn('SECONDS', df.columns)
        self.assertIn('PID', df.columns)
        self.assertIn('VALUE', df.columns)
        self.assertIn('UNITS', df.columns)
        
        # Check data types
        df['SECONDS'] = pd.to_numeric(df['SECONDS'], errors='coerce')
        df['VALUE'] = pd.to_numeric(df['VALUE'], errors='coerce')
        
        # Check specific values
        self.assertEqual(df['SECONDS'].iloc[0], 1000.0)
        self.assertEqual(df['VALUE'].iloc[0], 800)
        self.assertEqual(df['UNITS'].iloc[0], 'rpm')
        
    def test_load_vehicle_speed_csv(self):
        """Test loading vehicle speed CSV file."""
        csv_file = self.test_data_dir / "test_data_vehicle_speed.csv"
        
        df = pd.read_csv(csv_file, delimiter=';')
        
        self.assertEqual(len(df), 10)
        self.assertEqual(df['PID'].iloc[0], 'Vehicle speed')
        self.assertEqual(df['UNITS'].iloc[0], 'mph')
        
    def test_load_coolant_temp_csv(self):
        """Test loading coolant temperature CSV file."""
        csv_file = self.test_data_dir / "test_data_coolant_temp.csv"
        
        df = pd.read_csv(csv_file, delimiter=';')
        
        self.assertEqual(len(df), 10)
        self.assertEqual(df['PID'].iloc[0], 'Coolant temperature')
        self.assertEqual(df['UNITS'].iloc[0], 'F')
        
    def test_data_conversion(self):
        """Test numeric conversion of data."""
        csv_file = self.test_data_dir / "test_data_engine_rpm.csv"
        
        df = pd.read_csv(csv_file, delimiter=';')
        df['SECONDS'] = pd.to_numeric(df['SECONDS'], errors='coerce')
        df['VALUE'] = pd.to_numeric(df['VALUE'], errors='coerce')
        # Only drop NaN from SECONDS and VALUE columns, not the extra Unnamed column
        df = df.dropna(subset=['SECONDS', 'VALUE'])
        
        # Check that conversions worked
        self.assertEqual(df['SECONDS'].dtype, 'float64')
        self.assertTrue(df['VALUE'].dtype in ['int64', 'float64'])
        
        # Check range (after dropping NaN rows)
        self.assertGreaterEqual(df['SECONDS'].min(), 1000.0)
        self.assertLessEqual(df['SECONDS'].max(), 1009.0)
        self.assertGreater(len(df), 0)  # Should have data after dropping NaN
        
    def test_multiple_csv_loading(self):
        """Test loading multiple CSV files."""
        csv_files = [
            self.test_data_dir / "test_data_engine_rpm.csv",
            self.test_data_dir / "test_data_vehicle_speed.csv",
            self.test_data_dir / "test_data_coolant_temp.csv"
        ]
        
        data = {}
        for csv_file in csv_files:
            df = pd.read_csv(csv_file, delimiter=';')
            df['SECONDS'] = pd.to_numeric(df['SECONDS'], errors='coerce')
            df['VALUE'] = pd.to_numeric(df['VALUE'], errors='coerce')
            # Only drop NaN from SECONDS and VALUE columns
            df = df.dropna(subset=['SECONDS', 'VALUE'])
            
            pid_name = csv_file.stem.replace('test_data_', '')
            data[pid_name] = df
            
        # Check we loaded all files
        self.assertEqual(len(data), 3)
        self.assertIn('engine_rpm', data)
        self.assertIn('vehicle_speed', data)
        self.assertIn('coolant_temp', data)
        
        # Check each has data
        for pid, df in data.items():
            self.assertGreater(len(df), 0)
            self.assertIn('SECONDS', df.columns)
            self.assertIn('VALUE', df.columns)


class TestDataProcessing(unittest.TestCase):
    """Test data processing functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.test_data_dir = Path(__file__).parent
        
    def test_time_range_calculation(self):
        """Test time range calculation."""
        csv_file = self.test_data_dir / "test_data_engine_rpm.csv"
        df = pd.read_csv(csv_file, delimiter=';')
        df['SECONDS'] = pd.to_numeric(df['SECONDS'], errors='coerce')
        
        min_time = df['SECONDS'].min()
        max_time = df['SECONDS'].max()
        
        self.assertEqual(min_time, 1000.0)
        self.assertEqual(max_time, 1009.0)
        
    def test_unit_grouping(self):
        """Test grouping data by units."""
        csv_files = [
            self.test_data_dir / "test_data_engine_rpm.csv",
            self.test_data_dir / "test_data_vehicle_speed.csv",
            self.test_data_dir / "test_data_coolant_temp.csv"
        ]
        
        units = {}
        for csv_file in csv_files:
            df = pd.read_csv(csv_file, delimiter=';')
            pid_name = csv_file.stem.replace('test_data_', '')
            unit = df['UNITS'].iloc[0]
            units[pid_name] = unit
            
        # Check unit grouping
        self.assertEqual(units['engine_rpm'], 'rpm')
        self.assertEqual(units['vehicle_speed'], 'mph')
        self.assertEqual(units['coolant_temp'], 'F')
        
        # Group by units
        from collections import defaultdict
        unit_groups = defaultdict(list)
        for pid, unit in units.items():
            unit_groups[unit].append(pid)
            
        self.assertEqual(len(unit_groups['rpm']), 1)
        self.assertEqual(len(unit_groups['mph']), 1)
        self.assertEqual(len(unit_groups['F']), 1)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
