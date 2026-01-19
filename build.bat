@echo off
echo 🚀 TerraSim Build Script
echo =====================

echo 📦 Installing dependencies...
pip install pyinstaller
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install PyInstaller
    pause
    exit /b 1
)

npm install
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install Node.js dependencies
    pause
    exit /b 1
)

echo 🔨 Building all components...
python build-config.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Build failed
    pause
    exit /b 1
)

echo ✅ Build complete!
echo 📁 Check dist/ folder for executables
echo.
echo 🎯 Available executables:
echo   - dist/TerraSim-Backend.exe (Python backend)
echo   - dist/TerraSim-Desktop.exe (PyQt5 desktop)
echo   - dist-electron/TerraSim-Setup.exe (Electron installer)
echo.
echo 🚀 To run the application:
echo   - Backend: dist/TerraSim-Backend.exe
echo   - Desktop: dist/TerraSim-Desktop.exe
echo   - Web: npm run dev (then open http://localhost:3000)
echo.
pause
