#!/usr/bin/env python3
"""
Multi-Channel CSV Parser for OBD2 Data

Handles parsing of multi-channel CSV files where channels are interleaved
as separate rows, like the Car_scanner_nov_4.csv format.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from scipy import interpolate

logger = logging.getLogger(__name__)


class MultiChannelCSVParser:
    """
    Parser for multi-channel OBD2 CSV files.
    
    Handles CSV files where each row represents a different channel reading,
    with channels identified by a PID column.
    """
    
    MAX_FILE_SIZE_MB = 10
    MAX_CHANNELS = 100
    
    def __init__(self):
        """Initialize the parser."""
        self.required_columns = ['SECONDS', 'PID', 'VALUE', 'UNITS']
        
    def parse_csv_file(self, file_path: str) -> Tuple[Dict[str, pd.DataFrame], Dict[str, str]]:
        """
        Parse a multi-channel CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Tuple of (channels_data, units_mapping)
            
        Raises:
            ValueError: If file is too large, malformed, or exceeds limits
        """
        file_path_obj = Path(file_path)
        
        # Validate file size
        file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise ValueError(f"File size {file_size_mb:.1f}MB exceeds limit of {self.MAX_FILE_SIZE_MB}MB")
        
        logger.info(f"Parsing multi-channel CSV: {file_path_obj.name} ({file_size_mb:.1f}MB)")
        
        try:
            # Read the CSV file
            df = pd.read_csv(file_path, delimiter=';')
            
            # Validate required columns
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Check if this is multi-channel format
            if 'PID' not in df.columns or df['PID'].nunique() <= 1:
                logger.info("File appears to be single-channel format")
                return self._parse_single_channel(df)
            
            return self._parse_multi_channel(df)
            
        except Exception as e:
            logger.error(f"Error parsing CSV file {file_path}: {e}")
            raise ValueError(f"Failed to parse CSV file: {e}")
    
    def _parse_single_channel(self, df: pd.DataFrame) -> Tuple[Dict[str, pd.DataFrame], Dict[str, str]]:
        """
        Parse a single-channel CSV file.
        
        Args:
            df: DataFrame containing single channel data
            
        Returns:
            Tuple of (channels_data, units_mapping)
        """
        if 'PID' in df.columns and len(df) > 0:
            channel_name = str(df['PID'].iloc[0])
        else:
            # Use filename as channel name
            channel_name = "single_channel"
        
        # Clean channel name
        channel_name = self._sanitize_channel_name(channel_name)
        
        # Create channel data
        channel_df = df[['SECONDS', 'VALUE']].copy()
        channel_df = channel_df.sort_values('SECONDS').reset_index(drop=True)
        
        # Get units
        units = {channel_name: 'unknown'}
        if 'UNITS' in df.columns and len(df) > 0:
            units[channel_name] = str(df['UNITS'].iloc[0])
        
        return {channel_name: channel_df}, units
    
    def _parse_multi_channel(self, df: pd.DataFrame) -> Tuple[Dict[str, pd.DataFrame], Dict[str, str]]:
        """
        Parse a multi-channel CSV file with interleaved channels.
        
        Args:
            df: DataFrame containing multi-channel data
            
        Returns:
            Tuple of (channels_data, units_mapping)
        """
        logger.info(f"Processing multi-channel data with {df['PID'].nunique()} channels")
        
        # Check channel limit
        unique_channels = df['PID'].nunique()
        if unique_channels > self.MAX_CHANNELS:
            raise ValueError(f"Too many channels ({unique_channels}). Maximum allowed: {self.MAX_CHANNELS}")
        
        # Group data by PID
        channels_data = {}
        units_mapping = {}
        
        # Get all unique PIDs and their units
        channel_info = df.groupby('PID')['UNITS'].first().to_dict()
        
        # Create common timestamp grid
        all_timestamps = sorted(df['SECONDS'].unique())
        
        for pid in df['PID'].unique():
            if pd.isna(pid):
                continue
                
            # Clean channel name
            channel_name = self._sanitize_channel_name(str(pid))
            
            # Get data for this channel
            channel_df = df[df['PID'] == pid][['SECONDS', 'VALUE']].copy()
            channel_df = channel_df.sort_values('SECONDS').reset_index(drop=True)
            
            # Interpolate to common timestamp grid
            interpolated_df = self._interpolate_to_grid(channel_df, all_timestamps)
            
            channels_data[channel_name] = interpolated_df
            units_mapping[channel_name] = str(channel_info.get(pid, 'unknown'))
        
        logger.info(f"Successfully parsed {len(channels_data)} channels")
        return channels_data, units_mapping
    
    def _interpolate_to_grid(self, channel_df: pd.DataFrame, target_timestamps: List[float]) -> pd.DataFrame:
        """
        Interpolate channel data to a common timestamp grid.
        
        Args:
            channel_df: Original channel data with SECONDS and VALUE columns
            target_timestamps: List of target timestamps to interpolate to
            
        Returns:
            DataFrame with interpolated data
        """
        if len(channel_df) < 2:
            # Not enough points for interpolation, just return original
            return channel_df
        
        try:
            # Create interpolation function
            x = channel_df['SECONDS'].values
            y = channel_df['VALUE'].values
            
            # Remove NaN values
            valid_mask = ~(np.isnan(x) | np.isnan(y))
            if not np.any(valid_mask):
                logger.warning("No valid data points for interpolation")
                return pd.DataFrame({'SECONDS': target_timestamps, 'VALUE': [np.nan] * len(target_timestamps)})
            
            x_clean = x[valid_mask]
            y_clean = y[valid_mask]
            
            # Remove duplicate x values (keep first occurrence) to avoid divide-by-zero
            # This happens when multiple samples have the same timestamp
            _, unique_indices = np.unique(x_clean, return_index=True)
            unique_indices = np.sort(unique_indices)  # Preserve original order
            x_clean = x_clean[unique_indices]
            y_clean = y_clean[unique_indices]
            
            # Create interpolation function
            if len(x_clean) >= 2:
                interp_func = interpolate.interp1d(
                    x_clean, y_clean, 
                    kind='linear', 
                    bounds_error=False, 
                    fill_value='extrapolate'
                )
                
                # Interpolate to target timestamps
                interpolated_values = interp_func(target_timestamps)
                
                return pd.DataFrame({
                    'SECONDS': target_timestamps,
                    'VALUE': interpolated_values
                })
            else:
                # Not enough valid points, return NaN
                return pd.DataFrame({'SECONDS': target_timestamps, 'VALUE': [np.nan] * len(target_timestamps)})
                
        except Exception as e:
            logger.error(f"Error during interpolation: {e}")
            # Fall back to original data
            return channel_df
    
    def _sanitize_channel_name(self, channel_name: str) -> str:
        """
        Sanitize channel name for use in component IDs and database storage.
        
        Args:
            channel_name: Original channel name
            
        Returns:
            Sanitized channel name
        """
        # Remove problematic characters
        sanitized = channel_name.replace(' ', '_')
        sanitized = sanitized.replace('-', '_')
        sanitized = sanitized.replace('.', '_')
        sanitized = sanitized.replace('/', '_')
        sanitized = sanitized.replace('\\', '_')
        sanitized = sanitized.replace('(', '_')
        sanitized = sanitized.replace(')', '_')
        sanitized = sanitized.replace('[', '_')
        sanitized = sanitized.replace(']', '_')
        sanitized = sanitized.replace('{', '_')
        sanitized = sanitized.replace('}', '_')
        
        # Remove any characters that aren't alphanumeric or underscores
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '_')
        
        # Limit length
        if len(sanitized) > 50:
            sanitized = sanitized[:47] + '...'
        
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = 'ch_' + sanitized
        
        return sanitized or 'unnamed_channel'
    
    def validate_import_compatibility(self, existing_channels: Dict[str, pd.DataFrame], 
                                    new_channels: Dict[str, pd.DataFrame]) -> List[str]:
        """
        Validate that new import is compatible with existing imports.
        
        Args:
            existing_channels: Dictionary of existing channel data
            new_channels: Dictionary of new channel data
            
        Returns:
            List of conflict messages (empty if no conflicts)
        """
        conflicts = []
        
        # Check for duplicate channel names
        existing_names = set(existing_channels.keys())
        new_names = set(new_channels.keys())
        
        duplicates = existing_names.intersection(new_names)
        if duplicates:
            conflicts.append(f"Duplicate channel names found: {', '.join(duplicates)}")
        
        # Check time range compatibility (optional - for future use)
        # This could warn if time ranges are vastly different
        
        return conflicts
    
    def get_import_summary(self, channels_data: Dict[str, pd.DataFrame], 
                          units_mapping: Dict[str, str]) -> Dict[str, any]:
        """
        Get summary information about the parsed import.
        
        Args:
            channels_data: Parsed channel data
            units_mapping: Units mapping
            
        Returns:
            Dictionary with import summary
        """
        if not channels_data:
            return {
                'channel_count': 0,
                'total_data_points': 0,
                'time_range_start': 0,
                'time_range_end': 0,
                'duration': 0,
                'channels': [],
                'units': {}
            }
        
        # Calculate summary statistics
        all_timestamps = []
        total_points = 0
        
        for channel_name, df in channels_data.items():
            all_timestamps.extend(df['SECONDS'].values)
            total_points += len(df)
        
        if all_timestamps:
            time_start = min(all_timestamps)
            time_end = max(all_timestamps)
            duration = time_end - time_start
        else:
            time_start = time_end = duration = 0
        
        return {
            'channel_count': len(channels_data),
            'total_data_points': total_points,
            'time_range_start': time_start,
            'time_range_end': time_end,
            'duration': duration,
            'channels': list(channels_data.keys()),
            'units': units_mapping
        }
