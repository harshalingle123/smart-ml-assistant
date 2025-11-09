#!/bin/bash

echo "Starting Dual Query Intelligence Backend..."
echo ""

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo ""
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Starting FastAPI server..."
python run.py
