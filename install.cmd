@echo off
setlocal

where uv >nul 2>nul
if errorlevel 1 (
  echo Installing the small uv runtime...
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "irm https://astral.sh/uv/install.ps1 | iex"
  set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

where uv >nul 2>nul
if errorlevel 1 (
  echo Error: uv installation failed.
  exit /b 1
)

uv run --no-project "%~dp0scripts\install_mcp.py" %*
exit /b %ERRORLEVEL%
