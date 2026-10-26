from src.dominio.entidades import Factura
from src.dominio.excepciones import ErrorEntidadNoEncontrada, ErrorStockInsuficiente
from src.dominio.puertos import PuertoUnidadDeTrabajo

# =============================================================================
#  CASOS DE USO: GESTIÓN COMERCIAL Y FACTURACIÓN (CAPA 2 - APLICACIÓN)
# =============================================================================
#  DECISIÓN DE DISEÑO (TRANSACCIONES ACID Y ORQUESTACIÓN):
#
#   Acá se ve el verdadero poder del Patrón Unidad de Trabajo (UoW).
#  
#   Emitir una factura implica afectar dos tablas distintas: insertar la venta 
#   y descontar el stock del producto. Si falla el descuento de stock, la 
#   factura no se debe guardar. El bloque 'with self.uow:' garantiza que 
#   ambas operaciones ocurran como un bloque atómico.
# =============================================================================



class ServicioComercial:
    """
     Orquesta las operaciones de facturación, anulaciones y su impacto
     directo en el inventario.
    """

    def __init__(self, uow: PuertoUnidadDeTrabajo):
        self.uow = uow

    def emitir_factura(self, id_vendedor: int, id_cliente: int, id_producto: int, cantidad: float, descuento: float = 0.0) -> int:
        """
         Caso de Uso: Emisión de una nueva venta.
         Verifica el stock a través de la entidad, congela el precio histórico 
         del producto, guarda la factura y decrementa el stock, todo en una 
         sola transacción (Commit o Rollback).
        """
        with self.uow:
            # 1. Recuperamos el producto para validar reglas de negocio.
            producto = self.uow.productos.obtener_por_id(id_producto)
            
            if not producto:
                raise ErrorEntidadNoEncontrada("El producto que intentás facturar no existe o está inactivo.")
            
            # 2. Consultamos a la entidad si puede satisfacer la demanda (Alta Cohesión).
            if not producto.hay_stock_suficiente(cantidad):
                raise ErrorStockInsuficiente(
                    f"Stock insuficiente. Intentás vender {cantidad} pero solo hay {producto.stock_actual} disponibles."
                )
            
            # 3. Construimos la entidad Factura.
            # Nota: Congelamos el 'valor' con el precio de venta actual del producto, 
            # para que la contabilidad no se rompa si el producto aumenta mañana.
            nueva_factura = Factura(
                id_vendedor=id_vendedor,
                id_cliente=id_cliente,
                id_producto=id_producto,
                cantidad=cantidad,
                valor=producto.precio_venta,
                descuento=descuento
            )
            
            # 4. Guardamos la factura en el repositorio de ventas.
            id_factura = self.uow.ventas.guardar(nueva_factura)
            
            # 5. Descontamos el stock atómicamente en el repositorio de productos.
            # Pasamos la cantidad en negativo para restar.
            self.uow.productos.actualizar_stock(id_producto, -cantidad)
            
            return id_factura

    def anular_factura(self, id_factura: int) -> None:
        """
         Caso de Uso: Anulación de venta (Soft Delete).
         En un sistema real, una anulación no solo borra la factura de la vista, 
         sino que debe restituir el stock al inventario.
        """
        with self.uow:
            # En la iteración actual, asumimos que el repositorio de ventas 
            # aplica el borrado lógico. Para restituir el stock, primero deberíamos 
            # consultar la cantidad y el id_producto de esta factura.
            # Como aún no implementamos el 'obtener_por_id' en ventas, aplicamos 
            # la anulación básica. En la próxima iteración, agregaremos la lectura 
            # para hacer la restitución completa.
            self.uow.ventas.eliminar(id_factura)