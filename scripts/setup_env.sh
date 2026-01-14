#!/bin/bash

# Setup environment for AI Browser Agent
# Usage: bash scripts/setup_env.sh

set -e

echo "Setting up AI Browser Agent..."
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate || . venv/Scripts/activate

echo "Virtual environment activated"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies..."
pip install -e .

# Install playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env and add your ANTHROPIC_API_KEY"
else
    echo ".env file already exists"
fi

# Create necessary directories
echo "Creating project directories..."
mkdir -p screenshots
mkdir -p test_results
mkdir -p logs

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your ANTHROPIC_API_KEY"
echo "2. Run: python -m src.main"
echo ""
echo "Activate environment in future with:"
echo "  source venv/bin/activate  (macOS/Linux)"
echo "  venv\\Scripts\\activate    (Windows)"
