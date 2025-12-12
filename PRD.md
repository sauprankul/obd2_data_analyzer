# OBD2 Data Visualization Tool - Product Requirements Document

## Overview

A professional **native Windows application** for importing, processing, and visualizing OBD2 (On-Board Diagnostics) CSV data with support for multiple imports, mathematical channel creation, and persistent visualization snapshots.

**Technology Stack (Native App):**

- Python 3.8+
- PyQt6 for native Windows GUI
- PyQtGraph for hardware-accelerated charting
- No browser required - pure native desktop application

## Feature Groups

### 1. Data Import & Management

#### 1.1 CSV Import Functionality

**Requirements:**

- Support for single CSV file or folder containing multiple CSV files
- Multi-channel CSV support (interleaved rows like Car_scanner_nov_4.csv)
- Automatic channel detection and separation
- User-provided import naming
- Validation to prevent duplicate imports (by absolute file path)
- **Past Imports list on home screen** (cached file paths, not data)
- No database storage of actual CSV data - only file path references

**Implementation Status:** ✅ Fully Implemented (Native App)
**Current Working Components:**

- ✅ MultiChannelCSVParser handles interleaved CSVs correctly
- ✅ Data interpolation to common time grid
- ✅ Channel separation and unit extraction
- ✅ Backend creates 29+ channels from test data
- ✅ Native file dialogs for CSV selection
- ✅ Recent files list with persistence
- ✅ Past Imports home screen with recent files
- ✅ Time normalization (all imports start at t=0)

**Design Decision:** Store file paths only, not actual data. Re-parse CSV on each load for simplicity and to avoid data duplication.

#### 1.2 Multi-Channel Processing

**Requirements:**

- Parse multi-channel CSVs with interleaved rows
- Split into individual channel streams
- Maintain consistent time-series structure
- Preserve original metadata per channel

**Implementation Status:** ✅ Fully Implemented
**Current Working Components:**

- ✅ MultiChannelCSVParser correctly separates interleaved channels
- ✅ Interpolation aligns all channels to common time grid
- ✅ Preserves units and metadata for each channel
- ✅ Handles 29+ channels from real OBD2 data
- ✅ Creates pandas DataFrames with SECONDS and VALUE columns

**Design Decisions:**

1. **Different sampling rates:** Plot raw data as line graphs - no resampling needed
2. **Timestamp alignment:** Keep original sampling, no interpolation
3. **Malformed CSVs:** Fail with clear error message if CSV structure is invalid

### 2. Visualization & Plotting

#### 2.1 Multi-Graph Display

**Requirements:**

- Each channel displayed on separate graph
- Adjustable graph heights (180-220px per chart)
- Configurable time window (x-axis)
- Scrollable graph area for unlimited channels
- No graph overlap regardless of zoom level
- Responsive layout with minimal whitespace
- **Synchronized crosshair** - clicking on one chart shows values for all charts at that x position
- **Channel title shows current value** when crosshair is positioned
- **Scroll wheel scrolls graph area** (not zoom - use time nav for zoom)
- **Split window mode** - sidebar can be detached to separate window (View menu)

**Implementation Status:** ✅ Fully Implemented (Native App)
**Current Working Components:**

- ✅ PyQtGraph-based individual channel plots
- ✅ Hardware-accelerated OpenGL rendering
- ✅ Synchronized X-axis across all plots
- ✅ Click-to-position crosshair with synchronized values
- ✅ Channel titles display value at crosshair position
- ✅ Scrollable plot container
- ✅ 15px spacing between charts for readability
- ✅ Scroll wheel scrolls graph area (not zoom)
- ✅ Ctrl+scroll zooms X-axis (zoom in/out centered on view)
- ✅ Split window mode for dual monitor setups
- ✅ Charts sorted by unit then alphabetically (matching sidebar)

#### 2.2 Time Navigation Controls

**Requirements:**

- Start/end time text boxes
- Navigation buttons: ±0.1s, ±0.5s, ±1s, ±5s, ±15s, ±30s, ±1min, ±5min
- Zoom In/Out buttons (reduce/increase time range by 10%, 5% each side)
- Zoom In grayed out when time range ≤ 10 seconds (keeps x-axis markers readable)
- Zoom Out grayed out when already showing full data range
- Independent time controls per import
- Equal time window across all imports
- Synchronized time movement option

