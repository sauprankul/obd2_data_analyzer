#!/usr/bin/env python3
"""
Main OBD2 Viewer Application

Provides the main application interface with file upload, folder selection,
database persistence, and multi-import visualization.
"""

import dash
from dash import dcc, html, Input, Output, State, callback, ALL, MATCH
import dash_bootstrap_components as dbc
import os
import json
import tempfile
import base64
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

from ..core.data_loader import OBDDataLoader
from ..visualization.dashboard import OBD2Dashboard
from ..database import DatabaseManager, ImportRepository, ImportObject

logger = logging.getLogger(__name__)

# Color palette for imports
IMPORT_COLORS = [
    "#1f77b4",  # Blue
    "#ff7f0e",  # Orange  
    "#2ca02c",  # Green
    "#d62728",  # Red
    "#9467bd",  # Purple
    "#8c564b",  # Brown
    "#e377c2",  # Pink
    "#7f7f7f",  # Gray
    "#bcbd22",  # Yellow-green
    "#17becf",  # Cyan
]


class OBD2ViewerApp:
    """
    Main application class for the OBD2 Data Viewer.
    
    This class provides the complete application interface including
    file upload, data loading, and the visualization dashboard.
    """
    
    def __init__(self, cache_file: Optional[str] = None):
        """
        Initialize the main application.
        
        Args:
            cache_file: Path to the recent folders cache file
        """
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], 
                           suppress_callback_exceptions=True)
        
        # Setup cache file
        if cache_file:
            self.cache_file = Path(cache_file)
        else:
            self.cache_file = Path(__file__).parent.parent.parent.parent / "recent_folders.json"
        
        # Database
        self.db = DatabaseManager()
        self.import_repo = ImportRepository(self.db)
        self.db_available = self._check_db_connection()
        
        # Application state
        self.recent_folders = self.load_recent_folders()
        self.current_data_path = None
        self.obd_dashboard = None
        
        # Multi-import state: {import_id: {channels_data, units, color, name}}
        self.loaded_imports: Dict[str, Dict] = {}
        self.current_import_id: Optional[str] = None
        
        # Setup application
        self.setup_layout()
        self.setup_callbacks()
    
    def _check_db_connection(self) -> bool:
        """Check if database is available."""
        try:
            return self.db.test_connection()
        except Exception as e:
            logger.warning(f"Database not available: {e}")
            return False
        
    def load_recent_folders(self) -> List[str]:
        """
        Load recent folders from cache file.
        
        Returns:
            List of recent folder paths
        """
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading recent folders: {e}")
        return []
    
    def save_recent_folders(self):
        """Save recent folders to cache file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.recent_folders, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving recent folders: {e}")
    
    def add_to_recent_folders(self, folder_path: str):
        """
        Add a folder to recent folders cache.
        
        Args:
            folder_path: Path to add to recent folders
        """
        # Remove if already exists
        if folder_path in self.recent_folders:
            self.recent_folders.remove(folder_path)
        
        # Add to beginning
        self.recent_folders.insert(0, folder_path)
        
        # Keep only last 10 folders
        self.recent_folders = self.recent_folders[:10]
        
        self.save_recent_folders()
    
    def validate_data_directory(self, directory_path: str) -> tuple[bool, str]:
        """
        Validate that directory contains valid OBD2 CSV files.
        
        Args:
            directory_path: Path to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not os.path.exists(directory_path):
            return False, "Directory does not exist"
        
        loader = OBDDataLoader(directory_path)
        return loader.validate_data_directory()
    
    def setup_layout(self):
        """Setup the main application layout."""
        self.app.layout = html.Div([
            dcc.Location(id='url', refresh=False),
            html.Div(id='page-content')
        ])
    
    def create_start_page(self) -> html.Div:
        """
        Create the start page with file upload, saved imports, and recent folders.
        
        Returns:
            HTML div for the start page
        """
        # Get saved imports from database
        saved_imports_section = self._create_saved_imports_section()
        
        # Recent folders buttons
        recent_folders_buttons = []
        if self.recent_folders:
            recent_folders_buttons = [
                html.H5("Recent Folders:", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            os.path.basename(folder) if os.path.basename(folder) else folder,
                            id={'type': 'recent-folder-btn', 'index': i},
                            color="outline-primary",
                            className="me-2 mb-2",
                            size="sm",
                            style={'textOverflow': 'ellipsis', 'maxWidth': '200px'}
                        )
                    ], width="auto")
                    for i, folder in enumerate(self.recent_folders)
                ])
            ]
        
        # Database status indicator
        db_status = dbc.Badge(
            "Database Connected" if self.db_available else "Database Offline",
            color="success" if self.db_available else "warning",
            className="ms-2"
        )
        
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1(["OBD2 Data Visualization Tool", db_status], 
                           className="text-center mb-4 text-primary"),
                    html.H4("Compare and analyze OBD2 CSV data from vehicles", 
                           className="text-center mb-4 text-muted"),
                    html.Hr()
                ])
            ]),
            
            dbc.Row([
                # Left column: Upload new data
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Upload New Data", className="card-title"),
                            html.P("Select CSV files containing OBD2 sensor data:", 
                                  className="card-text"),
                            
                            # Import name input
                            dbc.InputGroup([
                                dbc.InputGroupText("Import Name:"),
                                dbc.Input(id='import-name-input', 
                                         placeholder="e.g., Nov 4 Highway Run",
                                         type="text")
                            ], className="mb-3"),
                            
                            # File upload area
                            html.Div([
                                dcc.Upload(
                                    id='csv-upload',
                                    children=html.Div([
                                        '📁 Drag and Drop or Click to Select CSV Files'
                                    ]),
                                    style={
                                        'width': '100%',
                                        'height': '80px',
                                        'lineHeight': '80px',
                                        'borderWidth': '2px',
                                        'borderStyle': 'dashed',
                                        'borderRadius': '5px',
                                        'textAlign': 'center',
                                        'margin': '10px 0',
                                        'backgroundColor': '#fafafa',
                                        'color': '#666'
                                    },
                                    multiple=True
                                )
                            ], className="mb-3"),
                            
                            # Selected files display
                            html.Div(id='selected-files-display', 
                                    className="mb-3 p-2 border rounded",
                                    style={"minHeight": "60px", "backgroundColor": "#f8f9fa"},
                                    children="No files selected"),
                            
                            # Validation status
                            html.Div(id='folder-validation', className="mb-3"),
                            
                            # Load button
                            dbc.Button("🚀 Load Data & Start Visualization", 
                                      id="load-data-btn", 
                                      color="primary", 
                                      size="lg", 
                                      className="w-100 mb-3"),
                        ])
                    ])
                ], width=6),
                
                # Right column: Saved imports
                dbc.Col([
                    saved_imports_section
                ], width=6)
            ], justify="center", className="mt-4"),
            
            # Instructions section
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📋 Instructions", className="card-title"),
                            html.Ul([
                                html.Li("Upload CSV files or select from saved imports"),
                                html.Li("Multi-channel CSVs (like Car Scanner exports) are supported"),
                                html.Li("Imports are saved to database for future use"),
                                html.Li("Load multiple imports to compare data side-by-side"),
                                html.Li("Same channels from different imports appear on the same graph")
                            ])
                        ])
                    ], className="mt-3")
                ], width=12)
            ], justify="center")
            
        ], fluid=True)
    
    def _create_saved_imports_section(self) -> dbc.Card:
        """Create the saved imports card section."""
        if not self.db_available:
            return dbc.Card([
                dbc.CardBody([
                    html.H4("Saved Imports", className="card-title"),
                    dbc.Alert("Database not available. Start PostgreSQL with: docker-compose up -d", 
                             color="warning")
                ])
            ])
        
        try:
            imports = self.import_repo.get_all_imports()
        except Exception as e:
            logger.error(f"Error loading imports: {e}")
            imports = []
        
        if not imports:
            import_items = [html.P("No saved imports yet. Upload a CSV to get started!", 
                                  className="text-muted")]
        else:
            import_items = []
            for i, imp in enumerate(imports[:10]):  # Show last 10
                color = IMPORT_COLORS[i % len(IMPORT_COLORS)]
                import_items.append(
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Div(
                                        style={"width": "12px", "height": "12px", 
                                               "backgroundColor": color, "borderRadius": "50%",
                                               "display": "inline-block", "marginRight": "8px"}
                                    ),
                                    html.Strong(imp.name),
                                    html.Br(),
                                    html.Small(f"{imp.channel_count} channels • {imp.total_data_points:,} points",
                                              className="text-muted")
                                ], width=8),
                                dbc.Col([
                                    dbc.Button("Load", 
                                              id={'type': 'load-import-btn', 'index': str(imp.id)},
                                              color="primary", size="sm", className="me-1"),
                                    dbc.Button("🗑️", 
                                              id={'type': 'delete-import-btn', 'index': str(imp.id)},
                                              color="danger", size="sm", outline=True)
                                ], width=4, className="text-end")
                            ])
                        ], className="py-2")
                    ], className="mb-2")
                )
        
        return dbc.Card([
            dbc.CardBody([
                html.H4("Saved Imports", className="card-title"),
                html.Div(import_items, id="saved-imports-list", 
                        style={"maxHeight": "400px", "overflowY": "auto"})
            ])
        ])
    
    def create_viewer_page(self) -> html.Div:
        """
        Create the visualization page.
        
        Returns:
            HTML div for the viewer page
        """
        if self.obd_dashboard:
            return self.obd_dashboard.layout
        else:
            return dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.H1("No Data Loaded", className="text-center mt-5"),
                        html.P("Please go back and load OBD2 data files.", 
                              className="text-center")
                    ])
                ])
            ], fluid=True)
    
    def setup_callbacks(self):
        """Setup application callbacks."""
        
        # Page routing
        @self.app.callback(
            Output('page-content', 'children'),
            Input('url', 'pathname')
        )
        def display_page(pathname):
            if pathname == '/viewer' and self.obd_dashboard:
                return self.create_viewer_page()
            else:
                return self.create_start_page()
        
        # File selection display
        @self.app.callback(
            Output('selected-files-display', 'children'),
            Input('csv-upload', 'contents'),
            State('csv-upload', 'filename')
        )
        def display_selected_files(contents, filenames):
            if contents and filenames:
                file_list = []
                for filename in filenames:
                    if filename.endswith('.csv'):
                        file_list.append(html.Div(f"📄 {filename}", className="mb-1"))
                
                if file_list:
                    return [
                        html.Div(f"Selected {len(file_list)} CSV files:", 
                                className="mb-2 fw-bold text-success"),
                        *file_list
                    ]
                else:
                    return html.Div("❌ No CSV files found", 
                                  className="text-warning")
            else:
                return "No files selected"
        
        # File validation
        @self.app.callback(
            Output('folder-validation', 'children'),
            Input('csv-upload', 'contents'),
            State('csv-upload', 'filename')
        )
        def validate_files(contents, filenames):
            if contents and filenames:
                csv_files = [f for f in filenames if f.endswith('.csv')]
                if csv_files:
                    return dbc.Alert(f"✅ Ready to load {len(csv_files)} CSV files", 
                                   color="success", dismissable=True)
                else:
                    return dbc.Alert("❌ No CSV files found in selection", 
                                   color="warning", dismissable=True)
            else:
                return ""
        
        # Load data and navigate to viewer
        @self.app.callback(
            Output('url', 'pathname'),
            Input('load-data-btn', 'n_clicks'),
            State('csv-upload', 'contents'),
            State('csv-upload', 'filename'),
            State('import-name-input', 'value'),
            prevent_initial_call=True
        )
        def load_data(n_clicks, contents, filenames, import_name):
            if n_clicks and contents and filenames:
                csv_files = [(content, filename) for content, filename in zip(contents, filenames) 
                           if filename.endswith('.csv')]
                
                if csv_files:
                    try:
                        # Create temporary directory and save files
                        temp_dir = tempfile.mkdtemp()
                        self.current_data_path = temp_dir
                        
                        # Calculate total file size
                        total_size = 0
                        
                        # Save uploaded files to temp directory
                        for content, filename in csv_files:
                            # Decode base64 content
                            content_type, content_string = content.split(',')
                            decoded = base64.b64decode(content_string)
                            total_size += len(decoded)
                            
                            # Save to file
                            filepath = os.path.join(temp_dir, filename)
                            with open(filepath, 'wb') as f:
                                f.write(decoded)
                            logger.info(f"Saved file: {filepath}")
                        
                        # Generate import name if not provided
                        if not import_name:
                            import_name = csv_files[0][1].replace('.csv', '') if len(csv_files) == 1 else f"Import {len(self.loaded_imports) + 1}"
                        
                        # Load data and save to database
                        self.create_dashboard_from_directory(
                            temp_dir, 
                            import_name=import_name,
                            file_size=total_size,
                            original_filename=csv_files[0][1] if csv_files else None
                        )
                        
                        return '/viewer'
                        
                    except Exception as e:
                        logger.error(f"Error loading data: {e}")
                        return '/'
                else:
                    return '/'
            
            return '/'
        
        # Load saved import from database
        @self.app.callback(
            Output('url', 'pathname', allow_duplicate=True),
            Input({'type': 'load-import-btn', 'index': ALL}, 'n_clicks'),
            prevent_initial_call=True
        )
        def load_saved_import(n_clicks):
            if not any(n_clicks):
                return dash.no_update
            
            # Find which button was clicked
            ctx = dash.callback_context
            if not ctx.triggered:
                return dash.no_update
            
            triggered_id = ctx.triggered[0]['prop_id']
            # Extract import ID from the pattern-matched ID
            import json as json_module
            try:
                id_dict = json_module.loads(triggered_id.split('.')[0])
                import_id = id_dict['index']
            except:
                return dash.no_update
            
            try:
                # Load from database
                import_obj = self.import_repo.get_import(uuid.UUID(import_id))
                if not import_obj:
                    logger.error(f"Import {import_id} not found")
                    return '/'
                
                channels_data, units = self.import_repo.get_import_channels(uuid.UUID(import_id))
                
                # Create display names
                display_names = {ch: ch.replace('_', ' ').title() for ch in channels_data.keys()}
                
                # Assign color
                color_idx = len(self.loaded_imports) % len(IMPORT_COLORS)
                color = IMPORT_COLORS[color_idx]
                
                # Store in loaded imports
                self.loaded_imports[import_id] = {
                    'name': import_obj.name,
                    'channels_data': channels_data,
                    'units': units,
                    'display_names': display_names,
                    'color': color,
                }
                self.current_import_id = import_id
                
                # Create dashboard
                self.obd_dashboard = OBD2Dashboard(
                    channels_data, units, display_names, app=self.app
                )
                
                logger.info(f"Loaded import '{import_obj.name}' with {len(channels_data)} channels")
                return '/viewer'
                
            except Exception as e:
                logger.error(f"Error loading import: {e}")
                return '/'
        
        # Delete import from database
        @self.app.callback(
            Output('page-content', 'children', allow_duplicate=True),
            Input({'type': 'delete-import-btn', 'index': ALL}, 'n_clicks'),
            prevent_initial_call=True
        )
        def delete_import(n_clicks):
            if not any(n_clicks):
                return dash.no_update
            
            ctx = dash.callback_context
            if not ctx.triggered:
                return dash.no_update
            
            triggered_id = ctx.triggered[0]['prop_id']
            import json as json_module
            try:
                id_dict = json_module.loads(triggered_id.split('.')[0])
                import_id = id_dict['index']
            except:
                return dash.no_update
            
            try:
                self.import_repo.delete_import(uuid.UUID(import_id))
                logger.info(f"Deleted import {import_id}")
            except Exception as e:
                logger.error(f"Error deleting import: {e}")
            
            # Refresh the page
            return self.create_start_page()
        
        # Recent folder selection
        @self.app.callback(
            Output('csv-upload', 'filename'),
            Input({'type': 'recent-folder-btn', 'index': dash.ALL}, 'n_clicks'),
            prevent_initial_call=True
        )
        def select_recent_folder(n_clicks):
            return dash.no_update
    
    def create_dashboard_from_directory(
        self, 
        directory_path: str,
        import_name: Optional[str] = None,
        file_size: int = 0,
        original_filename: Optional[str] = None
    ):
        """
        Create OBD2 dashboard from directory of CSV files.
        
        Args:
            directory_path: Path to directory containing CSV files
            import_name: Name for this import
            file_size: Size of uploaded file(s) in bytes
            original_filename: Original filename
        """
        try:
            # Load data using the data loader
            loader = OBDDataLoader(directory_path)
            channels_data, units = loader.load_csv_files()
            
            # Create display names mapping
            display_names = {}
            for channel in channels_data.keys():
                display_names[channel] = channel.replace('_', ' ').title()
            
            # Save to database if available
            import_id = None
            if self.db_available:
                try:
                    import_obj = self.import_repo.create_import(
                        name=import_name or "Unnamed Import",
                        channels_data=channels_data,
                        units_mapping=units,
                        original_filename=original_filename,
                        file_size_bytes=file_size,
                    )
                    import_id = str(import_obj.id)
                    logger.info(f"Saved import to database: {import_id}")
                except Exception as e:
                    logger.error(f"Failed to save to database: {e}")
            
            # Assign color for this import
            color_idx = len(self.loaded_imports) % len(IMPORT_COLORS)
            color = IMPORT_COLORS[color_idx]
            
            # Store in loaded imports
            if import_id:
                self.loaded_imports[import_id] = {
                    'name': import_name,
                    'channels_data': channels_data,
                    'units': units,
                    'display_names': display_names,
                    'color': color,
                }
                self.current_import_id = import_id
            
            # Create dashboard - pass main app so callbacks register on it
            self.obd_dashboard = OBD2Dashboard(channels_data, units, display_names, app=self.app)
            
            logger.info(f"Created dashboard with {len(channels_data)} channels from {directory_path}")
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            self.obd_dashboard = None
    
    def run(self, debug: bool = True, port: int = 8052):
        """
        Run the main application.
        
        Args:
            debug: Whether to run in debug mode
            port: Port number to run on
        """
        logger.info(f"Starting OBD2 Viewer Application on http://localhost:{port}")
        self.app.run(debug=debug, port=port)


def main():
    """Main function to run the OBD2 Viewer application."""
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and run application
    app = OBD2ViewerApp()
    app.run()


if __name__ == '__main__':
    main()
