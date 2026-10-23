@echo off
setlocal
title DraveBeat - herstellen
cd /d "%~dp0"
echo Dit verwijdert de virtuele omgeving ^(.venv^) en build-mappen.
echo De volgende keer start DraveBeat alles opnieuw op.
echo.
choice /c JN /m "Doorgaan"
if errorlevel 2 exit /b 0
if exist .venv rmdir /s /q .venv
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
echo Klaar. Start DraveBeat opnieuw met Start-DraveBeat.bat
pause
exit /b 0
