@echo off
echo Setting up Synoptik GPT Project...

REM Get the current directory
set PROJECT_DIR=%CD%

REM Delete existing virtual environment if it exists
if exist "%PROJECT_DIR%\venv" (
    echo Deleting existing virtual environment...
    rmdir /s /q "%PROJECT_DIR%\venv"
)

REM Create new virtual environment
echo Creating virtual environment...
python -m venv "%PROJECT_DIR%\venv"
if errorlevel 1 (
    echo Failed to create virtual environment. Please check your Python installation.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call "%PROJECT_DIR%\venv\Scripts\activate"
if errorlevel 1 (
    echo Failed to activate virtual environment. Please check the paths.
    pause
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip. Please check your internet connection or Python installation.
    pause
    exit /b 1
)

REM Install project and dependencies
echo Installing project dependencies...
pip install -e .
if errorlevel 1 (
    echo Failed to install project dependencies. Please check requirements.txt.
    pause
    exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install project dependencies. Please check requirements.txt.
    pause
    exit /b 1
)

echo Project setup complete!
pause