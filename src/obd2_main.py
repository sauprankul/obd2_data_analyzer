#!/usr/bin/env python3
"""
Main entry point for the OBD2 Data Visualization Tool.

This script provides a clean, professional interface for launching the OBD2
data visualization application with proper error handling and logging.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from obd2_viewer.app.main_application import OBD2ViewerApp


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
    """Main function to run the OBD2 Data Visualization Tool."""
    print("=" * 60)
    print("🚗 OBD2 Data Visualization Tool")
    print("=" * 60)
    print("A professional tool for analyzing and comparing OBD2 sensor data")
    print()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create and run the application
        logger.info("Starting OBD2 Data Visualization Tool")
        
        # Initialize the main application
        cache_file = Path(__file__).parent.parent / "recent_folders.json"
        app = OBD2ViewerApp(cache_file=str(cache_file))
        
        print("🌐 Starting web application...")
        print("📊 The application will open in your web browser")
        print("🔗 URL: http://localhost:8052")
        print("⏹️  Press Ctrl+C to stop the server")
        print()
        
        # Run the application
        app.run(debug=True, port=8052)
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        logger.info("Application stopped by user")
        
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        logger.error(f"Error starting application: {e}")
        sys.exit(1)
    
    finally:
        print("\n✅ OBD2 Data Visualization Tool closed successfully")


if __name__ == '__main__':
    main()
