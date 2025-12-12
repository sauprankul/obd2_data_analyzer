# PowerShell launcher for OBD2 Data Visualization Tool
Write-Host "OBD2 Data Visualization Tool" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Change to script directory
Set-Location $PSScriptRoot

# Check if requirements.txt exists
if (-not (Test-Path "requirements.txt")) {
    Write-Host "Error: requirements.txt not found" -ForegroundColor Red
    Write-Host "Please ensure requirements.txt is in the same directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Blue
try {
    python -m pip install -r requirements.txt
} catch {
    Write-Host "Error installing dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Run the new OBD2 viewer application
Write-Host "Starting OBD2 Data Visualization Tool..." -ForegroundColor Blue
Write-Host "This will open in your web browser at http://localhost:8052" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    python src\obd2_main.py
} catch {
    Write-Host "Error running the OBD2 Data Visualization Tool" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "OBD2 Data Visualization Tool closed successfully" -ForegroundColor Green
