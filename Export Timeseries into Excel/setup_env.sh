#!/bin/bash
echo "===== Telemetry Environment Setup (Linux/Ubuntu) ====="

# Check Python
if ! command -v python3 &> /dev/null
then
    echo "❌ Python3 is not installed. Install it: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

PYVER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYMAJOR=$(echo $PYVER | cut -d. -f1)
PYMINOR=$(echo $PYVER | cut -d. -f2)

if [ $PYMAJOR -lt 3 ] || ([ $PYMAJOR -eq 3 ] && [ $PYMINOR -lt 7 ]); then
    echo "❌ Python 3.7 or higher is required. Found $PYVER"
    exit 1
fi

echo "✅ Python version $PYVER detected."

# Create virtual environment
echo "Creating virtual environment in ./venv ..."
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip inside venv
python -m pip install --upgrade pip

# Install required packages
echo "Installing requests and openpyxl ..."
python -m pip install requests openpyxl

echo "🎉 Environment setup complete!"
echo "To run the telemetry exporter script:"
echo "Run the command on terminal:"
echo "source venv/bin/activate"
echo "python export_telemetry.py"

