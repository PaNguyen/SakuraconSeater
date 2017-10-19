@echo off
pip install -r requirements.txt
python main.py 5000
start "" "http://localhost:5000"
