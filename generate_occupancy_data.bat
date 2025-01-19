@echo off
REM Check for Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    exit /b
)



python src\data_manager\generate_occupancy.py

REM Wait for user input before closing
pause
