"""
Expression evaluation helpers for math channels and filters.

Provides safe math functions and statistical functions for use in
user-defined expressions.
"""

import numpy as np

# Shared help text for expression dialogs (DRY)
EXPRESSION_HELP_TEXT = (
    "<b>Inputs:</b> A, B, C, D, E<br>"
    "<b>Arithmetic:</b> +, -, *, /, **, %, comparisons (&lt;, &gt;, ==)<br>"
    "<b>Boolean:</b> &amp; (and), | (or), ~ (not)<br>"
    "<b>Functions:</b> abs, min, max, sqrt, log, exp, sin, cos, round, pow, floor, ceil<br>"
    "<b>Statistical:</b> rolling_avg(X, secs), rolling_min(X, secs), rolling_max(X, secs), delta, clip(X, min, max)<br>"
    "<b>Conditional:</b> if_else(condition, true_value, false_value)"
)


def get_math_functions():
    """Return dict of safe math functions available in expressions."""
    return {
        # Basic math
        'abs': abs,
        'min': min,
        'max': max,
        'round': round,
        'pow': pow,
        # Numpy math functions
        'sqrt': np.sqrt,
        'log': np.log,
        'log10': np.log10,
        'exp': np.exp,
        'sin': np.sin,
        'cos': np.cos,
        'tan': np.tan,
        'floor': np.floor,
        'ceil': np.ceil,
        # Constants
        'pi': np.pi,
        'e': np.e,
    }


def get_statistical_functions(times: np.ndarray = None):
    """Return dict of statistical functions for array operations.
    
    Args:
        times: Optional array of timestamps in seconds. If provided, rolling
               window functions will use seconds instead of data points.
    """
    def _seconds_to_points(seconds: float) -> int:
        """Convert seconds to approximate number of data points based on sample rate."""
        if times is None or len(times) < 2:
            return max(1, int(seconds))  # Fallback: treat as points
        # Estimate sample rate from timestamps
        avg_dt = (times[-1] - times[0]) / (len(times) - 1)
        if avg_dt <= 0:
            return max(1, int(seconds))
        points = int(seconds / avg_dt)
        return max(1, points)
    
    def rolling_avg(arr, window_seconds):
        """Compute rolling average with given window size in seconds."""
        window = _seconds_to_points(window_seconds)
        result = np.convolve(arr, np.ones(window)/window, mode='same')
        # Handle edges - use available data
        half = window // 2
        for i in range(half):
            if i < len(arr):
                result[i] = np.mean(arr[:i+half+1])
        for i in range(len(arr) - half, len(arr)):
            if i >= 0:
                result[i] = np.mean(arr[i-half:])
        return result
    
    def rolling_min(arr, window_seconds):
        """Compute rolling minimum with given window size in seconds."""
        window = _seconds_to_points(window_seconds)
        result = np.zeros_like(arr)
        for i in range(len(arr)):
            start = max(0, i - window // 2)
            end = min(len(arr), i + window // 2 + 1)
            result[i] = np.min(arr[start:end])
        return result
    
    def rolling_max(arr, window_seconds):
        """Compute rolling maximum with given window size in seconds."""
        window = _seconds_to_points(window_seconds)
        result = np.zeros_like(arr)
        for i in range(len(arr)):
            start = max(0, i - window // 2)
            end = min(len(arr), i + window // 2 + 1)
            result[i] = np.max(arr[start:end])
        return result
    
    def delta(arr):
        """Compute point-to-point difference (derivative approximation)."""
        result = np.zeros_like(arr)
        result[1:] = np.diff(arr)
        result[0] = result[1] if len(result) > 1 else 0
        return result
    
    def cumsum(arr):
        """Compute cumulative sum."""
        return np.cumsum(arr)
    
    def clip(arr, min_val, max_val):
        """Clip values to range [min_val, max_val]."""
        return np.clip(arr, min_val, max_val)
    
    return {
        'rolling_avg': rolling_avg,
        'rolling_min': rolling_min,
        'rolling_max': rolling_max,
        'delta': delta,
        'cumsum': cumsum,
        'clip': clip,
        'np_min': np.min,  # Array-wide min
        'np_max': np.max,  # Array-wide max
        'np_mean': np.mean,  # Array-wide mean
        'np_std': np.std,  # Standard deviation
    }
