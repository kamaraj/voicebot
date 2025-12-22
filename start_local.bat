@echo off
REM Quick Start Script for Local Development
REM No Docker, No Cloud - Just Run!

echo ========================================
echo VoiceBot AI - Local Development
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\" (
    echo [1/5] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/5] Virtual environment exists ✓
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Installing dependencies...
pip install -q -r requirements.txt

echo [4/5] Setting up local configuration...
if not exist ".env" (
    copy .env.local .env
    echo Configuration created ✓
) else (
    echo Configuration exists ✓
)

echo [5/5] Creating data directories...
if not exist "data\" mkdir data
if not exist "data\eval_datasets\" mkdir data\eval_datasets
if not exist "data\synthetic_data\" mkdir data\synthetic_data
if not exist "logs\" mkdir logs

echo.
echo ========================================
echo ✓ Setup Complete!
echo ========================================
echo.
echo Starting API server on http://localhost:9011
echo.
echo API Documentation: http://localhost:9011/docs
echo Health Check: http://localhost:9011/health
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the server
python -m uvicorn src.api.main:app --reload --port 9011
