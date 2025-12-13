#!/usr/bin/env python3
"""
Main Window for Native OBD2 Viewer.

Provides the main application window with file loading, channel controls,
time navigation, and the chart display area.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFileDialog, QMessageBox, QScrollArea, QFrame, QLabel,
    QPushButton, QGroupBox, QStatusBar, QApplication, QSizePolicy,
    QStackedWidget, QColorDialog, QCheckBox
)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QColor

from .chart_widget import OBD2ChartWidget
from .data_types import ImportData, FileLoaderThread, IMPORT_COLORS
from .widgets import (
    MultiImportChannelControl, ChannelControlWidget, ImportLegendWidget,
    SidebarWindow, HomeWidget, TimeNavigationWidget
)
from .dialogs import (
    LoadingDialog, SynchronizeDialog, MathChannelDialog, FilterDialog,
    CreatingChannelDialog, get_math_functions, get_statistical_functions
)
from .app_data import load_recent_files, save_recent_files, list_saved_views
from .view_manager import ViewManager

logger = logging.getLogger(__name__)



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
        
        # Math channel definitions: {name: {expression, inputs, unit}}
        self.math_channels: Dict[str, Dict] = {}
        
        # Filter definitions: ordered list of (name, definition_dict)
        # Order determines precedence: last in list = highest precedence (applied last)
        self.filter_order: List[str] = []  # Filter names in order
        self.filters: Dict[str, Dict] = {}  # {name: {expression, inputs, mode, buffer_seconds, enabled}}
        
        # Legacy single-import references (for compatibility)
        self.channels_data: Dict = {}
        self.units: Dict = {}
        self.display_names: Dict = {}
        
        # Recent files
        self.recent_files: List[str] = []
        self._load_recent_files()
        
        # Synchronize dialog reference
        self.sync_dialog: Optional[SynchronizeDialog] = None
        
        # Delayed sort timer (2 second delay after checkbox toggle)
        self.sort_timer = QTimer()
        self.sort_timer.setSingleShot(True)
        self.sort_timer.setInterval(2000)  # 2 seconds
        self.sort_timer.timeout.connect(self._sort_channel_controls)
        
        # Debounced zoom button update timer (1 second delay after mouse wheel zoom)
        self._zoom_button_timer = QTimer()
        self._zoom_button_timer.setSingleShot(True)
        self._zoom_button_timer.setInterval(1000)  # 1 second
        self._zoom_button_timer.timeout.connect(self._update_zoom_slider)
        
        # Split window mode
        self.sidebar_window: Optional['SidebarWindow'] = None
        self.is_split_mode = False
        
        # View manager for save/load
        self.view_manager = ViewManager(self)
        
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
        self.home_widget.open_files_requested.connect(self._load_multiple_files)
        self.home_widget.open_new_requested.connect(self._open_file_dialog)
        self.home_widget.clear_history_requested.connect(self.clear_recent_files)
        self.home_widget.open_view_requested.connect(self._load_saved_view)
        self.home_widget.delete_view_requested.connect(self._delete_saved_view)
        self.home_widget.delete_all_views_requested.connect(self._delete_all_saved_views)
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
        
        # Graph height buttons
        height_layout = QHBoxLayout()
        # Row 1: Taller, Shorter, Math Channel, Create Filter
        self.btn_taller = QPushButton("📈 Taller")
        self.btn_shorter = QPushButton("📉 Shorter")
        btn_style_blue = "background-color: #0288D1; color: white; font-weight: bold;"
        self.btn_taller.setStyleSheet(btn_style_blue)
        self.btn_shorter.setStyleSheet(btn_style_blue)
        self.btn_taller.clicked.connect(self._make_plots_taller)
        self.btn_shorter.clicked.connect(self._make_plots_shorter)
        height_layout.addWidget(self.btn_taller)
        height_layout.addWidget(self.btn_shorter)
        
        self.btn_create_math = QPushButton("➕ Math Channel")
        self.btn_create_math.setStyleSheet("background-color: #7B1FA2; color: white; font-weight: bold;")
        self.btn_create_math.clicked.connect(self._show_math_channel_dialog)
        height_layout.addWidget(self.btn_create_math)
        
        self.btn_create_filter = QPushButton("➕ Create Filter")
        self.btn_create_filter.setStyleSheet("background-color: #FF746C; color: white; font-weight: bold;")
        self.btn_create_filter.clicked.connect(self._show_filter_dialog)
        height_layout.addWidget(self.btn_create_filter)
        channel_layout.addLayout(height_layout)
        
        # Filters section (above channel list)
        self.filters_widget = QWidget()
        self.filters_layout = QVBoxLayout(self.filters_widget)
        self.filters_layout.setContentsMargins(0, 0, 0, 0)
        self.filters_layout.setSpacing(2)
        self.filters_label = QLabel("Filters")
        self.filters_label.setStyleSheet("font-weight: bold; color: #0288D1;")
        self.filters_layout.addWidget(self.filters_label)
        self.filters_widget.setVisible(False)  # Hidden until filters are created
        channel_layout.addWidget(self.filters_widget)
        
        # Show/Hide all buttons (under Filters section)
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
        self.home_widget.update_saved_views(list_saved_views())
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
        
        # Save/Load view actions
        save_view_action = QAction("&Save View...", self)
        save_view_action.setShortcut("Ctrl+S")
        save_view_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        save_view_action.triggered.connect(self._save_view_dialog)
        file_menu.addAction(save_view_action)
        self.addAction(save_view_action)  # Enable shortcut globally
        
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
        
        self.current_time_label = QLabel("")
        self.statusbar.addPermanentWidget(self.current_time_label)
        
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
        
        # Zoom slider
        nav.zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)
        
        nav.start_input.valueChanged.connect(self._on_time_input_changed)
        nav.end_input.valueChanged.connect(self._on_time_input_changed)
        
        # Import legend sync button
        self.import_legend.sync_requested.connect(self._show_synchronize_dialog)
        # Import legend color change
        self.import_legend.color_change_requested.connect(self._show_color_picker)
        
        # Chart time range changes
        self.chart_widget.time_range_changed.connect(self._on_chart_time_changed)
        
        # Crosshair position changes
        self.chart_widget.crosshair_moved.connect(self._on_crosshair_moved)
    
    def _make_plots_taller(self):
        """Make all plots taller by 5%."""
        self.chart_widget.make_plots_taller()
    
    def _make_plots_shorter(self):
        """Make all plots shorter by 5%."""
        self.chart_widget.make_plots_shorter()
    
    def _open_file_dialog(self):
        """Open file dialog to select one or more CSV files."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Open OBD2 CSV File(s)",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_paths:
            if len(file_paths) == 1:
                self._load_file(file_paths[0])
            else:
                self._load_multiple_files(file_paths)
    
    def _load_multiple_files(self, file_paths: List[str]):
        """Load multiple CSV files as separate imports.
        
        Files are loaded sequentially to avoid race conditions with the loading dialog.
        """
        if not file_paths:
            return
        
        # Queue files for sequential loading
        self._pending_files_queue = list(file_paths)
        self._load_next_queued_file()
    
    def _load_next_queued_file(self):
        """Load the next file from the queue."""
        if not hasattr(self, '_pending_files_queue') or not self._pending_files_queue:
            # Queue is empty - call view load callback if set
            if hasattr(self, '_view_load_callback') and self._view_load_callback:
                callback = self._view_load_callback
                self._view_load_callback = None
                callback()
            return
        
        file_path = self._pending_files_queue.pop(0)
        is_additional = len(self.imports) > 0  # Additional if we already have imports
        self._load_file(file_path, is_additional=is_additional)
    
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
        
        # Show loading dialog
        self._loading_dialog = LoadingDialog(f"Loading {Path(file_path).name}...", self)
        self._loading_dialog.show()
        
        self.statusbar.showMessage(f"Loading {file_path}...")
        
        # Store state for the callback
        self._pending_file_path = file_path
        self._pending_is_additional = is_additional
        
        # Start background thread for file loading
        self._loader_thread = FileLoaderThread(file_path, self)
        self._loader_thread.finished.connect(self._on_file_loaded)
        self._loader_thread.error.connect(self._on_file_load_error)
        self._loader_thread.start()
    
    def _on_file_loaded(self, channels_data: dict, units: dict):
        """Handle successful file load from background thread."""
        file_path = self._pending_file_path
        is_additional = self._pending_is_additional
        
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
            # Preserve visibility when adding additional imports
            self._process_imports(preserve_visibility=True)
        else:
            # Clear existing imports and start fresh
            self.imports = [import_data]
            self._process_imports(preserve_visibility=False)
        
        self._add_to_recent(file_path)
        self._show_viz()
        
        if self._loading_dialog:
            self._loading_dialog.close()
            self._loading_dialog = None
        self._loader_thread = None
        
        # Load next file from queue if any
        self._load_next_queued_file()
    
    def _on_file_load_error(self, error_msg: str):
        """Handle file load error from background thread."""
        if self._loading_dialog:
            self._loading_dialog.close()
            self._loading_dialog = None
        self._loader_thread = None
        
        QMessageBox.critical(self, "Error", f"Failed to load file:\n{error_msg}")
        self.statusbar.showMessage("Error loading file")
        
        # Continue loading next file from queue even if this one failed
        self._load_next_queued_file()
    
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
    
    def _process_imports(self, preserve_visibility: bool = False):
        """Process all imports and update the UI."""
        if not self.imports:
            return
        
        # Compute math channels for any imports that don't have them yet
        self._apply_math_channels_to_imports()
        
        # Update legend (includes per-import sync buttons)
        self.import_legend.update_legend(self.imports)
        
        # Base import defines time range
        base = self.imports[0]
        
        # For legacy compatibility, set single-import references
        self.channels_data = base.channels_data
        self.units = base.units
        self.display_names = base.display_names
        
        # Load data into chart widget
        self.chart_widget.load_data(self.imports)
        
        # Update channel controls for multi-import
        self._update_channel_controls_multi(preserve_visibility=preserve_visibility)
        
        # Update time navigation inputs
        self._update_time_inputs()
        
        # Update zoom slider position
        self._update_zoom_slider()
        
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
    
    def _update_channel_controls_multi(self, preserve_visibility: bool = False, 
                                        show_channels: Optional[set] = None):
        """Update channel controls for multi-import mode.
        
        Args:
            preserve_visibility: If True, restore visibility from existing controls
            show_channels: Set of channel names that should be shown (overrides preserve_visibility for these)
        """
        show_channels = show_channels or set()
        
        # Save current visibility state if preserving
        saved_visibility = {}
        saved_chart_visibility = {}
        if preserve_visibility:
            for channel, control in self.channel_controls.items():
                saved_visibility[channel] = list(control.import_visible)
                saved_chart_visibility[channel] = control.is_chart_visible()
        
        # Clear existing controls
        for control in self.channel_controls.values():
            self.channel_list_layout.removeWidget(control)
            control.deleteLater()
        self.channel_controls.clear()
        
        # Remove all items from layout (including section headers)
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
            
            is_math = channel in self.math_channels
            control = MultiImportChannelControl(channel, display_name, unit, import_colors, is_math)
            control.visibility_changed.connect(self._on_channel_import_toggled)
            control.chart_visibility_changed.connect(self._on_chart_visibility_toggled)
            control.edit_requested.connect(self._edit_math_channel)
            self.channel_controls[channel] = control
            
            # Determine visibility for this channel
            if channel in show_channels:
                # Explicitly show this channel (e.g., newly created math channel)
                control.set_chart_visible(True)
                self.chart_widget.set_chart_visible(channel, True)
                for i in range(len(import_colors)):
                    control.set_import_visible(i, True)
                    self.chart_widget.set_channel_import_visible(channel, i, True)
            elif preserve_visibility and channel in saved_visibility:
                # Restore chart visibility
                chart_vis = saved_chart_visibility.get(channel, True)
                control.set_chart_visible(chart_vis)
                self.chart_widget.set_chart_visible(channel, chart_vis)
                
                # Restore import visibility
                saved = saved_visibility[channel]
                for i in range(len(import_colors)):
                    if i < len(saved):
                        visible = saved[i]
                    else:
                        visible = saved[0] if saved else True
                    control.set_import_visible(i, visible)
                    self.chart_widget.set_channel_import_visible(channel, i, visible)
            elif preserve_visibility and channel not in saved_visibility:
                # New channel while preserving - default to hidden
                control.set_chart_visible(False)
                self.chart_widget.set_chart_visible(channel, False)
                for i in range(len(import_colors)):
                    control.set_import_visible(i, False)
                    self.chart_widget.set_channel_import_visible(channel, i, False)
            elif not preserve_visibility:
                # Fresh load - default to hidden for math channels only
                if is_math:
                    control.set_chart_visible(False)
                    self.chart_widget.set_chart_visible(channel, False)
                    for i in range(len(import_colors)):
                        control.set_import_visible(i, False)
                        self.chart_widget.set_channel_import_visible(channel, i, False)
        
        # Sort and add to layout
        self._sort_channel_controls()
    
    def _sort_channel_controls(self):
        """Sort channel controls with section headers: Shown/Hidden, then by unit."""
        # Remove all widgets from layout (but don't delete controls)
        while self.channel_list_layout.count() > 0:
            item = self.channel_list_layout.takeAt(0)
            widget = item.widget()
            # Only delete section headers (QLabel/QFrame), not controls
            if widget and widget not in self.channel_controls.values():
                widget.deleteLater()
        
        # Separate shown and hidden controls
        shown_controls = []
        hidden_controls = []
        
        for control in self.channel_controls.values():
            if control.is_any_selected():
                shown_controls.append(control)
            else:
                hidden_controls.append(control)
        
        # Sort each group by unit, then by name
        shown_controls.sort(key=lambda c: (c.unit.lower(), c.display_name.lower()))
        hidden_controls.sort(key=lambda c: (c.unit.lower(), c.display_name.lower()))
        
        def add_section_header(text: str, color: str = "#1976D2"):
            """Add a section header label."""
            header = QLabel(f"<b>{text}</b>")
            header.setStyleSheet(f"color: {color}; font-size: 11pt; padding: 5px 0px 2px 5px; background-color: #f0f0f0;")
            self.channel_list_layout.addWidget(header)
        
        def add_unit_header(unit: str):
            """Add a unit subheader."""
            header = QLabel(f"  {unit}" if unit else "  (no unit)")
            header.setStyleSheet("color: #666; font-size: 9pt; padding: 2px 0px 0px 10px; font-style: italic;")
            self.channel_list_layout.addWidget(header)
        
        # Add Shown section
        if shown_controls:
            add_section_header(f"▼ Shown ({len(shown_controls)})", "#388E3C")
            
            current_unit = None
            for control in shown_controls:
                if control.unit != current_unit:
                    current_unit = control.unit
                    add_unit_header(current_unit)
                self.channel_list_layout.addWidget(control)
        
        # Add Hidden section
        if hidden_controls:
            add_section_header(f"▼ Hidden ({len(hidden_controls)})", "#757575")
            
            current_unit = None
            for control in hidden_controls:
                if control.unit != current_unit:
                    current_unit = control.unit
                    add_unit_header(current_unit)
                self.channel_list_layout.addWidget(control)
        
        # Add stretch at end
        self.channel_list_layout.addStretch()
    
    def _on_channel_import_toggled(self, channel: str, import_index: int, visible: bool):
        """Handle channel visibility toggle for a specific import."""
        self.chart_widget.set_channel_import_visible(channel, import_index, visible)
        
        # Re-sort channel controls after 2 second delay (restart timer if already running)
        self.sort_timer.start()
    
    def _on_chart_visibility_toggled(self, channel: str, visible: bool):
        """Handle chart visibility toggle (show/hide entire chart)."""
        self.chart_widget.set_chart_visible(channel, visible)
        
        # Re-sort channel controls after 2 second delay
        self.sort_timer.start()
    
    def _show_synchronize_dialog(self, import_index: int):
        """Show the synchronize dialog for a specific import."""
        if import_index >= len(self.imports):
            return
        
        dialog = SynchronizeDialog(self.imports[import_index], import_index, self)
        dialog.offset_changed.connect(self._on_import_offset_changed)
        dialog.exec()
        # Reapply filters after dialog closes (offsets may have changed)
        if self.filters:
            self._apply_filters()
    
    def _on_import_offset_changed(self, import_index: int, new_offset: float):
        """Handle import time offset change."""
        if import_index < len(self.imports):
            self.imports[import_index].time_offset = new_offset
            self.chart_widget.update_import_offset(import_index, new_offset)
            # Update the offset display in the legend
            self.import_legend.update_offset(import_index, new_offset)
    
    def _show_color_picker(self, import_index: int):
        """Show color picker dialog for an import."""
        if import_index >= len(self.imports):
            return
        
        imp = self.imports[import_index]
        current_color = QColor(imp.color)
        
        color = QColorDialog.getColor(current_color, self, f"Choose Color for {imp.filename}")
        
        if color.isValid():
            new_color = color.name()
            imp.color = new_color
            # Update chart widget
            self.chart_widget.update_import_color(import_index, new_color)
            # Update legend
            self.import_legend.update_legend(self.imports)
            # Update channel controls (they show import colors)
            self._update_channel_controls_multi(preserve_visibility=True)
    
    def _show_math_channel_dialog(self, edit_channel: str = None):
        """Show dialog to create or edit a math channel."""
        if not self.imports:
            QMessageBox.warning(self, "No Data", "Please load a CSV file first.")
            return
        
        # Get all available channels from all imports (exclude math channels for input selection)
        all_channels = set()
        all_units = set()
        channel_units = {}  # Map channel name to unit
        for imp in self.imports:
            for ch in imp.channels_data.keys():
                if ch not in self.math_channels:  # Don't allow math channels as inputs
                    all_channels.add(ch)
                    if ch not in channel_units and ch in imp.units:
                        channel_units[ch] = imp.units[ch]
            all_units.update(imp.units.values())
        
        # Get edit data if editing
        edit_data = None
        if edit_channel and edit_channel in self.math_channels:
            edit_data = {'name': edit_channel, **self.math_channels[edit_channel]}
        
        dialog = MathChannelDialog(list(all_channels), list(all_units), channel_units, edit_data, self)
        dialog.channel_created.connect(lambda n, e, inputs_json, u: self._create_math_channel_with_spinner(n, e, inputs_json, u, edit_channel))
        dialog.exec()
    
    def _edit_math_channel(self, channel_name: str):
        """Open edit dialog for a math channel."""
        self._show_math_channel_dialog(edit_channel=channel_name)
    
    def _apply_math_channels_to_imports(self):
        """Apply all defined math channels to imports that don't have them yet."""
        import numpy as np
        import pandas as pd
        
        if not self.math_channels:
            return
        
        INPUT_LABELS = ['A', 'B', 'C', 'D', 'E']
        
        for name, definition in self.math_channels.items():
            expression = definition['expression']
            unit = definition['unit']
            
            # Handle both old format (input_a, input_b) and new format (inputs dict)
            if 'inputs' in definition:
                inputs = definition['inputs']
            else:
                # Legacy format
                inputs = {
                    'A': definition.get('input_a', ''),
                    'B': definition.get('input_b', ''),
                    'C': '', 'D': '', 'E': ''
                }
            
            for imp in self.imports:
                # Skip if this import already has this math channel
                if name in imp.channels_data:
                    continue
                
                # Skip if input A is not available
                input_a = inputs.get('A', '')
                if not input_a or input_a not in imp.channels_data:
                    logger.debug(f"Skipping math channel '{name}' for {imp.filename}: input A '{input_a}' not found")
                    continue
                
                # Get time points from input A
                df_a = imp.channels_data[input_a]
                times = df_a['SECONDS'].values
                
                # Build aligned values for all inputs
                aligned_values = {}
                for label in INPUT_LABELS:
                    input_ch = inputs.get(label, '')
                    if input_ch and input_ch in imp.channels_data:
                        df = imp.channels_data[input_ch]
                        times_ch = df['SECONDS'].values
                        values_raw = df['VALUE'].values
                        
                        # Align to A's time points
                        aligned = np.zeros(len(times))
                        for i, t in enumerate(times):
                            idx = np.searchsorted(times_ch, t)
                            if idx == 0:
                                aligned[i] = values_raw[0]
                            elif idx >= len(times_ch):
                                aligned[i] = values_raw[-1]
                            else:
                                diff_before = t - times_ch[idx - 1]
                                diff_after = times_ch[idx] - t
                                if diff_after <= diff_before:
                                    aligned[i] = values_raw[idx]
                                else:
                                    aligned[i] = values_raw[idx - 1]
                        aligned_values[label] = aligned
                    else:
                        aligned_values[label] = np.zeros(len(times))
                
                try:
                    # Build evaluation context with functions
                    context = {}
                    context.update(get_math_functions())
                    context.update(get_statistical_functions(times))
                    
                    # Add if_else for conditionals
                    def if_else(condition, true_val, false_val):
                        return np.where(condition, true_val, false_val)
                    context['if_else'] = if_else
                    
                    # Add aligned values
                    context.update(aligned_values)
                    
                    # Evaluate expression (vectorized)
                    result_values = eval(expression, {"__builtins__": {}}, context)
                    
                    # Ensure result is array
                    if isinstance(result_values, (int, float)):
                        result_values = np.full(len(times), result_values)
                    
                    new_df = pd.DataFrame({
                        'SECONDS': times,
                        'VALUE': result_values
                    })
                    
                    imp.channels_data[name] = new_df
                    imp.units[name] = unit
                    imp.display_names[name] = name.replace('_', ' ').title()
                    
                    logger.info(f"Applied math channel '{name}' to {imp.filename}")
                    
                except Exception as e:
                    logger.error(f"Error applying math channel '{name}' to {imp.filename}: {e}")
    
    def _create_math_channel(self, name: str, expression: str, inputs_json: str, unit: str, 
                             replacing: str = None):
        """Create a math channel from the given expression.
        
        Args:
            name: Channel name
            expression: Math expression using A, B, C, D, E variables
            inputs_json: JSON string mapping input labels to channel names
            unit: Output unit
            replacing: Name of channel being replaced (for edit mode)
        """
        import numpy as np
        import pandas as pd
        
        # Parse inputs JSON
        inputs = json.loads(inputs_json)
        
        INPUT_LABELS = ['A', 'B', 'C', 'D', 'E']
        used_inputs = {k: v for k, v in inputs.items() if v}
        
        logger.info(f"Creating math channel: {name} = {expression} (inputs={used_inputs})")
        
        # If replacing an existing channel, remove it first
        if replacing and replacing != name:
            for imp in self.imports:
                if replacing in imp.channels_data:
                    del imp.channels_data[replacing]
                    if replacing in imp.units:
                        del imp.units[replacing]
                    if replacing in imp.display_names:
                        del imp.display_names[replacing]
            if replacing in self.math_channels:
                del self.math_channels[replacing]
        
        # Store the math channel definition (new format)
        self.math_channels[name] = {
            'expression': expression,
            'inputs': inputs,
            'unit': unit
        }
        
        input_a = inputs.get('A', '')
        
        # Process for each import
        for imp in self.imports:
            if not input_a or input_a not in imp.channels_data:
                logger.warning(f"Input A '{input_a}' not found in {imp.filename}")
                continue
            
            # Get time points from input A
            df_a = imp.channels_data[input_a]
            times = df_a['SECONDS'].values
            
            # Build aligned values for all inputs
            aligned_values = {}
            for label in INPUT_LABELS:
                input_ch = inputs.get(label, '')
                if input_ch and input_ch in imp.channels_data:
                    df = imp.channels_data[input_ch]
                    times_ch = df['SECONDS'].values
                    values_raw = df['VALUE'].values
                    
                    # Align to A's time points (nearest neighbor)
                    aligned = np.zeros(len(times))
                    for i, t in enumerate(times):
                        idx = np.searchsorted(times_ch, t)
                        if idx == 0:
                            aligned[i] = values_raw[0]
                        elif idx >= len(times_ch):
                            aligned[i] = values_raw[-1]
                        else:
                            diff_before = t - times_ch[idx - 1]
                            diff_after = times_ch[idx] - t
                            if diff_after <= diff_before:
                                aligned[i] = values_raw[idx]
                            else:
                                aligned[i] = values_raw[idx - 1]
                    aligned_values[label] = aligned
                else:
                    aligned_values[label] = np.zeros(len(times))
            
            # Evaluate expression (vectorized)
            try:
                # Build evaluation context with functions
                context = {}
                context.update(get_math_functions())
                context.update(get_statistical_functions(times))
                
                # Add if_else for conditionals
                def if_else(condition, true_val, false_val):
                    return np.where(condition, true_val, false_val)
                context['if_else'] = if_else
                
                # Add aligned values
                context.update(aligned_values)
                
                # Evaluate expression
                result_values = eval(expression, {"__builtins__": {}}, context)
                
                # Ensure result is array
                if isinstance(result_values, (int, float)):
                    result_values = np.full(len(times), result_values)
                
                # Create DataFrame for the new channel
                new_df = pd.DataFrame({
                    'SECONDS': times,
                    'VALUE': result_values
                })
                
                # Add to import's channels_data
                imp.channels_data[name] = new_df
                imp.units[name] = unit
                imp.display_names[name] = name.replace('_', ' ').title()
                
                logger.info(f"Created math channel '{name}' for {imp.filename} with {len(new_df)} points")
                
            except Exception as e:
                logger.error(f"Error evaluating expression for {imp.filename}: {e}")
                QMessageBox.warning(self, "Error", f"Failed to create math channel for {imp.filename}:\n{e}")
                return
        
        # Add channel to chart widget
        display_name = name.replace('_', ' ').title()
        self.chart_widget.add_channel(name, display_name, unit)
        
        # Refresh the UI - preserve visibility, but show the new math channel
        self._update_channel_controls_multi(preserve_visibility=True, show_channels={name})
        self.statusbar.showMessage(f"{'Updated' if replacing else 'Created'} math channel: {name}", 5000)
        
        # Reapply filters to include the new channel
        if self.filters:
            self._apply_filters()
    
    def _create_math_channel_with_spinner(self, name: str, expression: str, inputs_json: str, 
                                           unit: str, replacing: str = None):
        """Show spinner dialog while creating a math channel."""
        # Show spinner dialog
        spinner = CreatingChannelDialog(f"Creating {name}...", self)
        spinner.show()
        QApplication.processEvents()  # Force UI update
        
        try:
            self._create_math_channel(name, expression, inputs_json, unit, replacing)
        finally:
            spinner.close()
    
    def _show_filter_dialog(self, edit_filter: str = None):
        """Show dialog to create or edit a filter."""
        if not self.imports:
            QMessageBox.warning(self, "No Data", "Please load a CSV file first.")
            return
        
        # Get all available channels (including math channels for filters)
        all_channels = set()
        channel_units = {}
        for imp in self.imports:
            for ch in imp.channels_data.keys():
                all_channels.add(ch)
                if ch not in channel_units and ch in imp.units:
                    channel_units[ch] = imp.units[ch]
        
        # Get edit data if editing
        edit_data = None
        if edit_filter and edit_filter in self.filters:
            edit_data = {'name': edit_filter, **self.filters[edit_filter]}
        
        dialog = FilterDialog(list(all_channels), channel_units, edit_data, self)
        dialog.filter_created.connect(lambda n, e, inputs_json, m, b: self._create_filter_with_spinner(n, e, inputs_json, m, b, edit_filter))
        dialog.exec()
    
    def _edit_filter(self, filter_name: str):
        """Open edit dialog for a filter."""
        self._show_filter_dialog(edit_filter=filter_name)
    
    def _create_filter(self, name: str, expression: str, inputs_json: str, mode: str, 
                       buffer_seconds: float, replacing: str = None):
        """Create or update a filter.
        
        Args:
            name: Filter name
            expression: Boolean expression
            inputs_json: JSON string mapping input labels to channel names
            mode: 'show' or 'hide'
            buffer_seconds: Time buffer in seconds
            replacing: Name of filter being replaced (for edit mode)
        """
        inputs = json.loads(inputs_json)
        used_inputs = {k: v for k, v in inputs.items() if v}
        
        logger.info(f"Creating filter: {name} = {expression} (mode={mode}, buffer={buffer_seconds}s, inputs={used_inputs})")
        
        # If replacing an existing filter, remove it first (keep position in order)
        old_position = -1
        if replacing and replacing in self.filters:
            if replacing in self.filter_order:
                old_position = self.filter_order.index(replacing)
                self.filter_order.remove(replacing)
            if replacing != name:
                del self.filters[replacing]
                self._remove_filter_control(replacing)
        
        # Store the filter definition
        self.filters[name] = {
            'expression': expression,
            'inputs': inputs,
            'mode': mode,
            'buffer_seconds': buffer_seconds,
            'enabled': True
        }
        
        # Add to order list (preserve position if editing, else add at end)
        if name not in self.filter_order:
            if old_position >= 0:
                self.filter_order.insert(old_position, name)
            else:
                self.filter_order.append(name)
        
        # Update filter controls UI
        self._update_filter_controls()
        
        # Apply filters to chart
        self._apply_filters()
        
        self.statusbar.showMessage(f"{'Updated' if replacing else 'Created'} filter: {name}", 5000)
    
    def _create_filter_with_spinner(self, name: str, expression: str, inputs_json: str, 
                                     mode: str, buffer_seconds: float, replacing: str = None):
        """Show spinner dialog while creating a filter."""
        # Show spinner dialog
        spinner = CreatingChannelDialog(f"Creating {name}...", self)
        spinner.show()
        QApplication.processEvents()  # Force UI update
        
        try:
            self._create_filter(name, expression, inputs_json, mode, buffer_seconds, replacing)
        finally:
            spinner.close()
    
    def _remove_filter_control(self, filter_name: str):
        """Remove a filter control widget from the UI."""
        # Find and remove the filter control widget
        for i in range(self.filters_layout.count()):
            item = self.filters_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'filter_name') and widget.filter_name == filter_name:
                    widget.deleteLater()
                    break
    
    def _update_filter_controls(self):
        """Update the filter controls in the sidebar."""
        # Clear existing filter controls (except the label)
        while self.filters_layout.count() > 1:
            item = self.filters_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        
        # Add controls for each filter in order (order determines precedence)
        for name in self.filter_order:
            if name in self.filters:
                definition = self.filters[name]
                control = self._create_filter_control(name, definition)
                self.filters_layout.addWidget(control)
        
        # Show/hide filters section based on whether we have filters
        self.filters_widget.setVisible(len(self.filters) > 0)
    
    def _create_filter_control(self, name: str, definition: Dict) -> QWidget:
        """Create a control widget for a filter."""
        widget = QWidget()
        widget.filter_name = name
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 2, 0, 2)
        
        # Up/Down buttons for reordering (precedence)
        up_btn = QPushButton("▲")
        up_btn.setFixedSize(20, 20)
        up_btn.setToolTip("Move up (lower precedence)")
        up_btn.clicked.connect(lambda _, n=name: self._move_filter(n, -1))
        layout.addWidget(up_btn)
        
        down_btn = QPushButton("▼")
        down_btn.setFixedSize(20, 20)
        down_btn.setToolTip("Move down (higher precedence)")
        down_btn.clicked.connect(lambda _, n=name: self._move_filter(n, 1))
        layout.addWidget(down_btn)
        
        # Checkbox to enable/disable (no text, just the checkbox)
        checkbox = QCheckBox()
        checkbox.setChecked(definition.get('enabled', True))
        checkbox.setToolTip(f"Expression: {definition['expression']}\nMode: {definition['mode']}\nBuffer: ±{definition['buffer_seconds']}s")
        checkbox.toggled.connect(lambda checked, n=name: self._toggle_filter(n, checked))
        layout.addWidget(checkbox)
        
        # Mode indicator (to the left of filter name)
        mode = definition.get('mode', 'show')
        mode_label = QLabel("👁" if mode == 'show' else "🚫")
        mode_label.setToolTip(f"Mode: {mode}")
        layout.addWidget(mode_label)
        
        # Filter name label
        name_label = QLabel(name)
        name_label.setToolTip(f"Expression: {definition['expression']}\nMode: {definition['mode']}\nBuffer: ±{definition['buffer_seconds']}s")
        layout.addWidget(name_label, 1)
        
        # Edit button
        edit_btn = QPushButton("✏")
        edit_btn.setFixedSize(24, 24)
        edit_btn.setToolTip("Edit filter")
        edit_btn.clicked.connect(lambda _, n=name: self._edit_filter(n))
        layout.addWidget(edit_btn)
        
        # Delete button
        delete_btn = QPushButton("🗑")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setToolTip("Delete filter")
        delete_btn.clicked.connect(lambda _, n=name: self._delete_filter(n))
        layout.addWidget(delete_btn)
        
        return widget
    
    def _move_filter(self, filter_name: str, direction: int):
        """Move a filter up or down in the order list.
        
        Args:
            filter_name: Name of the filter to move
            direction: -1 for up (lower precedence), +1 for down (higher precedence)
        """
        if filter_name not in self.filter_order:
            return
        
        idx = self.filter_order.index(filter_name)
        new_idx = idx + direction
        
        # Check bounds
        if new_idx < 0 or new_idx >= len(self.filter_order):
            return
        
        # Swap positions
        self.filter_order[idx], self.filter_order[new_idx] = self.filter_order[new_idx], self.filter_order[idx]
        
        # Update UI and reapply filters
        self._update_filter_controls()
        self._apply_filters()
    
    def _toggle_filter(self, filter_name: str, enabled: bool):
        """Toggle a filter on/off."""
        if filter_name in self.filters:
            self.filters[filter_name]['enabled'] = enabled
            self._apply_filters()
    
    def _delete_filter(self, filter_name: str):
        """Delete a filter."""
        if filter_name in self.filters:
            del self.filters[filter_name]
            if filter_name in self.filter_order:
                self.filter_order.remove(filter_name)
            self._update_filter_controls()
            self._apply_filters()
            self.statusbar.showMessage(f"Deleted filter: {filter_name}", 3000)
    
    def _apply_filters(self):
        """Apply all enabled filters to the chart widget with precedence.
        
        Filters are processed in order (filter_order list). Each filter modifies
        the visibility mask based on its mode:
        - Show: adds matching intervals to visible set
        - Hide: removes matching intervals from visible set
        
        Top filter = highest precedence (processed last, wins conflicts).
        
        IMPORTANT: Filter matches are unified across all imports. If ANY import
        matches a filter at time t, ALL imports are considered to match at that
        time (adjusted for their time offsets).
        """
        import numpy as np
        
        if not self.imports:
            return
        
        # Collect enabled filters in order
        active_filters = []
        for name in self.filter_order:
            if name in self.filters and self.filters[name].get('enabled', True):
                active_filters.append((name, self.filters[name]))
        
        if not active_filters:
            # No active filters - show all data
            self.chart_widget.set_filter_mask(None)
            return
        
        INPUT_LABELS = ['A', 'B', 'C', 'D', 'E']
        
        # PHASE 1: Collect matching intervals from ALL imports for each filter
        # Store as {filter_name: [(start, end), ...]} in absolute time (import 0's time frame)
        filter_unified_intervals = {}  # {filter_name: merged_intervals}
        
        for filter_name, definition in active_filters:
            expression = definition['expression']
            inputs = definition['inputs']
            buffer_seconds = definition['buffer_seconds']
            
            all_matching_times = []  # Collect from all imports in absolute time
            
            for imp_idx, imp in enumerate(self.imports):
                input_a = inputs.get('A', '')
                if not input_a or input_a not in imp.channels_data:
                    continue
                
                # Get time points from input A
                df_a = imp.channels_data[input_a]
                times = df_a['SECONDS'].values
                
                # Build aligned values for all inputs (vectorized)
                aligned_values = {}
                for label in INPUT_LABELS:
                    input_ch = inputs.get(label, '')
                    if input_ch and input_ch in imp.channels_data:
                        df = imp.channels_data[input_ch]
                        times_ch = df['SECONDS'].values
                        values_raw = df['VALUE'].values
                        
                        # Vectorized alignment using searchsorted
                        indices = np.searchsorted(times_ch, times)
                        indices = np.clip(indices, 1, len(times_ch) - 1)
                        
                        # Choose nearest neighbor
                        diff_before = times - times_ch[indices - 1]
                        diff_after = times_ch[indices] - times
                        use_after = diff_after <= diff_before
                        
                        aligned = np.where(use_after, values_raw[indices], values_raw[indices - 1])
                        aligned = np.where(indices == 0, values_raw[0], aligned)
                        aligned = np.where(indices >= len(times_ch), values_raw[-1], aligned)
                        
                        aligned_values[label] = aligned
                    else:
                        aligned_values[label] = np.zeros(len(times))
                
                try:
                    # Build evaluation context
                    context = {}
                    context.update(get_math_functions())
                    context.update(get_statistical_functions(times))
                    
                    def if_else(condition, true_val, false_val):
                        return np.where(condition, true_val, false_val)
                    context['if_else'] = if_else
                    context.update(aligned_values)
                    
                    # Evaluate expression
                    result = eval(expression, {"__builtins__": {}}, context)
                    
                    # Convert to boolean mask
                    if isinstance(result, np.ndarray):
                        bool_mask = result.astype(bool)
                    else:
                        bool_mask = np.full(len(times), bool(result))
                    
                    # Get matching time points and convert to absolute (display) time
                    # Absolute time = local time + offset (what's shown on chart)
                    matching_local_times = times[bool_mask]
                    matching_absolute_times = matching_local_times + imp.time_offset
                    
                    all_matching_times.extend(matching_absolute_times)
                    
                except Exception as e:
                    logger.error(f"Error evaluating filter '{filter_name}' for import {imp_idx}: {e}")
                    continue
            
            # Convert all matching times to intervals and merge
            if all_matching_times:
                intervals = [(t - buffer_seconds, t + buffer_seconds) for t in all_matching_times]
                intervals.sort(key=lambda x: x[0])
                merged = [intervals[0]]
                for start, end in intervals[1:]:
                    if start <= merged[-1][1]:
                        merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                    else:
                        merged.append((start, end))
                filter_unified_intervals[filter_name] = merged
                logger.info(f"Filter '{filter_name}': {len(all_matching_times)} total matches across all imports, {len(merged)} merged intervals")
            else:
                filter_unified_intervals[filter_name] = []
                logger.info(f"Filter '{filter_name}': 0 matches across all imports")
        
        # PHASE 2: Apply unified intervals to each import
        filter_masks = {}  # {import_index: {channel: mask_array}}
        filter_intervals = {}  # {import_index: [(start, end), ...]} for line breaks
        
        # Check if any show filter exists (determines initial state)
        has_any_show = any(defn['mode'] == 'show' for _, defn in active_filters)
        
        for imp_idx, imp in enumerate(self.imports):
            # Initialize visibility mask for each channel
            channel_masks = {}
            for ch_name, ch_df in imp.channels_data.items():
                if has_any_show:
                    # Start with nothing visible (shows add)
                    channel_masks[ch_name] = np.zeros(len(ch_df), dtype=bool)
                else:
                    # Start with all visible (hides remove)
                    channel_masks[ch_name] = np.ones(len(ch_df), dtype=bool)
            
            # Process filters BOTTOM to TOP (reverse order) so top = highest precedence
            for filter_name, definition in reversed(active_filters):
                mode = definition['mode']
                unified_intervals = filter_unified_intervals.get(filter_name, [])
                
                if not unified_intervals:
                    continue
                
                # Convert unified intervals (absolute/display time) to this import's local time
                # Local time = absolute time - offset (stored data times)
                local_intervals = [(start - imp.time_offset, end - imp.time_offset) 
                                   for start, end in unified_intervals]
                
                interval_starts = np.array([iv[0] for iv in local_intervals])
                interval_ends = np.array([iv[1] for iv in local_intervals])
                
                # Apply to each channel's mask
                for ch_name, ch_df in imp.channels_data.items():
                    ch_times = ch_df['SECONDS'].values
                    
                    # Check which points fall within the intervals
                    insert_idx = np.searchsorted(interval_starts, ch_times, side='right') - 1
                    in_interval = np.zeros(len(ch_times), dtype=bool)
                    valid_idx = insert_idx >= 0
                    in_interval[valid_idx] = ch_times[valid_idx] <= interval_ends[insert_idx[valid_idx]]
                    
                    # Apply based on mode
                    if mode == 'show':
                        channel_masks[ch_name] = channel_masks[ch_name] | in_interval
                    else:
                        channel_masks[ch_name] = channel_masks[ch_name] & ~in_interval
            
            # Store final masks
            filter_masks[imp_idx] = channel_masks
            
            # Compute visible intervals from the final mask for NaN separators
            if channel_masks:
                ref_channel = list(imp.channels_data.keys())[0]
                ref_times = imp.channels_data[ref_channel]['SECONDS'].values
                ref_mask = channel_masks[ref_channel]
                
                # Find contiguous visible regions
                visible_intervals = []
                in_visible = False
                start_time = None
                
                for i, (t, visible) in enumerate(zip(ref_times, ref_mask)):
                    if visible and not in_visible:
                        in_visible = True
                        start_time = t
                    elif not visible and in_visible:
                        in_visible = False
                        visible_intervals.append((start_time, ref_times[i-1]))
                
                if in_visible and start_time is not None:
                    visible_intervals.append((start_time, ref_times[-1]))
                
                if visible_intervals:
                    filter_intervals[imp_idx] = visible_intervals
            
            visible_count = np.sum(list(channel_masks.values())[0]) if channel_masks else 0
            logger.info(f"Import {imp_idx}: Final filter result, {visible_count} visible points, {len(filter_intervals.get(imp_idx, []))} intervals")
        
        # Pass filter masks and intervals to chart widget
        self.chart_widget.set_filter_mask(filter_masks, filter_intervals)
    
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
        
        # Update zoom slider position
        self._update_zoom_slider()
        
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
        for channel, control in self.channel_controls.items():
            if isinstance(control, MultiImportChannelControl):
                # Show chart
                control.set_chart_visible(True)
                self.chart_widget.set_chart_visible(channel, True)
                # Show all imports
                for i in range(len(control.import_visible)):
                    control.set_import_visible(i, True)
                    self.chart_widget.set_channel_import_visible(channel, i, True)
            else:
                control.checkbox.setChecked(True)
        
        # Re-sort controls
        self._sort_channel_controls()
    
    def _hide_all_channels(self):
        """Hide all channels."""
        for channel, control in self.channel_controls.items():
            if isinstance(control, MultiImportChannelControl):
                # Hide chart
                control.set_chart_visible(False)
                self.chart_widget.set_chart_visible(channel, False)
            else:
                control.checkbox.setChecked(False)
        
        # Re-sort controls
        self._sort_channel_controls()
    
    def _shift_time(self, delta: float):
        """Shift time range by delta seconds."""
        self.chart_widget.shift_time(delta)
        self._update_time_inputs()
    
    def _reset_time_range(self):
        """Reset to full time range."""
        self.chart_widget.reset_time_range()
        self._update_time_inputs()
        self._update_zoom_slider()
    
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
    
    def _on_zoom_slider_changed(self, value: int):
        """Handle zoom slider value change.
        
        Slider value 0 = fully zoomed out (full data range)
        Slider value 100 = fully zoomed in (min_duration seconds visible)
        
        Uses exponential scaling for natural zoom feel.
        Centers zoom on last clicked position if available, otherwise view center.
        """
        chart = self.chart_widget
        
        max_duration = chart.max_time - chart.min_time
        min_duration = 10.0  # Minimum zoom level (10 seconds)
        
        if max_duration <= min_duration:
            return
        
        # Exponential interpolation: duration = max * (min/max)^(value/100)
        # At value=0: duration = max
        # At value=100: duration = min
        ratio = value / 100.0
        new_duration = max_duration * ((min_duration / max_duration) ** ratio)
        
        # Use last clicked position as center if available, otherwise view center
        center = chart.get_zoom_center()
        
        new_start = center - new_duration / 2
        new_end = center + new_duration / 2
        
        # Boundary-aware clamping: keep boundary in view until center becomes centerable
        # If centering would push us past a boundary, pin to that boundary instead
        if new_start < chart.min_time:
            new_start = chart.min_time
            new_end = new_start + new_duration
        
        if new_end > chart.max_time:
            new_end = chart.max_time
            new_start = new_end - new_duration
        
        # Final clamp
        new_start = max(chart.min_time, new_start)
        new_end = min(chart.max_time, new_end)
        
        chart.set_time_range(new_start, new_end)
        self._update_time_inputs()
    
    def _update_zoom_slider(self):
        """Update zoom slider position to match current zoom level."""
        chart = self.chart_widget
        nav = self.time_nav
        
        current_duration = chart.current_end - chart.current_start
        max_duration = chart.max_time - chart.min_time
        min_duration = 10.0
        
        if max_duration <= min_duration or current_duration <= 0:
            return
        
        # Inverse of exponential: value = 100 * log(duration/max) / log(min/max)
        import math
        ratio = math.log(current_duration / max_duration) / math.log(min_duration / max_duration)
        slider_value = int(ratio * 100)
        slider_value = max(0, min(100, slider_value))
        
        nav.zoom_slider.blockSignals(True)
        nav.zoom_slider.setValue(slider_value)
        nav.zoom_slider.blockSignals(False)
    
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
        
        # Debounced zoom button update (restart timer on each change)
        self._zoom_button_timer.start()
    
    def _on_crosshair_moved(self, x: float):
        """Handle crosshair position change - update status bar."""
        self.current_time_label.setText(f"Current: {x:.2f}s")
    
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
        """Load recent files from JSON file."""
        self.recent_files = load_recent_files()
    
    def _save_recent_files(self):
        """Save recent files to JSON file."""
        save_recent_files(self.recent_files)
    
    def _add_to_recent(self, path: str):
        """Add path to recent files using absolute paths for deduplication."""
        # Normalize to absolute path for consistent deduplication
        abs_path = str(Path(path).resolve())
        
        # Remove any existing entry with the same absolute path
        self.recent_files = [p for p in self.recent_files if str(Path(p).resolve()) != abs_path]
        
        self.recent_files.insert(0, abs_path)
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
        # Prompt to save view if data is loaded
        if self.imports and not self.view_manager.prompt_save_view():
            event.ignore()
            return
        
        # Save geometry
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter_state", self.splitter.saveState())
        
        event.accept()
    
    def _save_view_dialog(self) -> bool:
        """Show save view dialog."""
        return self.view_manager.save_view_dialog()
    
    def _load_saved_view(self, view_path: str):
        """Load a saved view from file."""
        self.view_manager.load_saved_view(view_path)
    
    def _delete_saved_view(self, view_path: str):
        """Delete a single saved view."""
        from pathlib import Path
        reply = QMessageBox.question(
            self, "Delete View",
            f"Are you sure you want to delete this saved view?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                Path(view_path).unlink()
                self._update_home_screen()
                self.statusbar.showMessage("View deleted", 3000)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete view: {e}")
    
    def _delete_all_saved_views(self):
        """Delete all saved views."""
        from .app_data import list_saved_views
        views = list_saved_views()
        if not views:
            return
        
        reply = QMessageBox.question(
            self, "Delete All Views",
            f"Are you sure you want to delete all {len(views)} saved views?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from pathlib import Path
            deleted = 0
            for view in views:
                try:
                    Path(view['path']).unlink()
                    deleted += 1
                except Exception:
                    pass
            self._update_home_screen()
            self.statusbar.showMessage(f"Deleted {deleted} views", 3000)
