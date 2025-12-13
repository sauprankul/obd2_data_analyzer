# OBD2 Data Visualization Tool - Test Suite

## Test Files

- **`test_multi_channel_parser.py`** - Tests the multi-channel CSV parser
  - CSV parsing and channel separation
  - Data interpolation to common time grid
  - Units extraction and validation

- **`test_filter_stacking.py`** - Tests filter logic
  - Single/multiple hide filters
  - Show filters
  - Show/hide precedence and ordering
  - Cross-import filter synchronization with time offsets

## Test Data

- **`nov_4_test_data.csv`** - Multi-channel CSV file with interleaved sensor data
  - Contains multiple OBD2 PIDs in a single file
  - Used for testing multi-channel parsing

## Running Tests

```bash
# From repo root
pytest src/test/ -v
```
