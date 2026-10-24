#!/usr/bin/env bash
set -e

echo "TerraSim Qt Desktop"

if [ ! -f "desktop/main.py" ]; then
    echo "ERROR: Run this script from the TerraSim repository root."
    exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! "$PYTHON_BIN" -c "import PyQt5" >/dev/null 2>&1; then
    echo "PyQt5 is not installed."
    echo "Install the desktop dependencies with: $PYTHON_BIN -m pip install -r requirements.txt"
    exit 1
fi

exec "$PYTHON_BIN" terrasim.py "$@"
