"""
Reusable UI widgets for the OBD2 Viewer.
"""

from pathlib import Path
from typing import List, TYPE_CHECKING

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox,
    QListWidget, QListWidgetItem, QDoubleSpinBox, QMainWindow
)
from PyQt6.QtCore import Qt, pyqtSignal

if TYPE_CHECKING:
    from .data_types import ImportData


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
    
    sync_requested = pyqtSignal(int)
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
    
    def update_legend(self, imports: List['ImportData']):
        while self.main_layout.count() > 0:
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.offset_labels = []
        
        for i, imp in enumerate(imports):
            entry = QWidget()
            entry_layout = QVBoxLayout(entry)
            entry_layout.setContentsMargins(2, 2, 2, 2)
            entry_layout.setSpacing(2)
            
            row1 = QHBoxLayout()
            row1.setSpacing(4)
            
            color_label = ClickableColorLabel(i)
            color_label.setFixedSize(14, 14)
            color_label.setStyleSheet(f"background-color: {imp.color}; border-radius: 7px;")
            color_label.setToolTip("Click to change color")
            color_label.clicked.connect(self.color_change_requested.emit)
            row1.addWidget(color_label)
            
            name_label = QLabel(f"<b>{imp.filename}</b>")
            name_label.setToolTip(imp.file_path)
            row1.addWidget(name_label, 1)
            
            entry_layout.addLayout(row1)
            
            row2 = QHBoxLayout()
            row2.setSpacing(4)
            
            duration = imp.max_time - imp.min_time if hasattr(imp, 'max_time') else 0
            duration_label = QLabel(f"Duration: {self._format_duration(duration)}")
            duration_label.setStyleSheet("color: #666; font-size: 9pt;")
            row2.addWidget(duration_label)
            
            row2.addStretch()
            
            offset_text = "Base" if i == 0 else f"Offset: {imp.time_offset:+.1f}s"
            offset_label = QLabel(offset_text)
            offset_label.setStyleSheet("color: #666; font-size: 9pt;")
            row2.addWidget(offset_label)
            self.offset_labels.append(offset_label)
            
            if i > 0:
                sync_btn = QPushButton("Sync")
                sync_btn.setFixedSize(40, 20)
                sync_btn.setStyleSheet("background-color: #1976D2; color: white; font-size: 8pt;")
                sync_btn.clicked.connect(lambda checked, idx=i: self.sync_requested.emit(idx))
                row2.addWidget(sync_btn)
            
            entry_layout.addLayout(row2)
            self.main_layout.addWidget(entry)
    
    def update_offset(self, import_index: int, offset: float):
        if import_index < len(self.offset_labels):
            if import_index == 0:
                self.offset_labels[import_index].setText("Base")
            else:
                self.offset_labels[import_index].setText(f"Offset: {offset:+.1f}s")


class SidebarWindow(QMainWindow):
    """Separate window for sidebar controls in split window mode."""
    
    closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OBD2 Controls")
        self.setMinimumSize(350, 600)
        
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)
        self.layout.setContentsMargins(5, 5, 5, 5)
    
    def closeEvent(self, event):
        self.closed.emit()
        event.accept()


class HomeWidget(QWidget):
    """Home screen showing past imports."""
    
    open_file_requested = pyqtSignal(str)
    open_files_requested = pyqtSignal(list)
    open_new_requested = pyqtSignal()
    clear_history_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("OBD2 Data Visualization Tool")
        title.setStyleSheet("font-size: 24pt; font-weight: bold; color: #1976D2;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("High-performance native application for OBD2 data analysis")
        subtitle.setStyleSheet("font-size: 12pt; color: #666;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(30)
        
        btn_style = "background-color: #1976D2; color: white; font-weight: bold; font-size: 14pt; padding: 15px 30px; border-radius: 5px;"
        self.open_btn = QPushButton("📂 Import CSV File(s)")
        self.open_btn.setStyleSheet(btn_style)
        self.open_btn.clicked.connect(self.open_new_requested.emit)
        layout.addWidget(self.open_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(30)
        
        past_label = QLabel("Past Imports (select multiple with Ctrl+Click)")
        past_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(past_label)
        
        self.past_list = QListWidget()
        self.past_list.setMinimumHeight(200)
        self.past_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.past_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.past_list)
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        self.open_selected_btn = QPushButton("📂 Open Selected")
        self.open_selected_btn.setStyleSheet("background-color: #388E3C; color: white; font-weight: bold; font-size: 14pt; padding: 12px 40px; border-radius: 5px;")
        self.open_selected_btn.clicked.connect(self._open_selected)
        btn_row.addWidget(self.open_selected_btn)
        
        btn_row.addStretch()
        layout.addLayout(btn_row)
        
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
        self.clear_history_requested.emit()


class TimeNavigationWidget(QWidget):
    """Widget for time navigation controls."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)
        
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
        
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(2)
        
        self.btn_left_5min = QPushButton("◀5m")
        self.btn_left_1min = QPushButton("◀1m")
        self.btn_left_30 = QPushButton("◀30s")
        self.btn_left_15 = QPushButton("◀15s")
        self.btn_left_5 = QPushButton("◀5s")
        self.btn_left_1 = QPushButton("◀1s")
        self.btn_left_05 = QPushButton("◀.5s")
        self.btn_left_01 = QPushButton("◀.1s")
        
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold;")
        
        self.btn_right_01 = QPushButton(".1s▶")
        self.btn_right_05 = QPushButton(".5s▶")
        self.btn_right_1 = QPushButton("1s▶")
        self.btn_right_5 = QPushButton("5s▶")
        self.btn_right_15 = QPushButton("15s▶")
        self.btn_right_30 = QPushButton("30s▶")
        self.btn_right_1min = QPushButton("1m▶")
        self.btn_right_5min = QPushButton("5m▶")
        
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
