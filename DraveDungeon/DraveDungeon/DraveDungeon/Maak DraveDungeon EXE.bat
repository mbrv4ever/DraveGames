@echo off
title DraveDungeon - EXE bouwen
cd /d "%~dp0"

set PYEXE=
for %%V in (3.13 3.12 3.11 3.10) do (
  py -%%V -c "import sys" >nul 2>&1 && set PYEXE=py -%%V && goto found
)
where python >nul 2>&1 && set PYEXE=python
:found
if "%PYEXE%"=="" ( echo Python niet gevonden. & pause & exit /b 1 )

echo Installeren van bouw-afhankelijkheden (kan even duren)...
%PYEXE% -m pip install --upgrade pyinstaller pygame numpy neuvoice onnxruntime
%PYEXE% -m PyInstaller --noconfirm DraveDungeon.spec
echo.
echo Klaar. De EXE staat in de map dist\
pause
