"""
TerraSim Build Configuration
Executable bundling setup for cross-platform deployment
"""

import os
import sys
import subprocess
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
ELECTRON_DIR = PROJECT_ROOT / "electron"
DESKTOP_DIR = PROJECT_ROOT / "desktop"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"

def create_build_dirs():
    """Create build and distribution directories"""
    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)

def build_backend():
    """Build Python backend executable using PyInstaller"""
    print("[CONFIG] Building Python backend...")
    
    spec_file = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{BACKEND_DIR / "main.py"}'],
    pathex=['{PROJECT_ROOT}'],
    binaries=[],
    datas=[
        ('{BACKEND_DIR}', 'backend'),
        ('{FRONTEND_DIR / "dist"}', 'frontend'),
    ],
    hiddenimports=[
        'geopandas',
        'rasterio', 
        'shapely',
        'pyproj',
        'fastapi',
        'uvicorn',
        'numpy',
        'pandas',
        'scipy',
        'sklearn'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TerraSim-Backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    spec_path = PROJECT_ROOT / "backend.spec"
    with open(spec_path, 'w') as f:
        f.write(spec_file)
    
    # Run PyInstaller
    try:
        subprocess.run([
            'pyinstaller', 
            '--clean', 
            str(spec_path)
        ], check=True, cwd=PROJECT_ROOT)
        print("[OK] Backend built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Backend build failed: {e}")
        return False

def build_frontend():
    """Build frontend web application"""
    print("🌐 Building frontend web app...")
    
    try:
        # Install dependencies if needed
        subprocess.run(['npm', 'install'], check=True, cwd=PROJECT_ROOT)
        
        # Build for production
        subprocess.run(['npm', 'run', 'build'], check=True, cwd=PROJECT_ROOT)
        print("[OK] Frontend built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Frontend build failed: {e}")
        return False

def build_electron():
    """Build Electron desktop application"""
    print("🖥️ Building Electron desktop app...")
    
    try:
        # Install Electron dependencies
        subprocess.run(['npm', 'install'], check=True, cwd=ELECTRON_DIR)
        
        # Build Electron app
        subprocess.run(['npm', 'run', 'build'], check=True, cwd=ELECTRON_DIR)
        print("[OK] Electron app built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Electron build failed: {e}")
        return False

def build_pyqt():
    """Build PyQt5 desktop application"""
    print("🖼️ Building PyQt5 desktop app...")
    
    try:
        # Use PyInstaller for PyQt app
        spec_file = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{DESKTOP_DIR / "main.py"}'],
    pathex=['{PROJECT_ROOT}'],
    binaries=[],
    datas=[
        ('{DESKTOP_DIR}', 'desktop'),
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'geopandas',
        'rasterio',
        'shapely',
        'matplotlib',
        'plotly'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TerraSim-Desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
        
        spec_path = PROJECT_ROOT / "desktop.spec"
        with open(spec_path, 'w') as f:
            f.write(spec_file)
        
        subprocess.run([
            'pyinstaller', 
            '--clean', 
            str(spec_path)
        ], check=True, cwd=PROJECT_ROOT)
        print("[OK] PyQt5 app built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] PyQt5 build failed: {e}")
        return False

def create_installer():
    """Create installer packages"""
    print("📦 Creating installers...")
    
    # Windows NSIS installer (if available)
    if sys.platform == "win32":
        try:
            # Create NSIS script
            nsis_script = f"""
!define APPNAME "TerraSim"
!define VERSION "2.0.0"
!define PUBLISHER "TerraSim Team"

Name "${{APPNAME}}"
OutFile "${{APPNAME}}-${{VERSION}}-Setup.exe"
InstallDir "$PROGRAMFILES\\${{APPNAME}}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    File /r "dist\\TerraSim-Backend\\*"
    CreateShortCut "$DESKTOP\\${{APPNAME}}.lnk" "$INSTDIR\\TerraSim-Backend.exe"
    CreateShortCut "$STARTMENU\\Programs\\${{APPNAME}}.lnk" "$INSTDIR\\TerraSim-Backend.exe"
SectionEnd
"""
            
            nsis_path = PROJECT_ROOT / "installer.nsi"
            with open(nsis_path, 'w') as f:
                f.write(nsis_script)
            
            print("[NOTE] NSIS installer script created")
            print("🔨 Run with: makensis installer.nsi")
            
        except Exception as e:
            print(f"[WARN] Could not create NSIS installer: {e}")

def main():
    """Main build process"""
    print("STARTING TERRASIM BUILD PROCESS...")
    
    create_build_dirs()
    
    # Build components
    success = True
    
    # 1. Build frontend
    if not build_frontend():
        success = False
    
    # 2. Build backend
    if not build_backend():
        success = False
    
    # 3. Build Electron app
    if not build_electron():
        success = False
    
    # 4. Build PyQt5 app
    if not build_pyqt():
        success = False
    
    # 5. Create installers
    create_installer()
    
    if success:
        print("\n🎉 Build completed successfully!")
        print("[FOLDER] Check the 'dist' folder for executables")
    else:
        print("\n[ERROR] Build completed with errors")
        print("[CONFIG] Check the logs above for details")

if __name__ == "__main__":
    main()
