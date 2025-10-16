@echo off
echo ===== Telemetry Environment Setup (Windows) =====

:: Check Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Python is not installed. Download and install from https://www.python.org/downloads/
    exit /b 1
)

:: Create virtual environment
echo Creating virtual environment in .\venv ...
python -m venv venv

:: Activate venv
call venv\Scripts\activate.bat

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install required packages
echo Installing requests and openpyxl ...
python -m pip install requests openpyxl

echo 🎉 Environment setup complete!
echo To run the telemetry exporter script:
echo Open Command Prompt:
echo call venv\Scripts\activate.bat
echo python export_telemetry.py
pause
