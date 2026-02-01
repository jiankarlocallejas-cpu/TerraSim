@echo off
REM TerraSim Development Setup Script for Windows
REM Automates initial setup for development

echo.
echo 🚀 TerraSim Development Setup
echo ==============================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python not found. Please install Python 3.9 or higher
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION% found
echo.

REM Create virtual environment
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --quiet --upgrade pip setuptools wheel
echo ✓ pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
pip install --quiet -r requirements.txt
echo ✓ Production dependencies installed
echo.

REM Install dev dependencies
echo Installing development dependencies...
pip install --quiet -r requirements-dev.txt
echo ✓ Development dependencies installed
echo.

REM Setup pre-commit
echo Setting up pre-commit hooks...
pre-commit install
echo ✓ Pre-commit hooks installed
echo.

REM Copy environment template
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
    echo ⚠️  Please edit .env with your configuration
) else (
    echo ✓ .env file already exists
)
echo.

REM Summary
echo ✅ Setup Complete!
echo.
echo Next steps:
echo 1. Edit .env with your configuration
echo 2. Run 'python app.py' to start API
echo 3. Run 'python terrasim.py' to start desktop UI
echo.
echo For more information:
echo   - Documentation: docs\DEVELOPMENT.md
echo   - Contributing: CONTRIBUTING.md
echo   - Architecture: docs\ARCHITECTURE.md
echo.
