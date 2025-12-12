#!/usr/bin/env python3
"""
OBD2 Data Loader Module

Handles loading and parsing of OBD2 CSV data files with support for
multiple formats, multi-channel files, and automatic delimiter detection.
"""

import pandas as pd
import os
import glob
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from .multi_channel_parser import MultiChannelCSVParser

logger = logging.getLogger(__name__)


class OBDDataLoader:
    """
    Loads and processes OBD2 CSV data files.
    
    This class handles the loading of OBD2 data from CSV files, with support
    for multiple delimiters, multi-channel format detection, and data validation.
    """
    
    def __init__(self, data_directory: Optional[str] = None):
        """
        Initialize the data loader.
        
        Args:
            data_directory: Directory containing CSV files. Defaults to current directory.
        """
        self.data_directory = Path(data_directory) if data_directory else Path.cwd()
        self.parser = MultiChannelCSVParser()
        
    def load_csv_files(self) -> Tuple[Dict[str, pd.DataFrame], Dict[str, str]]:
        """
        Load all CSV files from the data directory.
        
        Returns:
            Tuple of (channels_data, units_mapping)
        """
        csv_files = list(self.data_directory.glob("*.csv"))
        
        logger.info(f"Found {len(csv_files)} CSV files in {self.data_directory}")
        
        if not csv_files:
            logger.warning("No CSV files found")
            return {}, {}
        
        # For now, handle single file loading (multi-file support comes later)
        if len(csv_files) > 1:
            logger.warning("Multiple CSV files found. Using first file only for now.")
        
        csv_file = csv_files[0]
        
        try:
            channels_data, units_mapping = self.parser.parse_csv_file(csv_file)
            logger.info(f"Successfully loaded {csv_file.name} with {len(channels_data)} channels")
            return channels_data, units_mapping
            
        except Exception as e:
            logger.error(f"Error loading {csv_file.name}: {e}")
            raise
    
    def load_single_file(self, file_path: str) -> Tuple[Dict[str, pd.DataFrame], Dict[str, str]]:
        """
        Load a single CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Tuple of (channels_data, units_mapping)
        """
        return self.parser.parse_csv_file(file_path)
    
    def validate_data_directory(self) -> Tuple[bool, str]:
        """
        Validate that the data directory exists and contains CSV files.
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not self.data_directory.exists():
            return False, f"Directory does not exist: {self.data_directory}"
        
        csv_files = list(self.data_directory.glob("*.csv"))
        if not csv_files:
            return False, f"No CSV files found in directory: {self.data_directory}"
        
        return True, f"Found {len(csv_files)} CSV files"
    
    def get_import_summary(self, channels_data: Dict[str, pd.DataFrame], 
                          units_mapping: Dict[str, str]) -> Dict[str, any]:
        """
        Get a summary of the loaded data.
        
        Args:
            channels_data: Dictionary of channel DataFrames
            units_mapping: Dictionary of units per channel
            
        Returns:
            Dictionary containing data summary information
        """
        return self.parser.get_import_summary(channels_data, units_mapping)
    
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
        return self.parser.validate_import_compatibility(existing_channels, new_channels)
