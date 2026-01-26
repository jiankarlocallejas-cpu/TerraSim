#!/usr/bin/env pwsh
<#
TerraSim - Python-Only Application Launcher
This script starts the complete TerraSim application (Backend + GUI)
#>

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TerraSim - Soil Erosion Modeling System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating Python virtual environment..." -ForegroundColor Yellow
& "./.venv/Scripts/Activate.ps1"

# Install/update dependencies
Write-Host "Checking dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt 2>$null

Write-Host "Starting TerraSim application..." -ForegroundColor Green
Write-Host ""

# Run the app
python app.py

Read-Host "Press Enter to exit"
