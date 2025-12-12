# Runtime hook to fix PyQt6 DLL loading on Windows
# This must run BEFORE PyQt6 is imported

import os
import sys

def _setup_pyqt6_dll_path():
    """Add the _internal directory to DLL search path for PyQt6."""
    if sys.platform == 'win32':
        # Get the base path (where the exe is)
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Add the base path to DLL search directories
        if hasattr(os, 'add_dll_directory'):
            # Python 3.8+ on Windows
            os.add_dll_directory(base_path)
            
            # Also add PyQt6 Qt6 bin path if it exists
            pyqt6_qt6_bin = os.path.join(base_path, 'PyQt6', 'Qt6', 'bin')
            if os.path.exists(pyqt6_qt6_bin):
                os.add_dll_directory(pyqt6_qt6_bin)
        
        # Also prepend to PATH as fallback
        os.environ['PATH'] = base_path + os.pathsep + os.environ.get('PATH', '')

_setup_pyqt6_dll_path()
