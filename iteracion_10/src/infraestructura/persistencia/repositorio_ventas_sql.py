import sqlite3
from src.dominio.entidades import Factura
from src.dominio.puertos import PuertoRepositorioVentas

# =================================================================================
#  REPOSITORIO DE VENTAS SQL (CAPA 3 - INFRAESTRUCTURA)
# =================================================================================
#  DECISIÓN DE DISEÑO (INMUTABILIDAD Y AUDITORÍA):
#
#  Este repositorio se encarga de persistir las transacciones comerciales.
#  
#  Como una factura es un documento legal/contable, no existe un método 
#  'modificar'. Si ocurre un error, se "anula" (soft delete) y se emite una nueva.
# =================================================================================



class RepositorioVentasSQL(PuertoRepositorioVentas):
    
    def __init__(self, conexion: sqlite3.Connection):
        """
         Recibe la conexión activa inyectada por el GestorSQLite (Unidad de Trabajo).
        """
        self.conexion = conexion

    def guardar(self, factura: Factura) -> int:
        """
         Registra un comprobante de venta en la base de datos.
        
         Nota de diseño: Le pedimos a la entidad de dominio que calcule su 
         propio total con sus reglas de negocio antes de guardar, y dejamos 
         que el motor SQLite asigne la fecha exacta con CURRENT_TIMESTAMP.
        """
        cursor = self.conexion.cursor()
        
        # 1. Ejecutamos la regla de negocio encapsulada.
        total_calculado = factura.calcular_total_estimado()
        
        # 2. Insertamos la transacción física.
        cursor.execute('''
            INSERT INTO facturas (
                id_vendedor, id_cliente, id_producto, 
                cantidad, valor, descuento, total, habilitado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', (
            factura.id_vendedor, 
            factura.id_cliente, 
            factura.id_producto, 
            factura.cantidad, 
            factura.valor, 
            factura.descuento, 
            total_calculado
        ))
        
        return cursor.lastrowid

    def eliminar(self, id_factura: int) -> None:
        """
         Aplica el Borrado Lógico (Soft Delete) cambiando habilitado a 0.
         Representa la 'Anulación' de una venta, preservando el registro 
         histórico para auditoría y analítica.
        """
        cursor = self.conexion.cursor()
        cursor.execute("UPDATE facturas SET habilitado = 0 WHERE id = ?", (id_factura,))