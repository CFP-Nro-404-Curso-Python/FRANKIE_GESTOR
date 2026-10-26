import sqlite3
from typing import Optional
from src.dominio.entidades import Producto
from src.dominio.puertos import PuertoRepositorioProductos
from src.infraestructura.persistencia.gestor_sqlite import obtener_o_crear

# ============================================================================
#  REPOSITORIO DE PRODUCTOS SQL (CAPA 3 - INFRAESTRUCTURA)
# ============================================================================
#  DECISIÓN DE DISEÑO (KISS Y 3FN):
#
#   Encapsula las sentencias SQL de inventario. Traduce nuestra entidad pura 
#   'Producto' a las tablas relacionales. Aplica el borrado lógico y gestiona 
#   atómicamente el incremento/decremento de stock para evitar condiciones de 
#   carrera.
# ============================================================================



class RepositorioProductosSQL(PuertoRepositorioProductos):
    
    def __init__(self, conexion: sqlite3.Connection):
        """
         Recibe la conexión activa inyectada por el GestorSQLite.
        """
        self.conexion = conexion

    def guardar(self, producto: Producto) -> int:
        """
         Inserta un nuevo producto en el catálogo e inicializa su estado 
         como 'Disponible' en la tabla puente.
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
            INSERT INTO productoxestados (id_producto, id_estado)
            VALUES (?, ?)
        ''', (id_nuevo_producto, id_estado))
        
        return id_nuevo_producto

    def modificar(self, producto: Producto) -> None:
        """
         Actualiza los valores comerciales y descriptivos de un producto existente.
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
        cursor.execute('''
            SELECT id, codigo, descripcion, categoria, id_proveedor, 
                   precio_costo, precio_venta, stock_actual, stock_minimo, 
                   vencimiento, habilitado
            FROM productos
            WHERE codigo = ? AND habilitado = 1
        ''', (codigo,))
        
        fila = cursor.fetchone()
        return self._mapear_a_entidad(fila) if fila else None

    def obtener_por_id(self, id_producto: int) -> Optional[Producto]:
        """
         Busca un producto directamente por su clave primaria (PK) física.
        """
        cursor = self.conexion.cursor()
        cursor.execute('''
            SELECT id, codigo, descripcion, categoria, id_proveedor, 
                   precio_costo, precio_venta, stock_actual, stock_minimo, 
                   vencimiento, habilitado
            FROM productos
            WHERE id = ? AND habilitado = 1
        ''', (id_producto,))
        
        fila = cursor.fetchone()
        return self._mapear_a_entidad(fila) if fila else None

    def actualizar_stock(self, id_producto: int, variacion: float) -> None:
        """
         Suma o resta cantidades al stock físico directamente en el motor SQL.
        
         NOTA DE DISEÑO: Delegar esta matemática a SQLite (stock_actual = stock_actual + variacion)
         previene las Condiciones de Carrera (Race Conditions) que ocurrirían si dos 
         usuarios facturan exactamente al mismo tiempo y sobreescriben la lectura del otro.
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
            habilitado=fila[10]
        )