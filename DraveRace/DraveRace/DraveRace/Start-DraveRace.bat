@echo off
setlocal enabledelayedexpansion
title DraveRace
cd /d "%~dp0"

echo ============================================
echo   DraveRace - Dravenlock Games
echo ============================================
echo.

rem --- Python zoeken: 3.13 -> 3.12 -> 3.11 -> 3.10 -> python ---
set "PYEXE="
for %%V in (3.13 3.12 3.11 3.10) do (
    if not defined PYEXE (
        py -%%V -c "import sys" >nul 2>&1 && set "PYEXE=py -%%V"
    )
)
if not defined PYEXE (
    python -c "import sys" >nul 2>&1 && set "PYEXE=python"
)
if not defined PYEXE goto geen_python

rem --- virtuele omgeving (zelfhelend) ---
if not exist ".venv\Scripts\python.exe" (
    echo Eenmalig opzetten van de omgeving...
    %PYEXE% -m venv .venv
)
set "VPY=.venv\Scripts\python.exe"
if not exist "%VPY%" (
    echo Omgeving herstellen...
    rmdir /s /q .venv 2>nul
    %PYEXE% -m venv .venv
)

rem --- kernpakketten controleren/installeren (verplicht) ---
"%VPY%" -c "import pygame, numpy, PIL" >nul 2>&1
if errorlevel 1 (
    echo Benodigde pakketten installeren ^(eenmalig^)...
    "%VPY%" -m pip install --upgrade pip
    "%VPY%" -m pip install --only-binary=:all: pygame numpy pillow
)
"%VPY%" -c "import pygame, numpy, PIL" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installatie van de kernpakketten is mislukt.
    echo Controleer uw internetverbinding en probeer opnieuw.
    pause
    exit /b 1
)

rem --- stem (mofasa) eenmalig installeren, niet-blokkerend ---
if not exist ".venv\stem_done.txt" (
    echo Stem ^(mofasa^) installeren ^(eenmalig, kan even duren^)...
    "%VPY%" -m pip install neuvoice onnxruntime soundfile huggingface-hub
    echo done> ".venv\stem_done.txt"
)

rem --- icoon aanmaken als het ontbreekt ---
if not exist "assets\logo.ico" (
    "%VPY%" maak_icoon.py
)

rem --- starten ---
echo Starten...
"%VPY%" DraveRace.py
if errorlevel 1 (
    echo.
    echo DraveRace is met een fout gestopt.
    pause
)
exit /b 0

:geen_python
echo.
echo Geen Python gevonden. Installeer Python 3.10 of nieuwer
echo via https://www.python.org/downloads/ en zet bij de installatie
echo het vinkje "Add Python to PATH" aan.
echo.
pause
exit /b 1
