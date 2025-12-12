@echo off
echo ============================================================
echo OBD2 Data Visualization Tool - Native Windows Edition
echo ============================================================
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install PyQt6 pyqtgraph numpy pandas scipy
    if errorlevel 1 (
        echo ERROR: Failed to install packages
        pause
        exit /b 1
    )
)

REM Run the native application
echo Starting native application...
python obd2_native.py

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
