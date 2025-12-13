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
    QDialog, QListWidget, QListWidgetItem, QStackedWidget, QGridLayout,
    QComboBox, QColorDialog
)
from PyQt6.QtCore import Qt, QSettings, QSize, pyqtSignal, QTimer, QStringListModel, QThread
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFont, QColor, QMovie
from PyQt6.QtWidgets import QCompleter

from .chart_widget import OBD2ChartWidget
from ..core.data_loader import OBDDataLoader

logger = logging.getLogger(__name__)


class FileLoaderThread(QThread):
    """Background thread for loading CSV files without blocking the UI."""
    
    finished = pyqtSignal(dict, dict)  # channels_data, units
    error = pyqtSignal(str)  # error message
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
    
    def run(self):
        try:
            loader = OBDDataLoader(str(Path(self.file_path).parent))
            channels_data, units = loader.load_single_file(self.file_path)
            self.finished.emit(channels_data, units)
        except Exception as e:
            self.error.emit(str(e))


class LoadingDialog(QDialog):
    """Loading dialog with animated GIF spinner."""
    
    def __init__(self, message: str = "Loading...", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading")
        self.setModal(True)
        self.setFixedSize(320, 140)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Animated GIF spinner
        spinner_layout = QHBoxLayout()
        spinner_layout.addStretch()
        
        self.spinner_label = QLabel()
        self.spinner_label.setFixedSize(64, 64)
        self.spinner_label.setScaledContents(True)
        
        # Load animated GIF
        import os
        gif_path = os.path.join(os.path.dirname(__file__), 'loading.gif')
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(QSize(64, 64))
        self.spinner_label.setMovie(self.movie)
        self.movie.start()
        
        spinner_layout.addWidget(self.spinner_label)
        spinner_layout.addStretch()
        layout.addLayout(spinner_layout)
        
        # Label with text scaling
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("font-size: 11pt;")
        self.label.setMinimumHeight(30)
        layout.addWidget(self.label)
        
        # Timer to keep animation running during blocking operations
        self.event_timer = QTimer(self)
        self.event_timer.timeout.connect(self._process_events)
        self.event_timer.start(50)  # Process events every 50ms
    
    def _process_events(self):
        """Keep the event loop responsive for animation."""
        QApplication.processEvents()
    
    def set_message(self, message: str):
        # Scale font if text is too long
        self.label.setText(message)
        font_size = 11
        if len(message) > 40:
            font_size = 10
        if len(message) > 60:
            font_size = 9
        self.label.setStyleSheet(f"font-size: {font_size}pt;")
        QApplication.processEvents()
    
    def closeEvent(self, event):
        self.event_timer.stop()
        self.movie.stop()
        super().closeEvent(event)


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
    # Signal: channel_name for edit button clicked (math channels only)
    edit_requested = pyqtSignal(str)
    
    def __init__(self, channel_name: str, display_name: str, unit: str, 
                 import_colors: List[str], is_math_channel: bool = False, parent=None):
        super().__init__(parent)
        
        self.channel_name = channel_name
        self.display_name = display_name
        self.unit = unit
        self.is_math_channel = is_math_channel
        self.checkboxes: List[QCheckBox] = []
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Checkboxes with color indicators on the LEFT (matching Filters layout)
        for i, color in enumerate(import_colors):
            # Checkbox first
            cb = QCheckBox()
            cb.setChecked(True)
            cb.stateChanged.connect(lambda state, idx=i: self._on_checkbox_changed(idx, state))
            self.checkboxes.append(cb)
            layout.addWidget(cb)
            
            # Color indicator after checkbox
            color_label = QLabel()
            color_label.setFixedSize(12, 12)
            color_label.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
            layout.addWidget(color_label)
        
        # Channel name label (no unit - unit shown in section header)
        name_label = QLabel(display_name)
        name_label.setMinimumWidth(150)
        layout.addWidget(name_label, 1)
        
        # Edit button for math channels
        if is_math_channel:
            edit_btn = QPushButton("✏")
            edit_btn.setFixedSize(24, 24)
            edit_btn.setToolTip("Edit math channel")
            edit_btn.setStyleSheet("background-color: #7B1FA2; color: white; font-size: 10pt;")
            edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.channel_name))
            layout.addWidget(edit_btn)
    
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


class ClickableColorLabel(QLabel):
    """A clickable color indicator label."""
    clicked = pyqtSignal(int)  # Emits import index
    
    def __init__(self, import_index: int, parent=None):
        super().__init__(parent)
        self.import_index = import_index
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.import_index)
        super().mousePressEvent(event)


