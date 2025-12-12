#!/usr/bin/env python3
"""
High-performance chart widget using PyQtGraph.

Provides hardware-accelerated plotting for OBD2 time-series data
with support for multiple synchronized channels.
"""

import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from typing import Dict, List, Optional, Any
import pandas as pd
import colorsys


# Signal for synchronized hover across all plots
class ChannelPlotWidget(pg.PlotWidget):
    """Individual channel plot with optimized rendering."""
    
    # Signal emitted when mouse hovers - sends x position
    hover_x_changed = pyqtSignal(float)
    # Signal emitted when x range changes via drag
    x_range_changed = pyqtSignal(float, float)
    
    def __init__(self, channel_name: str, unit: str, color: str, parent=None):
        super().__init__(parent)
        
        self.channel_name = channel_name
        self.unit = unit
        self.color = color
        self.data_line = None
        self._current_hover_value = None
        
        # Configure plot appearance
        self.setBackground('w')
        self.showGrid(x=True, y=True, alpha=0.3)
        
        # Set title with larger font for channel name and value
        self.setTitle(f'<span style="font-size: 11pt; font-weight: bold;">{channel_name}</span> <span style="font-size: 10pt; color: #666;">({unit})</span>')
        self.setLabel('left', '', units=unit)
        self.setLabel('bottom', 'Time', units='s')
        
        # Enable mouse interaction
        self.setMouseEnabled(x=True, y=False)
        self.enableAutoRange(axis='y', enable=True)
        
        # Create crosshair - vertical line only
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#1976D2', width=1, style=Qt.PenStyle.DashLine))
        self.addItem(self.vLine, ignoreBounds=True)
        
        # Connect mouse click instead of hover for performance
        self.scene().sigMouseClicked.connect(self.mouse_clicked)
        
        # Connect range change signal
        self.sigXRangeChanged.connect(self._on_x_range_changed)
        
        # Store data for hover lookup
        self._x_data = None
        self._y_data = None
    
    def set_data(self, x: np.ndarray, y: np.ndarray):
        """Set the data for this plot."""
        self._x_data = x
        self._y_data = y
        
        if self.data_line is None:
            pen = pg.mkPen(color=self.color, width=2)
            self.data_line = self.plot(x, y, pen=pen, name=self.channel_name)
        else:
            self.data_line.setData(x, y)
    
    def set_x_range(self, x_min: float, x_max: float):
        """Set the X axis range."""
        self.setXRange(x_min, x_max, padding=0)
    
    def _on_x_range_changed(self, view, range):
        """Handle X range change from user drag."""
        self.x_range_changed.emit(range[0], range[1])
    
    def mouse_clicked(self, event):
        """Handle mouse click for crosshair positioning."""
        pos = event.scenePos()
        if self.sceneBoundingRect().contains(pos):
            mouse_point = self.plotItem.vb.mapSceneToView(pos)
            x = mouse_point.x()
            
            self.vLine.setPos(x)
            self.update_hover_value(x)
            
            # Emit signal for synchronized crosshair
            self.hover_x_changed.emit(x)
    
    def update_hover_value(self, x: float):
        """Update the displayed hover value for given x position."""
        if self._x_data is not None and len(self._x_data) > 0:
            idx = np.searchsorted(self._x_data, x)
            idx = np.clip(idx, 0, len(self._x_data) - 1)
            
            y_val = self._y_data[idx]
            self._current_hover_value = y_val
            
            # Update title with current value
            self.setTitle(
                f'<span style="font-size: 11pt; font-weight: bold;">{self.channel_name}</span> '
                f'<span style="font-size: 10pt; color: #666;">({self.unit})</span> '
                f'<span style="font-size: 11pt; font-weight: bold; color: #1976D2;">= {y_val:.2f}</span>'
            )
            
            self.vLine.setPos(x)
    
    def clear_hover_value(self):
        """Clear the hover value from title."""
        self._current_hover_value = None
        self.setTitle(f'<span style="font-size: 11pt; font-weight: bold;">{self.channel_name}</span> <span style="font-size: 10pt; color: #666;">({self.unit})</span>')


