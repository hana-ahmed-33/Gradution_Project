@echo off
echo 🎯 Finance Analyzer Enhanced - Quick Start
echo ==========================================

echo.
echo 🔄 Setting up enhanced features...

REM Setup database and dependencies
python quick_setup.py
if errorlevel 1 (
    echo ❌ Setup failed!
    pause
    exit /b 1
)

echo.
echo 🚀 Starting Finance Analyzer Enhanced...
echo.
echo 📱 Access points:
echo    • Main App: http://localhost:8000/
echo    • Dashboard: http://localhost:8000/dashboard  
echo    • API Docs: http://localhost:8000/docs
echo.
echo 💡 Press Ctrl+C to stop the server
echo.

REM Start the server
python main.py

pause