class ImportLegendWidget(QWidget):
    """Widget showing the legend mapping filenames to colors with duration, offset, and sync buttons."""
    
    # Signal: import_index for sync button clicked
    sync_requested = pyqtSignal(int)
    # Signal: import_index for color change requested
    color_change_requested = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(4)
        self.offset_labels: List[QLabel] = []
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration as h:m:s."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def update_legend(self, imports: List[ImportData]):
        # Clear existing
        while self.main_layout.count() > 0:
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.offset_labels = []
        
        # Add legend entries
        for i, imp in enumerate(imports):
            entry = QWidget()
            entry_layout = QVBoxLayout(entry)
            entry_layout.setContentsMargins(2, 2, 2, 2)
            entry_layout.setSpacing(2)
            
            # Row 1: Color + Filename
            row1 = QHBoxLayout()
            row1.setSpacing(4)
            
            # Color indicator (clickable)
            color_label = ClickableColorLabel(i)
            color_label.setFixedSize(14, 14)
            color_label.setStyleSheet(f"background-color: {imp.color}; border-radius: 7px;")
            color_label.setToolTip("Click to change color")
            color_label.clicked.connect(self.color_change_requested.emit)
            row1.addWidget(color_label)
            
            # Filename
            name_label = QLabel(f"<b>{imp.filename}</b>")
            name_label.setToolTip(imp.file_path)
            row1.addWidget(name_label, 1)
            
            entry_layout.addLayout(row1)
            
            # Row 2: Duration + Offset + Sync button
            row2 = QHBoxLayout()
            row2.setSpacing(4)
            
            # Duration
            duration = imp.max_time - imp.min_time if hasattr(imp, 'max_time') else 0
            duration_label = QLabel(f"Duration: {self._format_duration(duration)}")
            duration_label.setStyleSheet("color: #666; font-size: 9pt;")
            row2.addWidget(duration_label)
            
            row2.addStretch()
            
            # Offset label
            offset_text = "Base" if i == 0 else f"Offset: {imp.time_offset:+.1f}s"
            offset_label = QLabel(offset_text)
            offset_label.setStyleSheet("color: #666; font-size: 9pt;")
            row2.addWidget(offset_label)
            self.offset_labels.append(offset_label)
            
            # Sync button (not for base import)
            if i > 0:
                sync_btn = QPushButton("Sync")
                sync_btn.setFixedSize(40, 20)
                sync_btn.setStyleSheet("background-color: #1976D2; color: white; font-size: 8pt;")
                sync_btn.clicked.connect(lambda checked, idx=i: self.sync_requested.emit(idx))
                row2.addWidget(sync_btn)
            
            entry_layout.addLayout(row2)
            
            self.main_layout.addWidget(entry)
    
    def update_offset(self, import_index: int, offset: float):
        """Update the offset display for a specific import."""
        if import_index < len(self.offset_labels):
            if import_index == 0:
                self.offset_labels[import_index].setText("Base")
            else:
                self.offset_labels[import_index].setText(f"Offset: {offset:+.1f}s")


class SynchronizeDialog(QDialog):
    """Dialog for adjusting time offset for a single import."""
    
    # Signal: (import_index, new_offset)
    offset_changed = pyqtSignal(int, float)
    
    def __init__(self, import_data: 'ImportData', import_index: int, parent=None):
        super().__init__(parent)
        
        self.import_index = import_index
        self.setWindowTitle(f"Synchronize: {import_data.filename}")
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout(self)
        
        # Color indicator + filename header
        header = QHBoxLayout()
        color_label = QLabel()
        color_label.setFixedSize(20, 20)
        color_label.setStyleSheet(f"background-color: {import_data.color}; border-radius: 10px;")
        header.addWidget(color_label)
        header.addWidget(QLabel(f"<b>{import_data.filename}</b>"))
        header.addStretch()
        layout.addLayout(header)
        
        # Current offset display with spinbox
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(QLabel("Time Offset:"))
        
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setDecimals(2)
        self.offset_spin.setSuffix(" s")
        self.offset_spin.setRange(-999999, 999999)
        self.offset_spin.setValue(import_data.time_offset)
        self.offset_spin.valueChanged.connect(lambda val: self.offset_changed.emit(self.import_index, val))
        offset_layout.addWidget(self.offset_spin)
        layout.addLayout(offset_layout)
        
        # Shift buttons - all in one row like time nav
        btn_style = "background-color: #616161; color: white; font-weight: bold;"
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(2)
        
        # All shift buttons in one row
        shifts = [
            (-300, "◀5m"), (-60, "◀1m"), (-30, "◀30s"), (-15, "◀15s"),
            (-5, "◀5s"), (-1, "◀1s"), (-0.5, "◀.5s"), (-0.1, "◀.1s"),
            (0.1, ".1s▶"), (0.5, ".5s▶"), (1, "1s▶"), (5, "5s▶"),
            (15, "15s▶"), (30, "30s▶"), (60, "1m▶"), (300, "5m▶")
        ]
        
        for delta, label in shifts:
            btn = QPushButton(label)
            btn.setStyleSheet(btn_style)
            btn.setFixedHeight(24)
            btn.clicked.connect(lambda checked, d=delta: self._shift_offset(d))
            nav_layout.addWidget(btn)
        
        layout.addLayout(nav_layout)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _shift_offset(self, delta: float):
        new_val = self.offset_spin.value() + delta
        self.offset_spin.setValue(new_val)


# Shared help text for expression dialogs (DRY)
EXPRESSION_HELP_TEXT = (
    "<b>Inputs:</b> A, B, C, D, E<br>"
    "<b>Arithmetic:</b> +, -, *, /, **, %, comparisons (&lt;, &gt;, ==)<br>"
    "<b>Boolean:</b> &amp; (and), | (or), ~ (not)<br>"
    "<b>Functions:</b> abs, min, max, sqrt, log, exp, sin, cos, round, pow, floor, ceil<br>"
    "<b>Statistical:</b> rolling_avg(X, secs), rolling_min(X, secs), rolling_max(X, secs), delta, clip(X, min, max)<br>"
    "<b>Conditional:</b> if_else(condition, true_value, false_value)"
)


# Helper functions for math channel expressions
def _get_math_functions():
    """Return dict of safe math functions available in expressions."""
    import numpy as np
    return {
        # Basic math
        'abs': abs,
        'min': min,
        'max': max,
        'round': round,
        'pow': pow,
        # Numpy math functions
        'sqrt': np.sqrt,
        'log': np.log,
        'log10': np.log10,
        'exp': np.exp,
        'sin': np.sin,
        'cos': np.cos,
        'tan': np.tan,
        'floor': np.floor,
        'ceil': np.ceil,
        # Constants
        'pi': np.pi,
        'e': np.e,
    }


