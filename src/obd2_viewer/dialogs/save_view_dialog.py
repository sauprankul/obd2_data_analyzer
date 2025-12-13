"""
Save View Dialog for OBD2 Viewer.

Provides a modal dialog for naming and saving the current view.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt


class SaveViewDialog(QDialog):
    """Dialog for saving the current view with a name."""
    
    def __init__(self, parent=None, existing_name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Save View")
        self.setModal(True)
        self.setMinimumWidth(350)
        
        self.view_name = ""
        
        self._setup_ui(existing_name)
    
    def _setup_ui(self, existing_name: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Name input
        name_label = QLabel("View Name:")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter a name for this view...")
        self.name_input.setText(existing_name)
        self.name_input.selectAll()
        layout.addWidget(self.name_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        # Focus on input
        self.name_input.setFocus()
    
    def _on_save(self):
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a name for the view.")
            return
        
        # Check for invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(c in name for c in invalid_chars):
            QMessageBox.warning(
                self, "Invalid Name",
                f"View name cannot contain: {' '.join(invalid_chars)}"
            )
            return
        
        self.view_name = name
        self.accept()
    
    def get_name(self) -> str:
        return self.view_name
