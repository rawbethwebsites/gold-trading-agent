@echo off
REM Gold Trading Agent - Windows Startup Script
REM Exness + MT5 Local-First Trading Agent

echo ============================================
echo  Gold Trading Agent - Windows
echo  Exness + MT5 Local-First
echo ============================================
echo.

REM Check if we're in the right directory
if not exist "backend\main.py" (
    echo Error: Please run this script from the gold-trading-agent directory
    pause
    exit /b 1
)

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

REM Check for Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js not found. Please install Node.js
    pause
    exit /b 1
)

echo Checking environment...

REM Check for .env file
if not exist "backend\.env" (
    echo Warning: backend\.env not found
    echo Please copy backend\.env.example to backend\.env and configure
    pause
)

REM Start Backend
echo.
echo [1/2] Starting Backend (FastAPI)...
cd backend

REM Create virtual environment if needed
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Installing Python dependencies...
pip install -q -r requirements.txt

REM Install MetaTrader5 (Windows only)
pip install -q MetaTrader5

echo Starting backend server...
start "Backend Server" cmd /k "python main.py"

cd ..

REM Wait for backend
TIMEOUT /T 3 /NOBREAK >nul

REM Start Frontend
echo.
echo [2/2] Starting Frontend (Next.js)...
cd frontend

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    call npm install
)

echo Starting frontend server...
start "Frontend Server" cmd /k "npm run dev"

cd ..

REM Wait for frontend
TIMEOUT /T 3 /NOBREAK >nul

echo.
echo ============================================
echo  Gold Trading Agent is running!
echo ============================================
echo.
echo   Dashboard:  http://localhost:3005
echo   API:        http://localhost:8000
echo   API Docs:   http://localhost:8000/docs
echo.
echo   Quick checks:
echo     curl http://localhost:8000/api/status
echo     curl http://localhost:8000/api/price
echo.
echo   Close the command windows to stop
echo.

REM Keep window open
pause
