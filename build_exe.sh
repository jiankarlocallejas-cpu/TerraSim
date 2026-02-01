#!/bin/bash
# TerraSim PyInstaller Build Script for macOS/Linux
# Creates standalone executable

echo ""
echo "========================================"
echo "   TerraSim Build with PyInstaller"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Please install Python3 first."
    exit 1
fi

echo "[1/3] Installing/updating PyInstaller..."
pip3 install --upgrade pyinstaller

echo ""
echo "[2/3] Cleaning previous builds..."
rm -rf build dist __pycache__

echo ""
echo "[3/3] Building TerraSim executable..."
pyinstaller --onefile --windowed \
  --add-data "backend:backend" \
  --add-data "frontend:frontend" \
  --add-data "sample_data:sample_data" \
  --name TerraSim \
  app.py

echo ""
echo "========================================"
echo "   Build Complete!"
echo "========================================"
echo "Executable created: dist/TerraSim"
echo ""
