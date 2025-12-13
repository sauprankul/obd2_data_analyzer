"""
Relocate Files Dialog for OBD2 Viewer.

Provides a modal dialog for locating missing CSV files when loading a saved view.
"""

from pathlib import Path
from typing import Dict, List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt


class RelocateFilesDialog(QDialog):
    """Dialog for relocating missing CSV files in a saved view."""
    
    def __init__(self, missing_files: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Locate Missing Files")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        # Map old paths to new paths
        self.relocated_files: Dict[str, str] = {}
        self.missing_files = missing_files.copy()
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Header
        header = QLabel(
            "The following files could not be found. "
            "Please locate each file or skip to continue without it."
        )
        header.setWordWrap(True)
        layout.addWidget(header)
        
        # File list
        self.file_list = QListWidget()
        self._update_file_list()
        layout.addWidget(self.file_list)
        
        # Action buttons for selected file
        action_layout = QHBoxLayout()
        
        locate_btn = QPushButton("Locate Selected...")
        locate_btn.clicked.connect(self._locate_selected)
        action_layout.addWidget(locate_btn)
        
        skip_btn = QPushButton("Skip Selected")
        skip_btn.clicked.connect(self._skip_selected)
        action_layout.addWidget(skip_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # Dialog buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setDefault(True)
        continue_btn.clicked.connect(self._on_continue)
        continue_btn.setStyleSheet("""
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
        btn_layout.addWidget(continue_btn)
        
        layout.addLayout(btn_layout)
    
    def _update_file_list(self):
        self.file_list.clear()
        
        for old_path in self.missing_files:
            if old_path in self.relocated_files:
                # Already relocated
                new_path = self.relocated_files[old_path]
                text = f"✓ {Path(old_path).name} → {Path(new_path).name}"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, old_path)
                item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                # Still missing
                text = f"✗ {Path(old_path).name}"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, old_path)
                item.setForeground(Qt.GlobalColor.red)
            
            item.setToolTip(old_path)
            self.file_list.addItem(item)
    
    def _locate_selected(self):
        current = self.file_list.currentItem()
        if not current:
            QMessageBox.information(self, "No Selection", "Please select a file to locate.")
            return
        
        old_path = current.data(Qt.ItemDataRole.UserRole)
        old_name = Path(old_path).name
        
        new_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Locate {old_name}",
            str(Path(old_path).parent) if Path(old_path).parent.exists() else "",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        
        if new_path:
            self.relocated_files[old_path] = new_path
            self._update_file_list()
    
    def _skip_selected(self):
        current = self.file_list.currentItem()
        if not current:
            return
        
        old_path = current.data(Qt.ItemDataRole.UserRole)
        
        # Remove from missing files (will be skipped)
        if old_path in self.missing_files:
            self.missing_files.remove(old_path)
        if old_path in self.relocated_files:
            del self.relocated_files[old_path]
        
        self._update_file_list()
    
    def _on_continue(self):
        # Check if any files are still unresolved
        unresolved = [f for f in self.missing_files if f not in self.relocated_files]
        
        if unresolved:
            result = QMessageBox.question(
                self,
                "Unresolved Files",
                f"{len(unresolved)} file(s) are still missing and will be skipped. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result != QMessageBox.StandardButton.Yes:
                return
        
        self.accept()
    
    def get_relocated_files(self) -> Dict[str, str]:
        """Get the mapping of old paths to new paths."""
        return self.relocated_files
    
    def get_skipped_files(self) -> List[str]:
        """Get list of files that were skipped (not relocated)."""
        return [f for f in self.missing_files if f not in self.relocated_files]
