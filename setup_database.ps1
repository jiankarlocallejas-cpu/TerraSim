#Requires -Version 5.0
<#
.SYNOPSIS
    TerraSim Database Setup Script for Windows PowerShell
    
.DESCRIPTION
    This script automates the complete database initialization process for TerraSim.
    It handles virtual environment creation, dependency installation, and database setup.
    
.EXAMPLE
    .\setup_database.ps1
    
.NOTES
    Author: TerraSim Team
    Requires: Python 3.8+, PowerShell 5.0+
#>

param(
    [switch]$Force = $false
)

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

# Banner
Clear-Host
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "          TerraSim Database Setup - Automated" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python Installation
Write-Info "Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python found: $pythonVersion"
}
catch {
    Write-Error-Custom "Python is not installed or not in PATH"
    Write-Host ""
    Write-Host "Please install Python 3.8 or higher from:" -ForegroundColor Yellow
    Write-Host "https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check pip Installation
Write-Info "Checking pip installation..."
try {
    $pipVersion = pip --version 2>&1
    Write-Success "pip found: $pipVersion"
}
catch {
    Write-Error-Custom "pip is not installed"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check Virtual Environment
Write-Info "Checking virtual environment..."
if (Test-Path "venv") {
    Write-Info "Virtual environment already exists"
    Write-Info "Activating existing virtual environment..."
    & ".\venv\Scripts\Activate.ps1"
    Write-Success "Virtual environment activated"
}
else {
    Write-Info "Creating virtual environment..."
    python -m venv venv
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Failed to create virtual environment"
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Success "Virtual environment created"
    Write-Host ""
    Write-Info "Activating virtual environment..."
    & ".\venv\Scripts\Activate.ps1"
    Write-Success "Virtual environment activated"
}

Write-Host ""

# Upgrade pip
Write-Info "Upgrading pip..."
python -m pip install --upgrade pip --quiet
Write-Success "pip upgraded"

Write-Host ""

# Install requirements
Write-Info "Installing dependencies from requirements.txt..."
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Failed to install dependencies"
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Success "Dependencies installed"
}
else {
    Write-Error-Custom "requirements.txt not found"
    Write-Info "Please make sure you're in the TerraSim project root directory"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "          Running Database Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Run setup script
if (Test-Path "setup_database.py") {
    Write-Info "Running setup_database.py..."
    Write-Host ""
    python setup_database.py
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Database setup failed"
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
}
else {
    Write-Error-Custom "setup_database.py not found"
    Write-Info "Please make sure you're in the TerraSim project root directory"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "          Setup Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Success "Your TerraSim database is ready to use!"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. To start the backend server, run:" -ForegroundColor Yellow
Write-Host "   python backend/main.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Access the API documentation at:" -ForegroundColor Yellow
Write-Host "   http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Default admin credentials:" -ForegroundColor Yellow
Write-Host "   Email: admin@example.com" -ForegroundColor Yellow
Write-Host "   (Check .env file for default password)" -ForegroundColor Yellow
Write-Host ""
Write-Host "For more information, see: SETUP_INSTRUCTIONS.md" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"
exit 0
