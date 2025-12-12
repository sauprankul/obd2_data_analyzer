#!/usr/bin/env python3
"""
Permanent tests for MultiChannelCSVParser
"""

import unittest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from obd2_viewer.core.multi_channel_parser import MultiChannelCSVParser


class TestMultiChannelParser(unittest.TestCase):
    """Test the multi-channel CSV parser functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = MultiChannelCSVParser()
        self.test_csv = Path(__file__).parent / "nov_4_test_data.csv"
    
    def test_parse_csv_file(self):
        """Test parsing a multi-channel CSV file."""
        self.assertTrue(self.test_csv.exists(), "Test CSV file should exist")
        
        channels_data, units = self.parser.parse_csv_file(str(self.test_csv))
        
        # Verify basic parsing
        self.assertGreater(len(channels_data), 0, "Should parse at least one channel")
        self.assertGreater(len(units), 0, "Should extract units")
        
        # Check specific expected channels
        expected_channels = [
            "Engine_RPM",
            "Vehicle_speed", 
            "Calculated_engine_load_value"
        ]
        
        for channel in expected_channels:
            self.assertIn(channel, channels_data, f"Should find channel {channel}")
            df = channels_data[channel]
            self.assertGreater(len(df), 0, f"Channel {channel} should have data")
            self.assertIn("SECONDS", df.columns, f"Channel {channel} should have SECONDS column")
            self.assertIn("VALUE", df.columns, f"Channel {channel} should have VALUE column")
        
        print(f"✅ Successfully parsed {len(channels_data)} channels")
    
    def test_get_import_summary(self):
        """Test import summary generation."""
        channels_data, units = self.parser.parse_csv_file(str(self.test_csv))
        
        summary = self.parser.get_import_summary(channels_data, units)
        
        # Verify summary structure
        self.assertIn("channel_count", summary)
        self.assertIn("total_data_points", summary)
        self.assertIn("duration", summary)
        
        # Verify summary values
        self.assertEqual(summary["channel_count"], len(channels_data))
        self.assertGreater(summary["total_data_points"], 0)
        self.assertGreater(summary["duration"], 0)
        
        print(f"✅ Import summary: {summary['channel_count']} channels, {summary['total_data_points']} points")
    
    def test_interpolation(self):
        """Test that channels are interpolated to common time grid."""
        channels_data, units = self.parser.parse_csv_file(str(self.test_csv))
        
        # Get time ranges for all channels
        time_ranges = []
        for channel, df in channels_data.items():
            if len(df) > 0:
                time_ranges.append((df['SECONDS'].min(), df['SECONDS'].max()))
        
        # All channels should have same time range after interpolation
        if len(time_ranges) > 1:
            first_range = time_ranges[0]
            for i, time_range in enumerate(time_ranges[1:], 1):
                self.assertAlmostEqual(
                    first_range[0], time_range[0], places=1,
                    msg=f"Channel {i} should have same start time"
                )
                self.assertAlmostEqual(
                    first_range[1], time_range[1], places=1,
                    msg=f"Channel {i} should have same end time"
                )
        
        print("✅ Interpolation working correctly - all channels on same time grid")
    
    def test_units_extraction(self):
        """Test that units are correctly extracted."""
        channels_data, units = self.parser.parse_csv_file(str(self.test_csv))
        
        # Check specific units
        expected_units = {
            "Engine_RPM": "rpm",
            "Vehicle_speed": "mph",
            "Calculated_engine_load_value": "%"
        }
        
        for channel, expected_unit in expected_units.items():
            if channel in units:
                self.assertEqual(units[channel], expected_unit, 
                               f"Channel {channel} should have unit {expected_unit}")
        
        print(f"✅ Units extracted correctly for {len(units)} channels")


if __name__ == '__main__':
    unittest.main(verbosity=2)
