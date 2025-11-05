#!/usr/bin/env python3
"""
WORKING viewer - simplified and guaranteed to display controls
"""

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from pathlib import Path

class WorkingOBDViewer:
    def __init__(self):
        self.csv_folder_path = Path(__file__).parent.parent / "test"
        self.data = {}
        self.units = {}
        self.colors = {}
        self.load_data()
        
        # Initialize with individual PIDs (no groups initially)
        self.pid_order = list(self.data.keys())
        
        # Start with no groups - all PIDs are individual
        self.groups = {}
        self.pid_groups = {}
        
        self.create_app()
        
    def load_data(self):
        """Load CSV data."""
        csv_files = list(self.csv_folder_path.glob("*.csv"))
        
        for csv_file in csv_files:  # Load ALL files, not just first 5
            try:
                df = pd.read_csv(csv_file, delimiter=';')
                if all(col in df.columns for col in ['SECONDS', 'PID', 'VALUE', 'UNITS']):
                    pid = df['PID'].iloc[0]
                    unit = df['UNITS'].iloc[0]
                    self.data[pid] = df
                    self.units[pid] = unit
                    self.colors[pid] = f'rgb({hash(pid) % 255}, {(hash(pid)*2) % 255}, {(hash(pid)*3) % 255})'
                    print(f"Loaded {pid}")
            except Exception as e:
                print(f"Error: {e}")
                
    def create_pid_controls(self):
        """Create PID controls with individual PIDs and groups."""
        controls = []
        
        # Add new group button at the top
        controls.append(html.Div([
            dbc.Button("+ New Group", id="btn-new-group", color="primary", size="sm"),
            html.Div(id="group-status", style={"marginTop": "5px", "fontSize": "12px", "color": "#6c757d"})
        ], className="mb-3 p-2 border rounded", style={"backgroundColor": "#e3f2fd"}))
        
        # Find individual PIDs (not in any group)
        individual_pids = [pid for pid in self.data.keys() if pid not in self.pid_groups]
        
        # Add individual PIDs first
        for pid in individual_pids:
            pid_control = self.create_individual_pid_control(pid)
            controls.append(pid_control)
        
        # Add group controls
        for group_name in self.groups.keys():
            group_controls = self.create_group_controls(group_name)
            controls.extend(group_controls)
        
        return controls
    
    def create_individual_pid_control(self, pid):
        """Create control for an individual PID."""
        return html.Div([
            # PID checkbox and name
            html.Div([
                dbc.Checkbox(
                    id=f"checkbox-{pid}",
                    label=f"{pid} ({self.units[pid]})",
                    value=True,
                    className="mb-1"
                )
            ], style={"width": "100%"}),
            
            # PID controls: up/down buttons (no remove button for individual PIDs)
            html.Div([
                # Up/down buttons
                html.Div([
                    dbc.Button("↑", id=f"up-{pid}", size="sm", 
                              className="me-1", style={"width": "30px"}),
                    dbc.Button("↓", id=f"down-{pid}", size="sm", 
                              style={"width": "30px"})
                ], style={"display": "inline-block", "verticalAlign": "top"})
                
            ], style={"width": "100%", "marginTop": "5px"})
            
        ], className="mb-2 p-2 border rounded", 
           style={"backgroundColor": "#f8f9fa", "borderLeft": "3px solid #6c757d"})
    
    def create_group_controls(self, group_name):
        """Create controls for a specific group."""
        controls = []
        
        # Group header with name, and up/down/delete buttons
        controls.append(html.Div([
            html.Div([
                html.Div([
                    html.H6(group_name, id={'type': 'group-name', 'index': group_name}, 
                           style={'margin': '0', 'display': 'inline-block', 'cursor': 'pointer', 'color': '#007bff'})
                ], style={'display': 'inline-block', 'verticalAlign': 'top'}),
                
                # Group up/down/delete buttons
                html.Div([
                    dbc.Button("🗑️", id=f"delete-{group_name}", size="sm", 
                              color="danger", className="me-1", style={"width": "35px"}),
                    dbc.Button("↑", id=f"group-up-{group_name}", size="sm", 
                              className="me-1", style={"width": "30px"}),
                    dbc.Button("↓", id=f"group-down-{group_name}", size="sm", 
                              style={"width": "30px"})
                ], style={"display": "inline-block", "float": "right"})
                
            ], className="p-2 border-bottom", style={"backgroundColor": "#f1f8e9"})
            
        ], className="border rounded mb-2"))
        
        # PIDs in this group
        for pid in self.groups[group_name]:
            pid_control = html.Div([
                # PID checkbox and name
                html.Div([
                    dbc.Checkbox(
                        id=f"checkbox-{pid}",
                        label=f"{pid} ({self.units[pid]})",
                        value=True,
                        className="mb-1"
                    )
                ], style={"width": "100%"}),
                
                # PID controls: up/down and remove from group
                html.Div([
                    # Up/down buttons
                    html.Div([
                        dbc.Button("↑", id=f"up-{pid}", size="sm", 
                                  className="me-1", style={"width": "30px"}),
                        dbc.Button("↓", id=f"down-{pid}", size="sm", 
                                  style={"width": "30px"})
                    ], style={"display": "inline-block", "verticalAlign": "top"}),
                    
                    # Remove from group button
                    html.Div([
                        dbc.Button("-", id={'type': 'remove-button', 'index': pid}, size="sm", 
                                  color="danger", style={"width": "30px"})
                    ], style={"display": "inline-block", "verticalAlign": "top", "marginLeft": "5px"})
                    
                ], style={"width": "100%", "marginTop": "5px"})
                
            ], className="p-2 mb-1", style={"backgroundColor": "#fafafa", "borderLeft": "3px solid #4caf50"})
            
            controls.append(pid_control)
        
        # Add PID button at bottom of group
        controls.append(html.Div([
            dbc.Button(f"+ Add PID to {group_name}", id={'type': 'add-button', 'index': group_name}, 
                      size="sm", color="success", style={"width": "100%"})
        ], className="p-2 mb-2", style={"backgroundColor": "#f5f5f5"}))
        
        return controls
        
    def create_app(self):
        """Create the Dash app."""
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], 
                       suppress_callback_exceptions=True)
        
        # Get the new PID controls with arrows and groups
        pid_controls = self.create_pid_controls()
        
        # Create layout with everything explicitly defined
        app.layout = html.Div([
            # Header
            html.H1("OBD Data Viewer", 
                   style={'textAlign': 'center', 'marginBottom': '20px', 'color': '#2c3e50'}),
            
            # Main container - FULL WIDTH
            html.Div([
                # Left sidebar - FIXED WIDTH
                html.Div([
                    # Control panel
                    html.Div([
                        html.H3("CONTROLS", style={'backgroundColor': '#007bff', 'color': 'white', 
                                                  'padding': '10px', 'margin': '0', 'fontSize': '18px'}),
                        
                        html.Div(style={'padding': '15px'}, children=[
                            # PID Selection
                            html.H4("PID Selection & Groups", style={'color': '#495057', 'marginBottom': '10px', 'fontSize': '16px'}),
                            # PID controls container for dynamic updates
                        html.Div(id="pid-controls-container", children=pid_controls, 
                                style={'backgroundColor': '#f8f9fa', 'padding': '12px', 
                                       'borderRadius': '5px', 'maxHeight': '400px', 'overflowY': 'auto'}),
                            
                            html.Hr(style={'margin': '15px 0'}),
                            
                            # Time Controls
                            html.H4("Time Navigation", style={'color': '#495057', 'marginBottom': '10px', 'fontSize': '16px'}),
                            html.Div([
                                html.Div([
                                    html.Button("← -10s", id='btn-left-10', 
                                              className='btn btn-outline-primary btn-sm me-2'),
                                    html.Button("← -5s", id='btn-left-5', 
                                              className='btn btn-outline-primary btn-sm me-2'),
                                    html.Button("← -1s", id='btn-left-1', 
                                              className='btn btn-outline-primary btn-sm'),
                                ], style={'marginBottom': '8px'}),
                                
                                html.Div([
                                    html.Label("Center Time:", style={'marginRight': '8px', 'fontSize': '14px'}),
                                    dcc.Input(type='number', id='center-time', value='5', 
                                             style={'width': '70px'}),
                                ], style={'marginBottom': '8px'}),
                                
                                html.Div([
                                    html.Button("+1s →", id='btn-right-1', 
                                              className='btn btn-outline-primary btn-sm me-2'),
                                    html.Button("+5s →", id='btn-right-5', 
                                              className='btn btn-outline-primary btn-sm me-2'),
                                    html.Button("+10s →", id='btn-right-10', 
                                              className='btn btn-outline-primary btn-sm'),
                                ])
                            ], style={'backgroundColor': '#f8f9fa', 'padding': '12px', 
                                    'borderRadius': '5px'}),
                            
                            html.Hr(style={'margin': '15px 0'}),
                            
                            # Zoom Controls
                            html.H4("Graph Height", style={'color': '#495057', 'marginBottom': '10px', 'fontSize': '16px'}),
                            html.Div([
                                html.Button("Zoom In", id='zoom-in', 
                                          className='btn btn-success btn-sm me-2'),
                                html.Button("Zoom Out", id='zoom-out', 
                                          className='btn btn-warning btn-sm me-2'),
                                html.Button("Reset", id='zoom-reset', 
                                          className='btn btn-secondary btn-sm'),
                            ], style={'backgroundColor': '#f8f9fa', 'padding': '12px', 
                                    'borderRadius': '5px'}),
                            
                            html.Hr(style={'margin': '15px 0'}),
                            
                            # Tick Interval Controls
                            html.H4("X-Axis Zoom", style={'color': '#495057', 'marginBottom': '10px', 'fontSize': '16px'}),
                            html.Div([
                                html.Button("Zoom In", id='tick-zoom-in', 
                                          className='btn btn-info btn-sm me-2'),
                                html.Button("Zoom Out", id='tick-zoom-out', 
                                          className='btn btn-outline-info btn-sm me-2'),
                                html.Button("Reset", id='tick-zoom-reset', 
                                          className='btn btn-outline-secondary btn-sm'),
                                html.Div(id='tick-status', 
                                        style={'marginTop': '8px', 'fontSize': '12px', 'color': '#6c757d'})
                            ], style={'backgroundColor': '#f8f9fa', 'padding': '12px', 
                                    'borderRadius': '5px'})
                        ])
                    ], style={'border': '2px solid #dee2e6', 'borderRadius': '5px', 'height': '100%'})
                ], style={'width': '350px', 'display': 'inline-block', 'verticalAlign': 'top', 
                         'paddingRight': '15px', 'height': 'calc(100vh - 120px)'}),
                
                # Right content - Graphs - TAKES REMAINING SPACE
                html.Div([
                    html.H3("Graphs", style={'color': '#495057', 'marginBottom': '15px', 'fontSize': '18px'}),
                    dcc.Graph(id='main-graph', style={'border': '1px solid #dee2e6', 'borderRadius': '5px', 
                                                     'height': 'calc(100vh - 180px)'})
                ], style={'width': 'calc(100% - 365px)', 'display': 'inline-block', 'verticalAlign': 'top'})
            ], style={'width': '100%', 'height': 'calc(100vh - 60px)', 'margin': '0', 'padding': '0 20px'}),
            
            # Status indicator
            html.Div(id='status', style={'position': 'fixed', 'bottom': '10px', 'right': '10px', 
                                        'backgroundColor': '#28a745', 'color': 'white', 
                                        'padding': '5px 10px', 'borderRadius': '3px', 'fontSize': '12px'}),
            
            # Modal for adding PIDs to groups (with unit selection)
            dbc.Modal([
                dbc.ModalHeader("Add PIDs to Group"),
                dbc.ModalBody([
                    html.H6("Select Unit:", style={"marginBottom": "10px"}),
                    dcc.RadioItems(
                        id='unit-selection-radio',
                        options=[],  # Will be populated dynamically
                        value=None,
                        style={"marginBottom": "20px"}
                    ),
                    html.H6("Select PIDs:", style={"marginBottom": "10px"}),
                    dcc.Checklist(
                        id='pid-selection-checklist',
                        options=[],  # Will be populated dynamically based on unit selection
                        value=[],
                        style={"marginBottom": "20px"}
                    ),
                    html.Div(id='selection-info', style={"fontSize": "12px", "color": "#6c757d"})
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancel", id='cancel-add-pid', color='secondary', className='me-2'),
                    dbc.Button("Add Selected PIDs", id='confirm-add-pid', color='primary')
                ])
            ], id='add-pid-modal', is_open=False, size='lg'),
            
            # Modal for renaming groups
            dbc.Modal([
                dbc.ModalHeader("Rename Group"),
                dbc.ModalBody([
                    html.P("Enter new name for this group:"),
                    dbc.Input(
                        id='group-name-input',
                        type='text',
                        placeholder='Enter new group name...',
                        style={"marginBottom": "20px"}
                    ),
                    html.Div(id='rename-info', style={"fontSize": "12px", "color": "#6c757d"})
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancel", id='cancel-rename-group', color='secondary', className='me-2'),
                    dbc.Button("Rename", id='confirm-rename-group', color='primary')
                ])
            ], id='rename-group-modal', is_open=False, size='md')
        ], style={'margin': '0', 'padding': '0', 'minHeight': '100vh', 'width': '100%'})
        
        # Store for managing group operations
        app.layout.children.append(dcc.Store(id='group-operation-store'))
        
        # Add hidden div to store all checkbox values for the graph callback
        app.layout.children.append(html.Div(id='checkbox-store', style={'display': 'none'}))
        
        # Initial checkboxes (hidden) to satisfy callback requirements
        for pid in self.data.keys():
            app.layout.children.append(
                dcc.Checklist(id=f'hidden-checkbox-{pid}', options=[{'label': pid, 'value': pid}], 
                             value=[pid], style={'display': 'none'})
            )
        
        # Combined callback for all group management operations
        @app.callback(
            Output('pid-controls-container', 'children'),
            Output('group-operation-store', 'data'),
            Output('add-pid-modal', 'is_open'),
            Output('unit-selection-radio', 'options'),
            Output('pid-selection-checklist', 'options'),
            Output('pid-selection-checklist', 'value'),
            Output('selection-info', 'children'),
            Output('rename-group-modal', 'is_open'),
            Output('group-name-input', 'value'),
            Output('rename-info', 'children'),
            Input('btn-new-group', 'n_clicks'),
            Input('cancel-add-pid', 'n_clicks'),
            Input('confirm-add-pid', 'n_clicks'),
            Input({'type': 'add-button', 'index': dash.ALL}, 'n_clicks'),
            Input('unit-selection-radio', 'value'),
            Input({'type': 'group-name', 'index': dash.ALL}, 'n_clicks'),
            Input('cancel-rename-group', 'n_clicks'),
            Input('confirm-rename-group', 'n_clicks'),
            Input({'type': 'remove-button', 'index': dash.ALL}, 'n_clicks'),
            State('add-pid-modal', 'is_open'),
            State('pid-selection-checklist', 'value'),
            State('group-operation-store', 'data'),
            State('rename-group-modal', 'is_open'),
            State('group-name-input', 'value')
        )
        def manage_all_group_operations(new_group_clicks, cancel_clicks, confirm_clicks, 
                                       add_clicks, unit_selection, group_name_clicks, cancel_rename, confirm_rename,
                                       remove_clicks, modal_is_open, selected_pids, store_data, rename_modal_open, rename_input):
            """Handle all group operations in one callback."""
            ctx = dash.callback_context
            
            if not ctx.triggered:
                return self.create_pid_controls(), {}, False, [], [], [], "", False, "", ""
            
            trigger_id = ctx.triggered[0]['prop_id']
            print(f"DEBUG: Callback triggered by: {trigger_id}")
            
            # Handle group name clicks (for renaming)
            if 'group-name' in trigger_id:
                # Parse the trigger ID to extract the group name
                trigger_base = trigger_id.split('.')[0]
                import ast
                try:
                    parsed_trigger = ast.literal_eval(trigger_base)
                    if isinstance(parsed_trigger, dict) and parsed_trigger.get('type') == 'group-name':
                        group_name = parsed_trigger.get('index')
                        print(f"Opening rename modal for group: {group_name}")
                        return self.create_pid_controls(), {"operation": "rename_prompt", "group": group_name}, False, [], [], [], "", True, group_name, f"Renaming group: {group_name}"
                except Exception as e:
                    print(f"Error parsing group name trigger ID: {e}")
            
            # Handle rename modal confirm
            elif trigger_id == 'confirm-rename-group.n_clicks' and confirm_rename:
                print(f"DEBUG: Rename confirm triggered - input: '{rename_input}', store: {store_data}")
                if store_data and 'group' in store_data and rename_input:
                    old_name = store_data['group']
                    new_name = rename_input.strip()
                    
                    if new_name and old_name != new_name:
                        if new_name in self.groups:
                            return self.create_pid_controls(), store_data, False, [], [], [], "", True, rename_input, f"Error: Group '{new_name}' already exists"
                        
                        # Perform the rename
                        pids = self.groups.pop(old_name)
                        self.groups[new_name] = pids
                        
                        # Update PID mappings
                        for pid in pids:
                            self.pid_groups[pid] = new_name
                        
                        print(f"Renamed group '{old_name}' to '{new_name}'")
                        return self.create_pid_controls(), {"operation": "renamed", "old_name": old_name, "new_name": new_name}, False, [], [], [], "", False, "", ""
                    else:
                        return self.create_pid_controls(), store_data, False, [], [], [], "", True, rename_input, "Error: Please enter a valid name"
            
            # Handle rename modal cancel
            elif trigger_id == 'cancel-rename-group' and cancel_rename:
                return self.create_pid_controls(), {}, False, [], [], [], "", False, "", ""
            
            # Handle add button clicks (pattern matching)
            if 'add-button' in trigger_id:
                # Parse the trigger ID to extract the dict
                trigger_base = trigger_id.split('.')[0]
                import ast
                try:
                    parsed_trigger = ast.literal_eval(trigger_base)
                    if isinstance(parsed_trigger, dict) and parsed_trigger.get('type') == 'add-button':
                        group_name = parsed_trigger.get('index')
                        
                        # Get the group's unit (if group has PIDs) or all available units
                        if self.groups.get(group_name):
                            # Group exists, get its unit from first PID
                            group_unit = None
                            for pid in self.groups[group_name]:
                                group_unit = self.units[pid]
                                break
                            
                            if group_unit:
                                # Only show this unit
                                unit_options = [{"label": group_unit, "value": group_unit}]
                                # Get PIDs with this unit that aren't already in the group
                                pid_options = []
                                for pid in self.data.keys():
                                    if (pid not in self.groups.get(group_name, []) and 
                                        self.units[pid] == group_unit):
                                        pid_options.append({"label": pid, "value": pid})
                                
                                info_text = f"Group uses unit: {group_unit}. {len(pid_options)} PIDs available."
                                return self.create_pid_controls(), {"operation": "add_prompt", "group": group_name, "unit": group_unit}, True, unit_options, pid_options, [], info_text, False, "", ""
                            else:
                                # Empty group, show all units
                                unique_units = sorted(set(self.units.values()))
                                unit_options = [{"label": unit, "value": unit} for unit in unique_units]
                                info_text = "Empty group. Select a unit first."
                                return self.create_pid_controls(), {"operation": "add_prompt", "group": group_name}, True, unit_options, [], [], info_text, False, "", ""
                        else:
                            # Group doesn't exist, show all units
                            unique_units = sorted(set(self.units.values()))
                            unit_options = [{"label": unit, "value": unit} for unit in unique_units]
                            info_text = "Select a unit first."
                            return self.create_pid_controls(), {"operation": "add_prompt", "group": group_name}, True, unit_options, [], [], info_text, False, "", ""
                            
                except Exception as e:
                    print(f"Error parsing trigger ID: {e}")
            
            # Handle unit selection (update PID checkboxes)
            elif trigger_id == 'unit-selection-radio.value' and unit_selection:
                if store_data and 'group' in store_data:
                    group_name = store_data['group']
                    
                    # Get PIDs with selected unit that aren't already in the group
                    pid_options = []
                    for pid in self.data.keys():
                        if (pid not in self.groups.get(group_name, []) and 
                            self.units[pid] == unit_selection):
                            pid_options.append({"label": pid, "value": pid})
                    
                    info_text = f"Unit: {unit_selection}. {len(pid_options)} PIDs available."
                    return self.create_pid_controls(), store_data, True, [{"label": unit_selection, "value": unit_selection}], pid_options, [], info_text, False, "", ""
            
            # Handle remove button clicks (pattern matching)
            if 'remove-button' in trigger_id:
                # Parse the trigger ID to extract the PID
                trigger_base = trigger_id.split('.')[0]
                import ast
                try:
                    parsed_trigger = ast.literal_eval(trigger_base)
                    if isinstance(parsed_trigger, dict) and parsed_trigger.get('type') == 'remove-button':
                        pid = parsed_trigger.get('index')
                        print(f"Removing PID from group: {pid}")
                        
                        # Find which group the PID is in
                        current_group = self.pid_groups.get(pid)
                        if current_group and current_group in self.groups:
                            # Remove PID from group
                            self.groups[current_group].remove(pid)
                            # Remove PID from pid_groups mapping
                            del self.pid_groups[pid]
                            
                            print(f"Removed {pid} from group {current_group}")
                            return self.create_pid_controls(), {"operation": "removed", "pid": pid, "from_group": current_group}, False, [], [], [], "", False, "", ""
                        
                except Exception as e:
                    print(f"Error parsing remove trigger ID: {e}")
            
            # Handle regular button clicks
            trigger_id = trigger_id.split('.')[0]
            
            # Handle new group creation
            if trigger_id == 'btn-new-group' and new_group_clicks:
                group_name = f"Group {len(self.groups) + 1}"
                self.groups[group_name] = []
                print(f"Created new group: {group_name}")
                return self.create_pid_controls(), {"operation": "new_group", "name": group_name}, False, [], [], [], "", False, "", ""
            
            # Handle modal cancel
            elif trigger_id == 'cancel-add-pid' and cancel_clicks:
                return self.create_pid_controls(), {}, False, [], [], [], "", False, "", ""
            
            # Handle modal confirm add (multiple PIDs)
            elif trigger_id == 'confirm-add-pid' and confirm_clicks:
                if selected_pids and store_data and 'group' in store_data:
                    group_name = store_data['group']
                    
                    # Validate all selected PIDs have the same unit
                    selected_units = set()
                    for pid in selected_pids:
                        if pid in self.units:
                            selected_units.add(self.units[pid])
                    
                    if len(selected_units) > 1:
                        # Shouldn't happen with our filtering, but just in case
                        print(f"Error: Selected PIDs have different units: {selected_units}")
                        return self.create_pid_controls(), store_data, True, [], [], [], "Error: PIDs have different units", False, "", ""
                    
                    # Check if the unit is compatible with the group
                    group_unit = None
                    if self.groups.get(group_name):
                        for pid in self.groups[group_name]:
                            group_unit = self.units[pid]
                            break
                    
                    if group_unit and selected_units and list(selected_units)[0] != group_unit:
                        print(f"Error: Cannot add PIDs with unit {list(selected_units)[0]} to group with unit {group_unit}")
                        return self.create_pid_controls(), store_data, True, [], [], [], f"Error: Group uses {group_unit}, selected PIDs use {list(selected_units)[0]}", False, "", ""
                    
                    # Add all selected PIDs to the group
                    added_count = 0
                    for pid in selected_pids:
                        # Remove PID from current group if it has one
                        old_group = self.pid_groups.get(pid)
                        if old_group and old_group in self.groups and pid in self.groups[old_group]:
                            self.groups[old_group].remove(pid)
                        
                        # Add to new group
                        if group_name not in self.groups:
                            self.groups[group_name] = []
                        if pid not in self.groups[group_name]:
                            self.groups[group_name].append(pid)
                            self.pid_groups[pid] = group_name
                            added_count += 1
                    
                    print(f"Added {added_count} PIDs to group {group_name}")
                    return self.create_pid_controls(), {"operation": "added", "pids": selected_pids, "group": group_name}, False, [], [], [], "", False, "", ""
            
            return self.create_pid_controls(), {}, False, [], [], [], "", False, "", ""
        
        # Store for dynamic callback triggers
        app.layout.children.append(dcc.Store(id='dynamic-trigger-store', data={'trigger': None}))
        
        # Callbacks to synchronize visible checkboxes to hidden checkboxes
        for pid in self.data.keys():
            @app.callback(
                Output(f'hidden-checkbox-{pid}', 'value'),
                Input(f'checkbox-{pid}', 'value')
            )
            def sync_checkbox_to_hidden(checked_value, pid=pid):
                """Sync visible checkbox to hidden checkbox for graph callback."""
                # Checklist expects array, convert boolean to array
                if checked_value:
                    return [pid]
                else:
                    return []
        
        # Simple callback to update graph
        @app.callback(
            Output('main-graph', 'figure'),
            [Input(f'hidden-checkbox-{pid}', 'value') for pid in self.data.keys()] +
            [Input('zoom-in', 'n_clicks'), Input('zoom-out', 'n_clicks'), Input('zoom-reset', 'n_clicks')] +
            [Input('tick-zoom-in', 'n_clicks'), Input('tick-zoom-out', 'n_clicks'), Input('tick-zoom-reset', 'n_clicks')]
        )
        def update_graph(*all_inputs):
            """Update the graph based on checkbox values and zoom controls."""
            # Split inputs: checkbox values, zoom clicks, and tick zoom clicks
            num_pids = len(self.data.keys())
            checkbox_values = all_inputs[:num_pids]
            zoom_in_clicks, zoom_out_clicks, zoom_reset_clicks = all_inputs[num_pids:num_pids+3]
            tick_zoom_in, tick_zoom_out, tick_zoom_reset = all_inputs[num_pids+3:]
            
            # Track zoom level
            if not hasattr(update_graph, 'zoom_level'):
                update_graph.zoom_level = 1.0
                
            # Track tick interval
            if not hasattr(update_graph, 'x_axis_range'):
                # Get full data range from first PID
                if self.data:
                    first_pid = list(self.data.keys())[0]
                    full_range = self.data[first_pid]['SECONDS'].max() - self.data[first_pid]['SECONDS'].min()
                    update_graph.x_axis_range = [self.data[first_pid]['SECONDS'].min(), self.data[first_pid]['SECONDS'].max()]
                    update_graph.original_range = update_graph.x_axis_range.copy()
                else:
                    update_graph.x_axis_range = [0, 10]
                    update_graph.original_range = [0, 10]
                
            # Handle zoom clicks
            ctx = dash.callback_context
            if ctx.triggered:
                trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
                
                if trigger_id == 'zoom-in' and zoom_in_clicks:
                    update_graph.zoom_level = min(update_graph.zoom_level * 1.2, 3.0)
                elif trigger_id == 'zoom-out' and zoom_out_clicks:
                    update_graph.zoom_level = max(update_graph.zoom_level / 1.2, 0.5)
                elif trigger_id == 'zoom-reset' and zoom_reset_clicks:
                    update_graph.zoom_level = 1.0
                elif trigger_id == 'tick-zoom-in' and tick_zoom_in:
                    # Zoom in x-axis: reduce range by 50% and center it
                    current_range = update_graph.x_axis_range
                    center = (current_range[0] + current_range[1]) / 2
                    current_width = current_range[1] - current_range[0]
                    new_width = max(current_width * 0.5, 0.5)  # Minimum 0.5 second range
                    update_graph.x_axis_range = [center - new_width/2, center + new_width/2]
                elif trigger_id == 'tick-zoom-out' and tick_zoom_out:
                    # Zoom out x-axis: increase range by 100% and center it
                    current_range = update_graph.x_axis_range
                    center = (current_range[0] + current_range[1]) / 2
                    current_width = current_range[1] - current_range[0]
                    new_width = min(current_width * 2.0, update_graph.original_range[1] - update_graph.original_range[0])
                    update_graph.x_axis_range = [center - new_width/2, center + new_width/2]
                elif trigger_id == 'tick-zoom-reset' and tick_zoom_reset:
                    # Reset x-axis to full range
                    update_graph.x_axis_range = update_graph.original_range.copy()
            
            # Get visible PIDs grouped by group AND individual PIDs
            visible_groups = {}
            for group_name in self.groups.keys():
                group_pids = []
                for pid in self.groups[group_name]:
                    pid_index = list(self.data.keys()).index(pid)
                    if checkbox_values[pid_index]:
                        group_pids.append(pid)
                if group_pids:  # Only add groups with visible PIDs
                    visible_groups[group_name] = group_pids
            
            # Get visible individual PIDs (not in any group)
            individual_pids = [pid for pid in self.data.keys() if pid not in self.pid_groups]
            visible_individual_pids = []
            for pid in individual_pids:
                pid_index = list(self.data.keys()).index(pid)
                if checkbox_values[pid_index]:
                    visible_individual_pids.append(pid)
            
            # Combine individual PIDs as their own "groups" for graphing
            for pid in visible_individual_pids:
                visible_groups[pid] = [pid]  # Just use PID name, not "Individual: PID"
            
            if not visible_groups:
                fig = go.Figure()
                fig.add_annotation(text="No PIDs selected", x=0.5, y=0.5, 
                                 xref='paper', yref='paper', showarrow=False)
                return fig
            
            # Create subplots - one per GROUP, not per PID
            fig = make_subplots(rows=len(visible_groups), cols=1, 
                              subplot_titles=list(visible_groups.keys()), vertical_spacing=0.05,
                              specs=[[{"secondary_y": False}] for _ in visible_groups])
            
            for i, (group_name, pids) in enumerate(visible_groups.items()):
                # Add all PIDs in this group to the same subplot
                for pid in pids:
                    df = self.data[pid]
                    fig.add_trace(
                        go.Scatter(x=df['SECONDS'], y=df['VALUE'], 
                                 name=pid, 
                                 line=dict(color=self.colors[pid]),
                                 showlegend=False),  # Disable global legend
                        row=i+1, col=1
                    )
                
                # Set y-axis title for the group (show unit name only once)
                if pids:
                    # All PIDs in group should have same unit, get it from first PID
                    unit = self.units[pids[0]]
                    fig.update_yaxes(title_text=unit, row=i+1, col=1)
                
                # Add custom legend for this subplot if it has multiple PIDs
                if len(pids) > 1:
                    legend_y = 0.95  # Start from top of subplot
                    for pid in pids:
                        # Add legend entry as annotation
                        fig.add_annotation(
                            x=1.01,  # Position to the right of subplot
                            y=legend_y,
                            xref="x domain",
                            yref="y domain",
                            text=f"● {pid}",
                            showarrow=False,
                            font=dict(size=10, color=self.colors[pid]),
                            xanchor="left",
                            yanchor="middle",
                            row=i+1, col=1
                        )
                        legend_y -= 0.05  # Move down for next entry
            
            # Apply zoom to height and disable Plotly zoom
            base_height = 250
            
            fig.update_layout(
                height=base_height * len(visible_groups) * update_graph.zoom_level, 
                showlegend=False,  # Disable global legend since we use custom annotations
                dragmode=False,  # Disable all drag/zoom modes
                xaxis=dict(showgrid=True, gridwidth=2, gridcolor='lightgray'),
                yaxis=dict(showgrid=True, gridwidth=2, gridcolor='lightgray'),
                margin=dict(r=120)  # Add right margin for custom legends
            )
            
            # Update all subplots to disable zoom and sync axes with custom x-axis range
            for i in range(1, len(visible_groups) + 1):
                fig.update_xaxes(
                    title_text="Time (seconds)" if i == len(visible_groups) else "",
                    row=i, col=1,
                    showgrid=True, gridwidth=2, gridcolor='lightgray',
                    fixedrange=True,  # Disable zoom/pan on x-axis
                    range=update_graph.x_axis_range,  # Set custom x-axis range
                    tickmode='linear',
                    tick0=update_graph.x_axis_range[0],
                    dtick=1.0  # Keep 1-second ticks but range changes
                )
                fig.update_yaxes(
                    row=i, col=1,
                    showgrid=True, gridwidth=2, gridcolor='lightgray',
                    fixedrange=True  # Disable zoom/pan on y-axis
                )
            
            return fig
        
        # Status callback
        @app.callback(
            Output('status', 'children'),
            [Input('main-graph', 'figure'), Input('zoom-in', 'n_clicks'), 
             Input('zoom-out', 'n_clicks'), Input('zoom-reset', 'n_clicks')]
        )
        def update_status(fig, zoom_in, zoom_out, zoom_reset):
            # Get current zoom level from the update_graph function
            zoom_level = getattr(update_graph, 'zoom_level', 1.0)
            return f"App Running - {len(self.data)} PIDs loaded - Zoom: {zoom_level:.1f}x"
        
        # Tick status callback
        @app.callback(
            Output('tick-status', 'children'),
            [Input('tick-zoom-in', 'n_clicks'), Input('tick-zoom-out', 'n_clicks'), 
             Input('tick-zoom-reset', 'n_clicks')]
        )
        def update_tick_status(tick_zoom_in, tick_zoom_out, tick_zoom_reset):
            # Get current x-axis range from the update_graph function
            x_range = getattr(update_graph, 'x_axis_range', [0, 10])
            range_width = x_range[1] - x_range[0]
            return f"X-axis range: {x_range[0]:.1f}s - {x_range[1]:.1f}s ({range_width:.1f}s total)"
        
        self.app = app
        
    def run(self):
        """Run the app."""
        print("=" * 60)
        print("WORKING OBD VIEWER STARTING")
        print("=" * 60)
        print(f"Loaded {len(self.data)} PIDs: {list(self.data.keys())}")
        print("Open http://localhost:8052")
        print("If you can't see the controls, there's a browser/system issue")
        print("=" * 60)
        self.app.run(debug=True, port=8052, host='0.0.0.0')

if __name__ == "__main__":
    viewer = WorkingOBDViewer()
    viewer.run()
