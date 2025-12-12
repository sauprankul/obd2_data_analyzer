#!/usr/bin/env python3
"""
Main Window for Native OBD2 Viewer.

Provides the main application window with file loading, channel controls,
time navigation, and the chart display area.
"""

import sys
import json
import logging
import colorsys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFileDialog, QMessageBox, QScrollArea, QFrame, QLabel,
    QPushButton, QLineEdit, QCheckBox, QGroupBox, QDoubleSpinBox,
    QStatusBar, QMenuBar, QMenu, QToolBar, QApplication, QSizePolicy,
    QDialog, QListWidget, QListWidgetItem, QStackedWidget, QGridLayout
)
from PyQt6.QtCore import Qt, QSettings, QSize, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFont, QColor

from .chart_widget import OBD2ChartWidget
from ..core.data_loader import OBDDataLoader

logger = logging.getLogger(__name__)

# Import colors for multi-import visualization
IMPORT_COLORS = [
    '#1976D2',  # Blue
    '#D32F2F',  # Red
    '#388E3C',  # Green
    '#7B1FA2',  # Purple
    '#F57C00',  # Orange
    '#0097A7',  # Cyan
    '#C2185B',  # Pink
    '#5D4037',  # Brown
]


@dataclass
class ImportData:
    """Represents a single imported CSV file."""
    file_path: str
    channels_data: Dict
    units: Dict
    display_names: Dict
    color: str
    time_offset: float = 0.0  # Offset relative to base import
    
    @property
    def filename(self) -> str:
        return Path(self.file_path).name
    
    @property
    def min_time(self) -> float:
        all_times = []
        for df in self.channels_data.values():
            if 'SECONDS' in df.columns and len(df) > 0:
                all_times.extend([df['SECONDS'].min(), df['SECONDS'].max()])
        return min(all_times) if all_times else 0.0
    
    @property
    def max_time(self) -> float:
        all_times = []
        for df in self.channels_data.values():
            if 'SECONDS' in df.columns and len(df) > 0:
                all_times.extend([df['SECONDS'].min(), df['SECONDS'].max()])
        return max(all_times) if all_times else 100.0


class MultiImportChannelControl(QWidget):
    """Widget for controlling channel visibility across multiple imports."""
    
    # Signal: (channel_name, import_index, visible)
    visibility_changed = pyqtSignal(str, int, bool)
    
    def __init__(self, channel_name: str, display_name: str, unit: str, 
                 import_colors: List[str], parent=None):
        super().__init__(parent)
        
        self.channel_name = channel_name
        self.display_name = display_name
        self.unit = unit
        self.checkboxes: List[QCheckBox] = []
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Channel name label
        name_label = QLabel(f"{display_name} ({unit})")
        name_label.setMinimumWidth(150)
        layout.addWidget(name_label)
        
        # One checkbox per import, with color indicator
        for i, color in enumerate(import_colors):
            # Color indicator
            color_label = QLabel()
            color_label.setFixedSize(12, 12)
            color_label.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
            layout.addWidget(color_label)
            
            # Checkbox
            cb = QCheckBox()
            cb.setChecked(True)
            cb.stateChanged.connect(lambda state, idx=i: self._on_checkbox_changed(idx, state))
            self.checkboxes.append(cb)
            layout.addWidget(cb)
        
        layout.addStretch()
    
    def _on_checkbox_changed(self, import_index: int, state: int):
        visible = state == Qt.CheckState.Checked.value
        self.visibility_changed.emit(self.channel_name, import_index, visible)
    
    def set_import_visible(self, import_index: int, visible: bool):
        if import_index < len(self.checkboxes):
            self.checkboxes[import_index].blockSignals(True)
            self.checkboxes[import_index].setChecked(visible)
            self.checkboxes[import_index].blockSignals(False)
    
    def is_any_selected(self) -> bool:
        """Return True if at least one import checkbox is checked."""
        return any(cb.isChecked() for cb in self.checkboxes)
    
    def sort_key(self, is_selected: bool) -> tuple:
        """Return sort key: (not selected, unit, display_name)."""
        # Selected items first (0), then unselected (1)
        # Then sort by unit, then by display name
        return (0 if is_selected else 1, self.unit.lower(), self.display_name.lower())


