#!/usr/bin/env python3
"""
OBD2 Data Visualization Tool

A native Windows application for visualizing and comparing OBD2 (On-Board Diagnostics) 
CSV data from vehicles. Uses PyQt6 for the UI and PyQtGraph for high-performance
chart rendering.
"""

from .core.data_loader import OBDDataLoader
from .core.data_processor import OBDDataProcessor

__version__ = "2.0.0"
__author__ = "OBD2 Data Visualization Team"

__all__ = [
    'OBDDataLoader',
    'OBDDataProcessor',
]
