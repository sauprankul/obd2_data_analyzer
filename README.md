# OBD2 Data Visualization Tool

[![CI/CD Pipeline](https://github.com/your-org/obd2-data-visualization/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/obd2-data-visualization/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/your-org/obd2-data-visualization/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/obd2-data-visualization)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional web-based tool for visualizing and comparing OBD2 (On-Board Diagnostics) CSV data from vehicles. Built with Plotly Dash, this application provides interactive dashboards for analyzing vehicle sensor data, creating custom groups, and exporting visualizations.

## 🚀 Features

- **Interactive Web Dashboard**: Modern, responsive interface built with Dash and Bootstrap
- **Multi-Format Support**: Handles various CSV formats with automatic delimiter detection
- **Real-Time Data Visualization**: Interactive charts with zoom, pan, and hover capabilities
- **PID Grouping**: Organize related sensors into custom groups for better analysis
- **Time Navigation**: Easily navigate through time-series data with intuitive controls
- **File Upload Interface**: Drag-and-drop or click-to-upload CSV files
- **Recent Folders**: Quick access to recently analyzed data folders
- **Data Validation**: Automatic validation and error handling for malformed files
- **Export Capabilities**: Save charts and analysis results

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/obd2-data-visualization.git
   cd obd2-data-visualization
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python src/obd2_main.py
   ```

4. **Open your browser** and navigate to `http://localhost:8052`

### Windows Users

Simply run the included PowerShell script:
```powershell
.\windows_run.ps1
```

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
src/obd2_viewer/
├── core/                    # Core data processing
│   ├── data_loader.py      # CSV file loading and validation
│   └── data_processor.py   # Data filtering and analysis
├── visualization/          # Dashboard and charts
│   └── dashboard.py        # Main Dash application
├── app/                     # Main application
│   └── main_application.py  # File upload and routing
└── utils/                   # Utilities
    └── file_utils.py        # File processing utilities
```

### Key Components

- **OBDDataLoader**: Handles CSV file loading with automatic format detection
- **OBDDataProcessor**: Provides data filtering, statistics, and group management
- **OBD2Dashboard**: Creates the interactive web visualization
- **OBD2ViewerApp**: Main application with file upload interface

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
data = loader.load_csv_files()
units = loader.get_units(data)
```

### OBDDataProcessor

```python
from obd2_viewer.core.data_processor import OBDDataProcessor

processor = OBDDataProcessor()
filtered_data = processor.filter_data_by_time(data, start_time, end_time)
stats = processor.get_statistics(data, "engine_rpm")
```

### OBD2Dashboard

```python
from obd2_viewer.visualization.dashboard import OBD2Dashboard

dashboard = OBD2Dashboard(data, units, display_names)
dashboard.run(debug=True, port=8052)
```

## 🚀 Deployment

### Docker (Coming Soon)

```bash
docker build -t obd2-viewer .
docker run -p 8052:8052 obd2-viewer
```

### Production

For production deployment, consider:

1. Use a production WSGI server (Gunicorn, uWSGI)
2. Set up reverse proxy (Nginx, Apache)
3. Configure SSL/TLS
4. Set up monitoring and logging

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

- Built with [Plotly Dash](https://dash.plotly.com/)
- UI components from [Dash Bootstrap Components](https://dash-bootstrap-components.opensource.faculty.ai/)
- Data processing with [Pandas](https://pandas.pydata.org/)

## 📈 Roadmap

- [ ] Docker containerization
- [ ] Cloud deployment options
- [ ] Advanced data analysis features
- [ ] Real-time data streaming support
- [ ] Mobile-responsive design improvements
- [ ] Additional chart types
- [ ] Data export in multiple formats
- [ ] User authentication and sharing

---

**Made with ❤️ for automotive data analysis**