**Implementation Status:** ✅ Fully Implemented (Native App)
**Current Working Components:**

- ✅ Start/end time text boxes
- ✅ Center time input with Go button
- ✅ Full granular navigation (±0.1s, ±0.5s, ±1s, ±5s, ±15s, ±30s, ±1min, ±5min)
- ✅ Reset View button
- ✅ Zoom In/Out buttons with proper graying when at limits
- ✅ Multi-import synchronization via Synchronize dialog

#### 2.3 Channel Visibility Management

**Requirements:**

- Show/hide individual channels (per import when multi-import)
- Show all / Hide all buttons
- Channel list in sidebar sorted by: selected first, then by unit, then alphabetically
- Default to show all channels
- Selecting a channel moves it to top of list
- Deselecting all imports for a channel moves it back to unselected pile

**Implementation Status:** ✅ Fully Implemented
**Current Working Components:**

- ✅ Individual channel checkboxes (per import)
- ✅ Show All / Hide All buttons
- ✅ Channel list in sidebar with units
- ✅ Defaults to show all channels
- ✅ Dynamic sorting: selected channels at top, sorted by unit then alphabetically
- ✅ Checkbox and color indicator on left side (consistent with Filters layout)

### 3. User Interface & Layout

#### 3.1 Responsive Layout System

**Requirements:**

- Drag-adjustable sidebar:graphs ratio via QSplitter
- Responsive design for vertical screens
- Maximum screen utilization
- Clean, professional interface

**Implementation Status:** ✅ Implemented (Native App)
**Current Working Components:**

- ✅ QSplitter for drag-adjustable sidebar:charts ratio
- ✅ Sidebar width resizable relative to window (minimum width enforced)
- ✅ Time navigation buttons expand with sidebar width
- ✅ Splitter state persisted across sessions
- ✅ Window geometry persistence

#### 3.2 Sidebar Controls

**Requirements:**

- Channel visibility controls (per import)
- Time navigation controls with all ± buttons in single row, red Reset in center
- Add Import button
- Import legend with: filename, color, duration (h:m:s), time offset, per-import Synchronize button
- Split window mode (detach sidebar to separate window)

**Implementation Status:** ✅ Fully Implemented
**Current Working Components:**

- ✅ Channel visibility controls with per-import checkboxes
- ✅ Time navigation with compact single-row layout, red Reset button in center
- ✅ Add Import button
- ✅ Import legend showing filename, color, duration (h:m:s), offset, per-import Sync button
- ✅ Split window mode via View menu
- ✅ Per-import Synchronize dialog for time offset adjustment
- ✅ Taller/Shorter/Math Channel/Create Filter buttons in single row
- ✅ Filters section above Show All/Hide All buttons

#### 3.3 Modal Interfaces

**Requirements:**

- Synchronize imports dialog (for time offset adjustment)
- Math channel creation modal

**Implementation Status:** ✅ Fully Implemented
**Current Working Components:**

- ✅ SynchronizeDialog for time offset adjustment
- ✅ Math channel creation modal with expression validation
- ✅ Math channel edit functionality

### 4. Mathematical Channel Creation

#### 4.1 Math Channel Expressions

**Requirements:**

- Input A (required numerical channel selection)
- Input B (optional numerical channel)
- Expression field supporting Python-style math: `(A/0.45) * 14.7` or `A + B` or `A * B / 2`
- Variables `A` and `B` represent channel values at each time point
- Expression validation: must evaluate to a number given numeric A and B
- Cannot save invalid expressions (Create/Update buttons disabled)
- Apply to all existing imports
- Math channels can be edited after creation
- Unit selection with autocomplete from existing units
- Shows units of selected inputs A and B in dialog

**Time Alignment for A and B:**

- Use Input A's time points as the x-axis
- For each A time point, find nearest B value by interpolation

**Implementation Status:** ✅ Fully Implemented
**Current Working Components:**

