@echo off
setlocal

cd /d "%~dp0"

echo ==========================================
echo  SECOP - Arrancar UI
 echo ==========================================

python -c "import sys" >nul 2>&1
if errorlevel 1 (
  echo ERROR: No se encontro Python en PATH.
  echo Instala Python 3.10+ y vuelve a intentar.
  pause
  exit /b 1
)

set "PYTHONPATH=%~dp0"

start "SECOP UI" cmd /k "python secop_ui.py"

REM Espera breve para que el servidor levante
if exist "%SystemRoot%\System32\timeout.exe" (
  timeout /t 2 >nul
) else (
  ping 127.0.0.1 -n 3 >nul
)

start "" "http://127.0.0.1:5000"

echo.
echo UI abierta en el navegador. El servidor queda en otra ventana.
echo.
pause
endlocal
