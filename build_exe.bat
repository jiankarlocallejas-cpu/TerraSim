@echo off
REM TerraSim PyInstaller Build Script for Windows
REM Creates standalone executable

echo.
echo ========================================
echo   TerraSim Build with PyInstaller
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)

echo [1/3] Installing/updating PyInstaller...
pip install --upgrade pyinstaller

echo.
echo [2/3] Cleaning previous builds...
rmdir /s /q build dist __pycache__ 2>nul

echo.
echo [3/3] Building TerraSim executable...
pyinstaller --onefile --windowed ^
  --add-data "backend:backend" ^
  --add-data "frontend:frontend" ^
  --add-data "sample_data:sample_data" ^
  --name TerraSim ^
  app.py

echo.
echo ========================================
echo   Build Complete!
echo ========================================
echo Executable created: dist\TerraSim.exe
echo.