- ✅ Math channel creation dialog with expression validation
- ✅ Input A and B selection with unit display
- ✅ Python-style expression evaluation
- ✅ Real-time expression validation
- ✅ Unit selection with autocomplete
- ✅ Edit button on math channels for modification
- ✅ Math channels automatically computed for new imports
- ✅ Math channels shown by default when created

#### 4.2 Advanced Math Operations

**Requirements:**

- Boolean operations and conditionals
- Statistical functions (min, max, avg, rolling average)
- Multi-channel expressions (C, D, E... inputs)

**Implementation Status:** ✅ Fully Implemented
**Current Working Components:**

- ✅ Multi-channel inputs (A, B, C, D, E) - up to 5 input channels
- ✅ Boolean/comparison operators: <, >, <=, >=, ==, !=
- ✅ Conditional expressions: if_else(condition, true_val, false_val)
- ✅ Math functions: abs, min, max, sqrt, log, log10, exp, sin, cos, tan, floor, ceil, round, pow
- ✅ Statistical functions: rolling_avg(X, seconds), rolling_min, rolling_max, delta, cumsum, clip(X, min, max)
- ✅ Rolling window functions use seconds (not sample count) for time-based windows
- ✅ Array-wide statistics: np_min, np_max, np_mean, np_std
- ✅ Constants: pi, e
- ✅ Vectorized evaluation for performance
- ✅ Backward compatible with legacy 2-input math channels
- ✅ Input dropdowns sorted by unit then alphabetically (matching sidebar)
- ✅ Channel names display with unit suffix in dropdowns

#### 4.3 Data Filters

**Requirements:**

- Button should be to the right of Create Math Channel, labeled "Create Filter"
- Filters should have names
- Allow the use of any channels (including math channels) as inputs
- Expression must evaluate to boolean, should validate immediately on-type in modal. Invalid should not allow saving.
- All basic and advanced math operations should be allowed in boolean expression
- Modal should allow Show and Hide options for filter as toggle. Ie, do you show or hide when filter evaluates to true
- Modal should allow defining a time buffer between +/- 0.5s and +/- 10 minutes. If Show mode, a singe point match should show all data within buffer. If Hide mode, a single point match should hide all data within buffer.
- Input channel matching on the x-axis should behave the same as math channels - reuse the interpolation/matching code.
- Filters should be listed in Filters section above Shown.
- Edit button and checkbox next to each filter.
- Filters should apply as a union. Ie if one import matches a filter, all imports should be assumed to match the filter at that point. Take the offsets into account. If import 1 matches a filter at X=5000, and import 2 has an offset of +500, import 2 should be assumed to match at X=5500.

**Implementation Status:** ✅ Fully Implemented
**Current Working Components:**

- ✅ "Create Filter" button next to "Math Channel" button
- ✅ FilterDialog with name, multi-channel inputs (A-E), boolean expression
- ✅ Real-time expression validation (must evaluate to boolean)
- ✅ All math functions from 4.2 available in filter expressions
- ✅ Show/Hide mode toggle with 👁/🚫 icons
- ✅ Time buffer selection (±0.1s to ±10min, default ±0.1s)
- ✅ Filters section in sidebar above channel list
- ✅ Enable/disable checkbox, mode icon, edit button, delete button per filter
- ✅ Filter masks applied to chart data
- ✅ Reuses interpolation/alignment code from math channels
- ✅ Optimized interval merging algorithm O(n + m log m) for performance
- ✅ Line breaks between non-overlapping filter intervals (NaN separators)
- ✅ Multiple Show filters merge overlapping intervals correctly
- ✅ Filter name validation (required, shows popup if empty)
- ✅ Input dropdowns sorted by unit then alphabetically (matching sidebar)
- ✅ Filter precedence: top filter = highest precedence, processed bottom-to-top
- ✅ Up/down buttons for filter reordering in sidebar
- ✅ Filters auto-apply when new math channels are created

### 5. Multi-Import Visualization

#### 5.1 Import Management

**Requirements:**

- Multiple imports in single visualization via "Add Import" button
- Prevent duplicate imports (compare by absolute file path)
- Color coding per import (distinct color per CSV file)
- Legend in sidebar showing filename → color mapping
- Each channel has N checkboxes (one per imported CSV)
- Base import (first loaded) defines the time window
- Additional imports clipped to base import's time range

