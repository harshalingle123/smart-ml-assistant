@echo off
echo Starting Dual Query Intelligence Backend...
echo.

if not exist venv (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    echo.
)

echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting FastAPI server...
python run.py
