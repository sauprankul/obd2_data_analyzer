#!/usr/bin/env python3
"""
OBD2 Data Visualization Tool

A comprehensive tool for visualizing and comparing OBD2 (On-Board Diagnostics) 
CSV data from vehicles. This package provides web-based dashboards for analyzing
vehicle sensor data, creating custom groups, and exporting visualizations.
"""

from .core.data_loader import OBDDataLoader
from .core.data_processor import OBDDataProcessor
from .visualization.dashboard import OBD2Dashboard
from .app.main_application import OBD2ViewerApp

__version__ = "1.0.0"
__author__ = "OBD2 Data Visualization Team"

__all__ = [
    'OBDDataLoader',
    'OBDDataProcessor', 
    'OBD2Dashboard',
    'OBD2ViewerApp'
]
