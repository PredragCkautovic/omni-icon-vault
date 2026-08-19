@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 goto use_py
where python >nul 2>&1
if not errorlevel 1 goto use_python
echo.
echo Python 3.10 or newer is required.
echo Install Python from python.org and enable "Add Python to PATH", then rerun this file.
pause
exit /b 1

:use_py
py -3 install.py %*
exit /b %errorlevel%

:use_python
python install.py %*
exit /b %errorlevel%
