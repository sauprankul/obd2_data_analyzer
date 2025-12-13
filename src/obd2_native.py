#!/usr/bin/env python3
"""
Native Windows OBD2 Data Visualization Tool

A high-performance native Windows application for analyzing and comparing
OBD2 sensor data. Uses PyQt6 for the UI and PyQtGraph for hardware-accelerated
chart rendering.

NO BROWSER. NO WEB SERVER. PURE NATIVE WINDOWS.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('obd2_viewer.log')
        ]
    )


def main():
    """Main function to run the native OBD2 Data Visualization Tool."""
    print("=" * 60)
    print("🚗 OBD2 Data Visualization Tool - Native Windows Edition")
    print("=" * 60)
    print("High-performance native application for OBD2 data analysis")
    print()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Import PyQt6 - this will fail fast if not installed
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont, QIcon
        
        # Import main window
        from obd2_viewer.main_window import OBD2MainWindow
        
        logger.info("Starting Native OBD2 Data Visualization Tool")
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("OBD2 Data Visualization Tool")
        app.setOrganizationName("OBD2Viewer")
        app.setOrganizationDomain("obd2viewer.local")
        
        # Set application style
        app.setStyle("Fusion")
        
        # Set default font
        font = QFont("Segoe UI", 9)
        app.setFont(font)
        
        # Set application icon (for taskbar)
        if getattr(sys, 'frozen', False):
            # Running as compiled exe - logo.ico is bundled in same folder as exe
            icon_path = Path(sys.executable).parent / "logo.ico"
        else:
            # Running from source - use logo.png from project root
            icon_path = Path(__file__).parent.parent / "logo.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # Create and show main window
        window = OBD2MainWindow()
        window.show()
        
        print("✅ Application started successfully!")
        print("📊 Open a CSV file to begin visualization")
        print()
        
        # Run event loop
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"\n❌ Missing required package: {e}")
        print("\nPlease install the required packages:")
        print("  pip install PyQt6 pyqtgraph numpy pandas scipy")
        logger.error(f"Import error: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        logger.error(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
