"""
Dialog for creating or editing a data filter.
"""

import json
import numpy as np
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QGroupBox, QGridLayout, QComboBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal

from .expression_helpers import EXPRESSION_HELP_TEXT, get_math_functions, get_statistical_functions


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
        if test_values is None:
            test_values = {label: np.array([1.0]) for label in self.INPUT_LABELS}
        
        context = {}
        context.update(get_math_functions())
        context.update(get_statistical_functions())
        
        def if_else(condition, true_val, false_val):
            return np.where(condition, true_val, false_val)
        
        context['if_else'] = if_else
        context.update(test_values)
        
        return context
    
    def _validate_expression(self):
        """Validate the boolean expression and update UI."""
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
