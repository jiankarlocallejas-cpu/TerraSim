#!/bin/bash

# TerraSim Development Setup Script
# Automates initial setup for development

set -e

echo "🚀 TerraSim Development Setup"
echo "=============================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version found"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --quiet --upgrade pip setuptools wheel
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --quiet -r requirements.txt
echo "✓ Production dependencies installed"

# Install dev dependencies
echo ""
echo "Installing development dependencies..."
pip install --quiet -r requirements-dev.txt
echo "✓ Development dependencies installed"

# Setup pre-commit
echo ""
echo "Setting up pre-commit hooks..."
pre-commit install
echo "✓ Pre-commit hooks installed"

# Copy environment template
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration"
else
    echo "✓ .env file already exists"
fi

# Database setup (optional)
read -p "Setup database? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Setting up database..."
    python database_setup.py
    alembic upgrade head
    echo "✓ Database initialized"
fi

# Summary
echo ""
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Run 'python app.py' to start API"
echo "3. Run 'python terrasim.py' to start desktop UI"
echo ""
echo "For more information:"
echo "  - Documentation: docs/DEVELOPMENT.md"
echo "  - Contributing: CONTRIBUTING.md"
echo "  - Architecture: docs/ARCHITECTURE.md"
echo ""
