@echo off
REM TerraSim Database Setup Script for Windows
REM This script automates the complete database initialization process
REM Created for TerraSim Research Platform

setlocal enabledelayedexpansion
title TerraSim Database Setup

REM Color codes for output
set GREEN=[92m
set RED=[91m
set YELLOW=[93m
set BLUE=[94m
set RESET=[0m

cls
echo.
echo ============================================================
echo          TerraSim Database Setup - Automated
echo ============================================================
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    color CF
    echo.
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python found
echo.

REM Check if pip is installed
echo Checking pip installation...
pip --version >nul 2>&1
if errorlevel 1 (
    color CF
    echo.
    echo [ERROR] pip is not installed
    echo.
    pause
    exit /b 1
)

echo [OK] pip found
echo.

REM Check if virtual environment exists
if exist "venv\" (
    echo Virtual environment already exists
    echo Activating existing virtual environment...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        color CF
        echo [ERROR] Failed to activate virtual environment
        pause
        exit /b 1
    )
) else (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        color CF
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        color CF
        echo [ERROR] Failed to activate virtual environment
        pause
        exit /b 1
    )
)

echo [OK] Virtual environment activated
echo.

REM Install/upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install requirements
echo.
echo Installing dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        color CF
        echo.
        echo [ERROR] Failed to install dependencies
        echo.
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
) else (
    color CF
    echo [ERROR] requirements.txt not found
    echo Please make sure you're in the TerraSim project root directory
    pause
    exit /b 1
)

echo.
echo ============================================================
echo          Running Database Setup
echo ============================================================
echo.

REM Run the setup script
if exist "setup_database.py" (
    echo Running setup_database.py...
    echo.
    python setup_database.py
    if errorlevel 1 (
        color CF
        echo.
        echo [ERROR] Database setup failed
        echo.
        pause
        exit /b 1
    )
) else (
    color CF
    echo [ERROR] setup_database.py not found
    echo Please make sure you're in the TerraSim project root directory
    pause
    exit /b 1
)

echo.
echo ============================================================
echo          Setup Complete!
echo ============================================================
echo.
echo Success! Your TerraSim database is ready to use.
echo.
echo Next steps:
echo 1. To start the backend server, run:
echo    python backend/main.py
echo.
echo 2. Access the API documentation at:
echo    http://localhost:8000/docs
echo.
echo 3. Default admin credentials:
echo    Email: admin@example.com
echo    (Check .env file for default password)
echo.
echo For more information, see: SETUP_INSTRUCTIONS.md
echo.
pause
exit /b 0
