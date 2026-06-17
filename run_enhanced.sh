#!/bin/bash

echo "🎯 Finance Analyzer Enhanced - Quick Start"
echo "=========================================="

echo ""
echo "🔄 Setting up enhanced features..."

# Setup database and dependencies
python3 quick_setup.py
if [ $? -ne 0 ]; then
    echo "❌ Setup failed!"
    exit 1
fi

echo ""
echo "🚀 Starting Finance Analyzer Enhanced..."
echo ""
echo "📱 Access points:"
echo "   • Main App: http://localhost:8000/"
echo "   • Dashboard: http://localhost:8000/dashboard"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 main.py