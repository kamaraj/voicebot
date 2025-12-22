@echo off
echo ========================================
echo Fixing Model Configuration
echo ========================================
echo.

echo Current .env has: phi3:mini
echo Changing to: tinyllama:latest
echo.

powershell -Command "(Get-Content .env) -replace 'OLLAMA_MODEL=phi3:mini', 'OLLAMA_MODEL=tinyllama:latest' | Set-Content .env"

echo.
echo ✓ Updated .env to use tinyllama:latest
echo.

echo Stopping phi3:mini...
ollama stop phi3:mini

echo.
echo Loading tinyllama...
ollama run tinyllama:latest "Ready for ultra-fast responses"

echo.
echo ========================================
echo Configuration Fixed!
echo ========================================
echo.
echo IMPORTANT: You must restart the server now:
echo   1. Press Ctrl+C in the server terminal
echo   2. Run: python -m uvicorn src.api.main:app --reload --port 9011
echo.
echo After restart, you should see LLM time around 300-500ms!
echo.
pause
