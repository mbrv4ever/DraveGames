@echo off
title DraveQuest
cd /d "%~dp0"

set PYEXE=
for %%V in (3.13 3.12 3.11 3.10) do (
  py -%%V -c "import sys" >nul 2>&1 && set PYEXE=py -%%V && goto found
)
where python >nul 2>&1 && set PYEXE=python
:found
if "%PYEXE%"=="" (
  echo Python niet gevonden. Installeer Python 3.10-3.13 van python.org
  pause
  exit /b 1
)

echo Controleren van pygame...
%PYEXE% -c "import pygame" >nul 2>&1 || %PYEXE% -m pip install pygame
echo Controleren van numpy (voor geluid)...
%PYEXE% -c "import numpy" >nul 2>&1 || %PYEXE% -m pip install numpy
echo Controleren van stemmen (neuvoice, optioneel)...
%PYEXE% -c "import neuvoice" >nul 2>&1 || %PYEXE% -m pip install neuvoice

%PYEXE% DraveQuest.py
if errorlevel 1 (
  echo.
  echo Er ging iets mis. Zie dravequest_fout.txt
  pause
)
