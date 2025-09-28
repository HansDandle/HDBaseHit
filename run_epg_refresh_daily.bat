@echo off
REM Daily EPG refresh batch script
REM Adjust PY_EXE if needed (e.g. path to python.exe)
set PY_EXE=python
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"
%PY_EXE% external_epg_refresh.py
exit /b %ERRORLEVEL%
