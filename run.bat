@echo off
REM TerraSim - Windows Launch Script
REM This script launches the TerraSim application with authentication

echo.
echo ============================================================
echo TerraSim - Terrain Simulation Platform
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from https://www.python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import tkinter; import numpy; import sqlalchemy; import matplotlib" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Required packages not installed
    echo Please run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Launch the application
echo Launching TerraSim...
echo.
python terrasim.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Application failed to launch
    pause
    exit /b 1
)
