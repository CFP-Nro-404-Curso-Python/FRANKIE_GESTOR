import sqlite3
from typing import List, Optional
from src.dominio.entidades import Factura
from src.dominio.puertos import PuertoRepositorioVentas

# ==================================================================================
#  REPOSITORIO DE VENTAS SQL (CAPA 3 - INFRAESTRUCTURA)
# ==================================================================================
#  DECISIÓN DE DISEÑO (INMUTABILIDAD Y AUDITORÍA):
#
#   Este repositorio se encarga de persistir las transacciones comerciales.
#
#   Como una factura es un documento legal/contable, no existe un método
#   'modificar'. Si ocurre un error, se "anula" (soft delete) y se emite una nueva.
# ==================================================================================


class RepositorioVentasSQL(PuertoRepositorioVentas):

    def __init__(self, conexion: sqlite3.Connection):
        """
         Recibe la conexión activa inyectada por el GestorSQLite (Unidad de Trabajo).
        """
        self.conexion = conexion

    def guardar(self, factura: Factura) -> int:
        """
         Registra un comprobante de venta en la base de datos.
         La columna 'total' se delega a GENERATED ALWAYS AS en SQLite.
        """
        cursor = self.conexion.cursor()

        # Ejecutamos la regla de negocio encapsulada para validar los montos en Dominio.
        factura.calcular_total_estimado()

        cursor.execute('''
            INSERT INTO facturacion (
                id_vendedor, id_cliente, id_producto,
                cantidad, valor, descuento, habilitado
            ) VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (
            factura.id_vendedor,
            factura.id_cliente,
            factura.id_producto,
            factura.cantidad,
            factura.valor,
            factura.descuento
        ))

        return cursor.lastrowid

    def obtener_por_id(self, id_factura: int) -> Optional[Factura]:
        """
         Recupera una factura activa por su clave primaria (PK).
         Requerido para restituir atómicamente el stock al anular un comprobante
         y prevenir anulaciones duplicadas sobre comprobantes ya deshabilitados.
        """
        cursor = self.conexion.cursor()
        cursor.execute('''
            SELECT id, id_vendedor, id_cliente, id_producto,
                   cantidad, valor, descuento, fecha, total, habilitado
            FROM facturacion
            WHERE id = ? AND habilitado = 1
        ''', (id_factura,))

        fila = cursor.fetchone()
        return self._mapear_a_entidad(fila) if fila else None

    def eliminar(self, id_factura: int) -> None:
        """
         Aplica el Borrado Lógico (Soft Delete) cambiando habilitado a 0.
         Representa la 'Anulación' de una venta, preservando el registro
         histórico para auditoría y analítica.
        """
        cursor = self.conexion.cursor()
        cursor.execute("UPDATE facturacion SET habilitado = 0 WHERE id = ?", (id_factura,))

    def listar_todos(self) -> List[Factura]:
        """
         Devuelve la lista completa del historial transaccional activo.
        """
        cursor = self.conexion.cursor()
        cursor.execute('''
            SELECT id, id_vendedor, id_cliente, id_producto,
                   cantidad, valor, descuento, fecha, total, habilitado
            FROM facturacion
            WHERE habilitado = 1
        ''')

        return [self._mapear_a_entidad(fila) for fila in cursor.fetchall()]

    def _mapear_a_entidad(self, fila: tuple) -> Factura:
        """
         Función privada auxiliar. Transforma la tupla cruda que devuelve SQLite
         a nuestro objeto puro de negocio.
        """
        return Factura(
            id=fila[0],
            id_vendedor=fila[1],
            id_cliente=fila[2],
            id_producto=fila[3],
            cantidad=fila[4],
            valor=fila[5],
            descuento=fila[6],
            fecha=fila[7],
            total=fila[8],
            habilitado=fila[9]
        )