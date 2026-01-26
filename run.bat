@echo off
REM TerraSim - Python-Only Application Launcher
REM This script starts the complete TerraSim application (Backend + GUI + Calculations)

echo ========================================
echo TerraSim - Soil Erosion Modeling System
echo ========================================
echo [MODE] Full Application with GIS + Calculations
echo ========================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo [ACTION] Activating Python virtual environment...
    call .venv\Scripts\activate.bat
)

REM Check if database exists
if not exist "test.db" (
    echo [ACTION] Initializing database...
    python setup_database.py
)

echo [ACTION] Starting TerraSim application...
echo [INFO] This will launch:
echo        - Backend API (Port 8000)
echo        - GIS Interface with Map Canvas
echo        - USPED Erosion Calculation Engine
echo        - Database Management System
echo.
echo [STATUS] Launching in 2 seconds...
timeout /t 2 /nobreak

echo Starting TerraSim...
cd /d "%~dp0"
python app.py

pause
