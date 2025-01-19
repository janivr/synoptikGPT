@echo off
REM Check for Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    exit /b
)

REM Activate the virtual environment if needed
if exist venv (
    echo Activating virtual environment...
    call venv\Scripts\activate
)

REM Run Streamlit application
REM streamlit run src\chat_gpt\app_cg_2.py
streamlit run src\cli\streamlit_gpt.py

REM Wait for user input before closing
pause
