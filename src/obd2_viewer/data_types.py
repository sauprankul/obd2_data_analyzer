"""
Data types and background threads for the OBD2 Viewer.
"""

from pathlib import Path
from typing import Dict
from dataclasses import dataclass

from PyQt6.QtCore import QThread, pyqtSignal

from .core.data_loader import OBDDataLoader


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