class OBD2ChartWidget(QWidget):
    """
    Main chart widget containing multiple synchronized channel plots.
    
    Uses PyQtGraph for hardware-accelerated rendering capable of
    handling millions of data points smoothly.
    """
    
    # Signal emitted when time range changes
    time_range_changed = pyqtSignal(float, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.channels_data: Dict[str, pd.DataFrame] = {}
        self.units: Dict[str, str] = {}
        self.display_names: Dict[str, str] = {}
        self.colors: Dict[str, str] = {}
        self.plots: Dict[str, ChannelPlotWidget] = {}
        self.visible_channels: set = set()
        
        # Time range
        self.min_time = 0.0
        self.max_time = 100.0
        self.current_start = 0.0
        self.current_end = 100.0
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area for plots
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container for plots
        self.plots_container = QWidget()
        self.plots_layout = QVBoxLayout(self.plots_container)
        self.plots_layout.setContentsMargins(5, 5, 5, 5)
        self.plots_layout.setSpacing(15)  # More space between charts
        
        self.scroll_area.setWidget(self.plots_container)
        layout.addWidget(self.scroll_area)
        
        # Configure PyQtGraph global settings
        pg.setConfigOptions(antialias=True, useOpenGL=True)
    
    def load_data(self, channels_data: Dict[str, pd.DataFrame], 
                  units: Dict[str, str], 
                  display_names: Dict[str, str]):
        """
        Load channel data into the chart widget.
        
        Args:
            channels_data: Dictionary of DataFrames indexed by channel name
            units: Dictionary mapping channels to their units
            display_names: Dictionary mapping sanitized names to display names
        """
        self.channels_data = channels_data
        self.units = units
        self.display_names = display_names
        
        # Use single color for all channels in this dataset
        # A consistent color makes it clear all data is from the same source
        self.dataset_color = '#1976D2'  # Material Blue 700 - professional, readable
        self.colors = {ch: self.dataset_color for ch in channels_data.keys()}
        
        # Calculate time range
        self._calculate_time_range()
        
        # Set all channels visible by default
        self.visible_channels = set(channels_data.keys())
        
        # Create plots
        self._create_plots()
        
        # Update all plots with data and set initial range
        self._update_all_plots()
        
        # Force set the initial time range explicitly
        self.set_time_range(self.min_time, self.max_time)
    
    def _generate_colors(self, channels: List[str]) -> Dict[str, str]:
        """Generate distinct colors for each channel."""
        colors = {}
        for i, channel in enumerate(channels):
            hue = (i * 0.618033988749895) % 1
            rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.8)
            color = '#%02x%02x%02x' % tuple(int(c * 255) for c in rgb)
            colors[channel] = color
        return colors
    
    def _calculate_time_range(self):
        """Calculate the overall time range from all channels."""
        all_times = []
        for df in self.channels_data.values():
            if 'SECONDS' in df.columns:
                all_times.extend(df['SECONDS'].values)
        
        if all_times:
            self.min_time = min(all_times)
            self.max_time = max(all_times)
            self.current_start = self.min_time
            self.current_end = self.max_time
    
    def _create_plots(self):
        """Create plot widgets for all channels."""
        # Clear existing plots
        for plot in self.plots.values():
            self.plots_layout.removeWidget(plot)
            plot.deleteLater()
        self.plots.clear()
        
        # Create new plots
        for channel in self.channels_data.keys():
            display_name = self.display_names.get(channel, channel)
            unit = self.units.get(channel, '')
            color = self.colors.get(channel, '#1f77b4')
            
            plot = ChannelPlotWidget(display_name, unit, color)
            plot.setMinimumHeight(180)  # Taller for better title visibility
            plot.setMaximumHeight(220)
            
            # Disable auto-range on X axis - we control it manually
            plot.enableAutoRange(axis='x', enable=False)
            
            # Link X axis to other plots for synchronized panning
            if self.plots:
                first_plot = list(self.plots.values())[0]
                plot.setXLink(first_plot)
            
            # Connect hover signal for synchronized crosshair
            plot.hover_x_changed.connect(self._on_hover_x_changed)
            
            # Connect x range change for drag updates
            plot.x_range_changed.connect(self._on_plot_x_range_changed)
            
            self.plots[channel] = plot
            self.plots_layout.addWidget(plot)
    
    def _update_all_plots(self):
        """Update all plots with current data and time range."""
        for channel, plot in self.plots.items():
            if channel in self.visible_channels and channel in self.channels_data:
                df = self.channels_data[channel]
                
                # Filter by time range
                mask = (df['SECONDS'] >= self.current_start) & (df['SECONDS'] <= self.current_end)
                filtered_df = df[mask]
                
                if len(filtered_df) > 0:
                    x = filtered_df['SECONDS'].values
                    y = filtered_df['VALUE'].values
                    plot.set_data(x, y)
                    plot.set_x_range(self.current_start, self.current_end)
                
                plot.show()
            else:
                plot.hide()
    
    def set_channel_visible(self, channel: str, visible: bool):
        """Set visibility of a specific channel."""
        if visible:
            self.visible_channels.add(channel)
        else:
            self.visible_channels.discard(channel)
        
        if channel in self.plots:
            if visible:
                self.plots[channel].show()
                # Update data
                if channel in self.channels_data:
                    df = self.channels_data[channel]
                    mask = (df['SECONDS'] >= self.current_start) & (df['SECONDS'] <= self.current_end)
                    filtered_df = df[mask]
                    if len(filtered_df) > 0:
                        self.plots[channel].set_data(
                            filtered_df['SECONDS'].values,
                            filtered_df['VALUE'].values
                        )
            else:
                self.plots[channel].hide()
    
    def show_all_channels(self):
        """Show all channels."""
        self.visible_channels = set(self.channels_data.keys())
        self._update_all_plots()
    
    def hide_all_channels(self):
        """Hide all channels."""
        self.visible_channels.clear()
        for plot in self.plots.values():
            plot.hide()
    
    def set_time_range(self, start: float, end: float):
        """Set the visible time range."""
        self.current_start = max(self.min_time, start)
        self.current_end = min(self.max_time, end)
        self._update_all_plots()
        self.time_range_changed.emit(self.current_start, self.current_end)
    
    def shift_time(self, delta: float):
        """Shift the time range by delta seconds."""
        duration = self.current_end - self.current_start
        new_start = self.current_start + delta
        new_end = self.current_end + delta
        
        # Clamp to data bounds
        if new_start < self.min_time:
            new_start = self.min_time
            new_end = new_start + duration
        if new_end > self.max_time:
            new_end = self.max_time
            new_start = new_end - duration
        
        self.set_time_range(new_start, new_end)
    
    def reset_time_range(self):
        """Reset to full time range."""
        self.set_time_range(self.min_time, self.max_time)
    
    def zoom_to_center(self, center: float, duration: float):
        """Zoom to a specific center time with given duration."""
        half_duration = duration / 2
        self.set_time_range(center - half_duration, center + half_duration)
    
    def _on_hover_x_changed(self, x: float):
        """Handle hover x change - update all plots' crosshairs and values."""
        for channel, plot in self.plots.items():
            if channel in self.visible_channels:
                plot.update_hover_value(x)
    
    def _on_plot_x_range_changed(self, x_min: float, x_max: float):
        """Handle x range change from plot drag."""
        # Update internal state
        self.current_start = max(self.min_time, x_min)
        self.current_end = min(self.max_time, x_max)
        
        # Emit signal to update time navigation inputs
        self.time_range_changed.emit(self.current_start, self.current_end)
