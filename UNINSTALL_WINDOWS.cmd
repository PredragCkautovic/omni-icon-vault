@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 goto use_py
python uninstall.py %*
exit /b %errorlevel%
:use_py
py -3 uninstall.py %*
exit /b %errorlevel%
