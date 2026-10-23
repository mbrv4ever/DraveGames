@echo off
rem === bouw-exe.bat - bouwt DraveShooter.exe via Panda3D build_apps ===
rem (nodig: internet - haalt de juiste Panda3D op voor het inpakken)
setlocal
cd /d "%~dp0"

set "PY="
for %%V in (3.13 3.12 3.11) do (
  if not defined PY ( py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V" )
)
if not defined PY ( py -3 -c "import sys" >nul 2>&1 && set "PY=py -3" )
if not defined PY ( python -c "import sys" >nul 2>&1 && set "PY=python" )
if not defined PY ( echo Geen Python gevonden. Installeer Python 3.11 of 3.12. & pause & exit /b 1 )

if not exist ".venv" ( %PY% -m venv .venv )
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install panda3d
if errorlevel 1 ( echo. & echo FOUT: installeren van panda3d mislukt ^(internet?^). & pause & exit /b 1 )

echo.
echo === Bouwen met Panda3D build_apps... ===
python setup.py build_apps
if errorlevel 1 ( echo. & echo FOUT: bouwen mislukt - lees de melding hierboven. & pause & exit /b 1 )

if exist "build\win_amd64\DraveShooter.exe" (
  echo.
  echo Klaar! Start:  build\win_amd64\DraveShooter.exe
) else (
  echo.
  echo LET OP: geen exe gevonden in build\win_amd64 - er ging iets mis hierboven.
)
echo.
pause
endlocal
