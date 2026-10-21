@echo off
setlocal enabledelayedexpansion
title DraveBricks - EXE bouwen
cd /d "%~dp0"

echo ============================================
echo   DraveBricks - Windows EXE bouwen
echo ============================================
echo.

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

if not exist ".venv\Scripts\python.exe" (
    %PYEXE% -m venv .venv
)
set "VPY=.venv\Scripts\python.exe"

echo Kernpakketten installeren...
"%VPY%" -m pip install --upgrade pip
"%VPY%" -m pip install --only-binary=:all: pygame numpy pillow

echo Stem ^(mofasa^) installeren voor in de EXE...
"%VPY%" -m pip install neuvoice onnxruntime soundfile huggingface-hub

echo PyInstaller installeren...
"%VPY%" -m pip install pyinstaller

echo Icoon aanmaken...
"%VPY%" maak_icoon.py

echo Oude build opruimen...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo EXE bouwen ^(dit kan even duren; de stem wordt meegebakken^)...
"%VPY%" -m PyInstaller --clean --noconfirm DraveBricks.spec

echo.
if exist "dist\DraveBricks.exe" (
    echo ============================================
    echo   GELUKT: dist\DraveBricks.exe is gemaakt.
    echo ============================================
) else (
    echo ============================================
    echo   MISLUKT: er is GEEN dist\DraveBricks.exe.
    echo   Bekijk de meldingen hierboven.
    echo ============================================
)
echo.
pause
exit /b 0

:geen_python
echo Geen Python gevonden. Installeer Python 3.10 of nieuwer
echo via https://www.python.org/downloads/ ^(Add Python to PATH^).
pause
exit /b 1
