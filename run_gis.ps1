# TerraSim GIS Launcher - PowerShell Script
# Starts the new GIS-style terrain simulation interface

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "TerraSim GIS - Terrain Simulator" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    python --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Install/update dependencies
Write-Host "Checking dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt -q 2>$null

Write-Host ""
Write-Host "Starting TerraSim GIS Interface..." -ForegroundColor Green
Write-Host ""

# Run the application
python run_gis.py

Read-Host "Press Enter to exit"
