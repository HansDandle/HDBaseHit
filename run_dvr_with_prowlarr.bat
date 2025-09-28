@echo off
REM TV Recorder Startup Script
REM This script starts the DVR application with configuration loaded from config.json

echo Starting TV Recorder for HDHomeRun...
echo.
echo Configuration will be loaded from config.json
echo If config.json doesn't exist, run: python setup.py
echo.
echo.

REM Keep existing BiratePay settings as fallback
set BIRATEPAY_ENABLED=1
set BIRATEPAY_API_URL=http://127.0.0.1:5055

cd /d "%~dp0"

echo Starting TV Recorder...
python dvr_web.py

pause