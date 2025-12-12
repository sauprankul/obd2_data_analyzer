# OBD2 Data Visualization Tool

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional **native Windows application** for visualizing and comparing OBD2 (On-Board Diagnostics) CSV data from vehicles. Built with PyQt6 and PyQtGraph for high-performance chart rendering.

## 🚀 Features

- **Native Windows Application**: Fast, responsive UI with no browser overhead
- **Multi-Import Comparison**: Load multiple CSV files and compare them side-by-side with time synchronization
- **Math Channels**: Create calculated channels using expressions like `(A/0.45) * 14.7`
- **Multi-Channel CSV Support**: Handles interleaved multi-channel OBD2 data (Car Scanner format)
- **Synchronized Time Navigation**: All channels stay in sync with granular time controls (0.1s to 5min)
- **Channel Visibility Controls**: Show/hide individual channels with per-import checkboxes
- **LOD Optimization**: Level-of-detail downsampling for smooth performance with large datasets
- **Crosshair & Value Display**: Click on charts to see exact values from all imports
- **Adjustable Graph Heights**: Taller/Shorter buttons to customize chart sizes
- **Recent Files**: Quick access to recently analyzed data
- **Window State Persistence**: Remembers window size, position, and panel layout

## 📦 Installation

### Prerequisites

- Python 3.9 or higher
- Windows 10/11

### Quick Start (Recommended)

1. **Install dependencies**:
   ```bash
   pip install PyQt6 pyqtgraph numpy pandas scipy
   ```

2. **Run the native application**:
   ```bash
   python src/obd2_native.py
   ```

   Or double-click `run_native.bat`

### Windows Users

Simply double-click:
```
run_native.bat
```

This will automatically install dependencies if needed and launch the application.

### Development Installation

For development with testing and code quality tools:
```bash
pip install -r requirements-dev.txt
```

## 📊 Data Format

The tool expects CSV files with the following columns:

### Required Columns
- `SECONDS`: Timestamp in seconds
- `VALUE`: Sensor reading/value

### Optional Columns
- `UNITS`: Unit of measurement (e.g., "rpm", "mph", "°F")
- `PID`: Parameter ID (sensor name)

### Example CSV Format
```csv
SECONDS;VALUE;UNITS;PID
0;800;rpm;Engine RPM
1;1200;rpm;Engine RPM
2;1500;rpm;Engine RPM
```

## 🎯 Usage

### 1. Load Data
- Launch the application
- Upload CSV files using the drag-and-drop interface
- Or select from recent folders

### 2. Visualize
- Select PIDs to display using checkboxes
- Use time navigation controls to focus on specific time ranges
- Zoom in/out for detailed analysis

### 3. Organize
- Create custom groups to organize related sensors
- Add/remove PIDs from groups as needed
- Rearrange groups for better comparison

### 4. Analyze
- Hover over charts to see detailed values
- Compare multiple sensors on the same timeline
- Export charts for reports

## 🏗️ Architecture

The application follows a clean, modular architecture:

```
src/
├── obd2_native.py              # Application entry point
└── obd2_viewer/
    ├── core/                   # Core data processing
    │   ├── data_loader.py      # CSV file loading and validation
    │   ├── data_processor.py   # Data filtering and analysis
    │   └── multi_channel_parser.py  # Multi-channel CSV parsing
    └── native/                 # Native Windows GUI
        ├── main_window.py      # Main application window
        └── chart_widget.py     # PyQtGraph chart components
```

### Key Components

- **OBDDataLoader**: Handles CSV file loading with automatic format detection
- **MultiChannelCSVParser**: Parses interleaved multi-channel CSV files
- **OBD2MainWindow**: Main PyQt6 application window with all controls
- **OBD2ChartWidget**: High-performance chart rendering with LOD optimization

## 🧪 Testing

### Run All Tests
```bash
pytest test/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest test/ -v -m unit

# Integration tests
pytest test/ -v -m integration

# With coverage report
pytest test/ -v --cov=src --cov-report=html
```

### Test Performance
```bash
pytest test/ -v -m performance
```

## 🔧 Development

### Code Quality Tools

The project includes several code quality tools:

- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Safety**: Dependency vulnerability scanning
- **Bandit**: Security linting

### Format Code
```bash
black src/ test/
```

### Lint Code
```bash
flake8 src/ test/
```

### Type Check
```bash
mypy src/
```

### Security Check
```bash
safety check -r requirements.txt
bandit -r src/
```

## 📝 API Reference

### OBDDataLoader

```python
from obd2_viewer.core.data_loader import OBDDataLoader

loader = OBDDataLoader("path/to/csv/files")
channels_data, units = loader.load_csv_files()
```

### Running the Application

```python
# From command line
python src/obd2_native.py

# Or double-click run_native.bat
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest test/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to new functions
- Write tests for new features
- Update documentation as needed
- Keep commits small and focused

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Full documentation](https://obd2-data-visualization.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/your-org/obd2-data-visualization/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/obd2-data-visualization/discussions)

## 🙏 Acknowledgments

- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- Charts powered by [PyQtGraph](https://www.pyqtgraph.org/)
- Data processing with [Pandas](https://pandas.pydata.org/) and [NumPy](https://numpy.org/)

## 📈 Roadmap

- [ ] Chart export (PNG, SVG)
- [ ] Advanced math operations (rolling average, derivatives)
- [ ] Data annotations and markers
- [ ] Session save/restore
- [ ] Additional CSV format support

---

**Made with ❤️ for automotive data analysis**
