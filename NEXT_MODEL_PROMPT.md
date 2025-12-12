# PROMPT FOR NEXT AI MODEL

## Project Context
You're taking over an OBD2 data visualization tool project. The previous developer was fired for failing to fix a critical frontend callback issue.

## Current Status
- ✅ **Backend is 100% working** - All 20 tests pass
- ✅ **Multi-channel CSV parsing implemented** - Handles 29+ channels correctly
- ✅ **Data processing pipeline complete** - Interpolation, unit extraction, figure creation all work
- ❌ **Frontend callbacks broken** - Browser shows empty graphs despite backend working perfectly

## Critical Issue: Frontend Callback Failure
**Problem:** Dash callbacks not triggering graph display in browser despite backend working perfectly.

**Symptoms:**
- Channel controls appear correctly in browser
- Graph container loads but remains empty
- Show/Hide All buttons don't work
- No JavaScript errors in console
- Backend creates figures with 29 traces correctly (verified by tests)

**What's Been Tried:**
- Multiple callback trigger approaches (interval, initial trigger, etc.)
- Different browser testing (including incognito)
- Complete test suite creation (all passing)
- Backend verification (perfect)

**Files to Focus On:**
1. `src/obd2_viewer/visualization/dashboard.py` - Main dashboard with broken callbacks
2. `src/obd2_viewer/app/main_application.py` - Application routing
3. `src/test/` - Complete test suite (all passing, use for verification)

## Your Mission
**FIX THE FRONTEND CALLBACKS SO GRAPHS DISPLAY IN BROWSER**

**Requirements:**
1. Make the dashboard show all 29 channel graphs immediately after CSV upload
2. Ensure Show/Hide All buttons work correctly
3. Ensure individual channel checkboxes work
4. Keep all existing backend functionality intact
5. Don't break any of the 20 passing tests

**Debugging Strategy:**
1. Start the main application: `python src/obd2_main.py`
2. Upload `src/test/nov_4_test_data.csv` 
3. Click "Load Data & Start Visualization"
4. You should see graphs but won't - that's the problem to fix
5. Use the test suite to verify backend still works: `cd src/test && python -m pytest -v`

**Technical Details:**
- Using Dash for web framework
- Plotly for visualization
- Multi-channel CSV with interleaved rows
- 29 channels with 8988 data points each
- Time range: 73664.3 - 74049.3 seconds

**Key Files to Examine:**
- `dashboard.py` lines 180-280: Main callback implementation
- Layout creation around line 140: Component structure
- Test files show expected behavior

**Expected Outcome:**
After uploading CSV, user should see all 29 channel graphs immediately with working controls.

## Project Structure
```
src/
├── obd2_viewer/
│   ├── visualization/dashboard.py    # 🔥 MAIN PROBLEM HERE
│   ├── app/main_application.py       # Routing
│   └── core/                         # Data processing (working)
├── test/                             # Complete test suite (use this!)
│   ├── nov_4_test_data.csv           # Test data
│   └── split_test_data/              # Individual CSVs
└── obd2_main.py                      # Entry point
```

## Success Criteria
1. Graphs display in browser after CSV upload
2. All 20 tests still pass
3. Show/Hide All functionality works
4. Individual channel checkboxes work

**Start by running the application and reproducing the issue, then fix the callback problem.**
