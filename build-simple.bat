@echo off
title TerraSim Builder
color 0A

echo.
echo  ██████╗ ███████╗██████╗ ███████╗███████╗████████╗
echo  ██╔══██╗██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝
echo  ██║  ██║█████╗  ██████╔╝███████╗█████╗     ██║   
echo  ██║  ██║██╔══╝  ██╔══██╗╚════██║██╔══╝     ██║   
echo  ██████╔╝███████╗██║  ██║███████║███████╗   ██║   
echo  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝   
echo.
echo  🌍 Advanced GIS Erosion Modeling Platform
echo  ==========================================
echo.

echo [1/4] Checking Python...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/4] Installing build tools...
pip install pyinstaller >nul 2>&1
echo ✅ PyInstaller installed

echo.
echo [3/4] Installing Node.js dependencies...
npm install >nul 2>&1
echo ✅ Node.js dependencies installed

echo.
echo [4/4] Building executables...
python build-config.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Build failed. Check the error messages above.
    pause
    exit /b 1
)

echo.
echo 🎉 BUILD SUCCESSFUL!
echo ================
echo.
echo 📁 Your executables are ready:
echo    📂 dist\TerraSim-Backend.exe    - Python backend server
echo    📂 dist\TerraSim-Desktop.exe    - PyQt5 desktop application
echo    📂 dist-electron\TerraSim-Setup.exe - Electron installer
echo.
echo 🚀 Quick start:
echo    1. Run dist\TerraSim-Backend.exe
echo    2. Open http://localhost:8000 in your browser
echo.
echo 📚 For more options, run:
echo    npm run dev     - Development server
echo    npm run build   - Web build only
echo.
echo Press any key to exit...
pause >nul
