@echo off
setlocal

echo TerraSim Qt Desktop
echo.

if not exist "desktop\main.py" (
    echo ERROR: Run this script from the TerraSim repository root.
    exit /b 1
)

python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo PyQt5 is not installed.
    echo Install the desktop dependencies with: python -m pip install -r requirements.txt
    exit /b 1
)

python terrasim.py %*
exit /b %errorlevel%
