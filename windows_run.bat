@echo off
REM Windows launcher for OBD Data Viewer
echo OBD Data Viewer - Windows Launcher
echo ====================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo Error: requirements.txt not found
    echo Please ensure requirements.txt is in the same directory
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
python -m pip install -r requirements.txt

REM Add src to Python path and run the viewer
echo Launching OBD Data Viewer...
set PYTHONPATH=%~dp0src;%PYTHONPATH%
python src\full_featured_viewer.py

REM Pause on exit to see any errors
if errorlevel 1 (
    echo.
    echo Error occurred while running the viewer
    pause
)
