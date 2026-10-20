@echo off
rem === Build-DraveNest-EXE.bat - maak een losse EXE van het spel ===
cd /d "%~dp0"

set "PY="
for %%V in (3.11 3.12 3.10 3.13) do (
  if not defined PY ( py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V" )
)
if not defined PY ( py -3 -c "import sys" >nul 2>&1 && set "PY=py -3" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )
if not defined PY ( echo Geen Python gevonden. Installeer Python 3.11 of 3.12. & pause & exit /b 1 )

%PY% -c "import pygame" >nul 2>&1
if errorlevel 1 ( echo Pygame installeren... & %PY% -m pip install pygame )
%PY% -c "import PIL" >nul 2>&1
if errorlevel 1 ( echo Pillow installeren... & %PY% -m pip install pillow )
%PY% -c "import PyInstaller" >nul 2>&1
if errorlevel 1 ( echo PyInstaller installeren... & %PY% -m pip install pyinstaller )

if exist make_icon.py ( %PY% make_icon.py )

taskkill /im DraveNest.exe /f >nul 2>&1
timeout /t 1 >nul
if exist "dist\DraveNest.exe" del /f /q "dist\DraveNest.exe" >nul 2>&1
if exist "build\DraveNest" rmdir /s /q "build\DraveNest"

echo.
echo === DraveNest bouwen ===
%PY% -m PyInstaller --noconfirm --clean --windowed --onefile ^
  --name DraveNest --icon "assets\icon.ico" main.py
if errorlevel 1 ( echo. & echo BOUWEN MISLUKT. & pause & exit /b 1 )

if not exist "dist\assets" mkdir "dist\assets"
copy /y "assets\icon.ico" "dist\assets\" >nul 2>&1

if not exist "dist\DraveNest.exe" (
  echo. & echo FOUT: DraveNest.exe niet gevonden. & pause & exit /b 1
)
echo.
echo === KLAAR! ===  "%~dp0dist\DraveNest.exe"
pause
