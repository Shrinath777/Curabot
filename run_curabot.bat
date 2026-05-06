@echo off
title CuraBot Launcher
color 0A
echo ========================================
echo    🚀 CuraBot - AI Differential Diagnosis
echo ========================================
echo.

:: Check if running in correct directory
if not exist backend (
    echo ❌ Error: backend folder not found!
    echo Please run this from the curabot project root.
    pause
    exit /b 1
)

:: Kill any existing processes
echo Stopping any existing servers...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: Clear screen
cls
echo ========================================
echo    🚀 Starting CuraBot Servers...
echo ========================================
echo.

:: Start Backend in new window (visible)
echo 1️⃣ Starting Backend Server...
start "CuraBot Backend" cmd /k "cd /d C:\projects\tcs project\curabot\backend && echo [BACKEND] Starting... && python main.py"

:: Wait for backend to initialize
echo Waiting for backend to start (5 seconds)...
timeout /t 5 /nobreak >nul

:: Start Frontend in new window (visible)
echo 2️⃣ Starting Frontend Server...
start "CuraBot Frontend" cmd /k "cd /d C:\projects\tcs project\curabot\frontend && echo [FRONTEND] Starting... && npm run dev"

:: Wait for frontend
timeout /t 3 /nobreak >nul

:: Open browser
echo 3️⃣ Opening Browser...
start http://localhost:5173

echo.
echo ========================================
echo ✅ CuraBot is running!
echo 📱 Frontend: http://localhost:5173
echo 🔧 Backend:  http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo ℹ️  Two windows should now be open:
echo   1. Backend window (running Python)
echo   2. Frontend window (running Vite)
echo.
echo 📌 To stop servers, just close both windows
echo.
pause