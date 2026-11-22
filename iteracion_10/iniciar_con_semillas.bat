@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ==============================================================
echo  FRANKIE GESTOR - MODO PRUEBAS CON SEMILLAS (ENTORNO EFIMERO)
echo ==============================================================
echo.

:: Validacion previa del entorno virtual.
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] No se encontro el entorno virtual en ".venv\Scripts\activate.bat".
    pause
    exit /b 1
)

:: 1. Borrar la base de datos si existe.
if exist "db\frankie_gestor.db" (
    echo [1/7] Eliminando base de datos previa...
    del /f /q "db\frankie_gestor.db" "db\frankie_gestor.db-wal" "db\frankie_gestor.db-shm" 2>nul
    if exist "db\frankie_gestor.db" (
        echo [ERROR] No se pudo borrar db\frankie_gestor.db. Verifica que no haya otra instancia abierta.
        pause
        exit /b 1
    )
) else (
    echo [1/7] No existe base de datos previa. Continuando...
)

:: 2. Activar el entorno virtual.
echo [2/7] Activando entorno virtual (.venv)...
call ".venv\Scripts\activate.bat"
set "PYTHONPATH=%CD%"

:: 3. Inicializar DB en blanco (esquema 3FN + roles base + admin) sin abrir GUI.
echo [3/7] Inicializando base de datos en blanco (esquema, roles y admin)...
python -c "import os, pathlib; from src.infraestructura.persistencia.gestor_sqlite import GestorSQLite; from src.infraestructura.seguridad.adaptador_bcrypt import AdaptadorBcrypt; os.makedirs('db', exist_ok=True); uow = GestorSQLite('db/frankie_gestor.db'); uow.__enter__(); c = uow.conexion.cursor(); c.executescript(pathlib.Path('db/esquema.sql').read_text(encoding='utf-8')); c.executemany('INSERT INTO roles (rol) VALUES (?)', [('Administrador',),('Gerente',),('Empleado - Ventas',),('Empleado - Compras',),('Proveedor',),('Cliente',)]); c.execute('INSERT INTO usuarios (usuario, password, nombres, apellidos, dni, habilitado) VALUES (?, ?, ?, ?, ?, 1)', ('admin', AdaptadorBcrypt().hashear_password('admin123'), 'David Hernan', 'Bravo', '00000000')); uid = c.lastrowid; rid = c.execute('SELECT id FROM roles WHERE rol = ?', ('Administrador',)).fetchone()[0]; c.execute('INSERT INTO usuxroles (id_usuario, id_rol, habilitado) VALUES (?, ?, 1)', (uid, rid)); uow.__exit__(None, None, None)"
if errorlevel 1 (
    echo [ERROR] Fallo la inicializacion de la base de datos en blanco.
    call deactivate
    pause
    exit /b 1
)

:: 4. Ejecutar el generador de semillas BI.
echo [4/7] Poblando base de datos con semillas de prueba...
python "semillas\generador_semilla_bi.py"
if errorlevel 1 (
    echo [ERROR] Fallo la ejecucion de semillas\generador_semilla_bi.py.
    call deactivate
    pause
    exit /b 1
)

:: 5. Iniciar login para pruebas (el script espera hasta que cierres la aplicacion).
echo [5/7] Iniciando FRANKIE GESTOR en modo pruebas...
echo       (Cerra la ventana del sistema para limpiar la DB y finalizar)
python "src\presentacion\escritorio\vistas\login.py"

:: 6. Esperar liberacion de handles (uvicorn/http.server) y borrar la DB efimera.
echo [6/7] Cerrando servicios y eliminando base de datos de pruebas...
timeout /t 2 /nobreak >nul
if exist "db\frankie_gestor.db" (
    del /f /q "db\frankie_gestor.db" "db\frankie_gestor.db-wal" "db\frankie_gestor.db-shm" 2>nul
    if exist "db\frankie_gestor.db" (
        echo [AVISO] La DB sigue bloqueada; reintentando en 2 segundos...
        timeout /t 2 /nobreak >nul
        del /f /q "db\frankie_gestor.db" "db\frankie_gestor.db-wal" "db\frankie_gestor.db-shm" 2>nul
    )
)

:: 7. Desactivar el entorno virtual.
echo [7/7] Desactivando entorno virtual...
call deactivate

echo.
echo Proceso finalizado. Base de datos temporal eliminada.
endlocal