import sqlite3
from typing import Optional, List
from src.dominio.entidades import Producto
from src.dominio.puertos import PuertoRepositorioProductos
from src.infraestructura.persistencia.utilidades_sql import obtener_o_crear



# ============================================================================
#  REPOSITORIO DE PRODUCTOS SQL (CAPA 3 - INFRAESTRUCTURA)
# ============================================================================
#  DECISIÓN DE DISEÑO (KISS Y 3FN):
#
#   Encapsula las sentencias SQL de inventario. Traduce nuestra entidad pura 
#   'Producto' a las tablas relacionales ('productos', 'estados', 
#   'productoxestados', 'ubicaciones_stock' y 'productoxubicaciones').
# ============================================================================

class RepositorioProductosSQL(PuertoRepositorioProductos):

    _SELECT_PRODUCTO_3FN = '''
        SELECT p.id, p.codigo, p.descripcion, p.categoria, p.id_proveedor, 
               p.precio_costo, p.precio_venta, p.stock_actual, p.stock_minimo, 
               p.vencimiento, p.habilitado,
               COALESCE(ub.ubicacion, 'S/D') AS ubicacion
        FROM productos p
        LEFT JOIN productoxubicaciones pxu ON p.id = pxu.id_producto AND pxu.habilitado = 1
        LEFT JOIN ubicaciones_stock ub ON pxu.id_ubicacion = ub.id
    '''
    
    def __init__(self, conexion: sqlite3.Connection):
        """
         Recibe la conexión activa inyectada por el GestorSQLite.
        """
        self.conexion = conexion

    def _obtener_o_crear_ubicacion(self, cursor: sqlite3.Cursor, ubicacion: str) -> int:
        """Busca o inserta la ubicación de depósito preservando su formato legible."""
        valor_limpio = str(ubicacion).strip() if ubicacion and str(ubicacion).strip() else "S/D"
        cursor.execute("SELECT id FROM ubicaciones_stock WHERE ubicacion = ?", (valor_limpio,))
        fila = cursor.fetchone()
        if fila:
            return fila[0]
        cursor.execute("INSERT INTO ubicaciones_stock (ubicacion, habilitado) VALUES (?, 1)", (valor_limpio,))
        return cursor.lastrowid

    def _sincronizar_ubicacion_stock(self, cursor: sqlite3.Cursor, id_producto: int, ubicacion: str) -> None:
        """Actualiza el vínculo 3FN entre el producto y su ubicación física en depósito."""
        cursor.execute("UPDATE productoxubicaciones SET habilitado = 0 WHERE id_producto = ?", (id_producto,))
        id_ubicacion = self._obtener_o_crear_ubicacion(cursor, ubicacion)
        cursor.execute(
            "INSERT INTO productoxubicaciones (id_producto, id_ubicacion, habilitado) VALUES (?, ?, 1)",
            (id_producto, id_ubicacion)
        )

    def guardar(self, producto: Producto) -> int:
        """
         Inserta un nuevo producto en el catálogo, inicializa su estado como 
         'Disponible' y vincula su ubicación física en las tablas puente 3FN.
        """
        cursor = self.conexion.cursor()
        
        # 1. Insertamos el producto en la tabla principal.
        cursor.execute('''
            INSERT INTO productos (
                codigo, descripcion, categoria, id_proveedor, 
                precio_costo, precio_venta, stock_actual, stock_minimo, vencimiento, habilitado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (
            producto.codigo, producto.descripcion, producto.categoria, 
            producto.id_proveedor, producto.precio_costo, producto.precio_venta, 
            producto.stock_actual, producto.stock_minimo, producto.vencimiento
        ))
        
        id_nuevo_producto = cursor.lastrowid
        
        # 2. Gestionamos el catálogo de estados satélite usando el helper DRY.
        id_estado = obtener_o_crear(cursor, "estados", "estado", "Disponible")
        
        # 3. Vinculamos producto y estado en la tabla puente.
        cursor.execute('''
            INSERT INTO productoxestados (id_producto, id_estado, habilitado)
            VALUES (?, ?, 1)
        ''', (id_nuevo_producto, id_estado))

        # 4. Vinculamos producto y ubicación física en depósito.
        self._sincronizar_ubicacion_stock(cursor, id_nuevo_producto, producto.ubicacion)
        
        return id_nuevo_producto

    def modificar(self, producto: Producto) -> None:
        """
         Actualiza los valores comerciales, descriptivos y de ubicación de un producto existente.
        """
        cursor = self.conexion.cursor()
        cursor.execute('''
            UPDATE productos 
            SET codigo = ?, descripcion = ?, categoria = ?, id_proveedor = ?, 
                precio_costo = ?, precio_venta = ?, stock_actual = ?, 
                stock_minimo = ?, vencimiento = ?
            WHERE id = ?
        ''', (
            producto.codigo, producto.descripcion, producto.categoria, 
            producto.id_proveedor, producto.precio_costo, producto.precio_venta, 
            producto.stock_actual, producto.stock_minimo, producto.vencimiento, 
            producto.id
        ))
        self._sincronizar_ubicacion_stock(cursor, producto.id, producto.ubicacion)

    def eliminar(self, id_producto: int) -> None:
        """
         Aplica el Borrado Lógico (Soft Delete) cambiando habilitado a 0.
         Esto garantiza que las facturas históricas no pierdan su referencia al producto.
        """
        cursor = self.conexion.cursor()
        cursor.execute("UPDATE productos SET habilitado = 0 WHERE id = ?", (id_producto,))

    def obtener_por_codigo(self, codigo: str) -> Optional[Producto]:
        """
         Busca un producto por su código de barras o SKU comercial.
         Solo retorna productos activos.
        """
        cursor = self.conexion.cursor()
        cursor.execute(
            f"{self._SELECT_PRODUCTO_3FN} WHERE p.codigo = ? AND p.habilitado = 1 GROUP BY p.id",
            (codigo,)
        )
        fila = cursor.fetchone()
        return self._mapear_a_entidad(fila) if fila else None

    def obtener_por_id(self, id_producto: int) -> Optional[Producto]:
        """
         Busca un producto directamente por su clave primaria (PK) física.
        """
        cursor = self.conexion.cursor()
        cursor.execute(
            f"{self._SELECT_PRODUCTO_3FN} WHERE p.id = ? AND p.habilitado = 1 GROUP BY p.id",
            (id_producto,)
        )
        fila = cursor.fetchone()
        return self._mapear_a_entidad(fila) if fila else None

    def listar_todos(self) -> List[Producto]:
        """
         Devuelve la lista completa de todos los productos activos en el catálogo.
        """
        cursor = self.conexion.cursor()
        cursor.execute(f"{self._SELECT_PRODUCTO_3FN} WHERE p.habilitado = 1 GROUP BY p.id")
        return [self._mapear_a_entidad(fila) for fila in cursor.fetchall()]

    def actualizar_stock(self, id_producto: int, variacion: float) -> None:
        """
         Suma o resta cantidades al stock físico directamente en el motor SQL.
        """
        cursor = self.conexion.cursor()
        cursor.execute('''
            UPDATE productos 
            SET stock_actual = stock_actual + ? 
            WHERE id = ?
        ''', (variacion, id_producto))

    def _mapear_a_entidad(self, fila: tuple) -> Producto:
        """
         Función privada auxiliar. Transforma la tupla cruda que devuelve SQLite 
         a nuestro objeto puro de negocio.
        """
        return Producto(
            id=fila[0],
            codigo=fila[1],
            descripcion=fila[2],
            categoria=fila[3],
            id_proveedor=fila[4],
            precio_costo=fila[5],
            precio_venta=fila[6],
            stock_actual=fila[7],
            stock_minimo=fila[8],
            vencimiento=fila[9],
            habilitado=fila[10],
            ubicacion=fila[11] if len(fila) > 11 and fila[11] else "S/D"
        )