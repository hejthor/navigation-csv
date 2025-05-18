#!/bin/bash

echo "[TERMINAL] Activating virtual environment"
python3 -m venv venv
source venv/bin/activate

echo "[TERMINAL] Upgrading pip to avoid warnings"
pip install --upgrade pip

echo "[TERMINAL] Installing Python dependencies"
pip install -r resources/requirements.txt

echo "[TERMINAL] Processing actions CSV"
python resources/process_paths_limited_ram.py --input output/actions.csv --output output

echo "[TERMINAL] Deactivating virtual environment"
deactivate