**Implementation Status:** ✅ Fully Implemented
**Current Working Components:**

- ✅ Single import visualization working
- ✅ Multi-import support via "Add Import" button
- ✅ Per-import color coding (8 distinct colors)
- ✅ Legend with filename-color mapping in sidebar
- ✅ Duplicate import prevention (by absolute path)
- ✅ Per-channel checkboxes for each import

#### 5.2 Time Synchronization Panel

**Requirements:**

- "Synchronize" button enabled when 2+ imports loaded
- Opens floating control panel
- First import is the "base" - cannot be shifted
- Each additional import has its own ±0.1s to ±5min shift buttons
- Shifting adjusts that import's time offset relative to base
- All imports share the same visible time window (base's range)
- If secondary import has less data, line simply ends
- If secondary import has more data, excess is not plotted

**Implementation Status:** ✅ Fully Implemented
**Current Working Components:**

- ✅ Synchronize button in Time Navigation (enabled with 2+ imports)
- ✅ Floating SynchronizeDialog with offset controls
- ✅ Base import fixed at 0.0s offset
- ✅ Full shift button set (±0.1s to ±5min) for each additional import
- ✅ Real-time offset updates reflected in charts

#### 5.3 Channel Consolidation

**Requirements:**

- Same channel names from different imports plotted on same graph
- Different colors per import (consistent across all channels)
- Legend showing import sources with colors
- Click shows values from all imports at that x position

**Implementation Status:** ✅ Fully Implemented
**Current Working Components:**

- ✅ Same channels consolidated on single graph with multiple lines
- ✅ Consistent colors per import across all channels
- ✅ Import legend in sidebar
- ✅ Click shows color-coded values from all imports

### 6. Persistence & Caching

#### 6.1 Past Imports (Home Screen)

**Requirements:**

- Home screen shows list of previously imported CSV files
- Store file paths only (not actual data)
- Display filename, path, last accessed date
- Click to re-open in visualization view
- Clear individual entries or clear all
- Persist across application restarts (QSettings)

**Implementation Status:** ✅ Fully Implemented
**Current Working Components:**

- ✅ Recent files menu in native app
- ✅ Dedicated home screen with Past Imports list
- ✅ Double-click to open past import
- ✅ Multi-select with Ctrl+Click for batch opening
- ✅ Large centered "Open Selected" button
- ✅ Clear History button (centered below)
- ✅ Persisted via QSettings
- ✅ Sequential file loading for multi-select (avoids race conditions)

#### 6.2 Window State Persistence

**Requirements:**

- Remember window size and position
- Remember splitter ratios
- Remember last opened file/folder

**Implementation Status:** ✅ Fully Implemented
**Current Working Components:**

- ✅ Window geometry saved/restored via QSettings
- ✅ Splitter state persisted

### 7. Data Processing & Validation

#### 7.1 CSV Parsing

**Requirements:**

- Robust CSV parsing with error handling
- Multiple delimiter support
- Encoding detection
- Large file handling
- Loading spinner/progress indicator during file parsing

**Implementation Status:** ⚠️ Partially Implemented
**Current Working Components:**

- ✅ Robust CSV parsing
- ✅ Semicolon delimiter support
- ✅ Loading dialog with animated GIF during file parsing
- ✅ Background thread for file loading (keeps UI responsive)

#### 7.2 Data Validation

**Requirements:**

- Required column validation
- Data type checking
- Time series validation
- Outlier detection
- Missing data handling

**Implementation Status:** ⚠️ Partially Implemented
**Known Issues:** Basic validation only

### 8. Performance & Scalability

#### 8.1 Large Dataset Handling

**Requirements:**

- Efficient memory usage
- Streaming data processing
- Lazy loading for large datasets
- Data downsampling for visualization

**Implementation Status:** ✅ Implemented
**Current Working Components:**

- ✅ LOD (Level of Detail) downsampling - max 2000 points per channel
- ✅ Peak-preserving downsampling maintains visual fidelity
- ✅ Handles large datasets efficiently

#### 8.2 Rendering Performance

**Requirements:**

- Smooth graph interactions
- Efficient redrawing
- GPU acceleration if available
- Progressive rendering

**Implementation Status:** ✅ Implemented
**Current Working Components:**

- ✅ Software rendering (stable, no blank graph issues)
- ✅ Antialiasing disabled for faster rendering
- ✅ Taller/Shorter buttons for adjustable graph heights (5% increments)
- ✅ Smooth scrolling through channel list

## Technical Architecture

### Native Application Stack

- **GUI Framework:** PyQt6 - mature, native Windows widgets
- **Charting:** PyQtGraph - OpenGL-accelerated, handles millions of points
- **Data Processing:** pandas, numpy, scipy
- **Persistence:** QSettings for preferences, JSON for recent files
- **No database required** - CSV files re-parsed on load

### Design Decisions

1. **File paths only** - Don't store CSV data in database, just paths
2. **Re-parse on load** - Simpler than maintaining data sync
3. **Single-process** - No client/server architecture needed
4. **Native widgets** - No web browser overhead

## Implementation Priority

### Phase 1 (MVP) ✅ COMPLETE

1. Multi-channel CSV parsing
2. Basic multi-import support

### Phase 2 ✅ COMPLETE

1. ✅ Math channel creation
2. ✅ Advanced time controls
3. ✅ Performance optimizations (LOD downsampling, caching)
4. ✅ Enhanced UI/UX (Taller/Shorter, loading spinner)

### Phase 3

1. Advanced math operations
2. Real-time data support
3. Collaboration features
4. Mobile responsiveness

## Past Issues

### ✅ Frontend Callback Failure - RESOLVED

**Issue:** Dash callbacks not triggering graph display in browser
**Status:** FIXED (Dec 2024)
**Root Cause:** Dashboard was creating its own Dash app instance, but main_application was only returning the layout without the callbacks. Callbacks were registered on a different app instance.
**Solution:** Modified OBD2Dashboard to accept external Dash app for callback registration.

**Files Modified:**

- `src/obd2_viewer/visualization/dashboard.py` - Added `app` parameter to constructor
- `src/obd2_viewer/app/main_application.py` - Passes main app to dashboard

### 📁 Test Organization

**Status:** ✅ Complete

- Permanent test suite created with 20 tests covering all components
- Tests organized in `src/test/` with proper structure
- Multi-channel and single-channel test data properly organized
- All tests passing, confirming backend functionality

### ✅ PyInstaller PyQt6 DLL Load Failure - RESOLVED

**Issue:** `DLL load failed while importing QtWidgets: The specified procedure could not be found` when running the PyInstaller-built exe
**Status:** FIXED (Dec 2025)
**Root Cause:** PyQt6 6.10.1 has DLL loading compatibility issues with PyInstaller on Windows. The newer PyQt6 version's `.pyd` bindings couldn't locate the correct Qt6 DLL procedures when bundled by PyInstaller. Additionally, `shiboken2` (PySide2's Qt5 binding library) was being bundled and conflicting with PyQt6/Qt6.
**Solution:**

1. Downgraded PyQt6 from 6.10.1 to 6.5.2 (`pip install PyQt6==6.5.2 PyQt6-Qt6==6.5.2 PyQt6-sip==13.5.2`)
2. Added exclusions for `PySide2`, `shiboken2`, `PySide6`, `shiboken6`, `PyQt5` in the spec file to prevent Qt version conflicts
3. Pinned PyQt6 version in `requirements.txt` to `>=6.5.0,<6.6.0`

**Files Modified:**

- `requirements.txt` - Pinned PyQt6 to 6.5.x series
- `run/obd2_analyzer.spec` - Added PySide/shiboken exclusions, added runtime hook for DLL path setup

## Known Limitations

1. **Data Formats:** Only supports semicolon-delimited CSV with SECONDS;PID;VALUE;UNITS columns
2. **Export:** No chart export functionality
3. **Views:** No way to save views and pull them up later.

## Success Metrics

1. **Performance:** Handle 10MB CSV files smoothly with 29+ channels
2. **Usability:** Load and visualize data within 3 clicks
3. **Responsiveness:** Smooth panning/zooming with hardware acceleration
4. **Data Quality:** 100% accurate data processing and visualization
