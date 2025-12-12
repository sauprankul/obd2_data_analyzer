# OBD2 Data Visualization Tool - Test Suite

## Test Organization

This test suite is organized into permanent, comprehensive tests that verify the complete functionality of the OBD2 data visualization tool.

### Test Files

#### Core Component Tests
- **`test_multi_channel_parser.py`** - Tests the multi-channel CSV parser functionality
  - CSV parsing and channel separation
  - Data interpolation to common time grid
  - Units extraction and validation
  - Import summary generation

- **`test_dashboard.py`** - Tests the OBD2 dashboard functionality
  - Dashboard creation and initialization
  - Figure generation with different channel selections
  - Channel controls creation and management
  - Time navigation and zoom functionality
  - Layout component verification

#### Integration Tests
- **`test_integration.py`** - Tests complete workflow integration
  - End-to-end CSV to dashboard workflow
  - Main application integration
  - Data consistency across components
  - Error handling for edge cases

- **`test_dashboard_callbacks.py`** - Tests dashboard callback behavior
  - Initial figure creation and data loading
  - Channel controls initialization
  - Show All/Hide All functionality
  - Time range functionality
  - Layout component verification

### Test Data

#### Multi-Channel Test Data
- **`nov_4_test_data.csv`** - Multi-channel CSV file with interleaved sensor data
  - Contains multiple OBD2 PIDs in a single file
  - Tests the parser's ability to separate and interpolate channels
  - Used for testing multi-channel functionality

#### Single-Channel Test Data
- **`split_test_data/`** - Directory containing individual CSV files
  - Each file contains data for a single sensor/PID
  - Used for testing single-channel processing
  - Examples: `test_data_engine_rpm.csv`, `test_data_vehicle_speed.csv`, etc.

### Running Tests

#### Run All Tests
```bash
cd src/test
python -m pytest -v
```

#### Run Specific Test Categories
```bash
# Multi-channel parser tests
python -m pytest test_multi_channel_parser.py -v

# Dashboard tests  
python -m pytest test_dashboard.py -v

# Integration tests
python -m pytest test_integration.py -v

# Callback tests
python -m pytest test_dashboard_callbacks.py -v
```

#### Run with Coverage
```bash
python -m pytest --cov=obd2_viewer --cov-report=html -v
```

### Test Coverage

The test suite covers:
- ✅ Multi-channel CSV parsing (29+ channels)
- ✅ Data interpolation and time alignment
- ✅ Dashboard creation and layout
- ✅ Figure generation and visualization
- ✅ Channel controls and interactivity
- ✅ Time navigation and zoom
- ✅ Show/Hide All functionality
- ✅ Error handling and edge cases
- ✅ Integration between all components
- ✅ Callback initialization and execution

### Key Test Scenarios

1. **Multi-Channel Parsing**: Verifies that interleaved CSV data is correctly separated into individual channels
2. **Figure Creation**: Ensures that graphs are generated with proper data traces
3. **Channel Controls**: Tests that channel checkboxes work correctly for show/hide functionality
4. **Time Navigation**: Validates time range selection and zoom functionality
5. **Integration Workflow**: Tests the complete flow from CSV upload to visualization

### Troubleshooting

If tests fail:
1. Ensure test data files exist in `src/test/` and `src/test/split_test_data/`
2. Check that all dependencies are installed (`pip install -r requirements.txt`)
3. Verify that the multi-channel parser can handle the test CSV format
4. Check dashboard callback initialization and figure creation

### Adding New Tests

When adding new functionality:
1. Create unit tests in the appropriate test file
2. Add integration tests to `test_integration.py`
3. Update this README with new test descriptions
4. Ensure all tests pass before committing changes
