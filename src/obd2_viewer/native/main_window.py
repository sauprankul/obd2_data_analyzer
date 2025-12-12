#!/usr/bin/env python3
"""
Main Window for Native OBD2 Viewer.

Provides the main application window with file loading, channel controls,
time navigation, and the chart display area.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFileDialog, QMessageBox, QScrollArea, QFrame, QLabel,
    QPushButton, QLineEdit, QCheckBox, QGroupBox, QDoubleSpinBox,
    QStatusBar, QMenuBar, QMenu, QToolBar, QApplication, QSizePolicy
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFont

from .chart_widget import OBD2ChartWidget
from ..core.data_loader import OBDDataLoader

logger = logging.getLogger(__name__)


class ChannelControlWidget(QWidget):
    """Widget for controlling channel visibility."""
    
    def __init__(self, channel_name: str, display_name: str, unit: str, 
                 color: str, parent=None):
        super().__init__(parent)
        
        self.channel_name = channel_name
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Color indicator
        color_label = QLabel()
        color_label.setFixedSize(12, 12)
        color_label.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
        layout.addWidget(color_label)
        
        # Checkbox with channel name
        self.checkbox = QCheckBox(f"{display_name} ({unit})")
        self.checkbox.setChecked(True)
        layout.addWidget(self.checkbox, 1)


class TimeNavigationWidget(QWidget):
    """Widget for time navigation controls."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Time range inputs
        range_layout = QHBoxLayout()
        
        range_layout.addWidget(QLabel("Start:"))
        self.start_input = QDoubleSpinBox()
        self.start_input.setDecimals(2)
        self.start_input.setSuffix(" s")
        self.start_input.setRange(-999999, 999999)
        range_layout.addWidget(self.start_input)
        
        range_layout.addWidget(QLabel("End:"))
        self.end_input = QDoubleSpinBox()
        self.end_input.setDecimals(2)
        self.end_input.setSuffix(" s")
        self.end_input.setRange(-999999, 999999)
        range_layout.addWidget(self.end_input)
        
        layout.addLayout(range_layout)
        
        # Center time input
        center_layout = QHBoxLayout()
        center_layout.addWidget(QLabel("Center:"))
        self.center_input = QDoubleSpinBox()
        self.center_input.setDecimals(2)
        self.center_input.setSuffix(" s")
        self.center_input.setRange(-999999, 999999)
        center_layout.addWidget(self.center_input)
        
        self.go_to_center_btn = QPushButton("Go")
        self.go_to_center_btn.setFixedWidth(40)
        center_layout.addWidget(self.go_to_center_btn)
        
        layout.addLayout(center_layout)
        
        # Navigation buttons - Row 1 (fine)
        nav_layout1 = QHBoxLayout()
        self.btn_left_01 = QPushButton("◀ 0.1s")
        self.btn_left_05 = QPushButton("◀ 0.5s")
        self.btn_left_1 = QPushButton("◀ 1s")
        self.btn_right_1 = QPushButton("1s ▶")
        self.btn_right_05 = QPushButton("0.5s ▶")
        self.btn_right_01 = QPushButton("0.1s ▶")
        
        for btn in [self.btn_left_01, self.btn_left_05, self.btn_left_1,
                    self.btn_right_1, self.btn_right_05, self.btn_right_01]:
            btn.setFixedHeight(28)
            nav_layout1.addWidget(btn)
        
        layout.addLayout(nav_layout1)
        
        # Navigation buttons - Row 2 (coarse)
        nav_layout2 = QHBoxLayout()
        self.btn_left_5 = QPushButton("◀ 5s")
        self.btn_left_15 = QPushButton("◀ 15s")
        self.btn_left_30 = QPushButton("◀ 30s")
        self.btn_right_30 = QPushButton("30s ▶")
        self.btn_right_15 = QPushButton("15s ▶")
        self.btn_right_5 = QPushButton("5s ▶")
        
        for btn in [self.btn_left_5, self.btn_left_15, self.btn_left_30,
                    self.btn_right_30, self.btn_right_15, self.btn_right_5]:
            btn.setFixedHeight(28)
            nav_layout2.addWidget(btn)
        
        layout.addLayout(nav_layout2)
        
        # Navigation buttons - Row 3 (very coarse)
        nav_layout3 = QHBoxLayout()
        self.btn_left_1min = QPushButton("◀ 1min")
        self.btn_left_5min = QPushButton("◀ 5min")
        self.btn_reset = QPushButton("Reset View")
        self.btn_right_5min = QPushButton("5min ▶")
        self.btn_right_1min = QPushButton("1min ▶")
        
        # Consistent gray button style
        btn_style = "background-color: #616161; color: white; font-weight: bold;"
        self.btn_reset.setStyleSheet(btn_style)
        
        for btn in [self.btn_left_1min, self.btn_left_5min, self.btn_reset,
                    self.btn_right_5min, self.btn_right_1min]:
            btn.setFixedHeight(28)
            nav_layout3.addWidget(btn)
        
        layout.addLayout(nav_layout3)
        
        # Zoom buttons - Row 4
        zoom_layout = QHBoxLayout()
        self.btn_zoom_in = QPushButton("🔍+ Zoom In")
        self.btn_zoom_out = QPushButton("🔍- Zoom Out")
        
        self.btn_zoom_in.setStyleSheet(btn_style)
        self.btn_zoom_out.setStyleSheet(btn_style)
        
        for btn in [self.btn_zoom_in, self.btn_zoom_out]:
            btn.setFixedHeight(32)
            zoom_layout.addWidget(btn)
        
        layout.addLayout(zoom_layout)


