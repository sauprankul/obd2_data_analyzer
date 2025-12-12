#!/usr/bin/env python3
"""
Create a simple working dashboard to test the actual issue
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
from obd2_viewer.core.data_loader import OBDDataLoader

def create_simple_dashboard():
    """Create a simple working dashboard."""
    
    print("🚀 Creating Simple Working Dashboard")
    print("=" * 50)
    
    # Load data
    test_csv = Path(__file__).parent / "src/test/nov_4_test_data.csv"
    loader = OBDDataLoader(test_csv.parent)
    channels_data, units = loader.load_csv_files()
    
    print(f"✅ Loaded {len(channels_data)} channels")
    
    # Create display names
    display_names = {}
    for channel in channels_data.keys():
        display_names[channel] = channel.replace('_', ' ').title()
    
    # Create app
    app = dash.Dash(__name__)
    
    # Create initial figure with ALL data
    fig = go.Figure()
    all_channels = list(channels_data.keys())
    
    for channel in all_channels:
        df = channels_data[channel]
        if len(df) > 0:
            fig.add_trace(go.Scatter(
                x=df['SECONDS'],
                y=df['VALUE'],
                mode='lines',
                name=display_names[channel],
                visible=True  # Make all visible by default
            ))
    
    print(f"✅ Created figure with {len(fig.data)} traces")
    
    # Create channel controls
    channel_controls = []
    for channel in all_channels:
        channel_controls.append(
            html.Div([
                dcc.Checklist(
                    id=f"checkbox-{channel}",
                    options=[{"label": f"{display_names[channel]} ({units.get(channel, 'unknown')})", "value": channel}],
                    value=[channel],  # All checked by default
                    inline=False
                )
            ], className="mb-2", style={"padding": "10px", "border": "1px solid #ddd", "margin": "5px"})
        )
    
    print(f"✅ Created {len(channel_controls)} channel controls")
    
    # Simple layout
    app.layout = html.Div([
        html.H1("Simple OBD2 Dashboard", style={"textAlign": "center"}),
        
        html.Div([
            html.H3("Channel Controls"),
            html.Button("Show All", id="show-all-btn", className="btn btn-primary me-2"),
            html.Button("Hide All", id="hide-all-btn", className="btn btn-secondary"),
            html.Div(id="controls-container", children=channel_controls)
        ], style={"width": "30%", "float": "left", "padding": "20px"}),
        
        html.Div([
            html.H3("Graph"),
            dcc.Graph(id="main-graph", figure=fig, style={"height": "80vh"}),
            html.Div(id="status", style={"marginTop": "20px"})
        ], style={"width": "65%", "float": "right", "padding": "20px"}),
        
        # Hidden store for visible channels
        dcc.Store(id="visible-channels-store", data=all_channels)
    ])
    
    # Simple callback to update graph
    @app.callback(
        [Output("main-graph", "figure"),
         Output("status", "children")],
        [Input("show-all-btn", "n_clicks"),
         Input("hide-all-btn", "n_clicks")] + 
        [Input(f"checkbox-{channel}", "value") for channel in all_channels],
        [State("visible-channels-store", "data")]
    )
    def update_graph(show_all_clicks, hide_all_clicks, *args):
        """Update the graph based on channel selections."""
        
        # Get the current visible channels from the checkbox values
        visible_channels = []
        checkbox_values = args[:-1]  # Last element is the state
        
        for i, channel in enumerate(all_channels):
            if i < len(checkbox_values) and checkbox_values[i] and channel in checkbox_values[i]:
                visible_channels.append(channel)
        
        # If no channels selected, return empty figure
        if not visible_channels:
            empty_fig = go.Figure()
            empty_fig.add_annotation(text="No channels selected", 
                                   xref="paper", yref="paper",
                                   x=0.5, y=0.5, showarrow=False,
                                   font=dict(size=20))
            return empty_fig, "No channels selected"
        
        # Create new figure with selected channels
        new_fig = go.Figure()
        
        for channel in visible_channels:
            df = channels_data[channel]
            if len(df) > 0:
                new_fig.add_trace(go.Scatter(
                    x=df['SECONDS'],
                    y=df['VALUE'],
                    mode='lines',
                    name=display_names[channel],
                    visible=True
                ))
        
        status = f"Displaying {len(visible_channels)} channels"
        return new_fig, status
    
    print("✅ Simple dashboard created successfully")
    print(f"📱 Running on http://localhost:8053")
    print("🎯 This should work - test it in browser!")
    
    return app

if __name__ == "__main__":
    app = create_simple_dashboard()
    
    # Run on different port to avoid conflict
    app.run(debug=True, port=8053, host="127.0.0.1")
