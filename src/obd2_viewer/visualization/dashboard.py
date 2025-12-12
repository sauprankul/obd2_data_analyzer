#!/usr/bin/env python3
"""
OBD2 Dashboard Module

Creates and manages the main Dash dashboard for OBD2 data visualization.
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from typing import Dict, List, Optional, Any
import logging

from ..core.data_processor import OBDDataProcessor

logger = logging.getLogger(__name__)

# Configure Plotly
pio.kaleido.scope.mathjax = None


class OBD2Dashboard:
    """
    Main dashboard class for OBD2 data visualization.
    
    This class creates and manages the Dash web application for visualizing
    OBD2 data with interactive controls and real-time updates.
    """
    
    def __init__(self, channels_data: Dict[str, Any], units: Dict[str, str], 
                 display_names: Dict[str, str], app: Optional[dash.Dash] = None):
        """
        Initialize the dashboard.
        
        Args:
            channels_data: Dictionary of DataFrames indexed by channel name
            units: Dictionary mapping channels to their units
            display_names: Dictionary mapping sanitized names to original names
            app: Optional existing Dash app to register callbacks on (for embedding)
        """
        self.channels_data = channels_data
        self.units = units
        self.display_names = display_names
        self.processor = OBDDataProcessor()
        
        # Generate colors for all channels
        self.colors = self.processor.generate_colors(list(channels_data.keys()))
        
        # Time navigation
        self.min_time, self.max_time = self.processor.get_time_range(channels_data)
        self.current_start = self.min_time
        self.current_end = self.max_time
        self.zoom_level = 1.0
        
        # Use provided app or create new one
        self.app = app if app else dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self._owns_app = app is None  # Track if we created the app
        self.layout = None  # Store layout separately
        self.setup_layout()
        self.setup_callbacks()
        
    def setup_layout(self):
        """Setup the main dashboard layout."""
        self.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("OBD2 Data Visualization Dashboard", 
                           className="text-center mb-4 text-primary"),
                    html.Hr()
                ])
            ]),
            
            # Control Panel and Graph
            dbc.Row([
                # Control Panel (Left side)
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Channel Controls", className="card-title mb-3"),
                            
                            # Show/Hide All Buttons
                            html.Div([
                                dbc.Button("Show All", id="btn-show-all", 
                                          color="success", size="sm", className="me-2 mb-3"),
                                dbc.Button("Hide All", id="btn-hide-all", 
                                          color="secondary", size="sm", className="mb-3"),
                                html.Div(id="channel-status", 
                                        style={"fontSize": "12px", "color": "#6c757d"})
                            ]),
                            
                            # Channel Controls (populated immediately)
                            html.Div(self.create_channel_controls(), id="channel-controls-container")
                        ])
                    ], className="h-100")
                ], width=4),
                
                # Graph (Right side)
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            # Time Navigation Controls
                            html.Div([
                                html.H6("Time Navigation", className="mb-2"),
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Start Time (s):"),
                                        dbc.Input(id="start-time-input", type="number", 
                                                 value=self.current_start, size="sm")
                                    ], width=3),
                                    dbc.Col([
                                        html.Label("End Time (s):"),
                                        dbc.Input(id="end-time-input", type="number", 
                                                 value=self.current_end, size="sm")
                                    ], width=3),
                                    dbc.Col([
                                        html.Label("Center Time (s):"),
                                        dbc.Input(id="center-time-input", type="number", 
                                                 size="sm", placeholder="Center")
                                    ], width=3),
                                    dbc.Col([
                                        html.Label("Actions:"),
                                        html.Div([
                                            dbc.Button("←", id="btn-left-30", size="sm", 
                                                      className="me-1"),
                                            dbc.Button("→", id="btn-right-30", size="sm", 
                                                      className="me-1"),
                                            dbc.Button("Reset", id="btn-zoom-reset", 
                                                      size="sm", color="secondary")
                                        ])
                                    ], width=3)
                                ])
                            ], className="mb-3"),
                            
                            # Main Graph
                            dcc.Graph(id="main-graph", style={"height": "600px"}),
                            
                            # Status Bar
                            html.Div(id="status", className="mt-2 text-muted small")
                        ])
                    ])
                ], width=8)
            ]),
            
            # Hidden storage for callback state
            dcc.Store(id="visible-channels-store", data=list(self.channels_data.keys())),
            dcc.Store(id="time-range-store", data=[self.current_start, self.current_end]),
            dcc.Store(id="graph-zoom-store", data=self.zoom_level),
            
            # Hidden trigger with initial value to force callback
            dcc.Interval(id="initial-trigger", interval=1000, n_intervals=0),
            
        ], fluid=True)
        
        # Only set app.layout if we own the app (standalone mode)
        if self._owns_app:
            self.app.layout = self.layout
        
    def setup_callbacks(self):
        """Setup all Dash callbacks."""
        
        # Show/Hide All buttons functionality
        @self.app.callback(
            [Output("channel-controls-container", "children", allow_duplicate=True),
             Output("visible-channels-store", "data", allow_duplicate=True)],
            [Input("btn-show-all", "n_clicks"),
             Input("btn-hide-all", "n_clicks")],
            prevent_initial_call=True
        )
        def update_channel_controls(show_all_clicks, hide_all_clicks):
            """Update channel controls on button clicks."""
            ctx = callback_context
            if not ctx.triggered:
                return self.create_channel_controls(), list(self.channels_data.keys())
            
            trigger_id = ctx.triggered[0]['prop_id']
            
            if "btn-show-all" in trigger_id and show_all_clicks:
                # Show all channels
                return self.create_channel_controls(all_checked=True), list(self.channels_data.keys())
            elif "btn-hide-all" in trigger_id and hide_all_clicks:
                # Hide all channels
                return self.create_channel_controls(all_checked=False), []
            
            return self.create_channel_controls(), list(self.channels_data.keys())
        
        # Main graph update callback
        @self.app.callback(
            [Output("main-graph", "figure"),
             Output("visible-channels-store", "data"),
             Output("time-range-store", "data"),
             Output("graph-zoom-store", "data"),
             Output("status", "children")],
            [Input("initial-trigger", "n_intervals"),
             Input({"type": "channel-checkbox", "index": dash.ALL}, "value"),
             Input("btn-left-30", "n_clicks"),
             Input("btn-right-30", "n_clicks"),
             Input("btn-zoom-reset", "n_clicks"),
             Input("start-time-input", "value"),
             Input("end-time-input", "value"),
             Input("center-time-input", "value"),
             Input("btn-show-all", "n_clicks"),
             Input("btn-hide-all", "n_clicks")],
            [State("visible-channels-store", "data"),
             State("time-range-store", "data"),
             State("graph-zoom-store", "data")]
        )
        def update_graph(n_intervals, channel_values, left_clicks, right_clicks, reset_clicks,
                        start_time, end_time, center_time, show_all_clicks, hide_all_clicks,
                        current_visible_channels, current_time_range, current_zoom):
            
            ctx = callback_context
            
            # Always initialize with all channels
            visible_channels = list(self.channels_data.keys())
            current_start, current_end = self.current_start, self.current_end
            zoom_level = self.zoom_level
            
            # Handle show/hide all buttons
            if ctx.triggered:
                trigger_id = ctx.triggered[0]['prop_id']
                
                if "btn-show-all" in trigger_id and show_all_clicks:
                    visible_channels = list(self.channels_data.keys())
                elif "btn-hide-all" in trigger_id and hide_all_clicks:
                    visible_channels = []
            
            # Handle time navigation
            if ctx.triggered:
                trigger_id = ctx.triggered[0]['prop_id']
                
                if "btn-left-30" in trigger_id and left_clicks:
                    shift = 30.0
                    new_start = max(self.min_time, current_start - shift)
                    new_end = max(self.min_time, current_end - shift)
                    current_start, current_end = new_start, new_end
                    
                elif "btn-right-30" in trigger_id and right_clicks:
                    shift = 30.0
                    new_start = min(self.max_time, current_start + shift)
                    new_end = min(self.max_time, current_end + shift)
                    current_start, current_end = new_start, new_end
                    
                elif "btn-zoom-reset" in trigger_id and reset_clicks:
                    current_start, current_end = self.min_time, self.max_time
                    zoom_level = 1.0
                    
                elif "start-time-input" in trigger_id and start_time is not None:
                    current_start = float(start_time)
                    
                elif "end-time-input" in trigger_id and end_time is not None:
                    current_end = float(end_time)
                    
                elif "center-time-input" in trigger_id and center_time is not None:
                    center = float(center_time)
                    duration = current_end - current_start
                    current_start = max(self.min_time, center - duration/2)
                    current_end = min(self.max_time, center + duration/2)
            
            # Handle channel checkbox changes
            if ctx.triggered and any("channel-checkbox" in str(trigger['prop_id']) for trigger in ctx.triggered):
                if channel_values:
                    visible_channels = []
                    for i, channel_val in enumerate(channel_values):
                        if channel_val and i < len(list(self.channels_data.keys())):
                            channel_name = list(self.channels_data.keys())[i]
                            visible_channels.append(channel_name)
            
            # Create figure
            fig = self.create_figure(visible_channels, current_start, current_end, zoom_level)
            
            # Update status
            status = f"Displaying {len(visible_channels)} channels | Time: {current_start:.1f}s - {current_end:.1f}s | Zoom: {zoom_level:.1f}x"
            
            return fig, visible_channels, [current_start, current_end], zoom_level, status
    
    def create_channel_controls(self, all_checked: bool = True) -> List[html.Div]:
        """
        Create channel control elements.
        
        Args:
            all_checked: Whether all checkboxes should be checked (default: True)
            
        Returns:
            List of HTML elements for channel controls
        """
        controls = []
        
        # Add channel controls for each channel
        for channel in self.channels_data.keys():
            control = self.create_individual_channel_control(channel, all_checked)
            controls.append(control)
        
        return controls
    
    def create_individual_channel_control(self, channel: str, checked: bool = True) -> html.Div:
        """
        Create control for an individual channel.
        
        Args:
            channel: Channel name
            checked: Whether checkbox should be checked
            
        Returns:
            HTML control element
        """
        display_name = self.display_names.get(channel, channel)
        unit = self.units.get(channel, 'unknown')
        
        return html.Div([
            html.Div([
                dbc.Checkbox(
                    id={"type": "channel-checkbox", "index": channel},
                    label=f"{display_name} ({unit})",
                    value=checked,
                    className="mb-2"
                )
            ])
        ], className="mb-3 p-2 border rounded", 
           style={"backgroundColor": "#f8f9fa"})
    
    def create_figure(self, visible_channels: List[str], 
                     start_time: float, end_time: float, 
                     zoom_level: float) -> go.Figure:
        """
        Create the main visualization figure.
        
        Args:
            visible_channels: List of channels to display
            start_time: Start time for data display
            end_time: End time for data display
            zoom_level: Zoom level for figure height
            
        Returns:
            Plotly figure object
        """
        if not visible_channels:
            # Return empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="No channels selected for display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # Filter data by time range
        filtered_data = self.processor.filter_data_by_time(
            self.channels_data, start_time, end_time
        )
        
        # Create subplots
        fig = make_subplots(
            rows=len(visible_channels), cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            subplot_titles=[self.display_names.get(channel, channel) for channel in visible_channels]
        )
        
        # Add traces for each channel
        for i, channel in enumerate(visible_channels, 1):
            if channel not in filtered_data:
                continue
                
            df = filtered_data[channel]
            if 'SECONDS' not in df.columns or 'VALUE' not in df.columns:
                continue
            
            color = self.colors.get(channel, '#1f77b4')
            unit = self.units.get(channel, '')
            
            fig.add_trace(
                go.Scatter(
                    x=df['SECONDS'],
                    y=df['VALUE'],
                    mode='lines',
                    name=f"{self.display_names.get(channel, channel)} ({unit})",
                    line=dict(color=color, width=2),
                    hovertemplate="<b>%{fullData.name}</b><br>" +
                                 "Time: %{x:.2f}s<br>" +
                                 "Value: %{y:.2f}<br>" +
                                 "<extra></extra>"
                ),
                row=i, col=1
            )
        
        # Update layout
        base_height = 250
        fig.update_layout(
            height=base_height * len(visible_channels) * zoom_level,
            showlegend=False,
            hovermode='x unified',
            dragmode=False,
            template='plotly_white',
            margin=dict(r=120)
        )
        
        # Update axes
        for i in range(1, len(visible_channels) + 1):
            fig.update_xaxes(
                title_text="Time (seconds)" if i == len(visible_channels) else "",
                row=i, col=1,
                showgrid=True, gridwidth=2, gridcolor='lightgray',
                fixedrange=True,
                range=[start_time, end_time]
            )
            fig.update_yaxes(
                row=i, col=1,
                showgrid=True, gridwidth=2, gridcolor='lightgray',
                fixedrange=True
            )
        
        return fig
    
    def run(self, debug: bool = True, port: int = 8050, host: str = '0.0.0.0'):
        """
        Run the Dash application.
        
        Args:
            debug: Whether to run in debug mode
            port: Port number to run on
            host: Host address to bind to
        """
        logger.info(f"Starting OBD2 Dashboard on http://{host}:{port}")
        self.app.run(debug=debug, port=port, host=host)
