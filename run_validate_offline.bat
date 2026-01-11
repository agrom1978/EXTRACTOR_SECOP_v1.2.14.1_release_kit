@echo off
setlocal enabledelayedexpansion

REM Validador OFFLINE (sin UI, sin Playwright)
REM Requiere: Python instalado y disponible en PATH.

cd /d "%~dp0"

echo ==========================================
echo  SECOP - Validador OFFLINE (RP + Rep. Legal)
echo ==========================================

python -c "import sys; print('Python OK:', sys.version)" >nul 2>&1
if errorlevel 1 (
  echo ERROR: No se encontro Python en PATH.
  echo Instala Python 3.10+ y vuelve a intentar.
  pause
  exit /b 1
)

REM Dependencias minimas
python -c "import bs4, openpyxl" >nul 2>&1
if errorlevel 1 (
  echo Instalando dependencias (beautifulsoup4, openpyxl)...
  python -m pip install --upgrade pip
  python -m pip install beautifulsoup4 openpyxl
)

echo Ejecutando validacion...
python validators\validate_offline.py

echo.
echo Listo. Revisa la carpeta: reports\offline
echo.
pause