def _get_statistical_functions(times: 'np.ndarray' = None):
    """Return dict of statistical functions for array operations.
    
    Args:
        times: Optional array of timestamps in seconds. If provided, rolling
               window functions will use seconds instead of data points.
    """
    import numpy as np
    
    def _seconds_to_points(seconds: float) -> int:
        """Convert seconds to approximate number of data points based on sample rate."""
        if times is None or len(times) < 2:
            return max(1, int(seconds))  # Fallback: treat as points
        # Estimate sample rate from timestamps
        avg_dt = (times[-1] - times[0]) / (len(times) - 1)
        if avg_dt <= 0:
            return max(1, int(seconds))
        points = int(seconds / avg_dt)
        return max(1, points)
    
    def rolling_avg(arr, window_seconds):
        """Compute rolling average with given window size in seconds."""
        window = _seconds_to_points(window_seconds)
        result = np.convolve(arr, np.ones(window)/window, mode='same')
        # Handle edges - use available data
        half = window // 2
        for i in range(half):
            if i < len(arr):
                result[i] = np.mean(arr[:i+half+1])
        for i in range(len(arr) - half, len(arr)):
            if i >= 0:
                result[i] = np.mean(arr[i-half:])
        return result
    
    def rolling_min(arr, window_seconds):
        """Compute rolling minimum with given window size in seconds."""
        window = _seconds_to_points(window_seconds)
        result = np.zeros_like(arr)
        for i in range(len(arr)):
            start = max(0, i - window // 2)
            end = min(len(arr), i + window // 2 + 1)
            result[i] = np.min(arr[start:end])
        return result
    
    def rolling_max(arr, window_seconds):
        """Compute rolling maximum with given window size in seconds."""
        window = _seconds_to_points(window_seconds)
        result = np.zeros_like(arr)
        for i in range(len(arr)):
            start = max(0, i - window // 2)
            end = min(len(arr), i + window // 2 + 1)
            result[i] = np.max(arr[start:end])
        return result
    
    def delta(arr):
        """Compute point-to-point difference (derivative approximation)."""
        result = np.zeros_like(arr)
        result[1:] = np.diff(arr)
        result[0] = result[1] if len(result) > 1 else 0
        return result
    
    def cumsum(arr):
        """Compute cumulative sum."""
        return np.cumsum(arr)
    
    def clip(arr, min_val, max_val):
        """Clip values to range [min_val, max_val]."""
        return np.clip(arr, min_val, max_val)
    
    return {
        'rolling_avg': rolling_avg,
        'rolling_min': rolling_min,
        'rolling_max': rolling_max,
        'delta': delta,
        'cumsum': cumsum,
        'clip': clip,
        'np_min': np.min,  # Array-wide min
        'np_max': np.max,  # Array-wide max
        'np_mean': np.mean,  # Array-wide mean
        'np_std': np.std,  # Standard deviation
    }


class MathChannelDialog(QDialog):
    """Dialog for creating or editing a math channel from an expression.
    
    Supports up to 5 input channels (A, B, C, D, E) and provides:
    - Basic math operations: +, -, *, /, **, %
    - Comparison operators: <, >, <=, >=, ==, !=
    - Conditional expressions: if_else(condition, true_val, false_val)
    - Math functions: abs, min, max, sqrt, log, exp, sin, cos, etc.
    - Statistical functions: rolling_avg, rolling_min, rolling_max, delta, etc.
    """
    
    # Signal: (name, expression, inputs_dict_json, unit)
    channel_created = pyqtSignal(str, str, str, str)
    
    # Input labels
    INPUT_LABELS = ['A', 'B', 'C', 'D', 'E']
    
    def __init__(self, available_channels: List[str], available_units: List[str],
                 channel_units: Dict[str, str] = None, edit_data: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        
        self.channel_units = channel_units or {}
        # Sort channels by unit then alphabetically, format with unit suffix
        self.available_channels = available_channels
        self.sorted_channel_items = self._sort_channels_by_unit(available_channels)
        self.edit_mode = edit_data is not None
        self.original_name = edit_data.get('name', '') if edit_data else ''
        
        self.setWindowTitle("Edit Math Channel" if self.edit_mode else "Create Math Channel")
        self.setMinimumWidth(550)
        
        layout = QVBoxLayout(self)
        
        # Channel name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Channel Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., AFR_Calculated")
        self.name_input.textChanged.connect(self._on_name_changed)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Input channels section
        inputs_group = QGroupBox("Input Channels")
        inputs_layout = QGridLayout(inputs_group)
        
        self.input_combos = {}
        self.input_unit_labels = {}
        
        for i, label in enumerate(self.INPUT_LABELS):
            row = i
            # Label
            lbl = QLabel(f"Input {label}:" if i == 0 else f"Input {label} (optional):")
            inputs_layout.addWidget(lbl, row, 0)
            
            # Combo box with channels sorted by unit
            combo = QComboBox()
            if i > 0:  # A is required, others optional
                combo.addItem("(None)")
            for display_text, channel_name in self.sorted_channel_items:
                combo.addItem(display_text, channel_name)
            combo.currentTextChanged.connect(self._update_unit_labels)
            inputs_layout.addWidget(combo, row, 1)
            self.input_combos[label] = combo
            
            # Unit label
            unit_lbl = QLabel("")
            unit_lbl.setStyleSheet("color: #666; font-style: italic;")
            unit_lbl.setMinimumWidth(80)
            inputs_layout.addWidget(unit_lbl, row, 2)
            self.input_unit_labels[label] = unit_lbl
        
        layout.addWidget(inputs_group)
        
        # Expression section
        expr_group = QGroupBox("Expression")
        expr_layout = QVBoxLayout(expr_group)
        
        self.expr_input = QLineEdit()
        self.expr_input.setPlaceholderText("e.g., (A / 0.45) * 14.7  or  if_else(A > B, A, B)")
        self.expr_input.textChanged.connect(self._validate_expression)
        expr_layout.addWidget(self.expr_input)
        
        # Help text (shared constant)
        func_help = QLabel(EXPRESSION_HELP_TEXT)
        func_help.setStyleSheet("color: #555; font-size: 8pt;")
        func_help.setWordWrap(True)
        expr_layout.addWidget(func_help)
        
        # Validation status
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: #666; font-size: 9pt;")
        expr_layout.addWidget(self.validation_label)
        
        layout.addWidget(expr_group)
        
        # Unit with autocomplete
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(QLabel("Output Unit:"))
        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("e.g., AFR")
        
        # Setup autocomplete for units
        self.unit_completer = QCompleter(sorted(set(available_units)))
        self.unit_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.unit_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.unit_input.setCompleter(self.unit_completer)
        
        unit_layout.addWidget(self.unit_input)
        layout.addLayout(unit_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_text = "Save" if self.edit_mode else "Create"
        self.create_btn = QPushButton(btn_text)
        self.create_btn.setStyleSheet("background-color: #1976D2; color: white; font-weight: bold;")
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self._create_channel)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.create_btn)
        layout.addLayout(btn_layout)
        
        # Pre-fill if editing
        if edit_data:
            self.name_input.setText(edit_data.get('name', ''))
            self.expr_input.setText(edit_data.get('expression', ''))
            self.unit_input.setText(edit_data.get('unit', ''))
            
            # Handle both old format (input_a, input_b) and new format (inputs dict)
            if 'inputs' in edit_data:
                inputs = edit_data['inputs']
                for label in self.INPUT_LABELS:
                    if label in inputs and inputs[label]:
                        ch = inputs[label]
                        if ch in self.available_channels:
                            # Find the combo index by itemData (channel name), not display text
                            combo = self.input_combos[label]
                            for i in range(combo.count()):
                                if combo.itemData(i) == ch:
                                    combo.setCurrentIndex(i)
                                    break
            else:
                # Legacy format
                input_a = edit_data.get('input_a', '')
                if input_a in self.available_channels:
                    combo = self.input_combos['A']
                    for i in range(combo.count()):
                        if combo.itemData(i) == input_a:
                            combo.setCurrentIndex(i)
                            break
                
                input_b = edit_data.get('input_b', '')
                if input_b and input_b in self.available_channels:
                    combo = self.input_combos['B']
                    for i in range(combo.count()):
                        if combo.itemData(i) == input_b:
                            combo.setCurrentIndex(i)
                            break
        
        # Initialize unit labels
        self._update_unit_labels()
    
    def _sort_channels_by_unit(self, channels: List[str]) -> List[tuple]:
        """Sort channels by unit then alphabetically, return list of (display_text, channel_name).
        
        Matches the sorting used in channel controls sidebar: by unit.lower(), then display_name.lower()
        """
        # Build list of (channel_name, display_name, unit)
        channel_info = []
        for ch in channels:
            unit = self.channel_units.get(ch, '')
            display_name = ch.replace('_', ' ').title()
            channel_info.append((ch, display_name, unit))
        
        # Sort by unit.lower(), then display_name.lower() (matching channel controls)
        channel_info.sort(key=lambda x: (x[2].lower(), x[1].lower()))
        
        # Build result with display text including unit
        result = []
        for ch, display_name, unit in channel_info:
            display = f"{ch} ({unit})" if unit else ch
            result.append((display, ch))
        return result
    
    def _get_channel_from_combo(self, combo: QComboBox) -> str:
        """Get the actual channel name from a combo box (handles display text with unit)."""
        data = combo.currentData()
        if data is not None:
            return data
        # Fallback for (None) or legacy
        text = combo.currentText()
        return text if text != "(None)" else ""
    
    def _update_unit_labels(self):
        """Update the unit labels for all inputs."""
        for label in self.INPUT_LABELS:
            combo = self.input_combos[label]
            unit_lbl = self.input_unit_labels[label]
            
            channel = self._get_channel_from_combo(combo)
            if channel and channel in self.channel_units:
                unit_lbl.setText(f"[{self.channel_units[channel]}]")
            else:
                unit_lbl.setText("")
        
        # Re-validate expression when inputs change
        self._validate_expression()
    
    def _on_name_changed(self):
        """Re-validate when name changes."""
        self._validate_expression()
    
    def _get_eval_context(self, test_values: Dict[str, float] = None):
        """Get the evaluation context with all available functions."""
        import numpy as np
        
        if test_values is None:
            test_values = {label: 1.0 for label in self.INPUT_LABELS}
        
        # Build context with functions and variables
        context = {}
        context.update(_get_math_functions())
        context.update(_get_statistical_functions())
        
        # Add if_else for conditionals (works element-wise on arrays)
        def if_else(condition, true_val, false_val):
            """Conditional expression: returns true_val where condition is True, else false_val."""
            return np.where(condition, true_val, false_val)
        
        context['if_else'] = if_else
        
        # Add test values
        context.update(test_values)
        
        return context
    
    def _validate_expression(self):
        """Validate the expression and update UI."""
        import numpy as np
        
        expr = self.expr_input.text().strip()
        name = self.name_input.text().strip()
        
        if not expr:
            self.validation_label.setText("")
            self.create_btn.setEnabled(False)
            return
        
        # Check that Input A is selected
        input_a = self._get_channel_from_combo(self.input_combos['A'])
        if not input_a:
            self.validation_label.setText("✗ Input A is required")
            self.validation_label.setStyleSheet("color: #D32F2F; font-size: 9pt;")
            self.create_btn.setEnabled(False)
            return
        
        # Build test values - use arrays to test statistical functions
        test_values = {}
        used_inputs = []
        for label in self.INPUT_LABELS:
            channel = self._get_channel_from_combo(self.input_combos[label])
            if channel:
                test_values[label] = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
                used_inputs.append(label)
            else:
                test_values[label] = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        
        # Try to evaluate with test values
        try:
            context = self._get_eval_context(test_values)
            result = eval(expr, {"__builtins__": {}}, context)
            
            # Handle both scalar and array results
            if isinstance(result, np.ndarray):
                if not np.issubdtype(result.dtype, np.number):
                    raise ValueError("Expression must return numeric values")
                result_str = f"[{result[0]:.2f}, {result[1]:.2f}, ...]" if len(result) > 2 else str(result)
            elif isinstance(result, (int, float)):
                result_str = f"{result:.4f}"
            else:
                raise ValueError("Expression must return a number or array")
            
            inputs_str = ", ".join([f"{l}=[1-5]" for l in used_inputs])
            self.validation_label.setText(f"✓ Valid ({inputs_str} → {result_str})")
            self.validation_label.setStyleSheet("color: #388E3C; font-size: 9pt;")
            self.create_btn.setEnabled(bool(name))
            
        except Exception as e:
            self.validation_label.setText(f"✗ Invalid: {str(e)}")
            self.validation_label.setStyleSheet("color: #D32F2F; font-size: 9pt;")
            self.create_btn.setEnabled(False)
    
    def _create_channel(self):
        """Emit signal to create the channel."""
        name = self.name_input.text().strip()
        expr = self.expr_input.text().strip()
        
        # Collect all inputs
        inputs = {}
        for label in self.INPUT_LABELS:
            channel = self._get_channel_from_combo(self.input_combos[label])
            inputs[label] = channel
        
        unit = self.unit_input.text().strip() or "unit"
        
        # Emit as JSON string for inputs dict
        import json
        inputs_json = json.dumps(inputs)
        
        self.channel_created.emit(name, expr, inputs_json, unit)
        self.accept()


class FilterDialog(QDialog):
    """Dialog for creating or editing a data filter.
    
    Filters use boolean expressions to show/hide data points based on channel values.
    Reuses the same expression evaluation infrastructure as MathChannelDialog.
    """
    
    # Signal: (name, expression, inputs_dict_json, mode, buffer_seconds)
    filter_created = pyqtSignal(str, str, str, str, float)
    
    # Input labels (same as MathChannelDialog)
    INPUT_LABELS = ['A', 'B', 'C', 'D', 'E']
    
    # Buffer options in seconds
    BUFFER_OPTIONS = [
        (0.1, "±0.1s"),
        (0.5, "±0.5s"),
        (1.0, "±1s"),
        (2.0, "±2s"),
        (5.0, "±5s"),
        (10.0, "±10s"),
        (30.0, "±30s"),
        (60.0, "±1min"),
        (120.0, "±2min"),
        (300.0, "±5min"),
        (600.0, "±10min"),
    ]
    
    def __init__(self, available_channels: List[str], channel_units: Dict[str, str] = None,
                 edit_data: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        
        self.channel_units = channel_units or {}
        self.available_channels = available_channels
        self.sorted_channel_items = self._sort_channels_by_unit(available_channels)
        self.edit_mode = edit_data is not None
        self.original_name = edit_data.get('name', '') if edit_data else ''
        
        self.setWindowTitle("Edit Filter" if self.edit_mode else "Create Filter")
        self.setMinimumWidth(550)
        
        layout = QVBoxLayout(self)
        
        # Filter name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Filter Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., High_RPM_Filter")
        self.name_input.textChanged.connect(self._on_name_changed)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Input channels section
        inputs_group = QGroupBox("Input Channels")
        inputs_layout = QGridLayout(inputs_group)
        
        self.input_combos = {}
        self.input_unit_labels = {}
        
        for i, label in enumerate(self.INPUT_LABELS):
            row = i
            lbl = QLabel(f"Input {label}:" if i == 0 else f"Input {label} (optional):")
            inputs_layout.addWidget(lbl, row, 0)
            
            combo = QComboBox()
            if i > 0:
                combo.addItem("(None)")
            for display_text, channel_name in self.sorted_channel_items:
                combo.addItem(display_text, channel_name)
            combo.currentTextChanged.connect(self._update_unit_labels)
            inputs_layout.addWidget(combo, row, 1)
            self.input_combos[label] = combo
            
            unit_lbl = QLabel("")
            unit_lbl.setStyleSheet("color: #666; font-style: italic;")
            unit_lbl.setMinimumWidth(80)
            inputs_layout.addWidget(unit_lbl, row, 2)
            self.input_unit_labels[label] = unit_lbl
        
        layout.addWidget(inputs_group)
        
        # Expression section
        expr_group = QGroupBox("Boolean Expression")
        expr_layout = QVBoxLayout(expr_group)
        
        self.expr_input = QLineEdit()
        self.expr_input.setPlaceholderText("e.g., A > 3000  or  (A > 2000) & (B < 100)")
        self.expr_input.textChanged.connect(self._validate_expression)
        expr_layout.addWidget(self.expr_input)
        
        # Help text (shared constant)
        func_help = QLabel(EXPRESSION_HELP_TEXT)
        func_help.setStyleSheet("color: #555; font-size: 8pt;")
        func_help.setWordWrap(True)
        expr_layout.addWidget(func_help)
        
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: #666; font-size: 9pt;")
        expr_layout.addWidget(self.validation_label)
        
        layout.addWidget(expr_group)
        
        # Filter mode section - horizontal toggle
        mode_group = QGroupBox("Filter Mode")
        mode_layout = QHBoxLayout(mode_group)
        
        self.mode_show_btn = QPushButton("👁 Show matching data")
        self.mode_hide_btn = QPushButton("🚫 Hide matching data")
        
        self.mode_show_btn.setCheckable(True)
        self.mode_hide_btn.setCheckable(True)
        self.mode_show_btn.setChecked(True)
        
        # Style for toggle buttons - selected has outline, unselected is faded
        toggle_style_selected = """
            QPushButton { 
                padding: 8px 16px; 
                background-color: #1976D2; 
                color: white; 
                border: 2px solid #0D47A1;
                font-weight: bold;
            }
        """
        toggle_style_unselected = """
            QPushButton { 
                padding: 8px 16px; 
                background-color: #e0e0e0; 
                color: #999;
                border: 1px solid #ccc;
            }
        """
        self._toggle_style_selected = toggle_style_selected
        self._toggle_style_unselected = toggle_style_unselected
        self._update_mode_button_styles()
        
        # Make them mutually exclusive
        self.mode_show_btn.clicked.connect(lambda: self._set_filter_mode('show'))
        self.mode_hide_btn.clicked.connect(lambda: self._set_filter_mode('hide'))
        
        mode_layout.addWidget(self.mode_show_btn)
        mode_layout.addWidget(self.mode_hide_btn)
        
        layout.addWidget(mode_group)
        
        # Time buffer section
        buffer_group = QGroupBox("Time Buffer")
        buffer_layout = QHBoxLayout(buffer_group)
        
        buffer_layout.addWidget(QLabel("Buffer:"))
        self.buffer_combo = QComboBox()
        for seconds, label in self.BUFFER_OPTIONS:
            self.buffer_combo.addItem(label, seconds)
        self.buffer_combo.setCurrentIndex(0)  # Default to ±0.1s
        buffer_layout.addWidget(self.buffer_combo)
        buffer_layout.addStretch()
        
        buffer_help = QLabel("Data within buffer of matching points will be shown/hidden")
        buffer_help.setStyleSheet("color: #666; font-size: 8pt;")
        buffer_layout.addWidget(buffer_help)
        
        layout.addWidget(buffer_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_text = "Save" if self.edit_mode else "Create"
        self.create_btn = QPushButton(btn_text)
        self.create_btn.setStyleSheet("background-color: #1976D2; color: white; font-weight: bold;")
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self._create_filter)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.create_btn)
        layout.addLayout(btn_layout)
        
        # Pre-fill if editing
        if edit_data:
            self.name_input.setText(edit_data.get('name', ''))
            self.expr_input.setText(edit_data.get('expression', ''))
            
            mode = edit_data.get('mode', 'show')
            self._set_filter_mode(mode)
            
            buffer_seconds = edit_data.get('buffer_seconds', 2.0)
            for i, (seconds, _) in enumerate(self.BUFFER_OPTIONS):
                if abs(seconds - buffer_seconds) < 0.01:
                    self.buffer_combo.setCurrentIndex(i)
                    break
            
            if 'inputs' in edit_data:
                inputs = edit_data['inputs']
                for label in self.INPUT_LABELS:
                    if label in inputs and inputs[label]:
                        ch = inputs[label]
                        if ch in self.available_channels:
                            # Find the combo index by itemData (channel name), not display text
                            combo = self.input_combos[label]
                            for i in range(combo.count()):
                                if combo.itemData(i) == ch:
                                    combo.setCurrentIndex(i)
                                    break
        
        self._update_unit_labels()
    
    def _sort_channels_by_unit(self, channels: List[str]) -> List[tuple]:
        """Sort channels by unit then alphabetically, return list of (display_text, channel_name).
        
        Matches the sorting used in channel controls sidebar: by unit.lower(), then display_name.lower()
        """
        # Build list of (channel_name, display_name, unit)
        channel_info = []
        for ch in channels:
            unit = self.channel_units.get(ch, '')
            display_name = ch.replace('_', ' ').title()
            channel_info.append((ch, display_name, unit))
        
        # Sort by unit.lower(), then display_name.lower() (matching channel controls)
        channel_info.sort(key=lambda x: (x[2].lower(), x[1].lower()))
        
        # Build result with display text including unit
        result = []
        for ch, display_name, unit in channel_info:
            display = f"{ch} ({unit})" if unit else ch
            result.append((display, ch))
        return result
    
    def _get_channel_from_combo(self, combo: QComboBox) -> str:
        """Get the actual channel name from a combo box (handles display text with unit)."""
        data = combo.currentData()
        if data is not None:
            return data
        text = combo.currentText()
        return text if text != "(None)" else ""
    
    def _update_unit_labels(self):
        """Update the unit labels for all inputs."""
        for label in self.INPUT_LABELS:
            combo = self.input_combos[label]
            unit_lbl = self.input_unit_labels[label]
            
            channel = self._get_channel_from_combo(combo)
            if channel and channel in self.channel_units:
                unit_lbl.setText(f"[{self.channel_units[channel]}]")
            else:
                unit_lbl.setText("")
        
        self._validate_expression()
    
    def _on_name_changed(self):
        """Re-validate when name changes."""
        self._validate_expression()
    
    def _get_eval_context(self, test_values: Dict[str, float] = None):
        """Get the evaluation context with all available functions."""
        import numpy as np
        
        if test_values is None:
            test_values = {label: np.array([1.0]) for label in self.INPUT_LABELS}
        
        context = {}
        context.update(_get_math_functions())
        context.update(_get_statistical_functions())
        
        def if_else(condition, true_val, false_val):
            return np.where(condition, true_val, false_val)
        
        context['if_else'] = if_else
        context.update(test_values)
        
        return context
    
    def _validate_expression(self):
        """Validate the boolean expression and update UI."""
        import numpy as np
        
        expr = self.expr_input.text().strip()
        name = self.name_input.text().strip()
        
        if not expr:
            self.validation_label.setText("")
            self.create_btn.setEnabled(False)
            return
        
        input_a = self._get_channel_from_combo(self.input_combos['A'])
        if not input_a:
            self.validation_label.setText("✗ Input A is required")
            self.validation_label.setStyleSheet("color: #D32F2F; font-size: 9pt;")
            self.create_btn.setEnabled(False)
            return
        
        # Build test values
        test_values = {}
        used_inputs = []
        for label in self.INPUT_LABELS:
            channel = self._get_channel_from_combo(self.input_combos[label])
            if channel:
                test_values[label] = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
                used_inputs.append(label)
            else:
                test_values[label] = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        
        try:
            context = self._get_eval_context(test_values)
            result = eval(expr, {"__builtins__": {}}, context)
            
            # Check if result is boolean-like
            if isinstance(result, np.ndarray):
                if result.dtype != np.bool_ and not np.issubdtype(result.dtype, np.number):
                    raise ValueError("Expression must return boolean values")
                # Convert to bool for display
                bool_result = result.astype(bool)
                true_count = np.sum(bool_result)
                result_str = f"{true_count}/{len(bool_result)} True"
            elif isinstance(result, (bool, np.bool_)):
                result_str = str(result)
            else:
                raise ValueError("Expression must return boolean values")
            
            inputs_str = ", ".join([f"{l}=[1-5]" for l in used_inputs])
            self.validation_label.setText(f"✓ Valid ({inputs_str} → {result_str})")
            self.validation_label.setStyleSheet("color: #388E3C; font-size: 9pt;")
            self.create_btn.setEnabled(bool(name))
            
        except Exception as e:
            self.validation_label.setText(f"✗ Invalid: {str(e)}")
            self.validation_label.setStyleSheet("color: #D32F2F; font-size: 9pt;")
            self.create_btn.setEnabled(False)
    
    def _set_filter_mode(self, mode: str):
        """Set the filter mode ('show' or 'hide')."""
        if mode == 'show':
            self.mode_show_btn.setChecked(True)
            self.mode_hide_btn.setChecked(False)
        else:
            self.mode_show_btn.setChecked(False)
            self.mode_hide_btn.setChecked(True)
        self._update_mode_button_styles()
    
    def _update_mode_button_styles(self):
        """Update the visual styles of mode buttons based on selection."""
        if self.mode_show_btn.isChecked():
            self.mode_show_btn.setStyleSheet(self._toggle_style_selected)
            self.mode_hide_btn.setStyleSheet(self._toggle_style_unselected)
        else:
            self.mode_show_btn.setStyleSheet(self._toggle_style_unselected)
            self.mode_hide_btn.setStyleSheet(self._toggle_style_selected)
    
    def _create_filter(self):
        """Emit signal to create the filter."""
        import json
        from PyQt6.QtWidgets import QMessageBox
        
        name = self.name_input.text().strip()
        expr = self.expr_input.text().strip()
        
        # Validate name is provided
        if not name:
            QMessageBox.warning(self, "Filter Name Required", "Filters must have a name.")
            self.name_input.setFocus()
            return
        
        inputs = {}
        for label in self.INPUT_LABELS:
            channel = self._get_channel_from_combo(self.input_combos[label])
            inputs[label] = channel
        
        mode = "show" if self.mode_show_btn.isChecked() else "hide"
        buffer_seconds = self.buffer_combo.currentData()
        
        inputs_json = json.dumps(inputs)
        
        self.filter_created.emit(name, expr, inputs_json, mode, buffer_seconds)
        self.accept()


class CreatingChannelDialog(QDialog):
    """Simple modal dialog showing a spinner while creating a channel/filter."""
    
    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Please Wait")
        self.setModal(True)
        self.setFixedSize(300, 100)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel(message)
        label.setStyleSheet("font-size: 12pt;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)


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
    
    # Signal emitted when user wants to open a file (single or multiple)
    open_file_requested = pyqtSignal(str)
    open_files_requested = pyqtSignal(list)  # For multiple files
    open_new_requested = pyqtSignal()
    clear_history_requested = pyqtSignal()
    
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
        self.open_btn = QPushButton("📂 Import CSV File(s)")
        self.open_btn.setStyleSheet(btn_style)
        self.open_btn.clicked.connect(self.open_new_requested.emit)
        layout.addWidget(self.open_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(30)
        
        # Past imports section
        past_label = QLabel("Past Imports (select multiple with Ctrl+Click)")
        past_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(past_label)
        
        self.past_list = QListWidget()
        self.past_list.setMinimumHeight(200)
        self.past_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # Allow multi-select
        self.past_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.past_list)
        
        # Buttons row
        btn_row = QHBoxLayout()
        
        btn_row.addStretch()
        
        # Open selected button - bigger and centered
        self.open_selected_btn = QPushButton("📂 Open Selected")
        self.open_selected_btn.setStyleSheet("background-color: #388E3C; color: white; font-weight: bold; font-size: 14pt; padding: 12px 40px; border-radius: 5px;")
        self.open_selected_btn.clicked.connect(self._open_selected)
        btn_row.addWidget(self.open_selected_btn)
        
        btn_row.addStretch()
        
        layout.addLayout(btn_row)
        
        # Clear button row (separate, smaller)
        clear_row = QHBoxLayout()
        clear_row.addStretch()
        clear_btn = QPushButton("Clear History")
        clear_btn.setStyleSheet("background-color: #616161; color: white;")
        clear_btn.clicked.connect(self._clear_history)
        clear_row.addWidget(clear_btn)
        clear_row.addStretch()
        layout.addLayout(clear_row)
        
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
    
    def _open_selected(self):
        """Open all selected items."""
        selected_items = self.past_list.selectedItems()
        paths = []
        for item in selected_items:
            path = item.data(Qt.ItemDataRole.UserRole)
            if path:
                paths.append(path)
        
        if len(paths) == 1:
            self.open_file_requested.emit(paths[0])
        elif len(paths) > 1:
            self.open_files_requested.emit(paths)
    
    def _clear_history(self):
        self.past_list.clear()
        # Signal to parent to clear settings
        self.clear_history_requested.emit()


class TimeNavigationWidget(QWidget):
    """Widget for time navigation controls."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)
        
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
        
        # All navigation buttons in ONE row: ◀5m ◀1m ◀30s ◀15s ◀5s ◀1s ◀.5s ◀.1s [Reset] .1s▶ .5s▶ 1s▶ 5s▶ 15s▶ 30s▶ 1m▶ 5m▶
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(2)
        
        # Left buttons (largest to smallest)
        self.btn_left_5min = QPushButton("◀5m")
        self.btn_left_1min = QPushButton("◀1m")
        self.btn_left_30 = QPushButton("◀30s")
        self.btn_left_15 = QPushButton("◀15s")
        self.btn_left_5 = QPushButton("◀5s")
        self.btn_left_1 = QPushButton("◀1s")
        self.btn_left_05 = QPushButton("◀.5s")
        self.btn_left_01 = QPushButton("◀.1s")
        
        # Reset button (red, in center)
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold;")
        
        # Right buttons (smallest to largest)
        self.btn_right_01 = QPushButton(".1s▶")
        self.btn_right_05 = QPushButton(".5s▶")
        self.btn_right_1 = QPushButton("1s▶")
        self.btn_right_5 = QPushButton("5s▶")
        self.btn_right_15 = QPushButton("15s▶")
        self.btn_right_30 = QPushButton("30s▶")
        self.btn_right_1min = QPushButton("1m▶")
        self.btn_right_5min = QPushButton("5m▶")
        
        # Add all buttons to layout
        all_nav_btns = [
            self.btn_left_5min, self.btn_left_1min, self.btn_left_30, self.btn_left_15,
            self.btn_left_5, self.btn_left_1, self.btn_left_05, self.btn_left_01,
            self.btn_reset,
            self.btn_right_01, self.btn_right_05, self.btn_right_1, self.btn_right_5,
            self.btn_right_15, self.btn_right_30, self.btn_right_1min, self.btn_right_5min
        ]
        
        for btn in all_nav_btns:
            btn.setFixedHeight(26)
            btn.setMinimumWidth(10)
            nav_layout.addWidget(btn)
        
        layout.addLayout(nav_layout)
        
        # Zoom buttons
        zoom_layout = QHBoxLayout()
        btn_style = "background-color: #616161; color: white; font-weight: bold;"
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
        self._zoom_button_timer.timeout.connect(self._update_zoom_buttons)
        
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
        self.home_widget.open_files_requested.connect(self._load_multiple_files)
        self.home_widget.open_new_requested.connect(self._open_file_dialog)
        self.home_widget.clear_history_requested.connect(self.clear_recent_files)
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
        
        # Import legend sync button
        self.import_legend.sync_requested.connect(self._show_synchronize_dialog)
        # Import legend color change
        self.import_legend.color_change_requested.connect(self._show_color_picker)
        
        # Chart time range changes
        self.chart_widget.time_range_changed.connect(self._on_chart_time_changed)
    
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
        
        self._loading_dialog.close()
        self._loading_dialog = None
        self._loader_thread = None
        
        # Load next file from queue if any
        self._load_next_queued_file()
    
    def _on_file_load_error(self, error_msg: str):
        """Handle file load error from background thread."""
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
        if preserve_visibility:
            for channel, control in self.channel_controls.items():
                saved_visibility[channel] = [cb.isChecked() for cb in control.checkboxes]
        
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
            control.edit_requested.connect(self._edit_math_channel)
            self.channel_controls[channel] = control
            
            # Determine visibility for this channel
            if channel in show_channels:
                # Explicitly show this channel (e.g., newly created math channel)
                for i in range(len(import_colors)):
                    control.set_import_visible(i, True)
                    self.chart_widget.set_channel_import_visible(channel, i, True)
            elif preserve_visibility and channel in saved_visibility:
                saved = saved_visibility[channel]
                for i in range(len(import_colors)):
                    if i < len(saved):
                        # Restore saved visibility
                        visible = saved[i]
                    else:
                        # New import - default to same as first import's visibility
                        visible = saved[0] if saved else True
                    control.set_import_visible(i, visible)
                    self.chart_widget.set_channel_import_visible(channel, i, visible)
            elif preserve_visibility and channel not in saved_visibility:
                # New channel while preserving - default to hidden
                for i in range(len(import_colors)):
                    control.set_import_visible(i, False)
                    self.chart_widget.set_channel_import_visible(channel, i, False)
            elif not preserve_visibility:
                # Fresh load - default to hidden for math channels only
                if is_math:
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
                    context.update(_get_math_functions())
                    context.update(_get_statistical_functions(times))
                    
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
                context.update(_get_math_functions())
                context.update(_get_statistical_functions(times))
                
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
                    context.update(_get_math_functions())
                    context.update(_get_statistical_functions(times))
                    
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
        
        # Debounced zoom button update (restart timer on each change)
        self._zoom_button_timer.start()
    
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
        # Save geometry
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter_state", self.splitter.saveState())
        
        event.accept()
