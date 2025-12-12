# OBD2 Data Visualization Tool - Product Requirements Document

## Overview

A professional web-based tool for importing, processing, and visualizing OBD2 (On-Board Diagnostics) CSV data with support for multiple imports, mathematical channel creation, and persistent visualization snapshots.

## Feature Groups

### 1. Data Import & Management

#### 1.1 CSV Import Functionality
**Requirements:**
- Support for single CSV file or folder containing multiple CSV files
- Multi-channel CSV support (interleaved rows like Car_scanner_nov_4.csv)
- Automatic channel detection and separation
- User-provided import naming
- Validation to prevent duplicate channel names across files
- RDB storage of import objects

**Implementation Status:** ✅ Multi-channel CSV parsing implemented
**Known Issues:** 
- ❌ No RDB persistence layer (schema exists, no Python connection layer)
- ⚠️ Basic import validation only (file size, required columns)

**Current Working Components:**
- ✅ MultiChannelCSVParser handles interleaved CSVs correctly
- ✅ Data interpolation to common time grid
- ✅ Channel separation and unit extraction
- ✅ Backend creates 29+ channels from test data
- ✅ Frontend callbacks now working (fixed Dec 2024)

**Questions for Implementation:**
1. What RDB system should we use? (SQLite for simplicity, PostgreSQL for scalability?)
2. Should imports be stored as file paths or actual binary data?
3. How should we handle very large CSV files (>1GB)?
4. Should we support CSV preview before import confirmation?

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

#### 1.3 Import Validation
**Requirements:**
- Detect duplicate channel names across files
- Fail gracefully with clear error messages
- Allow user to resolve conflicts before import
- Validate CSV structure and required columns

**Implementation Status:** ❌ Not Implemented
**Known Issues:** No validation logic exists

### 2. Visualization & Plotting

#### 2.1 Multi-Graph Display
**Requirements:**
- Each channel displayed on separate graph
- Adjustable graph heights
- Configurable time window (x-axis)
- Scrollable graph area for unlimited channels
- No graph overlap regardless of zoom level
- Responsive layout with minimal whitespace

**Implementation Status:** ✅ Working
**Current Working Components:**
- ✅ OBD2Dashboard creates figures with all 29 channels
- ✅ Plotly traces generated correctly with proper data
- ✅ Time range and zoom functionality works
- ✅ Dash callbacks working (fixed Dec 2024)
- ✅ Graphs display correctly in browser
- ⚠️ Uses subplots (not individual scrollable graphs yet)

**Questions for Implementation:**
1. Should we use individual Plotly graphs or stick with subplots?
2. How should we handle graph height persistence?
3. Should there be minimum/maximum height limits?

#### 2.2 Time Navigation Controls
**Requirements:**
- Start/end time text boxes
- Navigation buttons: ±0.1s, ±0.5s, ±1s, ±5s, ±15s, ±1min, ±5min
- Independent time controls per import
- Equal time window across all imports
- Synchronized time movement option

**Implementation Status:** ⚠️ Partially Implemented
**Current Working Components:**
- ✅ Start/end time text boxes
- ✅ Center time input
- ✅ Left/Right 30s navigation buttons
- ✅ Reset button
- ❌ Missing granular navigation (±0.1s, ±0.5s, etc.)
- ❌ No multi-import synchronization

#### 2.3 Channel Visibility Management
**Requirements:**
- Show/hide individual channels
- Show all / Hide all buttons
- Channel list in sidebar
- Default to show all channels

**Implementation Status:** ✅ Fully Implemented
**Current Working Components:**
- ✅ Individual channel checkboxes
- ✅ Show All / Hide All buttons
- ✅ Channel list in sidebar with units
- ✅ Defaults to show all channels

### 3. User Interface & Layout

#### 3.1 Responsive Layout System
**Requirements:**
- Drag-adjustable sidebar:graphs ratio
- Responsive design for vertical screens
- Sidebar repositioning (left/top)
- Maximum screen utilization
- Clean, professional interface

**Implementation Status:** ❌ Not Implemented
**Known Issues:** Fixed layout, no responsiveness

**Questions for Implementation:**
1. Should we use CSS Grid or Flexbox for layout?
2. How should we handle layout persistence across sessions?
3. Minimum sidebar width requirements?

