"""
Dialog for adjusting time offset for a single import.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDoubleSpinBox
)
from PyQt6.QtCore import pyqtSignal

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..data_types import ImportData


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
