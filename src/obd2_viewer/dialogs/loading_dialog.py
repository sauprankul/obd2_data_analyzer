"""
Loading dialog with animated GIF spinner.
"""

import os

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QMovie


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
        
        # Load animated GIF from parent directory (native/)
        gif_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'loading.gif')
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
