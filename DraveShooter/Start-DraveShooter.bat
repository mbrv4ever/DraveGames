@echo off
rem === Start-DraveShooter.bat - start het spel ===
cd /d "%~dp0"

set "PY="
for %%V in (3.13 3.12 3.11) do (
  if not defined PY ( py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V" )
)
if not defined PY ( py -3 -c "import sys" >nul 2>&1 && set "PY=py -3" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )
if not defined PY ( echo Geen Python gevonden. Installeer Python 3.11 of 3.12. & pause & exit /b 1 )

%PY% -c "import panda3d" >nul 2>&1
if errorlevel 1 (
  echo Panda3D installeren ^(eenmalig^)...
  %PY% -m pip install panda3d
)

start "" %PY% "%~dp0main.py"
