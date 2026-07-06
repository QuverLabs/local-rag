@echo off
rem install.bat - double-clickable wrapper around install.ps1.
rem Uses -ExecutionPolicy Bypass so the user doesn't need to change system policy.
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0install.ps1"
pause
