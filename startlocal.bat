@echo off
pip install -r requirements.txt
start python main.py 5000
start "" http://localhost:5000
