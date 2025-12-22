@echo off
echo ========================================
echo Switching to Faster AI Model
echo ========================================
echo.

echo Current model: llama3.1:8b (slow)
echo.
echo Choose a faster model:
echo   1. llama3.2:3b    - 3x faster, good quality
echo   2. phi3:mini      - 5x faster, smaller model  
echo   3. gemma2:2b      - 4x faster, Google's model
echo.

set /p choice="Enter choice (1/2/3): "

if "%choice%"=="1" (
    echo Pulling llama3.2:3b...
    ollama pull llama3.2:3b
    set MODEL=llama3.2:3b
) else if "%choice%"=="2" (
    echo Pulling phi3:mini...
    ollama pull phi3:mini
    set MODEL=phi3:mini
) else if "%choice%"=="3" (
    echo Pulling gemma2:2b...
    ollama pull gemma2:2b
    set MODEL=gemma2:2b
) else (
    echo Invalid choice
    pause
    exit
)

echo.
echo ========================================
echo Updating .env configuration...
echo ========================================

:: Update .env file
powershell -Command "(Get-Content .env.local) -replace 'OLLAMA_MODEL=.*', 'OLLAMA_MODEL=%MODEL%' | Set-Content .env.local"
copy /Y .env.local .env

echo.
echo ✓ Model changed to: %MODEL%
echo.
echo Please restart the server:
echo   1. Press Ctrl+C in the server terminal
echo   2. Run: python -m uvicorn src.api.main:app --reload --port 9011
echo.
pause
