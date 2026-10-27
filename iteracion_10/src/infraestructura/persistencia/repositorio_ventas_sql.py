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
        # Aunque SQLite calcula el total físico en disco, ejecutamos esto para que 
        # el Dominio valide matemáticamente los montos (ej. que no haya precios negativos).
        factura.calcular_total_estimado()
        
        # 2. Insertamos la transacción física.
        # -----------------------------------------------------------------------------
        # CAMBIO APLICADO:
        #  
        #  - Se corrigió el nombre de la tabla ('facturacion' en lugar de 'facturas').
        #  - Se quitó la inserción manual de la columna 'total' ya que SQLite 
        #    la genera automáticamente (GENERATED ALWAYS AS) según el esquema.sql.
        # -----------------------------------------------------------------------------
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

    def eliminar(self, id_factura: int) -> None:
        """
         Aplica el Borrado Lógico (Soft Delete) cambiando habilitado a 0.
         Representa la 'Anulación' de una venta, preservando el registro 
         histórico para auditoría y analítica.
        """
        cursor = self.conexion.cursor()
        
        # -----------------------------------------------------------------------------
        # CAMBIO APLICADO:
        #  
        #  - Se corrigió el nombre de la tabla ('facturacion' en lugar de 'facturas').
        # -----------------------------------------------------------------------------
        
        cursor.execute("UPDATE facturacion SET habilitado = 0 WHERE id = ?", (id_factura,))