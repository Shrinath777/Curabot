@echo off
title CuraBot Installer
echo ========================================
echo    CuraBot Installation Script
echo ========================================
echo.

:: Check if running as admin
NET SESSION >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  This script needs administrator privileges.
    echo    Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo ✅ Running with administrator privileges
echo.

:: Navigate to script directory
cd /d "%~dp0"
echo 📁 Working directory: %CD%
echo.

:: Remove existing venv
if exist venv (
    echo 🗑️  Removing existing virtual environment...
    rmdir /s /q venv
)

:: Create new venv
echo 📦 Creating Python virtual environment...
python -m venv venv
if %errorLevel% neq 0 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment created
echo.

:: Activate venv
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment activated
echo.

:: Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip
echo.

:: Install backend packages
echo 📚 Installing Python packages...
echo.

set packages=fastapi==0.104.1 uvicorn[standard]==0.24.0 langgraph==0.1.0 langchain==0.1.0 chromadb==0.4.22 sentence-transformers==2.2.2 pydantic==2.5.0 python-dotenv==1.0.0 sqlalchemy==2.0.23 numpy==1.24.3 pandas==2.1.3 websockets==12.0 python-multipart==0.0.6 pytest==7.4.3 pytest-asyncio==0.21.1 httpx==0.25.1

for %%p in (%packages%) do (
    echo Installing %%p...
    pip install %%p
    if !errorlevel! neq 0 (
        echo ⚠️  Warning: Failed to install %%p
    )
)

echo ✅ Backend packages installed
echo.

:: Frontend installation
echo ⚛️ Installing frontend packages...
echo.

if not exist frontend (
    echo 📁 Creating frontend directory...
    mkdir frontend
)

cd frontend

:: Check if node is installed
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Node.js is not installed!
    echo    Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo ✅ Node.js found
echo.

:: Create package.json if it doesn't exist
if not exist package.json (
    echo Creating package.json...
    echo {> package.json
    echo   "name": "curabot-frontend",>> package.json
    echo   "private": true,>> package.json
    echo   "version": "1.0.0",>> package.json
    echo   "type": "module",>> package.json
    echo   "scripts": {>> package.json
    echo     "dev": "vite",>> package.json
    echo     "build": "tsc && vite build",>> package.json
    echo     "preview": "vite preview">> package.json
    echo   }>> package.json
    echo }>> package.json
)

:: Install npm packages
echo Installing React packages...
npm install react@18.2.0 react-dom@18.2.0
npm install axios@1.6.2 socket.io-client@4.5.4
npm install framer-motion@10.16.16
npm install @headlessui/react@1.7.17 @heroicons/react@2.0.18
npm install react-chartjs-2@5.2.0 chart.js@4.4.1
npm install date-fns@2.30.0
npm install zustand@4.4.7
npm install -D @types/react@18.2.43 @types/react-dom@18.2.17
npm install -D @vitejs/plugin-react@4.2.1 autoprefixer@10.4.16 postcss@8.4.32 tailwindcss@3.3.6 typescript@5.2.2 vite@5.0.8

echo ✅ Frontend packages installed
echo.

cd ..

echo ========================================
echo ✅ INSTALLATION COMPLETE!
echo ========================================
echo.
echo 📝 Next steps:
echo.
echo 1. Start Backend:
echo    cd "%CD%"
echo    venv\Scripts\activate
echo    cd backend
echo    python main.py
echo.
echo 2. Start Frontend (in new terminal):
echo    cd "%CD%\frontend"
echo    npm run dev
echo.
echo 3. Open browser: http://localhost:5173
echo.
pause