@echo off
setlocal

REM Posicionarse en la carpeta donde está el proyecto
cd /d %~dp0

echo =========================================
echo   Iniciando Extractor SECOP
echo =========================================

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Ejecutar la UI
python secop_ui.py

endlocal
pause
