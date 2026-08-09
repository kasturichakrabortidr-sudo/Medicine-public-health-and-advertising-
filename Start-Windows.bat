@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py start.py
) else (
    python start.py
)
if errorlevel 1 (
    echo.
    echo If you saw "python is not recognized", install Python from
    echo https://www.python.org/downloads/  and TICK "Add Python to PATH".
)
pause
