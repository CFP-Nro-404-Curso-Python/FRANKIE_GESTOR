import sqlite3

# ==========================================================================
#  UTILIDADES SQL (CAPA 3 - INFRAESTRUCTURA)
# ==========================================================================
#  DECISIÓN DE DISEÑO (SRP Y PREVENCIÓN DE IMPORTACIONES CIRCULARES):
#
#   Extraemos esta función auxiliar a un módulo independiente puro.
#  
#   De esta forma, los distintos repositorios pueden consumirla sin generar 
#   un bucle infinito de dependencias con el GestorSQLite.
# ==========================================================================



def obtener_o_crear(cursor: sqlite3.Cursor, tabla: str, columna: str, valor: str) -> int:
    """
     Busca un valor en un catálogo satélite (ej. roles, estados, categorías). 
     Si existe, devuelve su ID. Si no existe, lo inserta y devuelve el nuevo ID.
     Al usar el cursor activo que se le inyecta por parámetro, participa en la 
     misma transacción ACID que está orquestando la Unidad de Trabajo.
    """
    if not valor or str(valor).strip() == "":
        return None
        
    valor_limpio = str(valor).strip().upper()
    
    # 1. Busca si el registro ya existe.
    query_busqueda = f"SELECT id FROM {tabla} WHERE {columna} = ?"
    cursor.execute(query_busqueda, (valor_limpio,))
    resultado = cursor.fetchone()
    
    if resultado:
        return resultado[0]
    
    # 2. Si no existe, lo inserta dinámicamente.
    query_insercion = f"INSERT INTO {tabla} ({columna}) VALUES (?)"
    cursor.execute(query_insercion, (valor_limpio,))
    
    # 3. Retorna la clave primaria (ID) recién generada por el motor SQLite.
    return cursor.lastrowid