class ChannelControlWidget(QWidget):
    """Widget for controlling channel visibility (single import, legacy)."""
    
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


class ImportLegendWidget(QWidget):
    """Widget showing the legend mapping filenames to colors."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(2)
    
    def update_legend(self, imports: List[ImportData]):
        # Clear existing
        while self.layout.count() > 0:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add legend entries
        for imp in imports:
            entry = QWidget()
            entry_layout = QHBoxLayout(entry)
            entry_layout.setContentsMargins(0, 0, 0, 0)
            
            # Color indicator
            color_label = QLabel()
            color_label.setFixedSize(16, 16)
            color_label.setStyleSheet(f"background-color: {imp.color}; border-radius: 8px;")
            entry_layout.addWidget(color_label)
            
            # Filename
            name_label = QLabel(imp.filename)
            name_label.setToolTip(imp.file_path)
            entry_layout.addWidget(name_label, 1)
            
            self.layout.addWidget(entry)


class SynchronizeDialog(QDialog):
    """Dialog for adjusting time offsets between imports."""
    
    # Signal: (import_index, new_offset)
    offset_changed = pyqtSignal(int, float)
    
    def __init__(self, imports: List[ImportData], parent=None):
        super().__init__(parent)
        
        self.imports = imports
        self.setWindowTitle("Synchronize Imports")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Info label
        info = QLabel("Adjust time offsets for each import relative to the base (first import).")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Base import (cannot be shifted)
        base_group = QGroupBox(f"Base: {imports[0].filename}")
        base_layout = QHBoxLayout(base_group)
        base_label = QLabel("Offset: 0.0s (fixed)")
        base_label.setStyleSheet("color: #666;")
        base_layout.addWidget(base_label)
        layout.addWidget(base_group)
        
        # Offset controls for each additional import
        self.offset_spinboxes: List[QDoubleSpinBox] = []
        btn_style = "background-color: #616161; color: white; font-weight: bold; padding: 2px 6px;"
        
        for i, imp in enumerate(imports[1:], start=1):
            group = QGroupBox(f"{imp.filename}")
            group_layout = QVBoxLayout(group)
            
            # Color indicator
            color_label = QLabel()
            color_label.setFixedSize(20, 20)
            color_label.setStyleSheet(f"background-color: {imp.color}; border-radius: 10px;")
            
            # Current offset display
            offset_layout = QHBoxLayout()
            offset_layout.addWidget(QLabel("Offset:"))
            
            offset_spin = QDoubleSpinBox()
            offset_spin.setDecimals(2)
            offset_spin.setSuffix(" s")
            offset_spin.setRange(-999999, 999999)
            offset_spin.setValue(imp.time_offset)
            offset_spin.valueChanged.connect(lambda val, idx=i: self.offset_changed.emit(idx, val))
            self.offset_spinboxes.append(offset_spin)
            offset_layout.addWidget(offset_spin)
            offset_layout.addWidget(color_label)
            
            group_layout.addLayout(offset_layout)
            
            # Shift buttons - Row 1 (fine)
            btn_row1 = QHBoxLayout()
            for delta, label in [(-0.1, "◀ 0.1s"), (-0.5, "◀ 0.5s"), (-1, "◀ 1s"),
                                  (1, "1s ▶"), (0.5, "0.5s ▶"), (0.1, "0.1s ▶")]:
                btn = QPushButton(label)
                btn.setStyleSheet(btn_style)
                btn.clicked.connect(lambda checked, idx=i, d=delta: self._shift_offset(idx, d))
                btn_row1.addWidget(btn)
            group_layout.addLayout(btn_row1)
            
            # Shift buttons - Row 2 (coarse)
            btn_row2 = QHBoxLayout()
            for delta, label in [(-5, "◀ 5s"), (-15, "◀ 15s"), (-30, "◀ 30s"),
                                  (30, "30s ▶"), (15, "15s ▶"), (5, "5s ▶")]:
                btn = QPushButton(label)
                btn.setStyleSheet(btn_style)
                btn.clicked.connect(lambda checked, idx=i, d=delta: self._shift_offset(idx, d))
                btn_row2.addWidget(btn)
            group_layout.addLayout(btn_row2)
            
            # Shift buttons - Row 3 (very coarse)
            btn_row3 = QHBoxLayout()
            for delta, label in [(-60, "◀ 1min"), (-300, "◀ 5min"),
                                  (300, "5min ▶"), (60, "1min ▶")]:
                btn = QPushButton(label)
                btn.setStyleSheet(btn_style)
                btn.clicked.connect(lambda checked, idx=i, d=delta: self._shift_offset(idx, d))
                btn_row3.addWidget(btn)
            group_layout.addLayout(btn_row3)
            
            layout.addWidget(group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _shift_offset(self, import_index: int, delta: float):
        spinbox = self.offset_spinboxes[import_index - 1]  # -1 because base is not in list
        new_val = spinbox.value() + delta
        spinbox.setValue(new_val)


class SidebarWindow(QMainWindow):
    """Separate window for sidebar controls in split window mode."""
    
    closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OBD2 Controls")
        self.setMinimumSize(350, 600)
        
        # Central widget will be set when sidebar is moved here
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)
        self.layout.setContentsMargins(5, 5, 5, 5)
    
    def closeEvent(self, event):
        self.closed.emit()
        event.accept()


class HomeWidget(QWidget):
    """Home screen showing past imports."""
    
    # Signal emitted when user wants to open a file
    open_file_requested = pyqtSignal(str)
    open_new_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title = QLabel("OBD2 Data Visualization Tool")
        title.setStyleSheet("font-size: 24pt; font-weight: bold; color: #1976D2;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("High-performance native application for OBD2 data analysis")
        subtitle.setStyleSheet("font-size: 12pt; color: #666;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(30)
        
        # Open new file button
        btn_style = "background-color: #1976D2; color: white; font-weight: bold; font-size: 14pt; padding: 15px 30px; border-radius: 5px;"
        self.open_btn = QPushButton("📂 Open CSV File")
        self.open_btn.setStyleSheet(btn_style)
        self.open_btn.clicked.connect(self.open_new_requested.emit)
        layout.addWidget(self.open_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(30)
        
        # Past imports section
        past_label = QLabel("Past Imports")
        past_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(past_label)
        
        self.past_list = QListWidget()
        self.past_list.setMinimumHeight(200)
        self.past_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.past_list)
        
        # Clear button
        clear_btn = QPushButton("Clear History")
        clear_btn.setStyleSheet("background-color: #616161; color: white;")
        clear_btn.clicked.connect(self._clear_history)
        layout.addWidget(clear_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addStretch()
    
    def update_past_imports(self, recent_files: List[str]):
        self.past_list.clear()
        for path in recent_files:
            item = QListWidgetItem(f"📄 {Path(path).name}")
            item.setToolTip(path)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.past_list.addItem(item)
        
        if not recent_files:
            item = QListWidgetItem("No past imports")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.past_list.addItem(item)
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.open_file_requested.emit(path)
    
    def _clear_history(self):
        self.past_list.clear()
        # Signal to parent to clear settings
        self.parent().clear_recent_files()


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
        
        # Synchronize button - Row 5 (only enabled with 2+ imports)
        self.btn_synchronize = QPushButton("⏱ Synchronize Imports")
        self.btn_synchronize.setFixedHeight(32)
        self.btn_synchronize.setEnabled(False)  # Disabled until 2+ imports
        self.btn_synchronize.setStyleSheet("background-color: #BDBDBD; color: #757575;")  # Disabled style
        layout.addWidget(self.btn_synchronize)


class OBD2MainWindow(QMainWindow):
    """
    Main application window for the native OBD2 viewer.
    
    Provides a professional native Windows interface with:
    - File loading via drag-drop or file dialog
    - Multi-import support with synchronized visualization
    - Channel visibility controls per import
    - Time navigation with multiple granularities
    - High-performance hardware-accelerated charts
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("OBD2 Data Visualization Tool")
        self.setMinimumSize(1200, 800)
        
        # Settings
        self.settings = QSettings("OBD2Viewer", "NativeApp")
        
        # Multi-import data storage
        self.imports: List[ImportData] = []
        self.channel_controls: Dict[str, MultiImportChannelControl] = {}
        
        # Legacy single-import references (for compatibility)
        self.channels_data: Dict = {}
        self.units: Dict = {}
        self.display_names: Dict = {}
        
        # Recent files
        self.recent_files: List[str] = []
        self._load_recent_files()
        
        # Synchronize dialog reference
        self.sync_dialog: Optional[SynchronizeDialog] = None
        
        # Split window mode
        self.sidebar_window: Optional['SidebarWindow'] = None
        self.is_split_mode = False
        
        # Setup UI
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()
        
        # Restore window geometry
        self._restore_geometry()
        
        # Show home screen initially
        self._show_home()
        
        logger.info("OBD2 Native Viewer initialized")
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for home/visualization views
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Home screen (index 0)
        self.home_widget = HomeWidget(self)
        self.home_widget.open_file_requested.connect(self._load_file)
        self.home_widget.open_new_requested.connect(self._open_file_dialog)
        self.stacked_widget.addWidget(self.home_widget)
        
        # Visualization screen (index 1)
        self.viz_widget = QWidget()
        viz_layout = QHBoxLayout(self.viz_widget)
        viz_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        viz_layout.addWidget(self.splitter)
        
        # Left panel - Controls (stored as instance variable for split window mode)
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Import legend group
        legend_group = QGroupBox("Imports")
        legend_layout = QVBoxLayout(legend_group)
        self.import_legend = ImportLegendWidget()
        legend_layout.addWidget(self.import_legend)
        
        # Add Import button
        btn_style = "background-color: #1976D2; color: white; font-weight: bold;"
        self.btn_add_import = QPushButton("➕ Add Import")
        self.btn_add_import.setStyleSheet(btn_style)
        self.btn_add_import.clicked.connect(self._add_import_dialog)
        legend_layout.addWidget(self.btn_add_import)
        
        left_layout.addWidget(legend_group)
        
        # Channel controls group
        channel_group = QGroupBox("Channel Controls")
        channel_layout = QVBoxLayout(channel_group)
        
        # Show/Hide all buttons
        btn_layout = QHBoxLayout()
        self.btn_show_all = QPushButton("Show All")
        self.btn_hide_all = QPushButton("Hide All")
        btn_style_gray = "background-color: #616161; color: white; font-weight: bold;"
        self.btn_show_all.setStyleSheet(btn_style_gray)
        self.btn_hide_all.setStyleSheet(btn_style_gray)
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
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.chart_widget)
        
        # Set initial splitter sizes (30% controls, 70% charts)
        self.splitter.setSizes([300, 900])
        
        self.stacked_widget.addWidget(self.viz_widget)
    
    def _show_home(self):
        """Show the home screen."""
        self.home_widget.update_past_imports(self.recent_files)
        self.stacked_widget.setCurrentIndex(0)
    
    def _show_viz(self):
        """Show the visualization screen."""
        self.stacked_widget.setCurrentIndex(1)
    
    def clear_recent_files(self):
        """Clear recent files list."""
        self.recent_files = []
        self._save_recent_files()
        self.home_widget.update_past_imports(self.recent_files)
        self._update_recent_menu()
    
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
        
        view_menu.addSeparator()
        
        self.split_window_action = QAction("&Split Window Mode", self)
        self.split_window_action.setShortcut("Ctrl+W")
        self.split_window_action.setCheckable(True)
        self.split_window_action.triggered.connect(self._toggle_split_window)
        view_menu.addAction(self.split_window_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Setup the toolbar."""
        # Toolbar is kept minimal - main actions are in File menu and home screen
        pass
    
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
        
        # Synchronize button
        nav.btn_synchronize.clicked.connect(self._show_synchronize_dialog)
        
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
    
    def _load_file(self, file_path: str, is_additional: bool = False):
        """Load a single CSV file.
        
        Args:
            file_path: Path to the CSV file
            is_additional: If True, add as additional import; if False, replace all imports
        """
        # Check for duplicate import
        abs_path = str(Path(file_path).resolve())
        for imp in self.imports:
            if str(Path(imp.file_path).resolve()) == abs_path:
                QMessageBox.warning(self, "Duplicate Import", 
                    f"This file is already imported:\n{Path(file_path).name}")
                return
        
        try:
            self.statusbar.showMessage(f"Loading {file_path}...")
            QApplication.processEvents()
            
            loader = OBDDataLoader(str(Path(file_path).parent))
            channels_data, units = loader.load_single_file(file_path)
            
            # Normalize time to start at 0
            # Find the minimum time across all channels
            min_time = float('inf')
            for df in channels_data.values():
                if 'SECONDS' in df.columns and len(df) > 0:
                    channel_min = df['SECONDS'].min()
                    if channel_min < min_time:
                        min_time = channel_min
            
            # Subtract min_time from all SECONDS values
            if min_time != float('inf') and min_time != 0:
                for ch, df in channels_data.items():
                    if 'SECONDS' in df.columns:
                        channels_data[ch] = df.copy()
                        channels_data[ch]['SECONDS'] = df['SECONDS'] - min_time
            
            # Create display names
            display_names = {
                ch: ch.replace('_', ' ').title() 
                for ch in channels_data.keys()
            }
            
            # Assign color
            color_index = len(self.imports) if is_additional else 0
            color = IMPORT_COLORS[color_index % len(IMPORT_COLORS)]
            
            # Create ImportData
            import_data = ImportData(
                file_path=file_path,
                channels_data=channels_data,
                units=units,
                display_names=display_names,
                color=color
            )
            
            if is_additional:
                self.imports.append(import_data)
            else:
                # Clear existing imports and start fresh
                self.imports = [import_data]
            
            self._process_imports()
            self._add_to_recent(file_path)
            self._show_viz()
            
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")
            self.statusbar.showMessage("Error loading file")
    
    def _add_import_dialog(self):
        """Open dialog to add an additional import."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Add Import - Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self._load_file(file_path, is_additional=True)
    
    def _process_imports(self):
        """Process all imports and update the UI."""
        if not self.imports:
            return
        
        # Update legend
        self.import_legend.update_legend(self.imports)
        
        # Enable/disable synchronize button with proper styling
        has_multiple = len(self.imports) >= 2
        self.time_nav.btn_synchronize.setEnabled(has_multiple)
        if has_multiple:
            self.time_nav.btn_synchronize.setStyleSheet("background-color: #616161; color: white; font-weight: bold;")
        else:
            self.time_nav.btn_synchronize.setStyleSheet("background-color: #BDBDBD; color: #757575;")
        
        # Base import defines time range
        base = self.imports[0]
        
        # For legacy compatibility, set single-import references
        self.channels_data = base.channels_data
        self.units = base.units
        self.display_names = base.display_names
        
        # Load data into chart widget
        self.chart_widget.load_data(self.imports)
        
        # Update channel controls for multi-import
        self._update_channel_controls_multi()
        
        # Update time navigation inputs
        self._update_time_inputs()
        
        # Update zoom button states
        self._update_zoom_buttons()
        
        # Update status
        total_channels = len(set().union(*[set(imp.channels_data.keys()) for imp in self.imports]))
        total_points = sum(
            sum(len(df) for df in imp.channels_data.values()) 
            for imp in self.imports
        )
        duration = self.chart_widget.max_time - self.chart_widget.min_time
        
        if len(self.imports) == 1:
            self.status_label.setText(f"Loaded: {base.filename}")
        else:
            self.status_label.setText(f"Loaded: {len(self.imports)} imports")
        
        self.channel_label.setText(f"{total_channels} channels")
        self.time_label.setText(f"Duration: {duration:.1f}s")
        
        self.statusbar.showMessage(
            f"Loaded {total_channels} channels with {total_points:,} data points from {len(self.imports)} import(s)",
            5000
        )
        
        logger.info(f"Processed {len(self.imports)} imports with {total_channels} channels")
    
    def _update_channel_controls_multi(self):
        """Update channel controls for multi-import mode."""
        # Clear existing controls
        for control in self.channel_controls.values():
            self.channel_list_layout.removeWidget(control)
            control.deleteLater()
        self.channel_controls.clear()
        
        # Remove all items from layout
        while self.channel_list_layout.count() > 0:
            item = self.channel_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get all unique channels across all imports
        all_channels = set()
        for imp in self.imports:
            all_channels.update(imp.channels_data.keys())
        
        # Get colors for each import
        import_colors = [imp.color for imp in self.imports]
        
        # Create controls for each channel (don't add to layout yet)
        for channel in all_channels:
            # Get display name and unit from first import that has this channel
            display_name = channel
            unit = ''
            for imp in self.imports:
                if channel in imp.channels_data:
                    display_name = imp.display_names.get(channel, channel)
                    unit = imp.units.get(channel, '')
                    break
            
            control = MultiImportChannelControl(channel, display_name, unit, import_colors)
            control.visibility_changed.connect(self._on_channel_import_toggled)
            self.channel_controls[channel] = control
        
        # Sort and add to layout
        self._sort_channel_controls()
    
    def _sort_channel_controls(self):
        """Sort channel controls: selected at top, then by unit, then alphabetically."""
        # Remove all widgets from layout (but don't delete them)
        while self.channel_list_layout.count() > 0:
            item = self.channel_list_layout.takeAt(0)
            # Don't delete - we're just reordering
        
        # Sort controls
        sorted_controls = sorted(
            self.channel_controls.values(),
            key=lambda c: c.sort_key(c.is_any_selected())
        )
        
        # Re-add in sorted order
        for control in sorted_controls:
            self.channel_list_layout.addWidget(control)
        
        # Add stretch at end
        self.channel_list_layout.addStretch()
    
    def _on_channel_import_toggled(self, channel: str, import_index: int, visible: bool):
        """Handle channel visibility toggle for a specific import."""
        self.chart_widget.set_channel_import_visible(channel, import_index, visible)
        
        # Re-sort channel controls
        self._sort_channel_controls()
    
    def _show_synchronize_dialog(self):
        """Show the synchronize imports dialog."""
        if len(self.imports) < 2:
            return
        
        dialog = SynchronizeDialog(self.imports, self)
        dialog.offset_changed.connect(self._on_import_offset_changed)
        dialog.exec()
    
    def _on_import_offset_changed(self, import_index: int, new_offset: float):
        """Handle import time offset change."""
        if import_index < len(self.imports):
            self.imports[import_index].time_offset = new_offset
            self.chart_widget.update_import_offset(import_index, new_offset)
    
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
            if isinstance(control, MultiImportChannelControl):
                for i in range(len(control.checkboxes)):
                    control.set_import_visible(i, True)
            else:
                control.checkbox.setChecked(True)
        
        # Update chart
        if self.imports:
            for channel in self.chart_widget.plots:
                for i in range(len(self.imports)):
                    self.chart_widget.set_channel_import_visible(channel, i, True)
        else:
            self.chart_widget.show_all_channels()
    
    def _hide_all_channels(self):
        """Hide all channels."""
        for control in self.channel_controls.values():
            if isinstance(control, MultiImportChannelControl):
                for i in range(len(control.checkboxes)):
                    control.set_import_visible(i, False)
            else:
                control.checkbox.setChecked(False)
        
        # Update chart
        if self.imports:
            for channel in self.chart_widget.plots:
                for i in range(len(self.imports)):
                    self.chart_widget.set_channel_import_visible(channel, i, False)
        else:
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
    
    def _toggle_split_window(self, checked: bool):
        """Toggle split window mode - sidebar in separate window."""
        if checked:
            # Enter split mode - move sidebar to separate window
            self.is_split_mode = True
            
            # Create sidebar window
            self.sidebar_window = SidebarWindow()
            self.sidebar_window.closed.connect(self._on_sidebar_window_closed)
            
            # Remove left panel from splitter
            self.left_panel.setParent(None)
            
            # Add to sidebar window
            self.sidebar_window.layout.addWidget(self.left_panel)
            
            # Show sidebar window
            self.sidebar_window.show()
            
            # Position sidebar window to the left of main window
            main_geo = self.geometry()
            self.sidebar_window.move(main_geo.left() - 360, main_geo.top())
            self.sidebar_window.resize(350, main_geo.height())
            
        else:
            # Exit split mode - move sidebar back to main window
            self._restore_sidebar()
    
    def _on_sidebar_window_closed(self):
        """Handle sidebar window being closed."""
        self.split_window_action.setChecked(False)
        self._restore_sidebar()
    
    def _restore_sidebar(self):
        """Restore sidebar to main window."""
        if self.sidebar_window:
            # Remove from sidebar window
            self.left_panel.setParent(None)
            
            # Add back to splitter at position 0
            self.splitter.insertWidget(0, self.left_panel)
            self.splitter.setSizes([300, 900])
            
            # Close and cleanup sidebar window
            self.sidebar_window.close()
            self.sidebar_window = None
        
        self.is_split_mode = False
    
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
