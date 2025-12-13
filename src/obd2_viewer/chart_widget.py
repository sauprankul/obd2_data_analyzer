#!/usr/bin/env python3
"""
High-performance chart widget using PyQtGraph.

Provides hardware-accelerated plotting for OBD2 time-series data
with support for multiple synchronized channels and multi-import visualization.
"""

import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .main_window import ImportData


class ChannelPlotWidget(pg.PlotWidget):
    """Individual channel plot with support for multiple data lines (multi-import)."""
    
    # Signal emitted when mouse clicks - sends x position
    hover_x_changed = pyqtSignal(float)
    # Signal emitted when x range changes via drag
    x_range_changed = pyqtSignal(float, float)
    # Signal emitted when user clicks to center on a position
    click_to_center = pyqtSignal(float)
    
    def __init__(self, channel_name: str, unit: str, parent=None):
        super().__init__(parent)
        
        self.channel_name = channel_name
        self.unit = unit
        
        # Multi-import support: list of data lines, one per import
        self.data_lines: List[Optional[pg.PlotDataItem]] = []
        self.import_colors: List[str] = []
        self.import_data: List[Dict] = []  # [{x, y, offset, visible}, ...]
        self._current_hover_values: List[Optional[float]] = []
        
        # Configure plot appearance
        self.setBackground('w')
        self.showGrid(x=True, y=True, alpha=0.3)
        
        # Performance optimizations
        self.setAntialiasing(False)  # Faster rendering
        
        # Set title with larger font for channel name and value
        self.setTitle(f'<span style="font-size: 11pt; font-weight: bold;">{channel_name}</span> <span style="font-size: 10pt; color: #666;">({unit})</span>')
        self.setLabel('left', '', units=unit)
        self.setLabel('bottom', 'Time', units='s')
        
        # Enable mouse interaction
        self.setMouseEnabled(x=True, y=False)
        self.enableAutoRange(axis='y', enable=True)
        
        # Store data bounds for zoom limiting
        self._x_min_bound = None
        self._x_max_bound = None
        
        # Last clicked position for zoom centering (set by mouse_clicked)
        self._last_click_x: Optional[float] = None
        
        # Create crosshair - vertical line only
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#1976D2', width=1, style=Qt.PenStyle.DashLine))
        self.addItem(self.vLine, ignoreBounds=True)
        
        # Connect mouse click instead of hover for performance
        self.scene().sigMouseClicked.connect(self.mouse_clicked)
        
        # Connect range change signal
        self.sigXRangeChanged.connect(self._on_x_range_changed)
        
        # Disable scroll wheel zoom - scroll should scroll the container, not zoom
        self.setMouseEnabled(x=True, y=False)
        self.getViewBox().setMouseEnabled(x=True, y=False)
        
        
    def wheelEvent(self, event):
        """Override wheel event - Ctrl+scroll zooms X axis, otherwise scroll container."""
        from PyQt6.QtCore import Qt
        
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Ctrl+scroll: zoom X axis
            delta = event.angleDelta().y()
            if delta != 0:
                # Get current view range
                view_range = self.viewRange()
                x_min, x_max = view_range[0]
                x_range = x_max - x_min
                
                # Use last clicked position as center if available
                x_center = (x_min + x_max) / 2
                if self._last_click_x is not None:
                    if self._x_min_bound is not None and self._x_max_bound is not None:
                        if self._x_min_bound <= self._last_click_x <= self._x_max_bound:
                            x_center = self._last_click_x
                
                # Zoom factor: scroll up = zoom in, scroll down = zoom out
                zoom_factor = 0.9 if delta > 0 else 1.1
                new_range = x_range * zoom_factor
                
                # Apply new range centered on click position
                new_min = x_center - new_range / 2
                new_max = x_center + new_range / 2
                
                # Boundary-aware clamping
                if self._x_min_bound is not None and new_min < self._x_min_bound:
                    new_min = self._x_min_bound
                    new_max = new_min + new_range
                if self._x_max_bound is not None and new_max > self._x_max_bound:
                    new_max = self._x_max_bound
                    new_min = new_max - new_range
                
                # Final clamp
                if self._x_min_bound is not None:
                    new_min = max(self._x_min_bound, new_min)
                if self._x_max_bound is not None:
                    new_max = min(self._x_max_bound, new_max)
                
                self.setXRange(new_min, new_max, padding=0)
                
            event.accept()
        else:
            # Normal scroll: pass to parent (scroll area)
            event.ignore()
        
    def set_import_count(self, count: int, colors: List[str]):
        """Initialize data structures for the given number of imports."""
        # Clear existing data lines
        for line in self.data_lines:
            if line is not None:
                self.removeItem(line)
        
        self.data_lines = [None] * count
        self.import_colors = colors
        self.import_data = [{'x': None, 'y': None, 'offset': 0.0, 'visible': True} for _ in range(count)]
        self._current_hover_values = [None] * count
    
    def set_import_data(self, import_index: int, x: np.ndarray, y: np.ndarray, offset: float = 0.0):
        """Set data for a specific import."""
        if import_index >= len(self.import_data):
            return
        
        self.import_data[import_index] = {
            'x': x,
            'y': y,
            'offset': offset,
            'visible': self.import_data[import_index].get('visible', True)
        }
        
        # Skip if no data
        if x is None or len(x) == 0:
            if self.data_lines[import_index] is not None:
                self.data_lines[import_index].setData([], [])
            return
        
        # Apply LOD downsampling for performance
        x_display, y_display = self._apply_lod(x, y, offset)
        
        color = self.import_colors[import_index] if import_index < len(self.import_colors) else '#1976D2'
        
        if self.data_lines[import_index] is None:
            pen = pg.mkPen(color=color, width=2)
            self.data_lines[import_index] = self.plot(x_display, y_display, pen=pen)
        else:
            self.data_lines[import_index].setData(x_display, y_display)
        
        # Set visibility
        if self.data_lines[import_index]:
            self.data_lines[import_index].setVisible(self.import_data[import_index]['visible'])
    
    def _apply_lod(self, x: np.ndarray, y: np.ndarray, offset: float, 
                   max_points: int = 2000) -> tuple:
        """Apply Level of Detail downsampling for performance.
        
        Uses peak-preserving downsampling to maintain visual fidelity
        while reducing point count for faster rendering.
        
        Args:
            x: Time values
            y: Data values  
            offset: Time offset to apply
            max_points: Maximum points to render (default 2000)
            
        Returns:
            Tuple of (x_display, y_display) arrays
        """
        x_display = x + offset
        
        if len(x) <= max_points:
            return x_display, y
        
        # Calculate downsample factor
        factor = len(x) // max_points
        
        # Peak-preserving downsampling: keep min and max in each bin
        # This preserves spikes and dips that simple decimation would miss
        n_bins = len(x) // factor
        x_out = []
        y_out = []
        
        for i in range(n_bins):
            start = i * factor
            end = min(start + factor, len(x))
            chunk_y = y[start:end]
            chunk_x = x_display[start:end]
            
            if len(chunk_y) == 0:
                continue
                
            # Find min and max indices
            min_idx = np.argmin(chunk_y)
            max_idx = np.argmax(chunk_y)
            
            # Add points in time order
            if min_idx < max_idx:
                x_out.extend([chunk_x[min_idx], chunk_x[max_idx]])
                y_out.extend([chunk_y[min_idx], chunk_y[max_idx]])
            else:
                x_out.extend([chunk_x[max_idx], chunk_x[min_idx]])
                y_out.extend([chunk_y[max_idx], chunk_y[min_idx]])
        
        return np.array(x_out), np.array(y_out)
    
    def set_import_visible(self, import_index: int, visible: bool):
        """Set visibility of a specific import's data line."""
        if import_index < len(self.import_data):
            self.import_data[import_index]['visible'] = visible
            if import_index < len(self.data_lines) and self.data_lines[import_index]:
                self.data_lines[import_index].setVisible(visible)
    
    def update_import_offset(self, import_index: int, offset: float):
        """Update the time offset for a specific import and redraw."""
        if import_index >= len(self.import_data):
            return
        
        data = self.import_data[import_index]
        data['offset'] = offset
        
        if data['x'] is not None and len(data['x']) > 0 and self.data_lines[import_index]:
            x_display, y_display = self._apply_lod(data['x'], data['y'], offset)
            self.data_lines[import_index].setData(x_display, y_display)
    
    def update_import_color(self, import_index: int, color: str):
        """Update the color for a specific import."""
        if import_index >= len(self.import_data):
            return
        
        self.import_colors[import_index] = color
        
        if self.data_lines[import_index]:
            pen = pg.mkPen(color=color, width=2)
            self.data_lines[import_index].setPen(pen)
        
        # Refresh title to update value colors
        self._refresh_title()
    
    def set_x_range(self, x_min: float, x_max: float):
        """Set the X axis range."""
        self.setXRange(x_min, x_max, padding=0)
    
    def set_x_limits(self, x_min: float, x_max: float):
        """Set the X axis limits to prevent zooming beyond data range."""
        self._x_min_bound = x_min
        self._x_max_bound = x_max
        self.setLimits(xMin=x_min, xMax=x_max)
    
    def _on_x_range_changed(self, view, range):
        """Handle X range change from user drag or scroll wheel."""
        x_min, x_max = range[0], range[1]
        
        # Clamp to bounds if set
        if self._x_min_bound is not None and self._x_max_bound is not None:
            if x_min < self._x_min_bound:
                x_min = self._x_min_bound
            if x_max > self._x_max_bound:
                x_max = self._x_max_bound
            
            if x_min != range[0] or x_max != range[1]:
                self.blockSignals(True)
                self.setXRange(x_min, x_max, padding=0)
                self.blockSignals(False)
        
        self.x_range_changed.emit(x_min, x_max)
    
    def mouse_clicked(self, event):
        """Handle mouse click for crosshair positioning and centering view."""
        pos = event.scenePos()
        if self.sceneBoundingRect().contains(pos):
            mouse_point = self.plotItem.vb.mapSceneToView(pos)
            x = mouse_point.x()
            
            # Store last clicked position for Ctrl+scroll zoom centering
            self._last_click_x = x
            
            self.vLine.setPos(x)
            self.update_hover_value(x)
            self.hover_x_changed.emit(x)
            
            # Emit signal to center view on clicked position
            self.click_to_center.emit(x)
    
    def update_hover_value(self, x: float):
        """Update the displayed hover value for given x position."""
        value_parts = []
        
        for i, data in enumerate(self.import_data):
            if data['x'] is not None and len(data['x']) > 0 and data['visible']:
                x_adjusted = x - data['offset']
                idx = np.searchsorted(data['x'], x_adjusted)
                idx = np.clip(idx, 0, len(data['x']) - 1)
                
                y_val = data['y'][idx]
                self._current_hover_values[i] = y_val
                
                color = self.import_colors[i] if i < len(self.import_colors) else '#1976D2'
                value_parts.append(f'<span style="color: {color}; font-weight: bold;">{y_val:.2f}</span>')
            else:
                if i < len(self._current_hover_values):
                    self._current_hover_values[i] = None
        
        if value_parts:
            values_str = ' | '.join(value_parts)
            self.setTitle(
                f'<span style="font-size: 11pt; font-weight: bold;">{self.channel_name}</span> '
                f'<span style="font-size: 10pt; color: #666;">({self.unit})</span> = {values_str}'
            )
        
        self.vLine.setPos(x)
    
    def clear_hover_value(self):
        """Clear the hover value from title."""
        self._current_hover_values = [None] * len(self.import_data)
        self.setTitle(f'<span style="font-size: 11pt; font-weight: bold;">{self.channel_name}</span> <span style="font-size: 10pt; color: #666;">({self.unit})</span>')
    
    def _refresh_title(self):
        """Refresh the title with current hover values and updated colors."""
        value_parts = []
        
        for i, val in enumerate(self._current_hover_values):
            if val is not None:
                color = self.import_colors[i] if i < len(self.import_colors) else '#1976D2'
                value_parts.append(f'<span style="color: {color}; font-weight: bold;">{val:.2f}</span>')
        
        if value_parts:
            values_str = ' | '.join(value_parts)
            self.setTitle(
                f'<span style="font-size: 11pt; font-weight: bold;">{self.channel_name}</span> '
                f'<span style="font-size: 10pt; color: #666;">({self.unit})</span> = {values_str}'
            )
        else:
            self.setTitle(f'<span style="font-size: 11pt; font-weight: bold;">{self.channel_name}</span> <span style="font-size: 10pt; color: #666;">({self.unit})</span>')


