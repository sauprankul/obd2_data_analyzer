"""
Unit tests for filter stacking logic with precedence.

Tests the _apply_filters logic to ensure:
1. Single hide filter removes matching points
2. Multiple hide filters stack (each removes more)
3. Show + Hide filters interact correctly with precedence
4. Filter order determines precedence (last = highest)
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockImportData:
    """Mock ImportData for testing."""
    def __init__(self, channels_data):
        self.channels_data = channels_data
        self.time_offset = 0.0


def create_test_channel(times, values):
    """Create a mock channel DataFrame."""
    return pd.DataFrame({'SECONDS': times, 'VALUE': values})


def apply_filters_multi_import(filter_order, filters, imports_data, time_offsets=None):
    """
    Apply filters across multiple imports with cross-import synchronization.
    
    If ANY import matches a filter at time t, ALL imports show that time range.
    """
    INPUT_LABELS = ['A', 'B', 'C', 'D', 'E']
    
    if time_offsets is None:
        time_offsets = [0.0] * len(imports_data)
    
    # Collect enabled filters in order
    active_filters = []
    for name in filter_order:
        if name in filters and filters[name].get('enabled', True):
            active_filters.append((name, filters[name]))
    
    if not active_filters:
        return [None] * len(imports_data)
    
    # PHASE 1: Collect matching intervals from ALL imports for each filter
    filter_unified_intervals = {}
    
    for filter_name, definition in active_filters:
        expression = definition['expression']
        inputs = definition['inputs']
        buffer_seconds = definition['buffer_seconds']
        
        all_matching_times = []
        
        for imp_idx, channels_data in enumerate(imports_data):
            input_a = inputs.get('A', '')
            if not input_a or input_a not in channels_data:
                continue
            
            df_a = channels_data[input_a]
            times = df_a['SECONDS'].values
            
            aligned_values = {}
            for label in INPUT_LABELS:
                input_ch = inputs.get(label, '')
                if input_ch and input_ch in channels_data:
                    df = channels_data[input_ch]
                    times_ch = df['SECONDS'].values
                    values_raw = df['VALUE'].values
                    
                    indices = np.searchsorted(times_ch, times)
                    indices = np.clip(indices, 1, len(times_ch) - 1)
                    
                    diff_before = times - times_ch[indices - 1]
                    diff_after = times_ch[indices] - times
                    use_after = diff_after <= diff_before
                    
                    aligned = np.where(use_after, values_raw[indices], values_raw[indices - 1])
                    aligned = np.where(indices == 0, values_raw[0], aligned)
                    aligned = np.where(indices >= len(times_ch), values_raw[-1], aligned)
                    
                    aligned_values[label] = aligned
                else:
                    aligned_values[label] = np.zeros(len(times))
            
            try:
                context = {'np': np}
                context.update(aligned_values)
                result = eval(expression, {"__builtins__": {}}, context)
                
                if isinstance(result, np.ndarray):
                    bool_mask = result.astype(bool)
                else:
                    bool_mask = np.full(len(times), bool(result))
                
                # Convert to absolute (display) time
                # Absolute = local + offset (what's shown on chart)
                matching_local_times = times[bool_mask]
                matching_absolute_times = matching_local_times + time_offsets[imp_idx]
                all_matching_times.extend(matching_absolute_times)
                
            except Exception as e:
                print(f"Error evaluating filter '{filter_name}' for import {imp_idx}: {e}")
                continue
        
        # Merge all matching times into intervals
        if all_matching_times:
            intervals = [(t - buffer_seconds, t + buffer_seconds) for t in all_matching_times]
            intervals.sort(key=lambda x: x[0])
            merged = [intervals[0]]
            for start, end in intervals[1:]:
                if start <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))
            filter_unified_intervals[filter_name] = merged
        else:
            filter_unified_intervals[filter_name] = []
    
    # PHASE 2: Apply unified intervals to each import
    has_any_show = any(defn['mode'] == 'show' for _, defn in active_filters)
    results = []
    
    for imp_idx, channels_data in enumerate(imports_data):
        channel_masks = {}
        for ch_name, ch_df in channels_data.items():
            if has_any_show:
                channel_masks[ch_name] = np.zeros(len(ch_df), dtype=bool)
            else:
                channel_masks[ch_name] = np.ones(len(ch_df), dtype=bool)
        
        for filter_name, definition in reversed(active_filters):
            mode = definition['mode']
            unified_intervals = filter_unified_intervals.get(filter_name, [])
            
            if not unified_intervals:
                continue
            
            # Convert to local time (stored data times)
            # Local = absolute - offset
            local_intervals = [(start - time_offsets[imp_idx], end - time_offsets[imp_idx]) 
                               for start, end in unified_intervals]
            
            interval_starts = np.array([iv[0] for iv in local_intervals])
            interval_ends = np.array([iv[1] for iv in local_intervals])
            
            for ch_name, ch_df in channels_data.items():
                ch_times = ch_df['SECONDS'].values
                
                insert_idx = np.searchsorted(interval_starts, ch_times, side='right') - 1
                in_interval = np.zeros(len(ch_times), dtype=bool)
                valid_idx = insert_idx >= 0
                in_interval[valid_idx] = ch_times[valid_idx] <= interval_ends[insert_idx[valid_idx]]
                
                if mode == 'show':
                    channel_masks[ch_name] = channel_masks[ch_name] | in_interval
                else:
                    channel_masks[ch_name] = channel_masks[ch_name] & ~in_interval
        
        results.append(channel_masks)
    
    return results


def apply_filters_logic(filter_order, filters, channels_data):
    """
    Extracted filter application logic for unit testing (single import).
    
    This mirrors the logic in OBD2MainWindow._apply_filters but without UI dependencies.
    """
    INPUT_LABELS = ['A', 'B', 'C', 'D', 'E']
    
    # Collect enabled filters in order
    active_filters = []
    for name in filter_order:
        if name in filters and filters[name].get('enabled', True):
            active_filters.append((name, filters[name]))
    
    if not active_filters:
        return None  # No filters, show all
    
    # Initialize visibility mask for each channel (start with all visible)
    channel_masks = {}
    for ch_name, ch_df in channels_data.items():
        channel_masks[ch_name] = np.ones(len(ch_df), dtype=bool)
    
    # Check if any show filter exists (determines initial state)
    # If any show filter exists, start with nothing visible (shows add)
    # If only hide filters, start with all visible (hides remove)
    has_any_show = any(defn['mode'] == 'show' for _, defn in active_filters)
    if has_any_show:
        # Start with nothing visible
        for ch_name in channel_masks:
            channel_masks[ch_name] = np.zeros(len(channel_masks[ch_name]), dtype=bool)
    
    # Process filters BOTTOM to TOP (reverse order) so top = highest precedence
    for filter_name, definition in reversed(active_filters):
        expression = definition['expression']
        inputs = definition['inputs']
        mode = definition['mode']
        buffer_seconds = definition['buffer_seconds']
        
        input_a = inputs.get('A', '')
        if not input_a or input_a not in channels_data:
            continue
        
        # Get time points from input A
        df_a = channels_data[input_a]
        times = df_a['SECONDS'].values
        
        # Build aligned values for all inputs
        aligned_values = {}
        for label in INPUT_LABELS:
            input_ch = inputs.get(label, '')
            if input_ch and input_ch in channels_data:
                df = channels_data[input_ch]
                times_ch = df['SECONDS'].values
                values_raw = df['VALUE'].values
                
                # Vectorized alignment using searchsorted
                indices = np.searchsorted(times_ch, times)
                indices = np.clip(indices, 1, len(times_ch) - 1)
                
                # Choose nearest neighbor
                diff_before = times - times_ch[indices - 1]
                diff_after = times_ch[indices] - times
                use_after = diff_after <= diff_before
                
                aligned = np.where(use_after, values_raw[indices], values_raw[indices - 1])
                aligned = np.where(indices == 0, values_raw[0], aligned)
                aligned = np.where(indices >= len(times_ch), values_raw[-1], aligned)
                
                aligned_values[label] = aligned
            else:
                aligned_values[label] = np.zeros(len(times))
        
        try:
            # Build evaluation context (simplified for testing)
            context = {'np': np}
            context.update(aligned_values)
            
            # Evaluate expression
            result = eval(expression, {"__builtins__": {}}, context)
            
            # Convert to boolean mask
            if isinstance(result, np.ndarray):
                bool_mask = result.astype(bool)
            else:
                bool_mask = np.full(len(times), bool(result))
            
            # Get matching time points
            matching_times = times[bool_mask]
            
            if len(matching_times) == 0:
                continue
            
            # Convert to intervals [t - buffer, t + buffer]
            intervals = [(t - buffer_seconds, t + buffer_seconds) for t in matching_times]
            
            # Merge overlapping intervals
            intervals.sort(key=lambda x: x[0])
            merged = [intervals[0]]
            for start, end in intervals[1:]:
                if start <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))
            
            # Apply this filter's effect to each channel's mask
            interval_starts = np.array([iv[0] for iv in merged])
            interval_ends = np.array([iv[1] for iv in merged])
            
            for ch_name, ch_df in channels_data.items():
                ch_times = ch_df['SECONDS'].values
                
                # Check which points fall within the merged intervals
                insert_idx = np.searchsorted(interval_starts, ch_times, side='right') - 1
                in_interval = np.zeros(len(ch_times), dtype=bool)
                valid_idx = insert_idx >= 0
                in_interval[valid_idx] = ch_times[valid_idx] <= interval_ends[insert_idx[valid_idx]]
                
                # Apply based on mode
                if mode == 'show':
                    # Show mode: add matching points to visible set
                    channel_masks[ch_name] = channel_masks[ch_name] | in_interval
                else:
                    # Hide mode: remove matching points from visible set
                    channel_masks[ch_name] = channel_masks[ch_name] & ~in_interval
                    
        except Exception as e:
            print(f"Error evaluating filter '{filter_name}': {e}")
            continue
    
    return channel_masks


class TestSingleHideFilter:
    """Test single hide filter behavior."""
    
    def test_hide_filter_removes_matching_points(self):
        """A single hide filter should remove points where expression is true."""
        # Create test data: values 0-9 at times 0-9
        times = np.arange(10, dtype=float)
        values = np.arange(10, dtype=float)
        
        channels_data = {
            'test_channel': create_test_channel(times, values)
        }
        
        # Hide where A < 5 (should hide values 0,1,2,3,4)
        filter_order = ['hide_low']
        filters = {
            'hide_low': {
                'expression': 'A < 5',
                'inputs': {'A': 'test_channel'},
                'mode': 'hide',
                'buffer_seconds': 0.1,
                'enabled': True
            }
        }
        
        result = apply_filters_logic(filter_order, filters, channels_data)
        
        # Should have 5 visible points (values 5,6,7,8,9)
        visible_count = np.sum(result['test_channel'])
        assert visible_count == 5, f"Expected 5 visible, got {visible_count}"
        
        # Check specific indices
        assert not result['test_channel'][0], "Value 0 should be hidden"
        assert not result['test_channel'][4], "Value 4 should be hidden"
        assert result['test_channel'][5], "Value 5 should be visible"
        assert result['test_channel'][9], "Value 9 should be visible"


class TestMultipleHideFilters:
    """Test multiple hide filters stacking."""
    
    def test_two_hide_filters_stack_correctly(self):
        """Two hide filters should each remove their matching points."""
        # Create test data: values 0-9 at times 0-9
        times = np.arange(10, dtype=float)
        values = np.arange(10, dtype=float)
        
        channels_data = {
            'test_channel': create_test_channel(times, values)
        }
        
        # Filter 1: Hide where A < 3 (hides 0,1,2)
        # Filter 2: Hide where A > 7 (hides 8,9)
        # Result: visible = 3,4,5,6,7 (5 points)
        filter_order = ['hide_low', 'hide_high']
        filters = {
            'hide_low': {
                'expression': 'A < 3',
                'inputs': {'A': 'test_channel'},
                'mode': 'hide',
                'buffer_seconds': 0.1,
                'enabled': True
            },
            'hide_high': {
                'expression': 'A > 7',
                'inputs': {'A': 'test_channel'},
                'mode': 'hide',
                'buffer_seconds': 0.1,
                'enabled': True
            }
        }
        
        result = apply_filters_logic(filter_order, filters, channels_data)
        
        # Should have 5 visible points (values 3,4,5,6,7)
        visible_count = np.sum(result['test_channel'])
        assert visible_count == 5, f"Expected 5 visible, got {visible_count}"
        
        # Check specific indices
        assert not result['test_channel'][0], "Value 0 should be hidden"
        assert not result['test_channel'][2], "Value 2 should be hidden"
        assert result['test_channel'][3], "Value 3 should be visible"
        assert result['test_channel'][7], "Value 7 should be visible"
        assert not result['test_channel'][8], "Value 8 should be hidden"
        assert not result['test_channel'][9], "Value 9 should be hidden"
    
    def test_overlapping_hide_filters(self):
        """Two hide filters with overlapping ranges should work correctly."""
        times = np.arange(10, dtype=float)
        values = np.arange(10, dtype=float)
        
        channels_data = {
            'test_channel': create_test_channel(times, values)
        }
        
        # Filter 1: Hide where A < 5 (hides 0,1,2,3,4)
        # Filter 2: Hide where A < 7 (hides 0,1,2,3,4,5,6)
        # Result: visible = 7,8,9 (3 points)
        filter_order = ['hide_low1', 'hide_low2']
        filters = {
            'hide_low1': {
                'expression': 'A < 5',
                'inputs': {'A': 'test_channel'},
                'mode': 'hide',
                'buffer_seconds': 0.1,
                'enabled': True
            },
            'hide_low2': {
                'expression': 'A < 7',
                'inputs': {'A': 'test_channel'},
                'mode': 'hide',
                'buffer_seconds': 0.1,
                'enabled': True
            }
        }
        
        result = apply_filters_logic(filter_order, filters, channels_data)
        
        # Should have 3 visible points (values 7,8,9)
        visible_count = np.sum(result['test_channel'])
        assert visible_count == 3, f"Expected 3 visible, got {visible_count}"


class TestShowFilter:
    """Test show filter behavior."""
    
    def test_single_show_filter(self):
        """A single show filter should only show matching points."""
        times = np.arange(10, dtype=float)
        values = np.arange(10, dtype=float)
        
        channels_data = {
            'test_channel': create_test_channel(times, values)
        }
        
        # Show where A > 5 (should show values 6,7,8,9)
        filter_order = ['show_high']
        filters = {
            'show_high': {
                'expression': 'A > 5',
                'inputs': {'A': 'test_channel'},
                'mode': 'show',
                'buffer_seconds': 0.1,
                'enabled': True
            }
        }
        
        result = apply_filters_logic(filter_order, filters, channels_data)
        
        # Should have 4 visible points (values 6,7,8,9)
        visible_count = np.sum(result['test_channel'])
        assert visible_count == 4, f"Expected 4 visible, got {visible_count}"


class TestShowHidePrecedence:
    """Test show + hide filter precedence."""
    
    def test_hide_after_show_removes_from_shown(self):
        """Hide filter below show: show has higher precedence, overrides hide."""
        times = np.arange(10, dtype=float)
        values = np.arange(10, dtype=float)
        
        channels_data = {
            'test_channel': create_test_channel(times, values)
        }
        
        # Filter order: show_high (top, highest precedence), hide_very_high (bottom)
        # Process bottom to top: hide_very_high first, then show_high
        # 1. Start with nothing visible (has show filter)
        # 2. hide_very_high: removes 8,9 from nothing → still nothing
        # 3. show_high: adds 4,5,6,7,8,9 → 6 visible (show overrides hide)
        # Result: 6 visible
        filter_order = ['show_high', 'hide_very_high']
        filters = {
            'show_high': {
                'expression': 'A > 3',
                'inputs': {'A': 'test_channel'},
                'mode': 'show',
                'buffer_seconds': 0.1,
                'enabled': True
            },
            'hide_very_high': {
                'expression': 'A > 7',
                'inputs': {'A': 'test_channel'},
                'mode': 'hide',
                'buffer_seconds': 0.1,
                'enabled': True
            }
        }
        
        result = apply_filters_logic(filter_order, filters, channels_data)
        
        # Should have 6 visible points (values 4,5,6,7,8,9) - show has higher precedence
        visible_count = np.sum(result['test_channel'])
        assert visible_count == 6, f"Expected 6 visible, got {visible_count}"
        
        # Check specific indices
        assert not result['test_channel'][3], "Value 3 should be hidden (not in show)"
        assert result['test_channel'][4], "Value 4 should be visible"
        assert result['test_channel'][8], "Value 8 should be visible (show overrides hide)"
        assert result['test_channel'][9], "Value 9 should be visible (show overrides hide)"
    
    def test_show_after_hide_adds_back(self):
        """Show filter after hide should add points back to visible set."""
        times = np.arange(10, dtype=float)
        values = np.arange(10, dtype=float)
        
        channels_data = {
            'test_channel': create_test_channel(times, values)
        }
        
        # Filter order: hide_low (top, highest precedence), show_two (bottom)
        # Process bottom to top: show_two first, then hide_low
        # 1. Start with nothing visible (has show filter)
        # 2. show_two: adds value 2 → 1 visible
        # 3. hide_low: removes 0,1,2,3,4 → removes 2 → 0 visible
        # Result: 0 visible (hide has higher precedence)
        filter_order = ['hide_low', 'show_two']
        filters = {
            'hide_low': {
                'expression': 'A < 5',
                'inputs': {'A': 'test_channel'},
                'mode': 'hide',
                'buffer_seconds': 0.1,
                'enabled': True
            },
            'show_two': {
                'expression': 'A == 2',
                'inputs': {'A': 'test_channel'},
                'mode': 'show',
                'buffer_seconds': 0.1,
                'enabled': True
            }
        }
        
        result = apply_filters_logic(filter_order, filters, channels_data)
        
        # Should have 0 visible points (hide has higher precedence, removes the shown point)
        visible_count = np.sum(result['test_channel'])
        assert visible_count == 0, f"Expected 0 visible, got {visible_count}"


class TestFilterOrder:
    """Test that filter order determines precedence."""
    
    def test_order_matters_for_show_hide(self):
        """Changing filter order should change the result."""
        times = np.arange(10, dtype=float)
        values = np.arange(10, dtype=float)
        
        channels_data = {
            'test_channel': create_test_channel(times, values)
        }
        
        filters = {
            'show_mid': {
                'expression': '(A >= 3) & (A <= 7)',
                'inputs': {'A': 'test_channel'},
                'mode': 'show',
                'buffer_seconds': 0.1,
                'enabled': True
            },
            'hide_five': {
                'expression': 'A == 5',
                'inputs': {'A': 'test_channel'},
                'mode': 'hide',
                'buffer_seconds': 0.1,
                'enabled': True
            }
        }
        
        # Order 1: show_mid (top, highest precedence), hide_five (bottom)
        # Process bottom to top: hide_five first, then show_mid
        # 1. Start with nothing visible (has show filter)
        # 2. hide_five: removes 5 from nothing → still nothing
        # 3. show_mid: adds 3,4,5,6,7 → 5 visible
        # Result: 5 visible (show has higher precedence, overrides hide)
        result1 = apply_filters_logic(['show_mid', 'hide_five'], filters, channels_data)
        visible1 = np.sum(result1['test_channel'])
        
        # Order 2: hide_five (top, highest precedence), show_mid (bottom)
        # Process bottom to top: show_mid first, then hide_five
        # 1. Start with nothing visible (has show filter)
        # 2. show_mid: adds 3,4,5,6,7 → 5 visible
        # 3. hide_five: removes 5 → 4 visible
        # Result: 4 visible (hide has higher precedence)
        result2 = apply_filters_logic(['hide_five', 'show_mid'], filters, channels_data)
        visible2 = np.sum(result2['test_channel'])
        
        assert visible1 == 5, f"Order 1: Expected 5 visible, got {visible1}"
        assert visible2 == 4, f"Order 2: Expected 4 visible, got {visible2}"
        assert visible1 != visible2, "Order should matter!"


class TestCrossImportFilterSync:
    """Test that filter matches from one import apply to all imports."""
    
    def test_filter_match_in_one_import_affects_all(self):
        """If import 1 matches filter at t=5, import 2 should also show t=5."""
        # Import 1: has a spike at t=5 (value=100)
        times1 = np.arange(10, dtype=float)
        values1 = np.array([0, 0, 0, 0, 0, 100, 0, 0, 0, 0], dtype=float)
        
        # Import 2: no spike, all zeros
        times2 = np.arange(10, dtype=float)
        values2 = np.zeros(10, dtype=float)
        
        imports_data = [
            {'test_channel': create_test_channel(times1, values1)},
            {'test_channel': create_test_channel(times2, values2)},
        ]
        
        # Filter: show where A > 50 (only import 1 has this at t=5)
        filter_order = ['show_spike']
        filters = {
            'show_spike': {
                'expression': 'A > 50',
                'inputs': {'A': 'test_channel'},
                'mode': 'show',
                'buffer_seconds': 0.5,
                'enabled': True
            }
        }
        
        # Apply filter to both imports using multi-import function
        results = apply_filters_multi_import(filter_order, filters, imports_data)
        
        # Import 1 should have visible points around t=5
        visible1 = np.sum(results[0]['test_channel'])
        assert visible1 > 0, "Import 1 should have visible points (has the spike)"
        
        # Import 2 should ALSO show points around t=5 because import 1 matched
        visible2 = np.sum(results[1]['test_channel'])
        assert visible2 > 0, (
            f"Import 2 should have visible points because import 1 matched at t=5. "
            f"Got {visible2} visible points. "
            f"Filter intervals should be shared across imports."
        )
        
        # Both should have same number of visible points (same time range)
        assert visible1 == visible2, f"Both imports should show same time range: {visible1} vs {visible2}"
    
    def test_filter_with_time_offset(self):
        """Filter match at t=5 in import 1 should match t=5.5 in import 2 with +0.5s offset."""
        # Import 1: spike at t=5 (local time = absolute time)
        times1 = np.arange(10, dtype=float)
        values1 = np.array([0, 0, 0, 0, 0, 100, 0, 0, 0, 0], dtype=float)
        
        # Import 2: same local times, but offset by +0.5s
        # So import 2's local t=5 corresponds to absolute t=5.5
        # And absolute t=5 corresponds to import 2's local t=4.5
        times2 = np.arange(10, dtype=float)
        values2 = np.zeros(10, dtype=float)
        
        imports_data = [
            {'test_channel': create_test_channel(times1, values1)},
            {'test_channel': create_test_channel(times2, values2)},
        ]
        time_offsets = [0.0, 0.5]  # Import 2 is offset by +0.5s
        
        filter_order = ['show_spike']
        filters = {
            'show_spike': {
                'expression': 'A > 50',
                'inputs': {'A': 'test_channel'},
                'mode': 'show',
                'buffer_seconds': 0.5,
                'enabled': True
            }
        }
        
        # Apply with offsets
        results = apply_filters_multi_import(filter_order, filters, imports_data, time_offsets)
        
        # Import 1 matches at local t=5 (absolute t=5)
        visible1 = np.sum(results[0]['test_channel'])
        assert visible1 > 0, "Import 1 should have visible points"
        
        # Import 2 should show points around local t=5.5 (absolute t=5 + offset 0.5)
        # With buffer 0.5s, the interval is [4.5, 5.5] in absolute time
        # For import 2 (offset +0.5), local interval is [5.0, 6.0]
        visible2 = np.sum(results[1]['test_channel'])
        assert visible2 > 0, (
            f"Import 2 should have visible points at local t=5-6 (absolute t=4.5-5.5). "
            f"Got {visible2} visible points."
        )
    
    def test_hide_filter_cross_import(self):
        """Hide filter match in one import should hide from all imports."""
        # Import 1: has a spike at t=5
        times1 = np.arange(10, dtype=float)
        values1 = np.array([0, 0, 0, 0, 0, 100, 0, 0, 0, 0], dtype=float)
        
        # Import 2: no spike
        times2 = np.arange(10, dtype=float)
        values2 = np.zeros(10, dtype=float)
        
        imports_data = [
            {'test_channel': create_test_channel(times1, values1)},
            {'test_channel': create_test_channel(times2, values2)},
        ]
        
        # Hide filter: hide where A > 50 (only import 1 has this at t=5)
        filter_order = ['hide_spike']
        filters = {
            'hide_spike': {
                'expression': 'A > 50',
                'inputs': {'A': 'test_channel'},
                'mode': 'hide',
                'buffer_seconds': 0.5,
                'enabled': True
            }
        }
        
        results = apply_filters_multi_import(filter_order, filters, imports_data)
        
        # Both imports should have t=5 hidden
        # Import 1: 10 points - 1 hidden = 9 visible
        visible1 = np.sum(results[0]['test_channel'])
        assert visible1 == 9, f"Import 1 should have 9 visible (t=5 hidden), got {visible1}"
        
        # Import 2: should also have t=5 hidden because import 1 matched
        visible2 = np.sum(results[1]['test_channel'])
        assert visible2 == 9, f"Import 2 should also have 9 visible (t=5 hidden), got {visible2}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
