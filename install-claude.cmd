@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-claude.ps1" %*
exit /b %ERRORLEVEL%
