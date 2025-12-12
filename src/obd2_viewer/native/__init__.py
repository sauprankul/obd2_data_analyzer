"""
Native Windows OBD2 Viewer using PyQt6 and PyQtGraph.

This module provides a high-performance native Windows application
for visualizing OBD2 data without any browser dependencies.
"""

from .main_window import OBD2MainWindow
from .chart_widget import OBD2ChartWidget

__all__ = ['OBD2MainWindow', 'OBD2ChartWidget']
