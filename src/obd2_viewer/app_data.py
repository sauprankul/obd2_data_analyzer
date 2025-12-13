"""
App data management for OBD2 Viewer.

Handles persistent storage in Documents/OBD2Analyzer folder:
- recent_files.json: List of recently opened CSV files
- views/: Folder containing saved view JSON files
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


def get_app_data_folder() -> Path:
    """Get the OBD2Analyzer folder in user's Documents directory."""
    # Use Windows-specific approach for Documents folder
    try:
        import ctypes.wintypes
        CSIDL_PERSONAL = 5  # Documents folder
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, 0, buf)
        documents = Path(buf.value)
    except Exception:
        # Fallback to expanduser
        documents = Path.home() / "Documents"
    
    app_folder = documents / "OBD2Analyzer"
    return app_folder


def ensure_app_folders() -> Path:
    """Ensure app data folders exist and return the app folder path."""
    app_folder = get_app_data_folder()
    app_folder.mkdir(parents=True, exist_ok=True)
    
    views_folder = app_folder / "views"
    views_folder.mkdir(exist_ok=True)
    
    return app_folder


# --- Recent Files ---

def load_recent_files() -> List[str]:
    """Load recent files list from JSON."""
    app_folder = get_app_data_folder()
    recent_file = app_folder / "recent_files.json"
    
    if not recent_file.exists():
        return []
    
    try:
        with open(recent_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("recent_files", [])
    except Exception as e:
        logger.warning(f"Failed to load recent files: {e}")
        return []


def save_recent_files(files: List[str]):
    """Save recent files list to JSON."""
    app_folder = ensure_app_folders()
    recent_file = app_folder / "recent_files.json"
    
    try:
        with open(recent_file, 'w', encoding='utf-8') as f:
            json.dump({"recent_files": files}, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save recent files: {e}")


# --- Saved Views ---

@dataclass
class SavedViewImport:
    """Represents an import within a saved view."""
    file_path: str
    color: str
    time_offset: float = 0.0


@dataclass
class SavedViewMathChannel:
    """Represents a math channel definition."""
    name: str
    expression: str
    inputs: Dict[str, str]  # {A: channel_name, B: channel_name, ...}
    unit: str


@dataclass
class SavedViewFilter:
    """Represents a filter definition."""
    name: str
    expression: str
    inputs: Dict[str, str]
    mode: str  # 'show' or 'hide'
    buffer_seconds: float
    enabled: bool = True


@dataclass
class SavedView:
    """Complete saved view state."""
    name: str
    created_at: str
    modified_at: str
    
    # Imports
    imports: List[SavedViewImport] = field(default_factory=list)
    
    # Math channels and filters
    math_channels: List[SavedViewMathChannel] = field(default_factory=list)
    filters: List[SavedViewFilter] = field(default_factory=list)
    filter_order: List[str] = field(default_factory=list)
    
    # Chart visibility: {channel_name: bool} - whether the chart is shown
    chart_visibility: Dict[str, bool] = field(default_factory=dict)
    
    # Import visibility per channel: {channel_name: {import_index: bool}}
    channel_visibility: Dict[str, Dict[str, bool]] = field(default_factory=dict)
    
    # Time range
    time_start: float = 0.0
    time_end: float = 100.0
    
    # Y-axis limits per channel: {channel_name: [y_min, y_max]} or None for auto
    y_axis_limits: Dict[str, Optional[List[float]]] = field(default_factory=dict)
    
    # Window state
    is_split_mode: bool = False
    
    # Plot height (base height in pixels)
    plot_height: int = 200
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "imports": [asdict(imp) for imp in self.imports],
            "math_channels": [asdict(mc) for mc in self.math_channels],
            "filters": [asdict(f) for f in self.filters],
            "filter_order": self.filter_order,
            "chart_visibility": self.chart_visibility,
            "channel_visibility": self.channel_visibility,
            "time_start": self.time_start,
            "time_end": self.time_end,
            "y_axis_limits": self.y_axis_limits,
            "is_split_mode": self.is_split_mode,
            "plot_height": self.plot_height,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SavedView':
        """Create from dictionary."""
        return cls(
            name=data.get("name", "Untitled"),
            created_at=data.get("created_at", ""),
            modified_at=data.get("modified_at", ""),
            imports=[SavedViewImport(**imp) for imp in data.get("imports", [])],
            math_channels=[SavedViewMathChannel(**mc) for mc in data.get("math_channels", [])],
            filters=[SavedViewFilter(**f) for f in data.get("filters", [])],
            filter_order=data.get("filter_order", []),
            chart_visibility=data.get("chart_visibility", {}),
            channel_visibility=data.get("channel_visibility", {}),
            time_start=data.get("time_start", 0.0),
            time_end=data.get("time_end", 100.0),
            y_axis_limits=data.get("y_axis_limits", {}),
            is_split_mode=data.get("is_split_mode", False),
            plot_height=data.get("plot_height", 200),
        )


def get_view_filename(name: str) -> str:
    """Convert view name to safe filename."""
    # Replace invalid characters
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
    return f"{safe_name}.json"


def save_view(view: SavedView) -> Path:
    """Save a view to the views folder. Returns the file path."""
    app_folder = ensure_app_folders()
    views_folder = app_folder / "views"
    
    view.modified_at = datetime.now().isoformat()
    if not view.created_at:
        view.created_at = view.modified_at
    
    filename = get_view_filename(view.name)
    view_path = views_folder / filename
    
    try:
        with open(view_path, 'w', encoding='utf-8') as f:
            json.dump(view.to_dict(), f, indent=2)
        logger.info(f"Saved view to {view_path}")
        return view_path
    except Exception as e:
        logger.error(f"Failed to save view: {e}")
        raise


def load_view(view_path: Path) -> SavedView:
    """Load a view from a JSON file."""
    with open(view_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return SavedView.from_dict(data)


def list_saved_views() -> List[Dict[str, Any]]:
    """List all saved views with metadata.
    
    Returns list of dicts with: name, path, created_at, modified_at
    """
    app_folder = get_app_data_folder()
    views_folder = app_folder / "views"
    
    if not views_folder.exists():
        return []
    
    views = []
    for view_file in views_folder.glob("*.json"):
        try:
            with open(view_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            views.append({
                "name": data.get("name", view_file.stem),
                "path": str(view_file),
                "created_at": data.get("created_at", ""),
                "modified_at": data.get("modified_at", ""),
            })
        except Exception as e:
            logger.warning(f"Failed to read view {view_file}: {e}")
    
    # Sort by modified date, newest first
    views.sort(key=lambda v: v.get("modified_at", ""), reverse=True)
    return views


def delete_view(view_path: Path) -> bool:
    """Delete a saved view file."""
    try:
        view_path.unlink()
        return True
    except Exception as e:
        logger.error(f"Failed to delete view {view_path}: {e}")
        return False


def check_view_files(view: SavedView) -> List[str]:
    """Check which import files are missing.
    
    Returns list of missing file paths.
    """
    missing = []
    for imp in view.imports:
        if not Path(imp.file_path).exists():
            missing.append(imp.file_path)
    return missing
