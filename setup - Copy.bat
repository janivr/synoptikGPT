@echo on
echo Setting up Synoptik GPT Project...

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate

REM Upgrade pip
pip install --upgrade pip

REM Install project and dependencies
pip install -e .
pip install -r requirements.txt

echo Project setup complete!
pause