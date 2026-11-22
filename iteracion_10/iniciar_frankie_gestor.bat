@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] No se encontro el entorno virtual en ".venv\Scripts\activate.bat".
    pause
    exit /b 1
)

:: 1. Activar el entorno virtual.
call ".venv\Scripts\activate.bat"
set "PYTHONPATH=%CD%"

:: 2. Ejecutar login.
python "src\presentacion\escritorio\vistas\login.py"

:: 3. Desactivar el entorno virtual.
call deactivate

endlocal