class OBD2ChartWidget(QWidget):
    """
    Main chart widget containing multiple synchronized channel plots.
    
    Uses PyQtGraph for hardware-accelerated rendering.
    All data is handled through the multi-import architecture.
    """
    
    time_range_changed = pyqtSignal(float, float)
    crosshair_moved = pyqtSignal(float)  # Emits current crosshair x position
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Import storage
        self.imports: List[Any] = []  # List of ImportData
        self.import_colors: List[str] = []
        
        # Plots keyed by channel name
        self.plots: Dict[str, ChannelPlotWidget] = {}
        
        # Visibility: {channel: {import_index: bool}}
        self.channel_visibility: Dict[str, Dict[int, bool]] = {}
        
        # Time range (based on first/base import)
        self.min_time = 0.0
        self.max_time = 100.0
        self.current_start = 0.0
        self.current_end = 100.0
        
        # Flag to prevent feedback during programmatic range changes
        self._updating_range = False
        
        # Last clicked position for zoom centering
        self._last_click_x: Optional[float] = None
        
        # Plot height settings
        self._base_plot_height = 200  # Base height in pixels
        self._plot_height_min = 200
        self._plot_height_max = 220
        
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
        self.plots_layout.setSpacing(15)
        
        self.scroll_area.setWidget(self.plots_container)
        layout.addWidget(self.scroll_area)
        
        # Configure PyQtGraph global settings
        # useOpenGL=False prevents blank rendering issues in scroll areas
        # The performance is still good with software rendering for our data sizes
        pg.setConfigOptions(antialias=False, useOpenGL=False)
    
    def load_data(self, imports: List[Any]):
        """
        Load data from imports.
        
        Args:
            imports: List of ImportData objects (can be 1 or more)
        """
        self.imports = imports
        self.import_colors = [imp.color for imp in imports]
        
        # Get all unique channels across all imports
        all_channels = set()
        for imp in imports:
            all_channels.update(imp.channels_data.keys())
        
        # Initialize visibility for all channels and imports
        self.channel_visibility = {
            ch: {i: True for i in range(len(imports))}
            for ch in all_channels
        }
        
        # Initialize chart visibility (whether each chart is shown at all)
        self.chart_visibility = {ch: True for ch in all_channels}
        
        # Time range from base (first) import
        if imports:
            base = imports[0]
            all_times = []
            for df in base.channels_data.values():
                if 'SECONDS' in df.columns and len(df) > 0:
                    all_times.extend([df['SECONDS'].min(), df['SECONDS'].max()])
            if all_times:
                self.min_time = min(all_times)
                self.max_time = max(all_times)
                self.current_start = self.min_time
                self.current_end = self.max_time
        
        # Create plots for all channels
        self._create_plots(all_channels)
        
        # Update all plots with data
        self._update_plots()
        
        # Set initial time range
        self.set_time_range(self.min_time, self.max_time)
    
    def _create_plots(self, channels: set):
        """Create plot widgets for all channels."""
        # Clear existing plots
        for plot in self.plots.values():
            self.plots_layout.removeWidget(plot)
            plot.deleteLater()
        self.plots.clear()
        
        # Sort channels by unit then alphabetically (matching sidebar organization)
        def get_channel_sort_key(ch):
            unit = ''
            for imp in self.imports:
                if ch in imp.channels_data:
                    unit = imp.units.get(ch, '')
                    break
            return (unit.lower(), ch.lower())
        
        sorted_channels = sorted(channels, key=get_channel_sort_key)
        
        # Create new plots
        for channel in sorted_channels:
            # Get display name and unit from first import that has this channel
            display_name = channel
            unit = ''
            for imp in self.imports:
                if channel in imp.channels_data:
                    display_name = imp.display_names.get(channel, channel)
                    unit = imp.units.get(channel, '')
                    break
            
            plot = ChannelPlotWidget(display_name, unit)
            plot.setMinimumHeight(self._plot_height_min)
            plot.setMaximumHeight(self._plot_height_max)
            
            # Initialize for imports
            plot.set_import_count(len(self.imports), self.import_colors)
            
            # Disable auto-range on X axis
            plot.enableAutoRange(axis='x', enable=False)
            
            # Link X axis to other plots
            if self.plots:
                first_plot = list(self.plots.values())[0]
                plot.setXLink(first_plot)
            
            # Connect signals
            plot.hover_x_changed.connect(self._on_hover_x_changed)
            plot.x_range_changed.connect(self._on_plot_x_range_changed)
            plot.click_to_center.connect(self._on_click_to_center)
            
            self.plots[channel] = plot
            self.plots_layout.addWidget(plot)
    
    def _update_plots(self):
        """Update all plots with data from all imports."""
        for channel, plot in self.plots.items():
            has_any_data = False
            
            for i, imp in enumerate(self.imports):
                if channel in imp.channels_data:
                    df = imp.channels_data[channel]
                    
                    if len(df) > 0:
                        x = df['SECONDS'].values
                        y = df['VALUE'].values
                        plot.set_import_data(i, x, y, imp.time_offset)
                        has_any_data = True
                else:
                    # This import doesn't have this channel - set empty data
                    plot.set_import_data(i, np.array([]), np.array([]), imp.time_offset)
            
            # Show/hide based on chart visibility setting
            chart_visible = self.chart_visibility.get(channel, True)
            
            if has_any_data and chart_visible:
                plot.set_x_range(self.current_start, self.current_end)
                plot.set_x_limits(self.min_time, self.max_time)
                plot.show()
            else:
                plot.hide()
    
    def add_channel(self, channel: str, display_name: str, unit: str):
        """Add a new channel (e.g., math channel) to the chart."""
        if channel in self.plots:
            # Channel already exists - just update data
            self._update_single_plot(channel)
            return
        
        # Initialize visibility
        self.channel_visibility[channel] = {i: False for i in range(len(self.imports))}
        
        # Create plot
        plot = ChannelPlotWidget(display_name, unit)
        plot.setMinimumHeight(self._plot_height_min)
        plot.setMaximumHeight(self._plot_height_max)
        plot.set_import_count(len(self.imports), self.import_colors)
        plot.enableAutoRange(axis='x', enable=False)
        
        # Link X axis to other plots
        if self.plots:
            first_plot = list(self.plots.values())[0]
            plot.setXLink(first_plot)
        
        # Connect signals
        plot.hover_x_changed.connect(self._on_hover_x_changed)
        plot.x_range_changed.connect(self._on_plot_x_range_changed)
        plot.click_to_center.connect(self._on_click_to_center)
        
        self.plots[channel] = plot
        self.plots_layout.addWidget(plot)
        
        # Update data for this plot
        self._update_single_plot(channel)
        
        # Set time range
        plot.set_x_range(self.current_start, self.current_end)
        plot.set_x_limits(self.min_time, self.max_time)
        
        # Start hidden
        plot.hide()
    
    def _update_single_plot(self, channel: str):
        """Update data for a single plot."""
        if channel not in self.plots:
            return
        
        plot = self.plots[channel]
        for i, imp in enumerate(self.imports):
            if channel in imp.channels_data:
                df = imp.channels_data[channel]
                if len(df) > 0:
                    x = df['SECONDS'].values
                    y = df['VALUE'].values
                    plot.set_import_data(i, x, y, imp.time_offset)
            else:
                plot.set_import_data(i, np.array([]), np.array([]), imp.time_offset)
    
    def set_channel_import_visible(self, channel: str, import_index: int, visible: bool):
        """Set visibility of a specific channel for a specific import."""
        if channel in self.channel_visibility:
            self.channel_visibility[channel][import_index] = visible
        
        if channel in self.plots:
            self.plots[channel].set_import_visible(import_index, visible)
    
    def set_chart_visible(self, channel: str, visible: bool):
        """Set visibility of an entire chart (show/hide the plot widget)."""
        # Track chart visibility state
        self.chart_visibility[channel] = visible
        
        if channel in self.plots:
            if visible:
                self.plots[channel].show()
            else:
                self.plots[channel].hide()
    
    def update_import_offset(self, import_index: int, offset: float):
        """Update the time offset for a specific import."""
        if import_index < len(self.imports):
            self.imports[import_index].time_offset = offset
            
            for channel, plot in self.plots.items():
                plot.update_import_offset(import_index, offset)
    
    def update_import_color(self, import_index: int, color: str):
        """Update the color for a specific import."""
        if import_index < len(self.imports):
            self.imports[import_index].color = color
            
            for channel, plot in self.plots.items():
                plot.update_import_color(import_index, color)
    
    def show_all_channels(self):
        """Show all channels for all imports."""
        for channel in self.plots:
            for i in range(len(self.imports)):
                self.set_channel_import_visible(channel, i, True)
        self._update_plots()
    
    def hide_all_channels(self):
        """Hide all channels for all imports."""
        for channel in self.plots:
            for i in range(len(self.imports)):
                self.set_channel_import_visible(channel, i, False)
        for plot in self.plots.values():
            plot.hide()
    
    def set_time_range(self, start: float, end: float):
        """Set the visible time range."""
        self._updating_range = True
        
        self.current_start = max(self.min_time, start)
        self.current_end = min(self.max_time, end)
        
        # Update X range on all plots
        for plot in self.plots.values():
            plot.set_x_range(self.current_start, self.current_end)
        
        self._updating_range = False
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
        for plot in self.plots.values():
            plot.update_hover_value(x)
        # Emit signal for status bar update
        self.crosshair_moved.emit(x)
    
    def _on_plot_x_range_changed(self, x_min: float, x_max: float):
        """Handle x range change from plot drag."""
        # Ignore if we're programmatically updating the range
        if self._updating_range:
            return
        
        self.current_start = max(self.min_time, x_min)
        self.current_end = min(self.max_time, x_max)
        self.time_range_changed.emit(self.current_start, self.current_end)
    
    def _on_click_to_center(self, x: float):
        """Handle click to center - shift view so clicked position is at center."""
        # Store last clicked position for zoom centering
        self._last_click_x = x
        
        duration = self.current_end - self.current_start
        half_duration = duration / 2
        
        new_start = x - half_duration
        new_end = x + half_duration
        
        # Clamp to data bounds
        if new_start < self.min_time:
            new_start = self.min_time
            new_end = new_start + duration
        if new_end > self.max_time:
            new_end = self.max_time
            new_start = new_end - duration
        
        self.set_time_range(new_start, new_end)
    
    def get_zoom_center(self) -> float:
        """Get the center point for zoom operations.
        
        Returns the last clicked position if available (within data bounds),
        otherwise returns the current view center.
        """
        view_center = (self.current_start + self.current_end) / 2
        
        if self._last_click_x is not None:
            # Use last click if it's within data bounds (not view bounds)
            # The zoom logic will handle boundary clamping
            if self.min_time <= self._last_click_x <= self.max_time:
                return self._last_click_x
        
        return view_center
    
    def make_plots_taller(self):
        """Increase plot heights by 5%."""
        self._base_plot_height = int(self._base_plot_height * 1.05)
        self._update_plot_heights()
    
    def make_plots_shorter(self):
        """Decrease plot heights by 5%."""
        new_height = int(self._base_plot_height * 0.95)
        # Minimum height of 80px
        if new_height >= 80:
            self._base_plot_height = new_height
            self._update_plot_heights()
    
    def _update_plot_heights(self):
        """Apply current height settings to all plots."""
        self._plot_height_min = self._base_plot_height
        self._plot_height_max = int(self._base_plot_height * 1.1)  # 10% range
        
        for plot in self.plots.values():
            plot.setMinimumHeight(self._plot_height_min)
            plot.setMaximumHeight(self._plot_height_max)
    
    def set_filter_mask(self, filter_masks: Optional[Dict[int, Dict[str, np.ndarray]]], 
                        filter_intervals: Optional[Dict[int, List[tuple]]] = None):
        """Apply filter masks to control which data points are visible.
        
        Args:
            filter_masks: Dict mapping import_index -> {channel_name: bool_mask_array}
                         If None, all data is shown (no filtering).
            filter_intervals: Dict mapping import_index -> [(start, end), ...] merged intervals.
                             Used to insert NaN separators between non-overlapping intervals.
        """
        self._filter_masks = filter_masks
        self._filter_intervals = filter_intervals
        
        if filter_masks is None:
            # No filtering - restore all data
            self._update_plots()
            return
        
        # Apply masks to each plot
        for channel, plot in self.plots.items():
            for i, imp in enumerate(self.imports):
                if channel not in imp.channels_data:
                    continue
                
                df = imp.channels_data[channel]
                if len(df) == 0:
                    continue
                
                x = df['SECONDS'].values
                y = df['VALUE'].values
                
                # Check if we have a mask for this import/channel
                if i in filter_masks and channel in filter_masks[i]:
                    mask = filter_masks[i][channel]
                    
                    # Apply mask - only show points where mask is True
                    if len(mask) == len(x):
                        x_filtered = x[mask]
                        y_filtered = y[mask]
                        
                        # Insert NaN separators between non-overlapping intervals
                        if filter_intervals and i in filter_intervals and len(filter_intervals[i]) > 1:
                            x_filtered, y_filtered = self._insert_nan_separators(
                                x_filtered, y_filtered, filter_intervals[i]
                            )
                    else:
                        # Mask length mismatch - show all data
                        x_filtered = x
                        y_filtered = y
                else:
                    # No mask for this channel - show all data
                    x_filtered = x
                    y_filtered = y
                
                # Update plot with filtered data
                plot.set_import_data(i, x_filtered, y_filtered, imp.time_offset)
        
        # Respect chart visibility after applying filter data
        for channel, plot in self.plots.items():
            if not self.chart_visibility.get(channel, True):
                plot.hide()
    
    def _insert_nan_separators(self, x: np.ndarray, y: np.ndarray, 
                                intervals: List[tuple]) -> tuple:
        """Insert NaN values between non-overlapping intervals to break lines.
        
        Args:
            x: Time values (already filtered)
            y: Data values (already filtered)
            intervals: List of (start, end) merged intervals
            
        Returns:
            (x_with_nans, y_with_nans) arrays with NaN separators inserted
        """
        if len(x) == 0 or len(intervals) <= 1:
            return x, y
        
        # For each point, determine which interval it belongs to
        interval_starts = np.array([iv[0] for iv in intervals])
        interval_ends = np.array([iv[1] for iv in intervals])
        
        # Find interval index for each point
        point_intervals = np.searchsorted(interval_starts, x, side='right') - 1
        
        # Find where interval changes (transition points)
        interval_changes = np.where(np.diff(point_intervals) != 0)[0]
        
        if len(interval_changes) == 0:
            # All points in same interval - no breaks needed
            return x, y
        
        # Build new arrays with NaN separators at interval boundaries
        # Each transition needs one NaN inserted
        new_len = len(x) + len(interval_changes)
        x_new = np.empty(new_len)
        y_new = np.empty(new_len)
        
        src_idx = 0
        dst_idx = 0
        
        for change_idx in interval_changes:
            # Copy points up to and including the change point
            count = change_idx - src_idx + 1
            x_new[dst_idx:dst_idx + count] = x[src_idx:src_idx + count]
            y_new[dst_idx:dst_idx + count] = y[src_idx:src_idx + count]
            dst_idx += count
            src_idx += count
            
            # Insert NaN separator
            x_new[dst_idx] = np.nan
            y_new[dst_idx] = np.nan
            dst_idx += 1
        
        # Copy remaining points
        remaining = len(x) - src_idx
        if remaining > 0:
            x_new[dst_idx:dst_idx + remaining] = x[src_idx:]
            y_new[dst_idx:dst_idx + remaining] = y[src_idx:]
        
        return x_new, y_new
