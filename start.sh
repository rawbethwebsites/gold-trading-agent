#!/bin/bash
# Gold Trading Agent - Startup Script
# Exness + MT5 Local-First Trading Agent

echo "🚀 Gold Trading Agent - Exness + MT5"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the gold-trading-agent directory"
    exit 1
fi

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check environment file
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Warning: backend/.env not found"
    echo "   Copy backend/.env.example to backend/.env and configure your settings"
    echo ""
fi

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     OS_TYPE=Linux;;
    Darwin*)    OS_TYPE=Mac;;
    CYGWIN*)    OS_TYPE=Windows;;
    MINGW*)     OS_TYPE=Windows;;
    MSYS*)      OS_TYPE=Windows;;
    *)          OS_TYPE="UNKNOWN:${OS}"
esac

echo "📱 Detected OS: $OS_TYPE"
echo ""

# Warn about MT5 on non-Windows
if [ "$OS_TYPE" != "Windows" ]; then
    echo "⚠️  Note: MetaTrader 5 requires Windows"
    echo "   On macOS/Linux, the system will use Mock Mode for testing"
    echo "   To use real trading, either:"
    echo "     1. Run this on Windows with MT5 installed"
    echo "     2. Use a Windows VM"
    echo "     3. Set DATA_PROVIDER=mock in backend/.env"
    echo ""
fi

# Start Backend
echo "📡 Starting Backend (FastAPI)..."
cd backend

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
pip install -q -r requirements.txt

# Run backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "   Waiting for backend to initialize..."
sleep 3

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start"
    echo "   Check backend logs for errors"
    exit 1
fi

echo "   ✅ Backend running on http://localhost:8000"
echo ""

# Start Frontend
echo "🎨 Starting Frontend (Next.js)..."
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    npm install
fi

# Run frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend
echo "   Waiting for frontend to initialize..."
sleep 3

# Check if frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start"
    cleanup
fi

echo "   ✅ Frontend running on http://localhost:3005"
echo ""

echo "======================================"
echo "✅ Gold Trading Agent is running!"
echo "======================================"
echo ""
echo "  📊 Dashboard:  http://localhost:3005"
echo "  🔌 API:        http://localhost:8000"
echo "  📖 API Docs:   http://localhost:8000/docs"
echo ""
echo "  💡 Quick checks:"
echo "     curl http://localhost:8000/api/status"
echo "     curl http://localhost:8000/api/price"
echo ""
echo "  Press Ctrl+C to stop"
echo ""

# Wait for both processes
wait
