@echo off
echo 🔧 Installing CuraBot Dependencies (Fixed Versions)
echo =================================================
echo.

cd backend

echo Activating virtual environment...
call ..\venv\Scripts\activate.bat

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Uninstalling conflicting packages first...
pip uninstall -y langchain langchain-community langchain-core langchain-google-genai langgraph langsmith google-generativeai chromadb sentence-transformers pydantic numpy pandas sqlalchemy httpx -q

echo.
echo Installing fresh dependencies...
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install pydantic==2.5.3
pip install python-dotenv==1.0.0

pip install langchain==0.1.0
pip install langchain-community==0.0.10
pip install langchain-core==0.1.10
pip install langchain-google-genai==0.0.11
pip install langgraph==0.0.20
pip install langsmith==0.0.77

pip install google-generativeai==0.3.2

pip install chromadb==0.4.22
pip install sentence-transformers==2.2.2

pip install numpy==1.24.3
pip install pandas==2.0.3
pip install sqlalchemy==2.0.19

pip install websockets==12.0
pip install python-multipart==0.0.6
pip install aiofiles==23.2.1

pip install pdfplumber==0.10.3
pip install reportlab==4.0.9

pip install pytest==7.4.3
pip install pytest-asyncio==0.21.1
pip install httpx==0.24.1

echo.
echo ✅ All dependencies installed successfully!
echo.
pip list | findstr langchain
pip list | findstr google
echo.
pause