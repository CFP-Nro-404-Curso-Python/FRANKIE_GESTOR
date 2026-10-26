import pytest
import sqlite3
from src.dominio.entidades import PerfilUsuario, Producto
from src.infraestructura.persistencia.repositorio_perfiles_sql import RepositorioPerfilesSQL
from src.infraestructura.persistencia.repositorio_productos_sql import RepositorioProductosSQL

# ========================================================================================
#  PRUEBA DE INTEGRACIÓN: REPOSITORIOS SQL (TDD CICLO 2 - INFRAESTRUCTURA)
# ========================================================================================
#  DECISIÓN DE DISEÑO (PIRÁMIDE DE TESTING Y AISLAMIENTO):
#
#   A diferencia de las pruebas unitarias puras, acá SÍ interactuamos con una 
#   base de datos (la efímera en RAM inyectada por el fixture 'conexion_sqlite_memoria').
#
#   El objetivo es garantizar que la traducción entre nuestros objetos de dominio 
#   y las tablas relacionales (3FN) sea exacta, y que los Triggers defensivos 
#   de SQLite reaccionen como esperamos ante intentos de corrupción de datos.
# ========================================================================================



# ---------------------------------------------------------------------------
#  1. TESTS DE INTEGRACIÓN: REPOSITORIO DE PERFILES (USUARIOS/RRHH/CLIENTES)
# ---------------------------------------------------------------------------

def test_guardar_perfil_ejecuta_transaccion_escalonada_3fn(conexion_sqlite_memoria):
    """
     Verifica que al guardar un usuario, el repositorio inserte los datos maestros 
     en 'usuarios' y resuelva automáticamente la tabla puente 'usuxroles', 
     manteniendo la normalización extrema sin romper la integridad.
    """
    repositorio = RepositorioPerfilesSQL(conexion_sqlite_memoria)
    
    nuevo_perfil = PerfilUsuario(
        nombres="Carlos",
        apellidos="Santana",
        dni="11223344",
        rol="Gerente",
        usuario="csantana",
        password_hash="hash_simulado_123"
    )
    
    # Ejecutamos el método a probar.
    id_generado = repositorio.guardar(nuevo_perfil)
    assert id_generado > 0
    
    # AUDITORÍA DIRECTA SQL: 
    # Hacemos una consulta cruda puenteando el repositorio para confirmar 
    # que los datos aterrizaron correctamente en las tablas físicas.
    cursor = conexion_sqlite_memoria.cursor()
    cursor.execute("SELECT dni FROM usuarios WHERE id = ?", (id_generado,))
    assert cursor.fetchone()[0] == "11223344"
    
    # Verificamos la resolución del Catálogo de Roles (N:M).
    cursor.execute('''
        SELECT r.rol FROM usuxroles uxr
        JOIN roles r ON uxr.id_rol = r.id
        WHERE uxr.id_usuario = ?
    ''', (id_generado,))
    assert cursor.fetchone()[0] == "GERENTE"


def test_trigger_sqlite_bloquea_borrado_fisico(conexion_sqlite_memoria):
    """
     Garantiza que el mecanismo de Hard Delete Lock a nivel motor funciona.
     Nadie (ni un programador inyectando SQL a mano) debería poder ejecutar 
     un DELETE real sobre la tabla usuarios.
    """
    cursor = conexion_sqlite_memoria.cursor()
    
    # Insertamos un usuario de prueba directamente.
    cursor.execute("INSERT INTO usuarios (nombres, apellidos, dni) VALUES ('Test', 'Test', '000')")
    id_test = cursor.lastrowid
    
    # Intentamos ejecutar el comando prohibido. SQLite debería abortar la transacción.
    with pytest.raises(sqlite3.DatabaseError, match="Violación de Seguridad Nivel 1"):
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_test,))


# ----------------------------------------------------------------
#  2. TESTS DE INTEGRACIÓN: REPOSITORIO DE PRODUCTOS E INVENTARIO
# ----------------------------------------------------------------

def test_guardar_producto_asigna_estado_disponible_por_defecto(conexion_sqlite_memoria):
    """
     Verifica que al registrar un producto nuevo, el repositorio consulte/cree 
     el estado 'Disponible' y lo asocie en la tabla puente 'productoxestados'.
    """
    cursor = conexion_sqlite_memoria.cursor()
    # ARRANGE: Preparar semilla para satisfacer la Foreign Key (id_proveedor = 1).
    cursor.execute("INSERT INTO usuarios (id, nombres, apellidos, dni) VALUES (1, 'Proveedor', 'Base', '000')")
    
    repositorio = RepositorioProductosSQL(conexion_sqlite_memoria)
    
    nuevo_producto = Producto(
        codigo="TEST-PROD-01",
        descripcion="Disco Solido 1TB",
        categoria="Almacenamiento",
        id_proveedor=1,
        precio_costo=50000.0,
        precio_venta=80000.0,
        stock_actual=15.0
    )
    
    id_prod = repositorio.guardar(nuevo_producto)
    
    # Verificamos la asignación del estado inicial puenteando el repo.
    cursor.execute('''
        SELECT e.estado FROM productoxestados pxe
        JOIN estados e ON pxe.id_estado = e.id
        WHERE pxe.id_producto = ?
    ''', (id_prod,))
    
    resultado = cursor.fetchone()
    assert resultado is not None
    assert resultado[0] == "DISPONIBLE"


def test_actualizar_stock_modifica_inventario_correctamente(conexion_sqlite_memoria):
    """
     Verifica que la función atómica de descontar o sumar stock 
     impacte físicamente en la columna correspondiente.
    """
    cursor = conexion_sqlite_memoria.cursor()
    # ARRANGE: Preparar semilla para satisfacer la Foreign Key (id_proveedor = 1).
    cursor.execute("INSERT INTO usuarios (id, nombres, apellidos, dni) VALUES (1, 'Proveedor', 'Base', '000')")
    
    repositorio = RepositorioProductosSQL(conexion_sqlite_memoria)
    
    # Primero creamos un producto con stock de 10.
    producto = Producto(
        codigo="STOCK-01", descripcion="RAM 8GB", categoria="Memorias",
        id_proveedor=1, precio_costo=10.0, precio_venta=20.0, stock_actual=10.0
    )
    id_prod = repositorio.guardar(producto)
    
    # Simulamos una venta de 3 unidades (variación negativa).
    repositorio.actualizar_stock(id_producto=id_prod, variacion=-3.0)
    
    # Verificamos que queden 7.
    cursor.execute("SELECT stock_actual FROM productos WHERE id = ?", (id_prod,))
    assert cursor.fetchone()[0] == 7.0