# OBD2 Data Visualization Tool

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Windows application for visualizing and comparing CSV data. Built with PyQt6 and PyQtGraph for high-performance chart rendering. Built for the purpose of comparing OBDII data, but can be used for anything.

## Features & User Guide

### Data Import

- **CSV File Loading**: Open single or multiple CSV files via File menu or drag-and-drop
- **Multi-Channel CSV Support**: Handles interleaved multi-channel data (Car Scanner format) - automatically separates channels
- **Past Imports**: Home screen shows recently opened files for quick access
  - Double-click to reopen
  - Ctrl+Click for multi-select, then "Open Selected" to load multiple files at once
  - Clear History button to reset
- **Add Import**: Load additional CSV files to compare against the current data

### Visualization

- **Individual Channel Plots**: Each channel displayed on its own graph with synchronized X-axis
- **Multi-Import Overlay**: Same channels from different files plotted on the same graph with different colors
- **Click-to-Position Crosshair**: Click anywhere on a chart to see exact values from all imports at that time
- **Channel Title Values**: Each chart title shows the current value at the crosshair position
- **Adjustable Graph Heights**: Taller/Shorter buttons adjust all chart heights by 5% increments
- **LOD Optimization**: Level-of-detail downsampling (max 2000 points) for smooth performance with large datasets
- **Scroll Wheel**: Scrolls the graph area vertically
- **Ctrl+Scroll**: Zooms X-axis in/out centered on current view

### Time Navigation

Located in the sidebar:
- **Start/End Time Inputs**: Directly set the visible time range
- **Center Time + Go**: Jump to a specific time
- **Navigation Buttons**: ±0.1s, ±0.5s, ±1s, ±5s, ±15s, ±30s, ±1min, ±5min
- **Zoom In/Out**: Reduce/increase time range by 10% (5% each side)
  - Zoom In disabled when range ≤ 10 seconds
  - Zoom Out disabled when showing full data range
- **Reset View**: Red button in center returns to full data range

### Channel Visibility

In the sidebar below time navigation:
- **Per-Import Checkboxes**: Each channel has checkboxes for each loaded CSV
- **Show All / Hide All**: Quick toggle buttons
- **Dynamic Sorting**: Selected channels appear at top, sorted by unit then alphabetically
- **Color Indicators**: Small colored dot shows which import each checkbox controls

### Import Management

In the "Imports" section of the sidebar:
- **Color Legend**: Each import has a distinct color (click the color dot to change it)
- **Duration Display**: Shows total time span of each import
- **Time Offset**: Shows offset relative to base import (first loaded)
- **Sync Button**: Opens synchronization dialog for non-base imports

### Time Synchronization

When comparing multiple CSV files:
- **Base Import**: First loaded file is the reference (offset = 0)
- **Synchronize Dialog**: Click "Sync" button next to any additional import
  - Adjust time offset with ±0.1s to ±5min buttons
  - Or type offset directly
  - Charts update in real-time as you adjust

### Math Channels

Create calculated channels from existing data:
- **Create Math Channel Button**: Opens the math channel dialog
- **Up to 5 Inputs**: Select channels A through E from dropdowns
- **Expression Field**: Python-style math expressions like `(A/0.45) * 14.7` or `A + B * C`
- **Real-time Validation**: Expression must evaluate to a number
- **Unit Selection**: Autocomplete from existing units
- **Edit Button**: Modify existing math channels

**Available Functions:**
- Basic: `abs`, `min`, `max`, `sqrt`, `log`, `log10`, `exp`, `pow`
- Trig: `sin`, `cos`, `tan`
- Rounding: `floor`, `ceil`, `round`
- Statistical: `rolling_avg(X, seconds)`, `rolling_min`, `rolling_max`, `delta`, `cumsum`
- Clipping: `clip(X, min, max)`
- Array-wide: `np_min`, `np_max`, `np_mean`, `np_std`
- Conditionals: `if_else(condition, true_val, false_val)`
- Constants: `pi`, `e`
- Comparisons: `<`, `>`, `<=`, `>=`, `==`, `!=`

### Data Filters

