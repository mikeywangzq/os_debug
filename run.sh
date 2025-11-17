#!/bin/bash
# Quick start script for OS Debugging Assistant

echo "🔍 OS Debugging Assistant"
echo "=========================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    cd backend
    pip3 install -r requirements.txt
    cd ..
    echo "✓ Dependencies installed"
    echo ""
fi

# Run tests
echo "🧪 Running tests..."
python3 test_analyzer.py
echo ""

# Start the server
echo "🚀 Starting web server..."
echo ""
echo "   Access the application at: http://localhost:5000"
echo "   Press Ctrl+C to stop the server"
echo ""

cd backend
python3 app.py
