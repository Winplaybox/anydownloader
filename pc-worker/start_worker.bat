@echo off
title OVD PC Worker
cd /d "%~dp0"

if not exist worker.env copy worker.env.example worker.env >nul
for /f "usebackq tokens=1,* delims==" %%A in ("worker.env") do if /i "%%A"=="NGROK_DOMAIN" set NGROK_DOMAIN=%%B
for /f "usebackq tokens=1,* delims==" %%A in ("worker.env") do if /i "%%A"=="PORT" set PORT=%%B
if "%PORT%"=="" set PORT=8787

if not exist .venv\Scripts\python.exe (
  echo [setup] creating Python environment (first run only)...
  py -3 -m venv .venv || python -m venv .venv
)
echo [setup] installing / updating yt-dlp, deno, ffmpeg...
.venv\Scripts\python.exe -m pip install -q --upgrade pip
.venv\Scripts\python.exe -m pip install -q --upgrade -r requirements.txt

where ngrok >nul 2>nul || (echo [error] ngrok not found. Install it: winget install ngrok.ngrok & pause & exit /b 1)
echo [start] ngrok tunnel https://%NGROK_DOMAIN%
start "OVD ngrok" /min ngrok http --url=%NGROK_DOMAIN% %PORT%

echo [start] worker (close this window to stop)
:loop
.venv\Scripts\python.exe worker.py
echo [warn] worker stopped, restarting in 10s...
timeout /t 10 >nul
goto loop
