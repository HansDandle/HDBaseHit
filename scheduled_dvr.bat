@echo off
REM Smart DVR scheduler - wakes PC and runs DVR during "active hours"

echo 🕐 Scheduled DVR Start - %date% %time%
cd /d "%~dp0"

REM Get current hour (24-hour format)
for /f "tokens=1-2 delims=:" %%a in ('time /t') do set hour=%%a

REM Only run during "active hours" (6 AM to 11 PM)
if %hour% LSS 06 goto sleep_time
if %hour% GTR 23 goto sleep_time

echo ✅ Active hours detected, starting DVR...
cd /d "%~dp0"
python dvr_web.py

goto end

:sleep_time
echo 😴 Sleep time detected, skipping DVR start
echo Will try again at next scheduled time

:end
echo 📋 DVR scheduler task completed