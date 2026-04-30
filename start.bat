@echo off
echo INSIDERS Dubai - Proposal Generator
echo.

REM Check if venv exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Start Flask app
echo.
echo Starting Flask server...
echo Open browser at: http://localhost:5000
echo Admin panel: http://localhost:5000/admin
echo.
python app.py

pause
