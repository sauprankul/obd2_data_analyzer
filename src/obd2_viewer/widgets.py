"""
Reusable UI widgets for the OBD2 Viewer.
"""

from pathlib import Path
from typing import List, TYPE_CHECKING

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox,
    QListWidget, QListWidgetItem, QDoubleSpinBox, QMainWindow, QSlider,
    QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

if TYPE_CHECKING:
    from .data_types import ImportData


class MultiImportChannelControl(QWidget):
    """Widget for controlling channel visibility across multiple imports.
    
    Layout: [Chart Checkbox] [Color Dot 1] [Color Dot 2] ... [Channel Name] [Edit btn]
    - Chart checkbox: toggles entire chart visibility
    - Color dots: clickable buttons to toggle individual import lines (hollow = disabled)
    """
    
    # Signal: (channel_name, import_index, visible)
    visibility_changed = pyqtSignal(str, int, bool)
    # Signal: (channel_name, chart_visible) - for toggling entire chart
    chart_visibility_changed = pyqtSignal(str, bool)
    # Signal: channel_name for edit button clicked (math channels only)
    edit_requested = pyqtSignal(str)
    
    def __init__(self, channel_name: str, display_name: str, unit: str, 
                 import_colors: List[str], is_math_channel: bool = False, parent=None):
        super().__init__(parent)
        
        self.channel_name = channel_name
        self.display_name = display_name
        self.unit = unit
        self.is_math_channel = is_math_channel
        self.import_colors = import_colors
        self.color_buttons: List[QPushButton] = []
        self.import_visible: List[bool] = [True] * len(import_colors)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Single checkbox for chart visibility
        self.chart_checkbox = QCheckBox()
        self.chart_checkbox.setChecked(True)
        self.chart_checkbox.setToolTip("Show/hide this chart")
        self.chart_checkbox.stateChanged.connect(self._on_chart_checkbox_changed)
        layout.addWidget(self.chart_checkbox)
        
        # Colored dot buttons for each import
        for i, color in enumerate(import_colors):
            btn = QPushButton()
            btn.setFixedSize(16, 16)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"Toggle import {i+1}")
            btn.clicked.connect(lambda checked, idx=i: self._on_color_button_clicked(idx))
            self._update_color_button_style(btn, color, True)
            self.color_buttons.append(btn)
            layout.addWidget(btn)
        
        # Channel name label
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
    
    def _update_color_button_style(self, btn: QPushButton, color: str, enabled: bool):
        """Update button style: solid circle if enabled, hollow ring if disabled."""
        if enabled:
            # Solid filled circle
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid {color};
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    border: 2px solid #333;
                }}
            """)
        else:
            # Hollow ring (just border, no fill)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 2px solid {color};
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    background-color: rgba(128, 128, 128, 0.2);
                }}
            """)
    
    def _on_chart_checkbox_changed(self, state: int):
        """Handle chart visibility checkbox change."""
        visible = state == Qt.CheckState.Checked.value
        self.chart_visibility_changed.emit(self.channel_name, visible)
    
    def _on_color_button_clicked(self, import_index: int):
        """Handle color button click - toggle import visibility."""
        self.import_visible[import_index] = not self.import_visible[import_index]
        visible = self.import_visible[import_index]
        
        # Update button style
        color = self.import_colors[import_index]
        self._update_color_button_style(self.color_buttons[import_index], color, visible)
        
        # Emit signal
        self.visibility_changed.emit(self.channel_name, import_index, visible)
    
    def set_import_visible(self, import_index: int, visible: bool):
        """Set visibility for a specific import (without emitting signal)."""
        if import_index < len(self.color_buttons):
            self.import_visible[import_index] = visible
            color = self.import_colors[import_index]
            self._update_color_button_style(self.color_buttons[import_index], color, visible)
    
    def set_chart_visible(self, visible: bool):
        """Set chart visibility (without emitting signal)."""
        self.chart_checkbox.blockSignals(True)
        self.chart_checkbox.setChecked(visible)
        self.chart_checkbox.blockSignals(False)
    
    def is_chart_visible(self) -> bool:
        """Return True if the chart checkbox is checked."""
        return self.chart_checkbox.isChecked()
    
    def is_any_selected(self) -> bool:
        """Return True if chart checkbox is checked (determines Shown vs Hidden pile)."""
        return self.chart_checkbox.isChecked()
    
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
        
        # Set initial size to 1024x768 and center on screen
        self.resize(1024, 768)
        self._center_on_screen()
        
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)
        self.layout.setContentsMargins(5, 5, 5, 5)
    
    def _center_on_screen(self):
        """Center the window on the primary screen."""
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2 + screen_geometry.x()
            y = (screen_geometry.height() - self.height()) // 2 + screen_geometry.y()
            self.move(x, y)
    
    def closeEvent(self, event):
        self.closed.emit()
        event.accept()


