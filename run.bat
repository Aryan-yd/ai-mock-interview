@echo off
title AI Interview Coach
echo ==============================================
echo       Starting AI Interview Coach on port 8503
echo ==============================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found!
    echo Please ensure venv is installed.
    pause
    exit /b 1
)

call "venv\Scripts\activate.bat"
echo Virtual environment activated.
echo Starting Streamlit application on port 8503...
echo.
python -m streamlit run app.py --server.port 8503

pause
