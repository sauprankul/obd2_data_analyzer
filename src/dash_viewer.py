#!/usr/bin/env python3
"""
OBD Data Viewer using Plotly Dash for fully integrated web interface
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import pandas as pd
import numpy as np
import os
from pathlib import Path
import glob
from collections import defaultdict
import colorsys
import base64
import io

class DashOBDViewer:
    """OBD Data Viewer using Plotly Dash for integrated web interface."""
    
    def __init__(self, csv_folder_path=None):
        """
        Initialize the viewer.
        
        Args:
            csv_folder_path: Path to folder containing CSV files
        """
        self.csv_folder_path = csv_folder_path or Path(__file__).parent.parent / "test"
        
        # Data storage
        self.data = {}
        self.units = {}
        self.unit_groups = defaultdict(list)
        self.colors = {}
        self.color_index = 0
        
        # Time navigation
        self.min_time = 0
        self.max_time = 0
        self.current_start = 0
        self.current_end = 0
        self.zoom_level = 1.0
        
        # Global zoom for graph height
        self.global_zoom_level = 1.0
        
        # Load data
        self.load_data()
        
        # Create Dash app
        self.create_app()
        
    def load_data(self):
        """Load data from CSV folder."""
        target_folder = Path(self.csv_folder_path)
        
        if not target_folder.exists():
            print(f"Warning: Folder not found: {target_folder}")
            return
            
        # Find all CSV files
        csv_files = list(target_folder.glob("*.csv"))
        
        if not csv_files:
            print(f"Warning: No CSV files found in {target_folder}")
            return
            
        # Load each CSV file
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, delimiter=';')
                
                # Check if required columns exist
                if all(col in df.columns for col in ['SECONDS', 'PID', 'VALUE', 'UNITS']):
                    pid = df['PID'].iloc[0]
                    unit = df['UNITS'].iloc[0]
                    
                    self.data[pid] = df
                    self.units[pid] = unit
                    self.unit_groups[unit].append(pid)
                    
                    # Assign color
                    self.colors[pid] = self.get_next_color()
                    
                    print(f"Loaded {csv_file.name}: {len(df)} rows, unit: {unit}")
                    
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
                
        if self.data:
            self.update_time_range()
            print(f"Loaded {len(self.data)} PIDs from {len(csv_files)} files")
            
    def get_next_color(self):
        """Get next color in sequence."""
        hue = (self.color_index * 0.618033988749895) % 1  # Golden ratio
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.8)
        color = '#%02x%02x%02x' % tuple(int(c * 255) for c in rgb)
        self.color_index += 1
        return color
        
    def update_time_range(self):
        """Update time range."""
        if not self.data:
            return
            
        all_times = []
        for df in self.data.values():
            all_times.extend(df['SECONDS'].values)
            
        if all_times:
            self.min_time = min(all_times)
            self.max_time = max(all_times)
            self.current_start = self.min_time
            self.current_end = self.max_time
            self.zoom_level = 1.0
            
    def create_app(self):
        """Create the Dash application."""
        # Initialize Dash app with Bootstrap theme
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        
        # Define the layout
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("OBD Data Viewer", className="text-center mb-4"),
                    html.Hr()
                ])
            ]),
            
            # Control Panel
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Controls"),
                        dbc.CardBody([
                            # PID Selection
                            html.H5("PID Selection", className="mb-3"),
                            self.create_pid_checkboxes(),
                            
                            html.Hr(),
                            
                            # Time Navigation
                            html.H5("Time Navigation", className="mb-3"),
                            self.create_time_controls(),
                            
                            html.Hr(),
                            
                            # Graph Height Zoom
                            html.H5("Graph Height", className="mb-3"),
                            self.create_graph_zoom_controls(),
                            
                            html.Hr(),
                            
                            # Data Loading
                            html.H5("Data", className="mb-3"),
                            dcc.Upload(
                                id='upload-data',
                                children=html.Div([
                                    'Drag and Drop or ',
                                    html.A('Select CSV Files')
                                ]),
                                style={
                                    'width': '100%',
                                    'height': '60px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px 0'
                                },
                                multiple=True
                            ),
                            html.Div(id='upload-status')
                        ])
                    ])
                ], width=3),
                
                # Plot Area
                dbc.Col([
                    dcc.Loading(
                        id="loading-spinner",
                        children=[dcc.Graph(id="main-graph")],
                        type="default"
                    )
                ], width=9)
            ]),
            
            # Store components for state
            dcc.Store(id='visible-pids-store', data=list(self.data.keys())),
            dcc.Store(id='time-range-store', data=[self.current_start, self.current_end]),
            dcc.Store(id='graph-zoom-store', data=self.global_zoom_level)
            
        ], fluid=True)
        
        # Define callbacks
        self.setup_callbacks()
        
    def create_pid_checkboxes(self):
        """Create PID checkbox controls."""
        checkboxes = []
        
        for unit, pids in self.unit_groups.items():
            checkboxes.append(html.H6(f"Unit: {unit}", className="mt-3 mb-2"))
            
            for pid in pids:
                checkbox = dbc.Checklist(
                    options=[{"label": pid, "value": pid}],
                    value=[pid],  # All visible by default
                    id={"type": "pid-checkbox", "index": pid},
                    className="mb-1"
                )
                checkboxes.append(checkbox)
                
        return checkboxes
        
    def create_time_controls(self):
        """Create time navigation controls."""
        return html.Div([
            # Navigation buttons
            html.Div([
                # Left buttons
                html.Div([
                    html.Span("←", className="me-2"),
                    dbc.Button("-30m", id="btn-left-1800", size="sm", className="me-1"),
                    dbc.Button("-1m", id="btn-left-60", size="sm", className="me-1"),
                    dbc.Button("-30s", id="btn-left-30", size="sm", className="me-1"),
                    dbc.Button("-10s", id="btn-left-10", size="sm", className="me-1"),
                    dbc.Button("-5s", id="btn-left-5", size="sm", className="me-1"),
                    dbc.Button("-3s", id="btn-left-3", size="sm", className="me-1"),
                    dbc.Button("-1s", id="btn-left-1", size="sm"),
                ], className="d-flex align-items-center mb-2"),
                
                # Center time
                html.Div([
                    html.Label("Center Time:", className="me-2"),
                    dbc.Input(
                        id="center-time-input",
                        type="number",
                        value=int((self.current_start + self.current_end) / 2),
                        size="sm",
                        style={"width": "100px"}
                    )
                ], className="d-flex align-items-center mb-2"),
                
                # Right buttons
                html.Div([
                    html.Span("→", className="me-2"),
                    dbc.Button("+1s", id="btn-right-1", size="sm", className="me-1"),
                    dbc.Button("+3s", id="btn-right-3", size="sm", className="me-1"),
                    dbc.Button("+5s", id="btn-right-5", size="sm", className="me-1"),
                    dbc.Button("+10s", id="btn-right-10", size="sm", className="me-1"),
                    dbc.Button("+30s", id="btn-right-30", size="sm", className="me-1"),
                    dbc.Button("+1m", id="btn-right-60", size="sm", className="me-1"),
                    dbc.Button("+30m", id="btn-right-1800", size="sm"),
                ], className="d-flex align-items-center mb-2"),
                
                # Time range
                html.Div([
                    html.Label("Time Range:", className="me-2"),
                    dbc.Input(
                        id="start-time-input",
                        type="number",
                        value=int(self.current_start),
                        size="sm",
                        style={"width": "80px"}
                    ),
                    html.Label(" to ", className="mx-2"),
                    dbc.Input(
                        id="end-time-input",
                        type="number",
                        value=int(self.current_end),
                        size="sm",
                        style={"width": "80px"}
                    )
                ], className="d-flex align-items-center")
            ])
        ])
        
    def create_graph_zoom_controls(self):
        """Create graph height zoom controls."""
        return html.Div([
            dbc.ButtonGroup([
                dbc.Button("Zoom In", id="btn-zoom-in", size="sm"),
                dbc.Button("Zoom Out", id="btn-zoom-out", size="sm"),
                dbc.Button("Reset", id="btn-zoom-reset", size="sm")
            ]),
            html.Div(id="zoom-status", className="mt-2 small text-muted")
        ])
        
    def setup_callbacks(self):
        """Setup all Dash callbacks."""
        
        # Update graph when any control changes
        @self.app.callback(
            [Output("main-graph", "figure"),
             Output("visible-pids-store", "data"),
             Output("time-range-store", "data"),
             Output("graph-zoom-store", "data"),
             Output("zoom-status", "children")],
            [Input({"type": "pid-checkbox", "index": dash.ALL}, "value"),
             Input("btn-left-1800", "n_clicks"),
             Input("btn-left-60", "n_clicks"),
             Input("btn-left-30", "n_clicks"),
             Input("btn-left-10", "n_clicks"),
             Input("btn-left-5", "n_clicks"),
             Input("btn-left-3", "n_clicks"),
             Input("btn-left-1", "n_clicks"),
             Input("btn-right-1", "n_clicks"),
             Input("btn-right-3", "n_clicks"),
             Input("btn-right-5", "n_clicks"),
             Input("btn-right-10", "n_clicks"),
             Input("btn-right-30", "n_clicks"),
             Input("btn-right-60", "n_clicks"),
             Input("btn-right-1800", "n_clicks"),
             Input("btn-zoom-in", "n_clicks"),
             Input("btn-zoom-out", "n_clicks"),
             Input("btn-zoom-reset", "n_clicks"),
             Input("center-time-input", "value"),
             Input("start-time-input", "value"),
             Input("end-time-input", "value")],
            [State("visible-pids-store", "data"),
             State("time-range-store", "data"),
             State("graph-zoom-store", "data")]
        )
        def update_graph(pid_values, *args):
            """Update the main graph based on all controls."""
            ctx = callback_context
            
            # Get current state
            visible_pids = args[-3] or list(self.data.keys())
            current_start, current_end = args[-2] or [self.current_start, self.current_end]
            global_zoom = args[-1] or self.global_zoom_level
            
            # Handle PID checkbox changes
            if ctx.triggered and any("pid-checkbox" in str(trigger['prop_id']) for trigger in ctx.triggered):
                visible_pids = []
                for pid_val in pid_values:
                    if pid_val:  # pid_val is a list, check if it's not empty
                        visible_pids.extend(pid_val)
                        
            # Handle time shift buttons
            elif ctx.triggered:
                trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
                
                if "btn-left" in trigger_id:
                    shift_seconds = int(trigger_id.split('-')[-1])
                    current_center = (current_start + current_end) / 2
                    new_center = current_center - abs(shift_seconds)
                    window_size = current_end - current_start
                    
                    current_start = new_center - window_size / 2
                    current_end = new_center + window_size / 2
                    
                elif "btn-right" in trigger_id:
                    shift_seconds = int(trigger_id.split('-')[-1])
                    current_center = (current_start + current_end) / 2
                    new_center = current_center + shift_seconds
                    window_size = current_end - current_start
                    
                    current_start = new_center - window_size / 2
                    current_end = new_center + window_size / 2
                    
                elif "btn-zoom-in" in trigger_id:
                    global_zoom = min(global_zoom * 1.2, 3.0)
                    
                elif "btn-zoom-out" in trigger_id:
                    global_zoom = max(global_zoom / 1.2, 0.5)
                    
                elif "btn-zoom-reset" in trigger_id:
                    global_zoom = 1.0
                    
                elif "center-time-input" in trigger_id:
                    new_center = args[-6]  # center-time-input value
                    if new_center is not None:
                        window_size = current_end - current_start
                        current_start = new_center - window_size / 2
                        current_end = new_center + window_size / 2
                        
                elif "start-time-input" in trigger_id or "end-time-input" in trigger_id:
                    new_start = args[-5]  # start-time-input value
                    new_end = args[-4]    # end-time-input value
                    if new_start is not None and new_end is not None and new_start < new_end:
                        current_start = new_start
                        current_end = new_end
                        
            # Keep within bounds
            if hasattr(self, 'min_time'):
                current_start = max(current_start, self.min_time)
                current_end = min(current_end, self.max_time)
                
            # Create the figure
            fig = self.create_figure(visible_pids, current_start, current_end, global_zoom)
            
            # Update status
            zoom_status = f"Zoom: {global_zoom:.1f}x"
            
            return fig, visible_pids, [current_start, current_end], global_zoom, zoom_status
            
        # File upload callback
        @self.app.callback(
            Output("upload-status", "children"),
            Input("upload-data", "contents"),
            State("upload-data", "filename")
        )
        def handle_upload(contents, filenames):
            """Handle file uploads."""
            if contents:
                # For now, just show status
                # In a real implementation, you'd parse the CSV files
                return html.Div([
                    f"Uploaded {len(filenames)} file(s):",
                    html.Ul([html.Li(fname) for fname in filenames])
                ], className="small text-success")
            return ""
            
    def create_figure(self, visible_pids, start_time, end_time, global_zoom):
        """Create the Plotly figure."""
        if not visible_pids:
            # Empty figure
            fig = go.Figure()
            fig.add_annotation(
                text="No PIDs selected",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                font=dict(size=16)
            )
            return fig
            
        # Group visible PIDs by unit
        visible_by_unit = defaultdict(list)
        for pid in visible_pids:
            if pid in self.units:
                visible_by_unit[self.units[pid]].append(pid)
                
        if not visible_by_unit:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                font=dict(size=16)
            )
            return fig
            
        # Calculate subplot layout
        n_units = len(visible_by_unit)
        
        # Create subplots with shared x-axis
        fig = make_subplots(
            rows=n_units, 
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05 / global_zoom,
            subplot_titles=[', '.join(pids) for pids in visible_by_unit.values()]
        )
        
        # Add traces for each PID
        for i, (unit, pids) in enumerate(visible_by_unit.items()):
            for pid in pids:
                if pid in self.data:
                    df = self.data[pid]
                    
                    # Filter data for current time range
                    mask = (df['SECONDS'] >= start_time) & (df['SECONDS'] <= end_time)
                    filtered_df = df[mask]
                    
                    if not filtered_df.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=filtered_df['SECONDS'],
                                y=filtered_df['VALUE'],
                                mode='lines+markers',
                                name=pid,
                                line=dict(color=self.colors.get(pid, 'blue'), width=2),
                                marker=dict(size=4),
                                hovertemplate=f"<b>{pid}</b><br>" +
                                             "Time: %{x:.1f}s<br>" +
                                             "Value: %{y:.2f} {unit}<br>" +
                                             "<extra></extra>"
                            ),
                            row=i+1, col=1
                        )
                        
            # Update y-axis label
            fig.update_yaxes(title_text=unit, row=i+1, col=1)
            
        # Update layout
        fig.update_layout(
            title="OBD Data Viewer",
            height=300 * n_units * global_zoom,
            showlegend=True,
            hovermode='x unified',
            dragmode='zoom',
            template='plotly_white'
        )
        
        # Update x-axis for all subplots
        for i in range(1, n_units + 1):
            fig.update_xaxes(
                title_text="Time (seconds)" if i == n_units else "",  # Only show title on bottom
                row=i, 
                col=1,
                showgrid=True,
                gridwidth=2,
                gridcolor='lightgray',
                showticklabels=True,
                tickmode='linear',
                tick0=0,
                dtick=1  # Show ticks every 1 second
            )
            
        # Update y-axis grid lines
        for i in range(1, n_units + 1):
            fig.update_yaxes(
                row=i, 
                col=1,
                showgrid=True,
                gridwidth=2,
                gridcolor='lightgray'
            )
        
        return fig
        
    def run(self, debug=True, port=8050):
        """Run the Dash application."""
        self.app.run(debug=debug, port=port, host='0.0.0.0')

def main():
    """Main function."""
    # Use test data folder for demo
    test_folder = Path(__file__).parent.parent / "test"
    
    app = DashOBDViewer(csv_folder_path=test_folder)
    
    print("Starting OBD Data Viewer...")
    print(f"Open http://localhost:8050 in your browser")
    print("Press Ctrl+C to stop")
    
    app.run(debug=False, port=8050)

if __name__ == "__main__":
    main()
