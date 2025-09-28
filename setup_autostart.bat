@echo off
REM Create Windows Task to auto-start DVR with Prowlarr

echo Creating Windows Scheduled Task for DVR auto-start...

REM Delete existing task if it exists
schtasks /Delete /TN "DVR_AutoStart" /F >nul 2>&1

REM Create new task that runs at startup
schtasks /Create ^
  /TN "DVR_AutoStart" ^
  /TR "\"C:\Users\brixw\Desktop\TV Recorder\run_dvr_with_prowlarr.bat\"" ^
  /SC ONSTART ^
  /RU "%USERNAME%" ^
  /RP ^
  /RL HIGHEST ^
  /F

if %ERRORLEVEL% EQU 0 (
    echo ✅ Task created successfully!
    echo DVR will now auto-start when Windows boots
    echo.
    echo To remove: schtasks /Delete /TN "DVR_AutoStart" /F
) else (
    echo ❌ Failed to create task. Run as Administrator?
)

pause