class HomeWidget(QWidget):
    """Home screen showing past imports and saved views."""
    
    open_file_requested = pyqtSignal(str)
    open_files_requested = pyqtSignal(list)
    open_new_requested = pyqtSignal()
    clear_history_requested = pyqtSignal()
    open_view_requested = pyqtSignal(str)  # Emits view path
    delete_view_requested = pyqtSignal(str)  # Emits view path
    delete_all_views_requested = pyqtSignal()
    
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
        
        # Two-column layout for lists using QGroupBox for equal sizing
        lists_layout = QHBoxLayout()
        
        # Left column: Past Imports
        left_group = QGroupBox("Past Imports (select multiple with Ctrl+Click)")
        left_group.setStyleSheet("QGroupBox { font-size: 14pt; font-weight: bold; }")
        left_col = QVBoxLayout(left_group)
        
        self.past_list = QListWidget()
        self.past_list.setMinimumHeight(200)
        self.past_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.past_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        left_col.addWidget(self.past_list)
        
        btn_row = QHBoxLayout()
        self.open_selected_btn = QPushButton("📂 Open Selected")
        self.open_selected_btn.setStyleSheet("background-color: #388E3C; color: white; font-weight: bold; padding: 8px 20px; border-radius: 5px;")
        self.open_selected_btn.clicked.connect(self._open_selected)
        btn_row.addWidget(self.open_selected_btn)
        
        clear_btn = QPushButton("Clear History")
        clear_btn.setStyleSheet("background-color: #616161; color: white; padding: 8px 15px;")
        clear_btn.clicked.connect(self._clear_history)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        left_col.addLayout(btn_row)
        
        lists_layout.addWidget(left_group, 1)
        
        # Right column: Saved Views
        right_group = QGroupBox("Saved Views")
        right_group.setStyleSheet("QGroupBox { font-size: 14pt; font-weight: bold; }")
        right_col = QVBoxLayout(right_group)
        
        self.views_list = QListWidget()
        self.views_list.setMinimumHeight(200)
        self.views_list.itemDoubleClicked.connect(self._on_view_double_clicked)
        right_col.addWidget(self.views_list)
        
        # Buttons row for saved views (matching left column)
        views_btn_row = QHBoxLayout()
        self.open_view_btn = QPushButton("📂 Open Selected")
        self.open_view_btn.setStyleSheet("background-color: #388E3C; color: white; font-weight: bold; padding: 8px 20px; border-radius: 5px;")
        self.open_view_btn.clicked.connect(self._open_selected_view)
        views_btn_row.addWidget(self.open_view_btn)
        
        delete_all_btn = QPushButton("Delete All")
        delete_all_btn.setStyleSheet("background-color: #D32F2F; color: white; padding: 8px 15px;")
        delete_all_btn.clicked.connect(self._delete_all_views)
        views_btn_row.addWidget(delete_all_btn)
        views_btn_row.addStretch()
        right_col.addLayout(views_btn_row)
        
        lists_layout.addWidget(right_group, 1)
        
        layout.addLayout(lists_layout)
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
    
    def update_saved_views(self, views: List[dict]):
        """Update the saved views list.
        
        Args:
            views: List of dicts with 'name', 'path', 'modified_at' keys
        """
        self.views_list.clear()
        for view in views:
            # Create a widget with label and delete button
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(2, 2, 2, 2)
            item_layout.setSpacing(5)
            
            label = QLabel(f"📋 {view['name']}")
            label.setToolTip(f"Modified: {view.get('modified_at', 'Unknown')}")
            item_layout.addWidget(label, 1)
            
            delete_btn = QPushButton("🗑")
            delete_btn.setFixedSize(24, 24)
            delete_btn.setStyleSheet("background-color: #D32F2F; color: white; border-radius: 3px; font-size: 10pt;")
            delete_btn.setToolTip("Delete this view")
            delete_btn.clicked.connect(lambda checked, p=view['path']: self._delete_view(p))
            item_layout.addWidget(delete_btn)
            
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, view['path'])
            item.setSizeHint(item_widget.sizeHint())
            self.views_list.addItem(item)
            self.views_list.setItemWidget(item, item_widget)
        
        if not views:
            item = QListWidgetItem("No saved views")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.views_list.addItem(item)
    
    def _on_view_double_clicked(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.open_view_requested.emit(path)
    
    def _open_selected_view(self):
        """Open the currently selected view."""
        selected_items = self.views_list.selectedItems()
        if selected_items:
            path = selected_items[0].data(Qt.ItemDataRole.UserRole)
            if path:
                self.open_view_requested.emit(path)
    
    def _delete_view(self, path: str):
        """Delete a single view."""
        self.delete_view_requested.emit(path)
    
    def _delete_all_views(self):
        """Delete all saved views."""
        self.delete_all_views_requested.emit()


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
        
        # Zoom slider: left = zoomed out (full range), right = zoomed in (1s per tick)
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("🔍-"))
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(0)
        self.zoom_slider.setMaximum(100)
        self.zoom_slider.setValue(0)  # Start fully zoomed out
        self.zoom_slider.setFixedHeight(24)
        self.zoom_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #616161, stop:1 #1976D2);
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 2px solid #1976D2;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
        """)
        zoom_layout.addWidget(self.zoom_slider, 1)
        
        zoom_layout.addWidget(QLabel("🔍+"))
        
        layout.addLayout(zoom_layout)
