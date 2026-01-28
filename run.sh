#!/bin/bash
# TerraSim - macOS/Linux Launch Script
# This script launches the TerraSim application with authentication

echo ""
echo "============================================================"
echo "TerraSim - Terrain Simulation Platform"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.10 or higher"
    echo ""
    echo "On macOS (with Homebrew):"
    echo "  brew install python3"
    echo ""
    echo "On Ubuntu/Debian:"
    echo "  sudo apt-get install python3 python3-pip"
    echo ""
    exit 1
fi

# Check if virtual environment exists, if not create one
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import tkinter; import numpy; import sqlalchemy; import matplotlib" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip install -q -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install required packages"
        exit 1
    fi
fi

# Launch the application
echo "Launching TerraSim..."
echo ""
python3 terrasim.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Application failed to launch"
    exit 1
fi
