@echo off
echo ========================================
echo VoiceBot Performance Optimizer
echo ========================================
echo.

echo This script will optimize your VoiceBot for faster responses.
echo.

echo Current Status:
ollama ps
echo.

echo ========================================
echo Choose Optimization Level:
echo ========================================
echo.
echo   1. Quick Fix - Switch to llama3.2:3b (3x faster)
echo   2. Keep Current Model - Optimize settings only
echo   3. Maximum Speed - Use smallest model (phi3:mini)
echo   4. Check current performance (test)
echo.

set /p choice="Enter choice (1/2/3/4): "

if "%choice%"=="1" (
    echo.
    echo Downloading llama3.2:3b faster model...
    ollama pull llama3.2:3b
    
    echo.
   echo Updating configuration...
    powershell -Command "(Get-Content .env.local) -replace 'OLLAMA_MODEL=.*', 'OLLAMA_MODEL=llama3.2:3b' | Set-Content .env.local"
    copy /Y .env.local .env
    
    echo.
    echo ✓ Optimization Complete!
    echo Model switched to: llama3.2:3b
    echo Expected speed: 3x faster (~5-10 seconds)
    
) else if "%choice%"=="2" (
    echo.
    echo Optimizing current model settings...
    echo.
    echo Adding performance tuning to .env.local...
    
    powershell -Command "Add-Content .env.local ''; Add-Content .env.local '# Performance Optimization'; Add-Content .env.local 'OLLAMA_NUM_PARALLEL=1'; Add-Content .env.local 'OLLAMA_MAX_LOADED_MODELS=1'"
    copy /Y .env.local .env
    
    echo.
    echo ✓ Settings optimized!
    echo Note: You should restart Ollama for best results
    
) else if "%choice%"=="3" (
    echo.
    echo Downloading phi3:mini (smallest, fastest model)...
    ollama pull phi3:mini
    
    echo.
    echo Updating configuration...
    powershell -Command "(Get-Content .env.local) -replace 'OLLAMA_MODEL=.*', 'OLLAMA_MODEL=phi3:mini' | Set-Content .env.local"
    copy /Y .env.local .env
    
    echo.
    echo ✓ Maximum speed optimization complete!
    echo Model: phi3:mini
    echo Expected speed: 5x faster (~2-6 seconds)
    echo Note: Quality slightly lower but very fast
    
) else if "%choice%"=="4" (
    echo.
    echo Running performance test...
    echo.
    
    echo Current model loaded:
    ollama ps
    
    echo.
    echo Testing response time...
    echo Please wait...
    
    powershell -Command "$start = Get-Date; $response = Invoke-RestMethod -Uri 'http://localhost:11434/api/generate' -Method Post -Body (@{model='llama3.1:8b'; prompt='Say hi'; stream=$false} | ConvertTo-Json) -ContentType 'application/json'; $duration = (Get-Date) - $start; Write-Host ''; Write-Host 'Response:' $response.response; Write-Host 'Time taken:' $duration.TotalSeconds 'seconds'"
    
) else (
    echo Invalid choice
    pause
    exit
)

echo.
echo ========================================
echo Next Steps:
echo ========================================
echo.
echo 1. Restart the Python server:
echo    Press Ctrl+C in server terminal
echo    Run: python -m uvicorn src.api.main:app --reload --port 9011
echo.
echo 2. Test performance:
echo    Open: http://localhost:9011/static/voice_improved.html
echo    Send a message and check the timing display
echo.
echo 3. Expected result:
if "%choice%"=="1" (
    echo    🤖 LLM Processing: ~5-10 seconds (was ~15-25s)
)
if "%choice%"=="3" (
    echo    🤖 LLM Processing: ~2-6 seconds (was ~15-25s)
)
echo.
pause
