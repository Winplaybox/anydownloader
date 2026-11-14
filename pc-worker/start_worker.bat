@echo off
title OVD PC Worker
cd /d "%~dp0"
if not exist worker.env copy worker.env.example worker.env >nul
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
if not exist .venv\Scripts\python.exe python -m venv .venv
.venv\Scripts\python.exe -m pip install -q --upgrade -r requirements.txt
:loop
.venv\Scripts\python.exe worker.py
echo Worker stopped, restarting in 10 seconds...
timeout /t 10 >nul
goto loop
