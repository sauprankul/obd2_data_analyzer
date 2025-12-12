#!/usr/bin/env python3
"""
OBD2 Data Processor Module

Handles data processing, filtering, and analysis operations on OBD2 data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import colorsys
import logging

logger = logging.getLogger(__name__)


class OBDDataProcessor:
    """
    Processes and analyzes OBD2 data.
    
    This class provides methods for filtering data by time ranges,
    managing groups of PIDs, generating colors, and performing basic
    statistical analysis on the data.
    """
    
    def __init__(self):
        """Initialize the data processor."""
        self.color_index = 0
        self.groups = {}  # Maps group names to lists of PIDs
        self.pid_groups = {}  # Maps PIDs to their group names
        
    def filter_data_by_time(self, data: Dict[str, pd.DataFrame], 
                           start_time: float, end_time: float) -> Dict[str, pd.DataFrame]:
        """
        Filter data by time range.
        
        Args:
            data: Dictionary of DataFrames indexed by PID
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            Filtered data dictionary
        """
        filtered_data = {}
        
        for pid, df in data.items():
            if 'SECONDS' in df.columns:
                mask = (df['SECONDS'] >= start_time) & (df['SECONDS'] <= end_time)
                filtered_df = df[mask].copy()
                filtered_data[pid] = filtered_df
            else:
                # If no SECONDS column, include the data as-is
                filtered_data[pid] = df.copy()
                
        return filtered_data
    
    def get_time_range(self, data: Dict[str, pd.DataFrame]) -> Tuple[float, float]:
        """
        Get the overall time range from the data.
        
        Args:
            data: Dictionary of DataFrames indexed by PID
            
        Returns:
            Tuple of (min_time, max_time)
        """
        if not data:
            return 0.0, 0.0
            
        all_times = []
        for df in data.values():
            if 'SECONDS' in df.columns:
                all_times.extend(df['SECONDS'].values)
        
        if not all_times:
            return 0.0, 0.0
            
        return min(all_times), max(all_times)
    
    def generate_colors(self, pids: List[str]) -> Dict[str, str]:
        """
        Generate colors for PIDs using golden ratio for better distribution.
        
        Args:
            pids: List of PID names
            
        Returns:
            Dictionary mapping PID names to hex color codes
        """
        colors = {}
        
        for i, pid in enumerate(pids):
            # Use golden ratio for better color distribution
            hue = (i * 0.618033988749895) % 1
            rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.8)
            color = '#%02x%02x%02x' % tuple(int(c * 255) for c in rgb)
            colors[pid] = color
            
        return colors
    
    def get_next_color(self) -> str:
        """
        Get the next color in the sequence.
        
        Returns:
            Hex color code
        """
        hue = (self.color_index * 0.618033988749895) % 1
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.8)
        color = '#%02x%02x%02x' % tuple(int(c * 255) for c in rgb)
        self.color_index += 1
        return color
    
    def create_group(self, group_name: str, pids: List[str]) -> bool:
        """
        Create a new group of PIDs.
        
        Args:
            group_name: Name of the group
            pids: List of PIDs to include in the group
            
        Returns:
            True if group was created successfully
        """
        if group_name in self.groups:
            logger.warning(f"Group '{group_name}' already exists")
            return False
            
        self.groups[group_name] = pids.copy()
        for pid in pids:
            self.pid_groups[pid] = group_name
            
        logger.info(f"Created group '{group_name}' with {len(pids)} PIDs")
        return True
    
    def add_pid_to_group(self, group_name: str, pid: str) -> bool:
        """
        Add a PID to an existing group.
        
        Args:
            group_name: Name of the group
            pid: PID to add
            
        Returns:
            True if PID was added successfully
        """
        if group_name not in self.groups:
            logger.warning(f"Group '{group_name}' does not exist")
            return False
            
        # Remove PID from current group if it exists
        if pid in self.pid_groups:
            old_group = self.pid_groups[pid]
            if pid in self.groups[old_group]:
                self.groups[old_group].remove(pid)
        
        # Add PID to new group
        self.groups[group_name].append(pid)
        self.pid_groups[pid] = group_name
        
        logger.info(f"Added PID '{pid}' to group '{group_name}'")
        return True
    
    def remove_pid_from_group(self, pid: str) -> bool:
        """
        Remove a PID from its current group.
        
        Args:
            pid: PID to remove
            
        Returns:
            True if PID was removed successfully
        """
        if pid not in self.pid_groups:
            logger.warning(f"PID '{pid}' is not in any group")
            return False
            
        group_name = self.pid_groups[pid]
        self.groups[group_name].remove(pid)
        del self.pid_groups[pid]
        
        # Remove group if it's empty
        if not self.groups[group_name]:
            del self.groups[group_name]
            
        logger.info(f"Removed PID '{pid}' from group '{group_name}'")
        return True
    
    def delete_group(self, group_name: str) -> bool:
        """
        Delete a group and move all PIDs to individual status.
        
        Args:
            group_name: Name of the group to delete
            
        Returns:
            True if group was deleted successfully
        """
        if group_name not in self.groups:
            logger.warning(f"Group '{group_name}' does not exist")
            return False
            
        # Remove all PIDs from the group
        for pid in self.groups[group_name]:
            if pid in self.pid_groups:
                del self.pid_groups[pid]
        
        del self.groups[group_name]
        
        logger.info(f"Deleted group '{group_name}'")
        return True
    
    def get_individual_pids(self, all_pids: List[str]) -> List[str]:
        """
        Get PIDs that are not in any group.
        
        Args:
            all_pids: List of all available PIDs
            
        Returns:
            List of PIDs that are not in any group
        """
        return [pid for pid in all_pids if pid not in self.pid_groups]
    
    def get_statistics(self, data: Dict[str, pd.DataFrame], 
                      pid: str) -> Dict[str, Any]:
        """
        Calculate basic statistics for a specific PID.
        
        Args:
            data: Dictionary of DataFrames indexed by PID
            pid: PID to analyze
            
        Returns:
            Dictionary containing statistics
        """
        if pid not in data:
            return {}
            
        df = data[pid]
        if 'VALUE' not in df.columns:
            return {}
            
        values = df['VALUE'].dropna()
        if len(values) == 0:
            return {}
            
        stats = {
            'count': len(values),
            'mean': float(values.mean()),
            'min': float(values.min()),
            'max': float(values.max()),
            'std': float(values.std()) if len(values) > 1 else 0.0,
            'median': float(values.median())
        }
        
        # Add time-based statistics if available
        if 'SECONDS' in df.columns:
            time_data = df.dropna(subset=['SECONDS', 'VALUE'])
            if len(time_data) > 1:
                time_diff = time_data['SECONDS'].max() - time_data['SECONDS'].min()
                stats['duration'] = float(time_diff)
                stats['sample_rate'] = len(time_data) / time_diff if time_diff > 0 else 0.0
        
        return stats
    
    def detect_anomalies(self, data: Dict[str, pd.DataFrame], 
                        pid: str, threshold: float = 2.0) -> List[int]:
        """
        Detect anomalies in data using z-score method.
        
        Args:
            data: Dictionary of DataFrames indexed by PID
            pid: PID to analyze
            threshold: Z-score threshold for anomaly detection
            
        Returns:
            List of indices where anomalies were detected
        """
        if pid not in data:
            return []
            
        df = data[pid]
        if 'VALUE' not in df.columns:
            return []
            
        values = df['VALUE'].dropna()
        if len(values) < 3:
            return []
            
        # Calculate z-scores
        z_scores = np.abs((values - values.mean()) / values.std())
        anomaly_indices = values[z_scores > threshold].index.tolist()
        
        return anomaly_indices
    
    def resample_data(self, data: Dict[str, pd.DataFrame], 
                     target_interval: float = 1.0) -> Dict[str, pd.DataFrame]:
        """
        Resample data to a uniform time interval.
        
        Args:
            data: Dictionary of DataFrames indexed by PID
            target_interval: Target time interval in seconds
            
        Returns:
            Resampled data dictionary
        """
        resampled_data = {}
        
        for pid, df in data.items():
            if 'SECONDS' not in df.columns or 'VALUE' not in df.columns:
                resampled_data[pid] = df.copy()
                continue
                
            # Set SECONDS as index and resample
            df_clean = df.dropna(subset=['SECONDS', 'VALUE']).set_index('SECONDS')
            
            # Create new time index
            min_time, max_time = self.get_time_range({pid: df})
            new_time_index = np.arange(min_time, max_time + target_interval, target_interval)
            
            # Interpolate to new time points
            df_interpolated = df_clean.reindex(new_time_index).interpolate(method='linear')
            df_interpolated = df_interpolated.reset_index()
            
            resampled_data[pid] = df_interpolated
            
        return resampled_data
