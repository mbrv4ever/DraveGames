@echo off
rem === Build-DraveHop-EXE.bat -> dist\DraveHop.exe ===
cd /d "%~dp0"

set "PY="
for %%V in (3.11 3.12 3.10 3.13) do (
  if not defined PY ( py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V" )
)
if not defined PY ( py -3 -c "import sys" >nul 2>&1 && set "PY=py -3" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )
if not defined PY ( echo Geen Python gevonden. & pause & exit /b 1 )

%PY% -c "import pygame" 2>nul || %PY% -m pip install pygame
%PY% -c "import PIL" 2>nul || %PY% -m pip install pillow
%PY% -c "import PyInstaller" 2>nul || %PY% -m pip install pyinstaller

echo Icoon (her)bouwen...
%PY% make_icon.py

taskkill /f /im DraveHop.exe >nul 2>&1
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo EXE bouwen...
%PY% -m PyInstaller --noconfirm --clean --windowed --onefile ^
  --name DraveHop --icon assets\icon.ico main.py

if not exist "dist\DraveHop.exe" (
  echo.
  echo BOUW MISLUKT - dist\DraveHop.exe niet gevonden.
  pause
  exit /b 1
)

if not exist "dist\assets" mkdir "dist\assets"
copy /y "assets\*.*" "dist\assets\" >nul

echo.
echo KLAAR:  dist\DraveHop.exe
pause
