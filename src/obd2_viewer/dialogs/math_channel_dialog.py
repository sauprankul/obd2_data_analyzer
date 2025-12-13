"""
Dialog for creating or editing a math channel from an expression.
"""

import json
import numpy as np
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QGroupBox, QGridLayout, QComboBox, QCompleter
)
from PyQt6.QtCore import Qt, pyqtSignal

from .expression_helpers import EXPRESSION_HELP_TEXT, get_math_functions, get_statistical_functions


class MathChannelDialog(QDialog):
    """Dialog for creating or editing a math channel from an expression.
    
    Supports up to 5 input channels (A, B, C, D, E) and provides:
    - Basic math operations: +, -, *, /, **, %
    - Comparison operators: <, >, <=, >=, ==, !=
    - Conditional expressions: if_else(condition, true_val, false_val)
    - Math functions: abs, min, max, sqrt, log, exp, sin, cos, etc.
    - Statistical functions: rolling_avg, rolling_min, rolling_max, delta, etc.
    """
    
    # Signal: (name, expression, inputs_dict_json, unit)
    channel_created = pyqtSignal(str, str, str, str)
    
    # Input labels
    INPUT_LABELS = ['A', 'B', 'C', 'D', 'E']
    
    def __init__(self, available_channels: List[str], available_units: List[str],
                 channel_units: Dict[str, str] = None, edit_data: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        
        self.channel_units = channel_units or {}
        # Sort channels by unit then alphabetically, format with unit suffix
        self.available_channels = available_channels
        self.sorted_channel_items = self._sort_channels_by_unit(available_channels)
        self.edit_mode = edit_data is not None
        self.original_name = edit_data.get('name', '') if edit_data else ''
        
        self.setWindowTitle("Edit Math Channel" if self.edit_mode else "Create Math Channel")
        self.setMinimumWidth(550)
        
        layout = QVBoxLayout(self)
        
        # Channel name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Channel Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., AFR_Calculated")
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
            # Label
            lbl = QLabel(f"Input {label}:" if i == 0 else f"Input {label} (optional):")
            inputs_layout.addWidget(lbl, row, 0)
            
            # Combo box with channels sorted by unit
            combo = QComboBox()
            if i > 0:  # A is required, others optional
                combo.addItem("(None)")
            for display_text, channel_name in self.sorted_channel_items:
                combo.addItem(display_text, channel_name)
            combo.currentTextChanged.connect(self._update_unit_labels)
            inputs_layout.addWidget(combo, row, 1)
            self.input_combos[label] = combo
            
            # Unit label
            unit_lbl = QLabel("")
            unit_lbl.setStyleSheet("color: #666; font-style: italic;")
            unit_lbl.setMinimumWidth(80)
            inputs_layout.addWidget(unit_lbl, row, 2)
            self.input_unit_labels[label] = unit_lbl
        
        layout.addWidget(inputs_group)
        
        # Expression section
        expr_group = QGroupBox("Expression")
        expr_layout = QVBoxLayout(expr_group)
        
        self.expr_input = QLineEdit()
        self.expr_input.setPlaceholderText("e.g., (A / 0.45) * 14.7  or  if_else(A > B, A, B)")
        self.expr_input.textChanged.connect(self._validate_expression)
        expr_layout.addWidget(self.expr_input)
        
        # Help text (shared constant)
        func_help = QLabel(EXPRESSION_HELP_TEXT)
        func_help.setStyleSheet("color: #555; font-size: 8pt;")
        func_help.setWordWrap(True)
        expr_layout.addWidget(func_help)
        
        # Validation status
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: #666; font-size: 9pt;")
        expr_layout.addWidget(self.validation_label)
        
        layout.addWidget(expr_group)
        
        # Unit with autocomplete
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(QLabel("Output Unit:"))
        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("e.g., AFR")
        
        # Setup autocomplete for units
        self.unit_completer = QCompleter(sorted(set(available_units)))
        self.unit_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.unit_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.unit_input.setCompleter(self.unit_completer)
        
        unit_layout.addWidget(self.unit_input)
        layout.addLayout(unit_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_text = "Save" if self.edit_mode else "Create"
        self.create_btn = QPushButton(btn_text)
        self.create_btn.setStyleSheet("background-color: #1976D2; color: white; font-weight: bold;")
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self._create_channel)
        
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
            self.unit_input.setText(edit_data.get('unit', ''))
            
            # Handle both old format (input_a, input_b) and new format (inputs dict)
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
            else:
                # Legacy format
                input_a = edit_data.get('input_a', '')
                if input_a in self.available_channels:
                    combo = self.input_combos['A']
                    for i in range(combo.count()):
                        if combo.itemData(i) == input_a:
                            combo.setCurrentIndex(i)
                            break
                
                input_b = edit_data.get('input_b', '')
                if input_b and input_b in self.available_channels:
                    combo = self.input_combos['B']
                    for i in range(combo.count()):
                        if combo.itemData(i) == input_b:
                            combo.setCurrentIndex(i)
                            break
        
        # Initialize unit labels
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
        # Fallback for (None) or legacy
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
        
        # Re-validate expression when inputs change
        self._validate_expression()
    
    def _on_name_changed(self):
        """Re-validate when name changes."""
        self._validate_expression()
    
    def _get_eval_context(self, test_values: Dict[str, float] = None):
        """Get the evaluation context with all available functions."""
        if test_values is None:
            test_values = {label: 1.0 for label in self.INPUT_LABELS}
        
        # Build context with functions and variables
        context = {}
        context.update(get_math_functions())
        context.update(get_statistical_functions())
        
        # Add if_else for conditionals (works element-wise on arrays)
        def if_else(condition, true_val, false_val):
            """Conditional expression: returns true_val where condition is True, else false_val."""
            return np.where(condition, true_val, false_val)
        
        context['if_else'] = if_else
        
        # Add test values
        context.update(test_values)
        
        return context
    
    def _validate_expression(self):
        """Validate the expression and update UI."""
        expr = self.expr_input.text().strip()
        name = self.name_input.text().strip()
        
        if not expr:
            self.validation_label.setText("")
            self.create_btn.setEnabled(False)
            return
        
        # Check that Input A is selected
        input_a = self._get_channel_from_combo(self.input_combos['A'])
        if not input_a:
            self.validation_label.setText("✗ Input A is required")
            self.validation_label.setStyleSheet("color: #D32F2F; font-size: 9pt;")
            self.create_btn.setEnabled(False)
            return
        
        # Build test values - use arrays to test statistical functions
        test_values = {}
        used_inputs = []
        for label in self.INPUT_LABELS:
            channel = self._get_channel_from_combo(self.input_combos[label])
            if channel:
                test_values[label] = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
                used_inputs.append(label)
            else:
                test_values[label] = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        
        # Try to evaluate with test values
        try:
            context = self._get_eval_context(test_values)
            result = eval(expr, {"__builtins__": {}}, context)
            
            # Handle both scalar and array results
            if isinstance(result, np.ndarray):
                if not np.issubdtype(result.dtype, np.number):
                    raise ValueError("Expression must return numeric values")
                result_str = f"[{result[0]:.2f}, {result[1]:.2f}, ...]" if len(result) > 2 else str(result)
            elif isinstance(result, (int, float)):
                result_str = f"{result:.4f}"
            else:
                raise ValueError("Expression must return a number or array")
            
            inputs_str = ", ".join([f"{l}=[1-5]" for l in used_inputs])
            self.validation_label.setText(f"✓ Valid ({inputs_str} → {result_str})")
            self.validation_label.setStyleSheet("color: #388E3C; font-size: 9pt;")
            self.create_btn.setEnabled(bool(name))
            
        except Exception as e:
            self.validation_label.setText(f"✗ Invalid: {str(e)}")
            self.validation_label.setStyleSheet("color: #D32F2F; font-size: 9pt;")
            self.create_btn.setEnabled(False)
    
    def _create_channel(self):
        """Emit signal to create the channel."""
        name = self.name_input.text().strip()
        expr = self.expr_input.text().strip()
        
        # Collect all inputs
        inputs = {}
        for label in self.INPUT_LABELS:
            channel = self._get_channel_from_combo(self.input_combos[label])
            inputs[label] = channel
        
        unit = self.unit_input.text().strip() or "unit"
        
        # Emit as JSON string for inputs dict
        inputs_json = json.dumps(inputs)
        
        self.channel_created.emit(name, expr, inputs_json, unit)
        self.accept()
