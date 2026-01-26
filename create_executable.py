"""
PyInstaller Configuration for TerraSim Database Setup Executable

This script generates a standalone Windows .exe file for database setup.
The exe requires no Python installation on the end user's system.

Usage:
    1. Install PyInstaller: pip install pyinstaller
    2. Run this script: python create_executable.py
    3. Find exe in: ./dist/setup_database.exe

Created for: TerraSim Research Platform
"""


import os
import sys
from pathlib import Path

def create_executable():
    """Create standalone Windows executable for database setup"""
    
    print("=" * 60)
    print("TerraSim Database Setup - Executable Generator")
    print("=" * 60)
    print()
    
    # Verify we're in the right directory
    if not Path("setup_database.py").exists():
        print("[ERROR] Error: setup_database.py not found")
        print("Make sure you're in the TerraSim project root directory")
        sys.exit(1)
    
    print("[OK] Found setup_database.py")
    
    # Check for PyInstaller
    try:
        import PyInstaller.__main__  # type: ignore
        print("[OK] PyInstaller is installed")
    except (ImportError, AttributeError):
        print("[ERROR] PyInstaller not found")
        print("Install it with: pip install pyinstaller")
        sys.exit(1)
    
    print()
    print("Creating executable...")
    print("-" * 60)
    
    # PyInstaller arguments
    args = [
        "setup_database.py",
        "--name=setup_database",
        "--onefile",
        "--windowed=False",
        "--console",
        "--distpath=./dist",
        "--buildpath=./build",
        "--specpath=./",
        f"--add-data=requirements.txt:.",
        "--collect-submodules=backend",
        "--collect-submodules=alembic",
        "--hidden-import=backend",
        "--hidden-import=backend.db",
        "--hidden-import=backend.models",
        "--hidden-import=backend.schemas",
        "--hidden-import=backend.core",
        "--hidden-import=backend.services",
        "--hidden-import=alembic",
        "--hidden-import=alembic.config",
        "--hidden-import=sqlalchemy",
        "--hidden-import=pydantic",
        "--icon=NONE",
    ]
    
    try:
        PyInstaller.__main__.run(args)  # type: ignore
        print()
        print("=" * 60)
        print("[OK] Executable created successfully!")
        print("=" * 60)
        print()
        print("Location: ./dist/setup_database.exe")
        print()
        print("You can now:")
        print("1. Double-click setup_database.exe to run setup")
        print("2. Distribute setup_database.exe to end users")
        print("3. No Python installation required on target system")
        print()
        print("Note: The .exe file is ~50-100 MB (includes Python runtime)")
        print()
        
    except Exception as e:
        print()
        print("[ERROR] Error creating executable:")
        print(str(e))
        sys.exit(1)

if __name__ == "__main__":
    create_executable()