Show or hide data based on conditions:
- **Create Filter Button**: Opens filter dialog
- **Filter Name**: Required identifier
- **Boolean Expression**: Must evaluate to True/False (e.g., `A > 100`)
- **Show/Hide Mode**: 
  - Show (👁): Display only matching data
  - Hide (🚫): Hide matching data
- **Time Buffer**: ±0.1s to ±10min around each match point
- **Filter Precedence**: Top filter = highest precedence (use up/down buttons to reorder)
- **Cross-Import Sync**: If any import matches, all imports show/hide that time range (respects offsets)
- **Enable/Disable**: Checkbox to toggle each filter without deleting

### Window Layout

- **Resizable Sidebar**: Drag the splitter between sidebar and charts
- **Split Window Mode**: View menu → Detach sidebar to separate window (useful for dual monitors)
- **Persistence**: Window size, position, and splitter ratio saved between sessions

## Data Format

The tool expects semicolon-delimited CSV files with these columns:

| Column | Required | Description |
|--------|----------|-------------|
| SECONDS | Yes | Timestamp in seconds |
| VALUE | Yes | Sensor reading |
| UNITS | Yes | Unit of measurement (e.g., "rpm", "°F") |
| PID | Yes | Channel/sensor name |

**Example (Car Scanner format):**
```csv
SECONDS;VALUE;UNITS;PID
0.0;800;rpm;Engine RPM
0.0;25;°C;Coolant Temp
0.1;850;rpm;Engine RPM
0.1;25;°C;Coolant Temp
```

The parser handles interleaved rows - different channels can have different sample rates.

## Installation

### Running the Executable

Download and run:
```
run/dist/obd2_analyzer.exe
```

### Development Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python src/obd2_native.py
   ```

### Building the Executable

Run the build script from the repo root:
```bash
run/build_exe.bat
```

This will:
1. Install PyInstaller if needed
2. Convert `logo.png` to `run/logo.ico`
3. Build the executable using `run/obd2_analyzer.spec`

Output will be in `run/dist/obd2_analyzer.exe`

## Architecture

```bash
src/
├── obd2_native.py              # Application entry point
└── obd2_viewer/
    ├── core/                   # Core data processing
    │   ├── data_loader.py      # CSV file loading
    │   └── multi_channel_parser.py  # Multi-channel CSV parsing
    └── native/                 # Native Windows GUI
        ├── main_window.py      # Main application window
        └── chart_widget.py     # PyQtGraph chart components
```

## Testing

```bash
# Run all tests
pytest src/test/ -v
```

## Known Limitations

1. **Data Format**: Only supports semicolon-delimited CSV with SECONDS;PID;VALUE;UNITS columns
2. **Export**: No chart export functionality yet
3. **Sessions**: No way to save/restore visualization sessions

## Roadmap

- [ ] Chart export (PNG, SVG)
- [ ] Data annotations and markers
- [ ] Session save/restore
- [ ] Additional CSV format support

## Past Issues & RCAs

### PyInstaller PyQt6 DLL Load Failure (Dec 2025)

**Issue:** `DLL load failed while importing QtWidgets` when running the PyInstaller-built exe

**Root Cause:** PyQt6 6.10.1 has DLL loading compatibility issues with PyInstaller on Windows. Additionally, `shiboken2` (PySide2's Qt5 binding) was being bundled and conflicting with PyQt6.

**Solution:**
1. Downgraded PyQt6 to 6.5.2
2. Added exclusions for PySide2, shiboken2, PySide6, shiboken6, PyQt5 in spec file
3. Pinned PyQt6 version in requirements.txt to `>=6.5.0,<6.6.0`

### Frontend Callback Failure (Dec 2024)

**Issue:** Dash callbacks not triggering graph display (legacy web version)

**Root Cause:** Dashboard was creating its own Dash app instance, but callbacks were registered on a different instance.

**Solution:** Modified dashboard to accept external Dash app for callback registration.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- Charts powered by [PyQtGraph](https://www.pyqtgraph.org/)
- Data processing with [Pandas](https://pandas.pydata.org/) and [NumPy](https://numpy.org/)
- Data format from [Car Scanner](https://www.carscanner.info/)
