@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM TerraSim Application Launcher
REM ============================================================
REM Automatically launches Backend API + Frontend Web Dev Server
REM ============================================================

REM Set environment variables
set VENV_PATH=.venv
set LOG_DIR=logs
set BACKEND_PORT=8000
set FRONTEND_PORT=5173

echo.
echo ============================================================
echo TerraSim Application Launcher
echo ============================================================
echo.

REM Check if running from correct directory
if not exist "backend" (
    echo ERROR: Please run this script from the TerraSim root directory
    echo Current directory: %cd%
    pause
    exit /b 1
)

REM Check virtual environment
if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo.
    echo ERROR: Virtual environment not found at %VENV_PATH%
    echo Please run setup.bat first to initialize the environment
    echo.
    pause
    exit /b 1
)

echo Activating virtual environment...
call "%VENV_PATH%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Create logs directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Check dependencies
echo Checking required packages...
python -c "import numpy, geopandas, shapely, rasterio, sqlalchemy, fastapi, pydantic, uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Required packages not installed
    echo Please run: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Dependencies validated successfully.
echo.

REM ============================================================
REM Parse command line arguments
REM ============================================================
if "%1"=="" (
    REM Default: Launch full stack (Backend + Frontend)
    set MODE=all
) else (
    set MODE=%1
)

REM Validate mode
if /i "%MODE%"=="desktop" goto launch_desktop
if /i "%MODE%"=="backend" goto launch_backend
if /i "%MODE%"=="frontend" goto launch_frontend
if /i "%MODE%"=="all" goto launch_all

echo.
echo ERROR: Invalid launch mode '%MODE%'
echo.
echo Usage: run.bat [mode]
echo.
echo Available modes:
echo   all       - Backend API + Web Frontend (DEFAULT)
echo   frontend  - Web Frontend development server only
echo   backend   - Backend API server only
echo   desktop   - Desktop application
echo.
echo Example: run.bat frontend
echo.
exit /b 1

REM ============================================================
REM Launch Desktop Application
REM ============================================================
:launch_desktop
echo Launching TerraSim Desktop Application...
echo Mode: Desktop UI with integrated backend
echo.
python terrasim.py
goto end

REM ============================================================
REM Launch Backend API Server
REM ============================================================
:launch_backend
echo Launching TerraSim Backend API Server...
echo Mode: Backend API (Frontend/Desktop clients can connect)
echo API Server: http://localhost:%BACKEND_PORT%
echo Geoprocessing: 40+ REST endpoints for advanced analysis
echo.
if not exist "%LOG_DIR%\backend.log" (
    echo Backend starting... > "%LOG_DIR%\backend.log"
)
python -m uvicorn backend.api:app --host 0.0.0.0 --port %BACKEND_PORT% --reload
goto end

REM ============================================================
REM Launch Frontend Web Dev Server Only
REM ============================================================
:launch_frontend
echo Launching TerraSim Web Frontend...
echo Mode: Frontend development server
echo Web UI: http://localhost:%FRONTEND_PORT%
echo Connect to backend at: http://localhost:%BACKEND_PORT%
echo.
cd frontend-web
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)
start "TerraSim Web Frontend" cmd /k "npm run dev"
timeout /t 3 /nobreak
echo Opening browser to http://localhost:%FRONTEND_PORT%...
powershell -Command "Start-Process 'http://localhost:%FRONTEND_PORT%'" 2>nul
cd ..
echo.
echo Frontend server started in separate window
echo Press any key to return to main window...
pause
goto end

REM ============================================================
REM Launch Full Stack (Backend + Frontend) - DEFAULT MODE
REM ============================================================
:launch_all
echo Launching TerraSim Full Stack (Automatic)...
echo Mode: Backend API + Web Frontend
echo.
echo This will open 2 terminal windows:
echo   1. Backend API Server (http://localhost:%BACKEND_PORT%)
echo   2. Frontend Web Server (http://localhost:%FRONTEND_PORT%)
echo.
echo Then open your default browser to http://localhost:%FRONTEND_PORT%
echo.
timeout /t 2 /nobreak

REM Start backend in separate window with persistent console
echo [%date% %time%] Starting Backend API Server...
start "TerraSim Backend API" cmd /k "python -m uvicorn backend.api:app --host 0.0.0.0 --port %BACKEND_PORT% --reload"
timeout /t 4 /nobreak

REM Check if backend is running
echo [%date% %time%] Checking Backend API connection...
powershell -Command "for ($i=0; $i -lt 5; $i++) { try { $null = Invoke-WebRequest -Uri 'http://localhost:%BACKEND_PORT%/docs' -UseBasicParsing -TimeoutSec 1; Write-Host 'Backend API is running'; exit 0 } catch { if ($i -lt 4) { Start-Sleep -Milliseconds 500 } } }; Write-Host 'Backend API may not be ready yet (continuing anyway)'" 2>nul

REM Start frontend in separate window
echo [%date% %time%] Starting Frontend Web Server...
cd frontend-web
if not exist "node_modules" (
    echo Installing frontend dependencies...
    npm install
)
start "TerraSim Web Frontend" cmd /k "npm run dev"
cd ..
timeout /t 5 /nobreak

REM Open browser automatically
echo [%date% %time%] Opening browser...
powershell -Command "Start-Process 'http://localhost:%FRONTEND_PORT%'" 2>nul

echo.
echo ============================================================
echo TerraSim Full Stack started successfully!
echo ============================================================
echo.
echo Backend API:  http://localhost:%BACKEND_PORT%
echo Web Frontend: http://localhost:%FRONTEND_PORT%
echo API Docs:     http://localhost:%BACKEND_PORT%/docs
echo.
echo To stop the servers:
echo   1. Close the Backend API window, or
echo   2. Close the Frontend window, or
echo   3. Press Ctrl+C in each window
echo.
echo Logs saved to: logs\
echo ============================================================
echo.
pause
goto end

REM ============================================================
REM Error handling and cleanup
REM ============================================================
:end
if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo ERROR: Application exited with error code %errorlevel%
    echo ============================================================
    if exist "%LOG_DIR%\backend.log" (
        echo.
        echo Recent backend logs:
        type "%LOG_DIR%\backend.log" | findstr /r ".*" | more
    )
    echo.
    echo For support, check:
    echo  - logs/ directory for detailed error information
    echo  - README.md for troubleshooting
    echo  - DEVELOPMENT.md for development setup
    echo.
    pause
)
endlocal
exit /b %errorlevel%
