#!/bin/bash
echo "🚀 TerraSim Build Script"
echo "====================="

echo "📦 Installing dependencies..."
pip install pyinstaller
npm install

echo "🔨 Building all components..."
python build-config.py

echo "✅ Build complete!"
echo "📁 Check dist/ folder for executables"
