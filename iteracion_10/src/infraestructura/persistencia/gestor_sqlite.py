import sqlite3
from typing import Optional
from src.dominio.puertos import PuertoUnidadDeTrabajo
from src.infraestructura.persistencia.repositorio_perfiles_sql import RepositorioPerfilesSQL
from src.infraestructura.persistencia.repositorio_productos_sql import RepositorioProductosSQL
from src.infraestructura.persistencia.repositorio_ventas_sql import RepositorioVentasSQL

# ===============================================================================
#  HELPER CENTRALIZADO DE TRANSACCIONES (PRINCIPIO DRY)
# ===============================================================================
#  DECISIÓN DE DISEÑO (KISS):
#  
#   En lugar de copiar y pegar esta lógica en cada repositorio como hacíamos 
#   en la Iteración 08/09, la centralizamos acá. Sirve para poblar los catálogos 
#   satélites (3FN) de forma dinámica sin romper la integridad relacional.
# ===============================================================================



def obtener_o_crear(cursor: sqlite3.Cursor, tabla: str, columna: str, valor: str) -> int:
    """
     Busca un valor en un catálogo satélite (ej. ciudades, estados). 
     Si existe, devuelve su ID. Si no existe, lo inserta y devuelve el nuevo ID.
     Al usar el cursor activo, participa en la misma transacción ACID en curso.
    """
    if not valor or str(valor).strip() == "":
        return None
        
    valor_limpio = str(valor).strip().upper()
    
    # Busca si el registro ya existe.
    query_busqueda = f"SELECT id FROM {tabla} WHERE {columna} = ?"
    cursor.execute(query_busqueda, (valor_limpio,))
    resultado = cursor.fetchone()
    
    if resultado:
        return resultado[0]
    
    # Si no existe, lo crea.
    query_insercion = f"INSERT INTO {tabla} ({columna}) VALUES (?)"
    cursor.execute(query_insercion, (valor_limpio,))
    return cursor.lastrowid



# ===========================================================================
#  GESTOR DE TRANSACCIONES / UNIDAD DE TRABAJO (CAPA 3 - INFRAESTRUCTURA)
# ===========================================================================
#  DECISIÓN DE DISEÑO (PATRÓN UNIT OF WORK):
#
#   Controla el ciclo de vida de la conexión a la base de datos (ACID).
#
#   Se usa con la sentencia 'with'. Abre la conexión al entrar y, al salir, 
#   si todo salió bien hace COMMIT, pero si falló CUALQUIER paso intermedio, 
#   hace un ROLLBACK automático evitando datos corruptos o huérfanos.
# ===========================================================================



class GestorSQLite(PuertoUnidadDeTrabajo):
    
    def __init__(self, ruta_db: str):
        self.ruta_db = ruta_db
        self.conexion: Optional[sqlite3.Connection] = None

    def __enter__(self):
        """
         Se ejecuta al iniciar el bloque 'with'.
         Abre la conexión, habilita las claves foráneas (vital para 3FN) e 
         instancia los repositorios inyectándoles esta misma conexión.
        """
        # check_same_thread=False es necesario porque FastAPI maneja múltiples peticiones asíncronas.
        self.conexion = sqlite3.connect(self.ruta_db, check_same_thread=False)
        self.conexion.execute("PRAGMA foreign_keys = ON;")
        
        # Instanciamos los repositorios concretos.
        self.perfiles = RepositorioPerfilesSQL(self.conexion)
        self.productos = RepositorioProductosSQL(self.conexion)
        self.ventas = RepositorioVentasSQL(self.conexion)
        
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        """
         Se ejecuta al finalizar el bloque 'with', haya habido error o no.
        """
        if exc_type is not None:
            # Si hubo una excepción (ej. Error de negocio, o Trigger de SQLite abortando), 
            # deshacemos todos los INSERT/UPDATE de esa transacción.
            self.rollback()
        else:
            # Si el bloque terminó con éxito, guardamos los cambios físicos.
            self.commit()
            
        # Siempre cerramos la conexión para liberar recursos de RAM y disco.
        if self.conexion:
            self.conexion.close()

    def commit(self) -> None:
        """Fuerza la persistencia de la transacción actual."""
        if self.conexion:
            self.conexion.commit()

    def rollback(self) -> None:
        """Revierte la transacción actual, descartando cambios en memoria."""
        if self.conexion:
            self.conexion.rollback()