@echo off
REM TerraSim GIS Launcher - Windows Batch Script
REM Starts the new GIS-style terrain simulation interface

echo.
echo ====================================
echo TerraSim GIS - Terrain Simulator
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

echo Checking dependencies...
python -m pip install -r requirements.txt --quiet

echo.
echo Starting TerraSim GIS Interface...
echo.

REM Run the application
python run_gis.py

pause
