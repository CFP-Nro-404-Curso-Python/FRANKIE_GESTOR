import pytest
import sqlite3
import os

# ==================================================================================
#  CONFIGURACIÓN GLOBAL DE TESTS (PYTEST FIXTURES - TDD CICLO 2)
# ==================================================================================
#  DECISIÓN DE DISEÑO (AISLAMIENTO ACID):
#
#   Para que las pruebas de integración no corrompan la base de datos de producción 
#   (frankie_gestor.db) ni dependan de registros previos, orquestamos una base de 
#   datos efímera directamente en la memoria RAM (:memory:).
#  
#   Pytest inyectará esta conexión limpia en cada test y la destruirá al terminar, 
#   garantizando que todas las pruebas sean deterministas e independientes.
# ==================================================================================



@pytest.fixture
def conexion_sqlite_memoria():
    """
     Fixture principal. Levanta una conexión a SQLite en RAM, lee el archivo 
     físico 'esquema.sql' y construye toda la estructura relacional 3FN 
     (Tablas, Vistas y Triggers) en milisegundos.
    """
    # 1. Anclaje de directorios para ubicar esquema.sql dinámicamente.
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    directorio_raiz = os.path.dirname(directorio_actual)
    ruta_esquema = os.path.join(directorio_raiz, "db", "esquema.sql")

    # 2. Conexión aislada en memoria RAM.
    conexion = sqlite3.connect(":memory:")
    
    # 3. Activación estricta de Foreign Keys (SQLite las apaga por defecto).
    # Vital para probar que la 3FN y las eliminaciones en cascada funcionen.
    conexion.execute("PRAGMA foreign_keys = ON;")

    # 4. Construcción del ecosistema relacional.
    try:
        with open(ruta_esquema, "r", encoding="utf-8") as archivo_sql:
            script_ddl = archivo_sql.read()
            conexion.executescript(script_ddl)
    except FileNotFoundError:
        pytest.fail(f"Error Crítico TDD: No se encontró el DDL en {ruta_esquema}")

    # 5. Yield pausa la función y entrega la conexión lista al test que la pidió.
    yield conexion

    # 6. Teardown: Al finalizar el test, se cierra la conexión y la RAM se libera.
    conexion.close()