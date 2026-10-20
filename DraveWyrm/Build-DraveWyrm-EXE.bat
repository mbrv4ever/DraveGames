@echo off
rem === Build-DraveWyrm-EXE.bat - maak een losse EXE van het spel ===
cd /d "%~dp0"

rem --- Python vinden ---
set "PY="
for %%V in (3.11 3.12 3.10 3.13) do (
  if not defined PY ( py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V" )
)
if not defined PY ( py -3 -c "import sys" >nul 2>&1 && set "PY=py -3" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )
if not defined PY ( echo Geen Python gevonden. Installeer Python 3.11 of 3.12. & pause & exit /b 1 )

rem --- benodigdheden (eenmalig) ---
%PY% -c "import pygame" >nul 2>&1
if errorlevel 1 ( echo Pygame installeren... & %PY% -m pip install pygame )
%PY% -c "import PIL" >nul 2>&1
if errorlevel 1 ( echo Pillow installeren ^(voor icoon^)... & %PY% -m pip install pillow )
%PY% -c "import PyInstaller" >nul 2>&1
if errorlevel 1 ( echo PyInstaller installeren... & %PY% -m pip install pyinstaller )

rem --- icoon (her)maken uit het draaklogo ---
if exist make_icon.py ( %PY% make_icon.py )

rem --- draaiend spel sluiten + oude build wissen (anti "toegang geweigerd") ---
taskkill /im DraveWyrm.exe /f >nul 2>&1
timeout /t 1 >nul
if exist "dist\DraveWyrm.exe" del /f /q "dist\DraveWyrm.exe" >nul 2>&1
if exist "build\DraveWyrm" rmdir /s /q "build\DraveWyrm"

echo.
echo === DraveWyrm bouwen (kan een minuut duren) ===
%PY% -m PyInstaller --noconfirm --clean --windowed --onefile ^
  --name DraveWyrm --icon "assets\icon.ico" main.py
if errorlevel 1 ( echo. & echo BOUWEN MISLUKT. Lees de melding hierboven. & pause & exit /b 1 )

rem --- assets naast de EXE (voor het venster-icoon); spel blijft portable ---
if not exist "dist\assets" mkdir "dist\assets"
copy /y "assets\icon.ico" "dist\assets\" >nul 2>&1

rem --- controleren of de EXE er echt is ---
if not exist "dist\DraveWyrm.exe" (
  echo. & echo FOUT: DraveWyrm.exe niet gevonden in dist\. & pause & exit /b 1
)

echo.
echo === KLAAR! ===
echo Het spel staat in:  "%~dp0dist\DraveWyrm.exe"
echo (De cache/record komt naast de .exe te staan, dus blijft portable.)
echo.
pause
