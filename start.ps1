# VoiceBot Application Startup Script
# Runs the FastAPI server with all production features enabled

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 79 -ForegroundColor Cyan
Write-Host "🚀 VoiceBot Agentic AI Platform - Production Mode" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
python --version

# Check if database exists
Write-Host "`nChecking database..." -ForegroundColor Yellow
if (Test-Path "data/voicebot.db") {
    Write-Host "✅ Database found: data/voicebot.db" -ForegroundColor Green
    $dbInfo = Get-Item "data/voicebot.db"
    Write-Host "   Size: $($dbInfo.Length) bytes" -ForegroundColor Cyan
    Write-Host "   Created: $($dbInfo.CreationTime)" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  Database not found - will be created on startup" -ForegroundColor Yellow
}

# Check if Ollama is running
Write-Host "`nChecking Ollama service..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -UseBasicParsing
    Write-Host "✅ Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Ollama is not running" -ForegroundColor Red
    Write-Host "   Please start Ollama first: ollama serve" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🎯 Production Features Enabled:" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "  ✅ Database Persistence      (SQLite with WAL mode)" -ForegroundColor Cyan
Write-Host "  ✅ API Key Authentication    (Secure, hashed)" -ForegroundColor Cyan
Write-Host "  ✅ Rate Limiting            (60 req/min default)" -ForegroundColor Cyan
Write-Host "  ✅ Thread-Safe Operations   (Concurrent users safe)" -ForegroundColor Cyan
Write-Host "  ✅ Health Checks            (/health endpoints)" -ForegroundColor Cyan
Write-Host "  ✅ Input Validation         (DoS protection)" -ForegroundColor Cyan
Write-Host "  ✅ RAG with ChromaDB        (Knowledge base)" -ForegroundColor Cyan
Write-Host "  ✅ Async Guardrails         (Zero blocking)" -ForegroundColor Cyan
Write-Host "  ✅ Token Tracking           (Usage monitoring)" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

Write-Host "📡 Starting FastAPI Server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Server will be available at:" -ForegroundColor Cyan
Write-Host "  🌐 API:          http://localhost:9011" -ForegroundColor Green
Write-Host "  📚 Docs:         http://localhost:9011/docs" -ForegroundColor Green
Write-Host "  ❤️  Health:       http://localhost:9011/health" -ForegroundColor Green
Write-Host "  🎤 Voice Chat:   http://localhost:9011/static/voice_streaming.html" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Start the server
python -m uvicorn src.api.main:app --reload --port 9011 --log-level info
