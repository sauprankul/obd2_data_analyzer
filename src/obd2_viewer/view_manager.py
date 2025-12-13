"""
View Manager for OBD2 Viewer.

Handles saving and loading of views, including:
- Creating SavedView from current application state
- Restoring application state from SavedView
- Prompting for save on close
- Handling missing file relocation
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from PyQt6.QtWidgets import QMessageBox

from .app_data import (
    SavedView, SavedViewImport, SavedViewMathChannel, SavedViewFilter,
    save_view, load_view, check_view_files
)
from .dialogs import SaveViewDialog, RelocateFilesDialog

if TYPE_CHECKING:
    from .main_window import OBD2MainWindow

logger = logging.getLogger(__name__)


class ViewManager:
    """Manages saving and loading of views for the main window."""
    
    def __init__(self, main_window: 'OBD2MainWindow'):
        self.main_window = main_window
        self._last_saved_state: Optional[dict] = None
        self._current_view_name: Optional[str] = None  # Name of currently loaded/saved view
    
    def _get_current_state_hash(self) -> dict:
        """Get a hashable representation of current view state."""
        mw = self.main_window
        
        if not mw.imports:
            return {}
        
        # Collect imports state
        imports = tuple(
            (imp.file_path, imp.color, imp.time_offset)
            for imp in mw.imports
        )
        
        # Collect math channels state
        math_channels = tuple(sorted(
            (name, ch.get('expression', ''), ch.get('unit', ''))
            for name, ch in mw.math_channels.items()
        ))
        
        # Collect filters state
        filters = tuple(
            (name, mw.filters.get(name, {}).get('expression', ''),
             mw.filters.get(name, {}).get('enabled', True))
            for name in mw.filter_order
        )
        
        # Collect chart visibility (show/hide entire chart)
        chart_visibility = tuple(sorted(
            (ch, control.is_chart_visible())
            for ch, control in mw.channel_controls.items()
        ))
        
        # Collect import visibility per channel
        import_visibility = tuple(sorted(
            (ch, tuple(control.import_visible))
            for ch, control in mw.channel_controls.items()
        ))
        
        return {
            'imports': imports,
            'math_channels': math_channels,
            'filters': filters,
            'filter_order': tuple(mw.filter_order),
            'chart_visibility': chart_visibility,
            'import_visibility': import_visibility,
            'time_range': (mw.chart_widget.current_start, mw.chart_widget.current_end),
            'is_split_mode': mw.is_split_mode,
            'plot_height': mw.chart_widget._base_plot_height
        }
    
    def has_unsaved_changes(self) -> bool:
        """Check if current state differs from last saved state."""
        if self._last_saved_state is None:
            # Never saved - check if there's any data
            return bool(self.main_window.imports)
        
        current = self._get_current_state_hash()
        return current != self._last_saved_state
    
    def mark_as_saved(self):
        """Mark current state as saved."""
        self._last_saved_state = self._get_current_state_hash()
    
    def clear_saved_state(self):
        """Clear saved state (e.g., when loading new data)."""
        self._last_saved_state = None
    
    def prompt_save_view(self) -> bool:
        """Prompt user to save current view.
        
        Returns:
            True to continue (saved or discarded), False to cancel.
        """
        # Skip prompt if no unsaved changes
        if not self.has_unsaved_changes():
            return True
        
        result = QMessageBox.question(
            self.main_window,
            "Save View?",
            "Do you want to save the current view before closing?",
            QMessageBox.StandardButton.Save | 
            QMessageBox.StandardButton.Discard | 
            QMessageBox.StandardButton.Cancel
        )
        
        if result == QMessageBox.StandardButton.Save:
            return self.save_view_dialog()
        elif result == QMessageBox.StandardButton.Discard:
            return True
        else:  # Cancel
            return False
    
    def save_view_dialog(self) -> bool:
        """Show save view dialog.
        
        Returns:
            True if saved successfully or user cancelled dialog, False otherwise.
        """
        mw = self.main_window
        
        if not mw.imports:
            QMessageBox.information(mw, "No Data", "No data loaded to save.")
            return True
        
        dialog = SaveViewDialog(mw, existing_name=self._current_view_name or "")
        if dialog.exec() != SaveViewDialog.DialogCode.Accepted:
            return False
        
        view_name = dialog.get_name()
        view = self.create_saved_view(view_name)
        
        try:
            save_view(view)
            self._current_view_name = view_name  # Remember the name
            self.mark_as_saved()  # Mark state as saved
            QMessageBox.information(mw, "View Saved", f"View '{view_name}' saved successfully.")
            return True
        except Exception as e:
            QMessageBox.critical(mw, "Save Failed", f"Failed to save view: {e}")
            return False
    
    def create_saved_view(self, name: str) -> SavedView:
        """Create a SavedView from current application state."""
        mw = self.main_window
        
        # Collect imports
        imports = []
        for imp in mw.imports:
            imports.append(SavedViewImport(
                file_path=imp.file_path,
                color=imp.color,
                time_offset=imp.time_offset
            ))
        
        # Collect math channels
        math_channels = []
        for ch_name, ch_def in mw.math_channels.items():
            math_channels.append(SavedViewMathChannel(
                name=ch_name,
                expression=ch_def.get('expression', ''),
                inputs=ch_def.get('inputs', {}),
                unit=ch_def.get('unit', '')
            ))
        
        # Collect filters
        filters = []
        for f_name in mw.filter_order:
            f_def = mw.filters.get(f_name, {})
            filters.append(SavedViewFilter(
                name=f_name,
                expression=f_def.get('expression', ''),
                inputs=f_def.get('inputs', {}),
                mode=f_def.get('mode', 'show'),
                buffer_seconds=f_def.get('buffer_seconds', 0.0),
                enabled=f_def.get('enabled', True)
            ))
        
        # Collect chart visibility (whether each chart is shown/hidden)
        chart_visibility = {}
        for channel, control in mw.channel_controls.items():
            chart_visibility[channel] = control.is_chart_visible()
        
        # Collect import visibility per channel
        # Convert int keys to str for JSON compatibility
        channel_visibility = {}
        for channel, control in mw.channel_controls.items():
            channel_visibility[channel] = {str(i): v for i, v in enumerate(control.import_visible)}
        
        return SavedView(
            name=name,
            created_at="",
            modified_at="",
            imports=imports,
            math_channels=math_channels,
            filters=filters,
            filter_order=mw.filter_order.copy(),
            chart_visibility=chart_visibility,
            channel_visibility=channel_visibility,
            time_start=mw.chart_widget.current_start,
            time_end=mw.chart_widget.current_end,
            y_axis_limits={},  # TODO: Implement Y-axis customization
            is_split_mode=mw.is_split_mode,
            plot_height=mw.chart_widget._base_plot_height
        )
    
    def load_saved_view(self, view_path: str) -> bool:
        """Load a saved view from file.
        
        Returns:
            True if loaded successfully, False otherwise.
        """
        mw = self.main_window
        
        try:
            view = load_view(Path(view_path))
        except Exception as e:
            QMessageBox.critical(mw, "Load Failed", f"Failed to load view: {e}")
            return False
        
        # Check for missing files
        missing = check_view_files(view)
        relocated: Dict[str, str] = {}
        skipped: List[str] = []
        
        if missing:
            dialog = RelocateFilesDialog(missing, mw)
            if dialog.exec() != RelocateFilesDialog.DialogCode.Accepted:
                return False
            relocated = dialog.get_relocated_files()
            skipped = dialog.get_skipped_files()
        
        # Clear current state
        self._clear_current_state()
        
        # Build list of files to load with their colors/offsets
        files_to_load = []
        for imp in view.imports:
            file_path = imp.file_path
            
            # Check if relocated
            if file_path in relocated:
                file_path = relocated[file_path]
            elif file_path in skipped:
                continue  # Skip this import
            
            files_to_load.append({
                'path': file_path,
                'color': imp.color,
                'time_offset': imp.time_offset
            })
        
        if not files_to_load:
            QMessageBox.warning(mw, "No Data", "No files could be loaded from this view.")
            return False
        
        # Store view data for restoration after files load
        self._pending_view = view
        self._pending_view_files = files_to_load
        
        # Queue files for loading using main window's queue system
        file_paths = [f['path'] for f in files_to_load]
        mw._pending_files_queue = file_paths
        mw._view_load_callback = self._on_view_files_loaded
        mw._load_next_queued_file()
        
        return True
    
    def _on_view_files_loaded(self):
        """Called after all files from a saved view have been loaded."""
        mw = self.main_window
        view = self._pending_view
        files_info = self._pending_view_files
        
        if not view or not mw.imports:
            return
        
        # Apply colors and offsets to loaded imports
        for i, file_info in enumerate(files_info):
            if i < len(mw.imports):
                mw.imports[i].color = file_info['color']
                mw.imports[i].time_offset = file_info['time_offset']
                mw.chart_widget.update_import_color(i, file_info['color'])
                mw.chart_widget.update_import_offset(i, file_info['time_offset'])
                mw.import_legend.update_offset(i, file_info['time_offset'])
        
        # Restore math channels
        for mc in view.math_channels:
            mw.math_channels[mc.name] = {
                'expression': mc.expression,
                'inputs': mc.inputs,
                'unit': mc.unit
            }
        
        # Apply math channels to compute their data
        if mw.math_channels:
            mw._apply_math_channels_to_imports()
        
        # Restore filters
        mw.filter_order = view.filter_order.copy()
        for f in view.filters:
            mw.filters[f.name] = {
                'expression': f.expression,
                'inputs': f.inputs,
                'mode': f.mode,
                'buffer_seconds': f.buffer_seconds,
                'enabled': f.enabled
            }
        
        # Rebuild channel controls to include math channels
        mw._update_channel_controls_multi(preserve_visibility=False)
        
        # Restore chart visibility (show/hide entire charts)
        for channel, visible in view.chart_visibility.items():
            if channel in mw.channel_controls:
                mw.channel_controls[channel].set_chart_visible(visible)
                mw.chart_widget.set_chart_visible(channel, visible)
        
        # Restore import visibility per channel
        for channel, vis_dict in view.channel_visibility.items():
            if channel in mw.channel_controls:
                control = mw.channel_controls[channel]
                for idx_str, visible in vis_dict.items():
                    idx = int(idx_str)
                    if idx < len(control.import_visible):
                        control.set_import_visible(idx, visible)
                        mw.chart_widget.set_channel_import_visible(channel, idx, visible)
        
        # Restore time range
        mw.chart_widget.set_time_range(view.time_start, view.time_end)
        
        # Restore plot height
        mw.chart_widget._base_plot_height = view.plot_height
        mw.chart_widget._update_plot_heights()
        
        # Restore split mode
        if view.is_split_mode and not mw.is_split_mode:
            mw._toggle_split_mode()
        
        # Update UI
        mw._update_filter_controls()
        mw._sort_channel_controls()
        mw._apply_filters()
        
        # Remember view name for future saves
        self._current_view_name = view.name
        
        # Clear pending view data
        self._pending_view = None
        self._pending_view_files = None
        
        # Mark as saved since we just loaded this view
        self.mark_as_saved()
    
    def _clear_current_state(self):
        """Clear current imports and state."""
        mw = self.main_window
        
        mw.imports.clear()
        mw.math_channels.clear()
        mw.filters.clear()
        mw.filter_order.clear()
        mw.channel_controls.clear()
        
        # Clear chart widget
        for plot in list(mw.chart_widget.plots.values()):
            mw.chart_widget.plots_layout.removeWidget(plot)
            plot.deleteLater()
        mw.chart_widget.plots.clear()
        mw.chart_widget.imports.clear()
        mw.chart_widget.import_colors.clear()
        mw.chart_widget.channel_visibility.clear()
