#!/usr/bin/env python3
"""
WORKING viewer - simplified and guaranteed to display controls
"""

import dash
from dash import dcc, html, Input, Output
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
                
    def create_app(self):
        """Create the Dash app."""
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        
        # Create PID checkboxes directly in layout
        pid_checkboxes = []
        for pid in self.data.keys():
            checkbox = html.Div([
                dbc.Checkbox(
                    id=f'checkbox-{pid}',
                    label=f"{pid} ({self.units[pid]})",
                    value=True
                )
            ], className="mb-2")
            pid_checkboxes.append(checkbox)
        
        # Create layout with everything explicitly defined
        app.layout = html.Div([
            # Header
            html.H1("OBD Data Viewer - WORKING VERSION", 
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
                            html.H4("PID Selection", style={'color': '#495057', 'marginBottom': '10px', 'fontSize': '16px'}),
                            html.Div(pid_checkboxes, style={'backgroundColor': '#f8f9fa', 
                                                           'padding': '12px', 'borderRadius': '5px', 'maxHeight': '300px', 'overflowY': 'auto'}),
                            
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
                                        'padding': '5px 10px', 'borderRadius': '3px', 'fontSize': '12px'})
        ], style={'margin': '0', 'padding': '0', 'minHeight': '100vh', 'width': '100%'})
        
        # Simple callback to update graph
        @app.callback(
            Output('main-graph', 'figure'),
            [Input(f'checkbox-{pid}', 'value') for pid in self.data.keys()] +
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
            
            # Get visible PIDs
            visible_pids = []
            for i, pid in enumerate(self.data.keys()):
                if checkbox_values[i]:
                    visible_pids.append(pid)
            
            if not visible_pids:
                fig = go.Figure()
                fig.add_annotation(text="No PIDs selected", x=0.5, y=0.5, 
                                 xref='paper', yref='paper', showarrow=False)
                return fig
            
            # Create subplots
            fig = make_subplots(rows=len(visible_pids), cols=1, 
                              subplot_titles=visible_pids, vertical_spacing=0.05)
            
            for i, pid in enumerate(visible_pids):
                df = self.data[pid]
                fig.add_trace(
                    go.Scatter(x=df['SECONDS'], y=df['VALUE'], 
                             name=pid, line=dict(color=self.colors[pid])),
                    row=i+1, col=1
                )
                fig.update_yaxes(title_text=self.units[pid], row=i+1, col=1)
            
            # Apply zoom to height and disable Plotly zoom
            base_height = 250
            fig.update_layout(
                height=base_height * len(visible_pids) * update_graph.zoom_level, 
                showlegend=False,
                dragmode=False,  # Disable all drag/zoom modes
                xaxis=dict(showgrid=True, gridwidth=2, gridcolor='lightgray'),
                yaxis=dict(showgrid=True, gridwidth=2, gridcolor='lightgray')
            )
            
            # Update all subplots to disable zoom and sync axes with custom x-axis range
            for i in range(1, len(visible_pids) + 1):
                fig.update_xaxes(
                    title_text="Time (seconds)" if i == len(visible_pids) else "",
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
