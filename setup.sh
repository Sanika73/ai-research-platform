#!/bin/bash

# AI Research Platform Setup Script
# This script sets up the development environment for the AI Research Platform

set -e

echo "🔬 AI Research Platform Setup"
echo "=============================="

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.8"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    echo "✅ Python $python_version is compatible"
else
    echo "❌ Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r config/requirements.txt
echo "✅ Dependencies installed"

# Initialize database
echo "🗄️ Initializing database..."
python -c "from models.database import init_db; init_db()"
echo "✅ Database initialized"

# Check for .env file
echo "🔐 Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  Creating .env template file..."
    cat > .env << EOL
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration (optional)
# DATABASE_URL=sqlite:///research_platform.db

# Debug Mode (optional)
# DEBUG=false
EOL
    echo "⚠️  Please edit .env file and add your OpenAI API key"
    echo "    You can get your API key from: https://platform.openai.com/api-keys"
else
    echo "✅ Environment file exists"
fi

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Run the application:"
echo "   source .venv/bin/activate"
echo "   python app.py"
echo ""
echo "3. Open your browser to: http://localhost:8000"
echo ""
echo "For more information, see README.md"
