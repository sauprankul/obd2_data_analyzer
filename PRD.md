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

**Questions for Implementation:**

1. How should we handle channels with different sampling rates?
2. Should we interpolate to align timestamps or keep original sampling?
3. How to detect channel boundaries in malformed CSVs?

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
- ✅ Scroll wheel zoom capped to data range
- ✅ Split window mode for dual monitor setups

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
- ✅ Splitter state persisted across sessions
- ✅ Window geometry persistence

#### 3.2 Sidebar Controls

**Requirements:**

- Channel visibility controls (per import)
- Time navigation controls with all ± buttons in single row, red Reset in center
- Add Import button
- Import legend with: filename, color, duration (h:m:s), time offset, per-import Synchronize button
- Split window mode (detach sidebar to separate window)

**Implementation Status:** ⚠️ Partially Implemented
**Current Working Components:**

- ✅ Channel visibility controls with per-import checkboxes
- ✅ Time navigation with full granularity
- ✅ Add Import button
- ✅ Import legend showing filename-color mapping
- ✅ Split window mode via View menu
- ❌ Compact single-row time nav layout (pending)
- ❌ Per-import Synchronize buttons with offset display (pending)
- ❌ Duration display per import (pending)

#### 3.3 Modal Interfaces

**Requirements:**

- Synchronize imports dialog (for time offset adjustment)
- Math channel creation modal (future)

**Implementation Status:** ⚠️ Partially Implemented
**Current Working Components:**

- ✅ SynchronizeDialog for time offset adjustment
- ❌ Math channel creation modal (future feature)

### 4. Mathematical Channel Creation

#### 4.1 Basic Math Operations

**Requirements:**

- Input A (numerical channel selection)
- Input B (numerical channel with same units)
- Basic arithmetic operations (+, -, *, /)
- Apply to all existing imports
- New graph placement below input A's graph

**Implementation Status:** ❌ Not Implemented
**Known Issues:** No math channel functionality

**Questions for Implementation:**

1. Should we support more complex expressions (A*B, A/B, etc.)?
2. How should we handle unit validation?
3. Should math channels be editable after creation?

#### 4.2 Advanced Math Operations (Future)

**Requirements:**

- Boolean operations
- Conditional expressions
- Statistical functions
- Custom formulas

**Implementation Status:** ❌ Not Planned Yet

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
- ✅ Clear History button
- ✅ Persisted via QSettings

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
- ❌ Loading spinner during parsing (pending)

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

#### 8.1 Large Dataset Handling (Low Priority)

**Requirements:**

- Efficient memory usage
- Streaming data processing
- Lazy loading for large datasets
- Data downsampling for visualization

**Implementation Status:** ❌ Not Implemented (Low Priority)
**Known Issues:** Loads entire dataset into memory. Current approach works fine for typical OBD2 files (<10MB).

#### 8.2 Rendering Performance

**Requirements:**

- Smooth graph interactions
- Efficient redrawing
- GPU acceleration if available
- Progressive rendering

**Implementation Status:** ⚠️ Partially Implemented
**Known Issues:** Performance degrades with many channels

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

### Phase 1 (MVP)

1. Multi-channel CSV parsing
2. Basic multi-import support
3. Improved layout system
4. Snapshot functionality

### Phase 2

1. Math channel creation
2. Advanced time controls
3. Performance optimizations
4. Enhanced UI/UX

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

## Known Limitations

1. **Current Implementation:** ✅ Multi-import fully supported
2. **Performance:** Memory limitations with large datasets (10MB file limit)
3. **Data Formats:** Only supports semicolon-delimited CSV with SECONDS;PID;VALUE;UNITS columns
4. **Export:** No chart export functionality
5. **Scroll Zoom:** ✅ Now capped to prevent zooming beyond data range

## Success Metrics

1. **Performance:** Handle 10MB CSV files smoothly with 29+ channels
2. **Usability:** Load and visualize data within 3 clicks
3. **Responsiveness:** Smooth panning/zooming with hardware acceleration
4. **Data Quality:** 100% accurate data processing and visualization
