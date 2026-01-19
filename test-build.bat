@echo off
echo Testing TerraSim Build Environment
echo ==================================

echo.
echo Checking dependencies...
echo.

echo [Python]
python --version 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Python installed
) else (
    echo ❌ Python not found
)

echo.
echo [Node.js]
node --version 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Node.js installed
) else (
    echo ❌ Node.js not found
)

echo.
echo [npm]
npm --version 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ npm installed
) else (
    echo ❌ npm not found
)

echo.
echo [PyInstaller]
pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ PyInstaller installed
) else (
    echo ❌ PyInstaller not installed
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo [Project files]
if exist "backend\main.py" (
    echo ✅ Backend file found
) else (
    echo ❌ Backend file not found
)

if exist "frontend\src\index.ts" (
    echo ✅ Frontend files found
) else (
    echo ❌ Frontend files not found
)

if exist "package.json" (
    echo ✅ package.json found
) else (
    echo ❌ package.json not found
)

echo.
echo Test complete. Press any key to continue...
pause