class OBD2MainWindow(QMainWindow):
    """
    Main application window for the native OBD2 viewer.
    
    Provides a professional native Windows interface with:
    - File loading via drag-drop or file dialog
    - Channel visibility controls
    - Time navigation with multiple granularities
    - High-performance hardware-accelerated charts
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("OBD2 Data Visualization Tool")
        self.setMinimumSize(1200, 800)
        
        # Settings
        self.settings = QSettings("OBD2Viewer", "NativeApp")
        
        # Data
        self.channels_data: Dict = {}
        self.units: Dict = {}
        self.display_names: Dict = {}
        self.channel_controls: Dict[str, ChannelControlWidget] = {}
        
        # Recent files
        self.recent_files: List[str] = []
        self._load_recent_files()
        
        # Setup UI
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()
        
        # Restore window geometry
        self._restore_geometry()
        
        logger.info("OBD2 Native Viewer initialized")
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Channel controls group
        channel_group = QGroupBox("Channel Controls")
        channel_layout = QVBoxLayout(channel_group)
        
        # Show/Hide all buttons
        btn_layout = QHBoxLayout()
        self.btn_show_all = QPushButton("Show All")
        self.btn_hide_all = QPushButton("Hide All")
        btn_style = "background-color: #616161; color: white; font-weight: bold;"
        self.btn_show_all.setStyleSheet(btn_style)
        self.btn_hide_all.setStyleSheet(btn_style)
        btn_layout.addWidget(self.btn_show_all)
        btn_layout.addWidget(self.btn_hide_all)
        channel_layout.addLayout(btn_layout)
        
        # Channel list scroll area
        self.channel_scroll = QScrollArea()
        self.channel_scroll.setWidgetResizable(True)
        self.channel_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.channel_list_widget = QWidget()
        self.channel_list_layout = QVBoxLayout(self.channel_list_widget)
        self.channel_list_layout.setContentsMargins(0, 0, 0, 0)
        self.channel_list_layout.setSpacing(2)
        self.channel_list_layout.addStretch()
        
        self.channel_scroll.setWidget(self.channel_list_widget)
        channel_layout.addWidget(self.channel_scroll)
        
        left_layout.addWidget(channel_group)
        
        # Time navigation group
        time_group = QGroupBox("Time Navigation")
        time_layout = QVBoxLayout(time_group)
        self.time_nav = TimeNavigationWidget()
        time_layout.addWidget(self.time_nav)
        
        left_layout.addWidget(time_group)
        
        # Right panel - Charts
        self.chart_widget = OBD2ChartWidget()
        
        # Add panels to splitter
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(self.chart_widget)
        
        # Set initial splitter sizes (30% controls, 70% charts)
        self.splitter.setSizes([300, 900])
        
        # Welcome message when no data loaded
        self._show_welcome_message()
    
    def _show_welcome_message(self):
        """Show welcome message when no data is loaded."""
        # This will be replaced when data is loaded
        pass
    
    def _setup_menu(self):
        """Setup the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open CSV...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_file_dialog)
        file_menu.addAction(open_action)
        
        open_folder_action = QAction("Open &Folder...", self)
        open_folder_action.setShortcut("Ctrl+Shift+O")
        open_folder_action.triggered.connect(self._open_folder_dialog)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        # Recent files submenu
        self.recent_menu = file_menu.addMenu("Recent Files")
        self._update_recent_menu()
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        reset_view_action = QAction("&Reset Time Range", self)
        reset_view_action.setShortcut("Ctrl+R")
        reset_view_action.triggered.connect(self._reset_time_range)
        view_menu.addAction(reset_view_action)
        
        view_menu.addSeparator()
        
        show_all_action = QAction("&Show All Channels", self)
        show_all_action.setShortcut("Ctrl+A")
        show_all_action.triggered.connect(self._show_all_channels)
        view_menu.addAction(show_all_action)
        
        hide_all_action = QAction("&Hide All Channels", self)
        hide_all_action.setShortcut("Ctrl+H")
        hide_all_action.triggered.connect(self._hide_all_channels)
        view_menu.addAction(hide_all_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Setup the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Open file button
        open_btn = QPushButton("📂 Open CSV")
        open_btn.clicked.connect(self._open_file_dialog)
        toolbar.addWidget(open_btn)
    
    def _setup_statusbar(self):
        """Setup the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.status_label = QLabel("Ready - Open a CSV file to begin")
        self.statusbar.addWidget(self.status_label, 1)
        
        self.time_label = QLabel("")
        self.statusbar.addPermanentWidget(self.time_label)
        
        self.channel_label = QLabel("")
        self.statusbar.addPermanentWidget(self.channel_label)
    
    def _connect_signals(self):
        """Connect UI signals to slots."""
        # Channel control buttons
        self.btn_show_all.clicked.connect(self._show_all_channels)
        self.btn_hide_all.clicked.connect(self._hide_all_channels)
        
        # Time navigation
        nav = self.time_nav
        nav.btn_left_01.clicked.connect(lambda: self._shift_time(-0.1))
        nav.btn_left_05.clicked.connect(lambda: self._shift_time(-0.5))
        nav.btn_left_1.clicked.connect(lambda: self._shift_time(-1))
        nav.btn_left_5.clicked.connect(lambda: self._shift_time(-5))
        nav.btn_left_15.clicked.connect(lambda: self._shift_time(-15))
        nav.btn_left_30.clicked.connect(lambda: self._shift_time(-30))
        nav.btn_left_1min.clicked.connect(lambda: self._shift_time(-60))
        nav.btn_left_5min.clicked.connect(lambda: self._shift_time(-300))
        
        nav.btn_right_01.clicked.connect(lambda: self._shift_time(0.1))
        nav.btn_right_05.clicked.connect(lambda: self._shift_time(0.5))
        nav.btn_right_1.clicked.connect(lambda: self._shift_time(1))
        nav.btn_right_5.clicked.connect(lambda: self._shift_time(5))
        nav.btn_right_15.clicked.connect(lambda: self._shift_time(15))
        nav.btn_right_30.clicked.connect(lambda: self._shift_time(30))
        nav.btn_right_1min.clicked.connect(lambda: self._shift_time(60))
        nav.btn_right_5min.clicked.connect(lambda: self._shift_time(300))
        
        nav.btn_reset.clicked.connect(self._reset_time_range)
        nav.go_to_center_btn.clicked.connect(self._go_to_center)
        
        # Zoom buttons
        nav.btn_zoom_in.clicked.connect(self._zoom_in)
        nav.btn_zoom_out.clicked.connect(self._zoom_out)
        
        nav.start_input.valueChanged.connect(self._on_time_input_changed)
        nav.end_input.valueChanged.connect(self._on_time_input_changed)
        
        # Chart time range changes
        self.chart_widget.time_range_changed.connect(self._on_chart_time_changed)
    
    def _open_file_dialog(self):
        """Open file dialog to select CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open OBD2 CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self._load_file(file_path)
    
    def _open_folder_dialog(self):
        """Open folder dialog to select directory with CSV files."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with CSV Files"
        )
        
        if folder_path:
            self._load_folder(folder_path)
    
    def _load_file(self, file_path: str):
        """Load a single CSV file."""
        try:
            self.statusbar.showMessage(f"Loading {file_path}...")
            QApplication.processEvents()
            
            loader = OBDDataLoader(str(Path(file_path).parent))
            channels_data, units = loader.load_single_file(file_path)
            
            self._process_loaded_data(channels_data, units, file_path)
            self._add_to_recent(file_path)
            
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")
            self.statusbar.showMessage("Error loading file")
    
    def _load_folder(self, folder_path: str):
        """Load CSV files from a folder."""
        try:
            self.statusbar.showMessage(f"Loading from {folder_path}...")
            QApplication.processEvents()
            
            loader = OBDDataLoader(folder_path)
            channels_data, units = loader.load_csv_files()
            
            self._process_loaded_data(channels_data, units, folder_path)
            self._add_to_recent(folder_path)
            
        except Exception as e:
            logger.error(f"Error loading folder: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load folder:\n{e}")
            self.statusbar.showMessage("Error loading folder")
    
    def _process_loaded_data(self, channels_data: Dict, units: Dict, source: str):
        """Process loaded data and update UI."""
        self.channels_data = channels_data
        self.units = units
        
        # Create display names
        self.display_names = {
            ch: ch.replace('_', ' ').title() 
            for ch in channels_data.keys()
        }
        
        # Update chart
        self.chart_widget.load_data(channels_data, units, self.display_names)
        
        # Update channel controls
        self._update_channel_controls()
        
        # Update time navigation inputs
        self._update_time_inputs()
        
        # Update zoom button states
        self._update_zoom_buttons()
        
        # Update status
        num_channels = len(channels_data)
        total_points = sum(len(df) for df in channels_data.values())
        duration = self.chart_widget.max_time - self.chart_widget.min_time
        
        self.status_label.setText(f"Loaded: {Path(source).name}")
        self.channel_label.setText(f"{num_channels} channels")
        self.time_label.setText(f"Duration: {duration:.1f}s")
        
        self.statusbar.showMessage(
            f"Loaded {num_channels} channels with {total_points:,} data points",
            5000
        )
        
        logger.info(f"Loaded {num_channels} channels from {source}")
    
    def _update_channel_controls(self):
        """Update the channel control list."""
        # Clear existing controls
        for control in self.channel_controls.values():
            self.channel_list_layout.removeWidget(control)
            control.deleteLater()
        self.channel_controls.clear()
        
        # Remove stretch
        while self.channel_list_layout.count() > 0:
            item = self.channel_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create new controls
        colors = self.chart_widget.colors
        for channel in self.channels_data.keys():
            display_name = self.display_names.get(channel, channel)
            unit = self.units.get(channel, '')
            color = colors.get(channel, '#1f77b4')
            
            control = ChannelControlWidget(channel, display_name, unit, color)
            control.checkbox.stateChanged.connect(
                lambda state, ch=channel: self._on_channel_toggled(ch, state)
            )
            
            self.channel_controls[channel] = control
            self.channel_list_layout.addWidget(control)
        
        # Add stretch at end
        self.channel_list_layout.addStretch()
    
    def _update_time_inputs(self):
        """Update time navigation input values."""
        nav = self.time_nav
        chart = self.chart_widget
        
        nav.start_input.blockSignals(True)
        nav.end_input.blockSignals(True)
        nav.center_input.blockSignals(True)
        
        nav.start_input.setRange(chart.min_time, chart.max_time)
        nav.end_input.setRange(chart.min_time, chart.max_time)
        nav.center_input.setRange(chart.min_time, chart.max_time)
        
        nav.start_input.setValue(chart.current_start)
        nav.end_input.setValue(chart.current_end)
        nav.center_input.setValue((chart.current_start + chart.current_end) / 2)
        
        nav.start_input.blockSignals(False)
        nav.end_input.blockSignals(False)
        nav.center_input.blockSignals(False)
    
    def _on_channel_toggled(self, channel: str, state: int):
        """Handle channel visibility toggle."""
        visible = state == Qt.CheckState.Checked.value
        self.chart_widget.set_channel_visible(channel, visible)
    
    def _show_all_channels(self):
        """Show all channels."""
        for control in self.channel_controls.values():
            control.checkbox.setChecked(True)
        self.chart_widget.show_all_channels()
    
    def _hide_all_channels(self):
        """Hide all channels."""
        for control in self.channel_controls.values():
            control.checkbox.setChecked(False)
        self.chart_widget.hide_all_channels()
    
    def _shift_time(self, delta: float):
        """Shift time range by delta seconds."""
        self.chart_widget.shift_time(delta)
        self._update_time_inputs()
    
    def _reset_time_range(self):
        """Reset to full time range."""
        self.chart_widget.reset_time_range()
        self._update_time_inputs()
        self._update_zoom_buttons()
    
    def _zoom_in(self):
        """Zoom in by reducing time range by 10% (5% each side)."""
        chart = self.chart_widget
        duration = chart.current_end - chart.current_start
        center = (chart.current_start + chart.current_end) / 2
        
        # Reduce duration by 10% (5% each side)
        new_duration = duration * 0.9
        
        # Minimum duration check (approximately 10 seconds to keep markers readable)
        min_duration = 10.0
        if new_duration < min_duration:
            new_duration = min_duration
        
        new_start = center - new_duration / 2
        new_end = center + new_duration / 2
        
        chart.set_time_range(new_start, new_end)
        self._update_time_inputs()
        self._update_zoom_buttons()
    
    def _zoom_out(self):
        """Zoom out by increasing time range by 10% (5% each side)."""
        chart = self.chart_widget
        duration = chart.current_end - chart.current_start
        center = (chart.current_start + chart.current_end) / 2
        
        # Increase duration by ~11% (inverse of 0.9)
        new_duration = duration / 0.9
        
        # Maximum is full data range
        max_duration = chart.max_time - chart.min_time
        if new_duration > max_duration:
            new_duration = max_duration
        
        new_start = center - new_duration / 2
        new_end = center + new_duration / 2
        
        # Clamp to data bounds
        if new_start < chart.min_time:
            new_start = chart.min_time
            new_end = new_start + new_duration
        if new_end > chart.max_time:
            new_end = chart.max_time
            new_start = new_end - new_duration
        
        chart.set_time_range(new_start, new_end)
        self._update_time_inputs()
        self._update_zoom_buttons()
    
    def _update_zoom_buttons(self):
        """Update zoom button enabled states."""
        chart = self.chart_widget
        nav = self.time_nav
        
        current_duration = chart.current_end - chart.current_start
        max_duration = chart.max_time - chart.min_time
        min_duration = 10.0  # Minimum zoom level
        
        # Consistent button styles
        btn_style_enabled = "background-color: #616161; color: white; font-weight: bold;"
        btn_style_disabled = "background-color: #BDBDBD; color: #757575;"
        
        # Disable zoom in if at minimum duration
        at_min_zoom = current_duration <= min_duration
        nav.btn_zoom_in.setEnabled(not at_min_zoom)
        nav.btn_zoom_in.setStyleSheet(btn_style_disabled if at_min_zoom else btn_style_enabled)
        
        # Disable zoom out if at maximum duration (full range)
        at_max_zoom = current_duration >= max_duration * 0.99  # 99% tolerance
        nav.btn_zoom_out.setEnabled(not at_max_zoom)
        nav.btn_zoom_out.setStyleSheet(btn_style_disabled if at_max_zoom else btn_style_enabled)
    
    def _go_to_center(self):
        """Go to the center time specified in input."""
        center = self.time_nav.center_input.value()
        duration = self.chart_widget.current_end - self.chart_widget.current_start
        self.chart_widget.zoom_to_center(center, duration)
        self._update_time_inputs()
    
    def _on_time_input_changed(self):
        """Handle time input value changes."""
        start = self.time_nav.start_input.value()
        end = self.time_nav.end_input.value()
        
        if start < end:
            self.chart_widget.set_time_range(start, end)
    
    def _on_chart_time_changed(self, start: float, end: float):
        """Handle time range changes from chart."""
        nav = self.time_nav
        nav.start_input.blockSignals(True)
        nav.end_input.blockSignals(True)
        nav.center_input.blockSignals(True)
        
        nav.start_input.setValue(start)
        nav.end_input.setValue(end)
        nav.center_input.setValue((start + end) / 2)
        
        nav.start_input.blockSignals(False)
        nav.end_input.blockSignals(False)
        nav.center_input.blockSignals(False)
        
        self.time_label.setText(f"{start:.1f}s - {end:.1f}s")
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About OBD2 Data Visualization Tool",
            "<h2>OBD2 Data Visualization Tool</h2>"
            "<p>A professional native Windows application for analyzing "
            "and comparing OBD2 sensor data.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>High-performance hardware-accelerated charts</li>"
            "<li>Multi-channel CSV support</li>"
            "<li>Synchronized time navigation</li>"
            "<li>Channel visibility controls</li>"
            "</ul>"
            "<p>Built with PyQt6 and PyQtGraph</p>"
        )
    
    def _load_recent_files(self):
        """Load recent files from settings."""
        self.recent_files = self.settings.value("recent_files", [], type=list)
    
    def _save_recent_files(self):
        """Save recent files to settings."""
        self.settings.setValue("recent_files", self.recent_files)
    
    def _add_to_recent(self, path: str):
        """Add path to recent files."""
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:10]  # Keep only 10
        self._save_recent_files()
        self._update_recent_menu()
    
    def _update_recent_menu(self):
        """Update the recent files menu."""
        self.recent_menu.clear()
        
        for path in self.recent_files:
            action = QAction(Path(path).name, self)
            action.setToolTip(path)
            action.triggered.connect(lambda checked, p=path: self._open_recent(p))
            self.recent_menu.addAction(action)
        
        if not self.recent_files:
            action = QAction("(No recent files)", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
    
    def _open_recent(self, path: str):
        """Open a recent file or folder."""
        if Path(path).is_dir():
            self._load_folder(path)
        else:
            self._load_file(path)
    
    def _restore_geometry(self):
        """Restore window geometry from settings."""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        splitter_state = self.settings.value("splitter_state")
        if splitter_state:
            self.splitter.restoreState(splitter_state)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save geometry
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter_state", self.splitter.saveState())
        
        event.accept()
