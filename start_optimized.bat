@echo off
echo ========================================
echo VoiceBot - PERFORMANCE OPTIMIZED Startup
echo ========================================
echo.

echo [1/5] Checking Ollama status...
ollama ps
echo.

echo [2/5] Loading phi3:mini model (fastest)...
ollama run phi3:mini "Hi" > nul 2>&1
echo Model loaded into memory ✓
echo.

echo [3/5] Setting performance environment variables...
set DEBUG=false
set LOG_LEVEL=WARNING
set MAX_TOKENS_PER_REQUEST=500
set GUARDRAILS_ENABLED=false
set PROMETHEUS_ENABLED=false
set OLLAMA_KEEP_ALIVE=10m
echo Performance settings applied ✓
echo.

echo [4/5] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo [5/5] Starting optimized server...
echo ========================================
echo.
echo 🚀 Server starting with PERFORMANCE OPTIMIZATIONS:
echo    • Model: phi3:mini (fastest)
echo    • Max Tokens: 500 (reduced for speed)
echo    • Logging: Minimal
echo    • Guardrails: Disabled
echo    • Monitoring: Disabled
echo.
echo Expected Response Time: 2-6 seconds
echo.
echo API Server: http://localhost:9011
echo Voice Chat: http://localhost:9011/static/voice_improved.html
echo API Docs: http://localhost:9011/docs
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

python -m uvicorn src.api.main:app --reload --port 9011 --log-level warning
