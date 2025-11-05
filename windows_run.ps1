# PowerShell launcher for OBD Data Viewer
Write-Host "OBD Data Viewer - PowerShell Launcher" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

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

# Add src to Python path and run the viewer
Write-Host "Launching OBD Data Viewer..." -ForegroundColor Blue
$env:PYTHONPATH = "$PSScriptRoot\src;$env:PYTHONPATH"

try {
    python src\full_featured_viewer.py
} catch {
    Write-Host "Error occurred while running the viewer" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "OBD Data Viewer closed successfully" -ForegroundColor Green