#### 3.2 Sidebar Controls
**Requirements:**
- Channel visibility controls
- Time navigation controls
- Graph size controls
- New import button
- Color selection per import
- Math channel creation

**Implementation Status:** ⚠️ Partially Implemented
**Known Issues:** Limited controls, no color selection, no math channels

#### 3.3 Modal Interfaces
**Requirements:**
- New import modal (replicates home page functionality)
- Math channel creation modal
- Clean, accessible modal design

**Implementation Status:** ❌ Not Implemented
**Known Issues:** No modal system exists

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
- Multiple imports in single visualization
- Independent time controls per import
- Synchronized time windows
- Color coding per import
- Import merging functionality

**Implementation Status:** ❌ Not Implemented
**Known Issues:** Single import only

**Questions for Implementation:**
1. How should we handle imports with different channel sets?
2. Should imports be able to be removed individually?
3. How to handle time zone differences between imports?

#### 5.2 Channel Consolidation
**Requirements:**
- Same channel names plotted on same graph
- Different colors per import
- Legend showing import sources
- Hover information with import details

**Implementation Status:** ❌ Not Implemented

### 6. Persistence & Snapshots

#### 6.1 Visualization Snapshots
**Requirements:**
- Save complete visualization state
- Graph heights and zoom levels
- Time ranges per import
- Math channels
- Color schemes
- Renameable snapshots
- Snapshot listing on home screen

**Implementation Status:** ❌ Not Implemented
**Known Issues:** No persistence layer

**Questions for Implementation:**
1. Should snapshots store actual data or just references?
2. How should we handle snapshot sharing between users?
3. Export/import snapshot functionality?

#### 6.2 Import Management
**Requirements:**
- List of available imports on home screen
- Import metadata display
- Import deletion/archiving
- Import sharing between snapshots

**Implementation Status:** ❌ Not Implemented

### 7. Data Processing & Validation

#### 7.1 CSV Parsing
**Requirements:**
- Robust CSV parsing with error handling
- Multiple delimiter support
- Encoding detection
- Large file handling
- Progress indicators

**Implementation Status:** ⚠️ Partially Implemented
**Known Issues:** Limited error handling, no progress indication

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

**Implementation Status:** ❌ Not Implemented
**Known Issues:** Loads entire dataset into memory

**Questions for Implementation:**
1. What's the maximum dataset size we should support?
2. Should we implement server-side processing?
3. Caching strategy for frequently accessed data?

#### 8.2 Rendering Performance
**Requirements:**
- Smooth graph interactions
- Efficient redrawing
- GPU acceleration if available
- Progressive rendering

**Implementation Status:** ⚠️ Partially Implemented
**Known Issues:** Performance degrades with many channels

## Technical Architecture Questions

### Database Schema
1. Should we use SQLite for simplicity or PostgreSQL for scalability?
2. How to store large CSV data - file paths or binary blobs?
3. Indexing strategy for time-series data?

### Frontend Framework
1. Continue with Dash or consider React/Vue for better performance?
2. How to handle state management across multiple imports?
3. Real-time data streaming requirements?

### Backend Architecture
1. Monolithic application or microservices?
2. API design for data import/export?
3. Authentication and user management?

### Deployment
1. Cloud deployment strategy (AWS, GCP, Azure)?
2. Container requirements (Docker)?
3. Scaling strategy for multiple users?

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

## Critical Issues Requiring Immediate Attention

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

1. **Current Implementation:** Single import only, fixed layout, no persistence
2. **Performance:** Memory limitations with large datasets (10MB file limit)
3. **Data Formats:** Only supports semicolon-delimited CSV with SECONDS;PID;VALUE;UNITS columns
4. **Export:** No chart export functionality
5. **Layout:** Fixed sidebar ratio, no drag-to-resize
6. **Graphs:** Uses subplots instead of individual scrollable graphs

## Success Metrics

1. **Performance:** Handle 100MB CSV files within 10 seconds
2. **Usability:** Complete workflow within 3 clicks
3. **Reliability:** 99.9% uptime for production deployment
4. **Scalability:** Support 100+ simultaneous users
5. **Data Quality:** 100% accurate data processing and visualization
