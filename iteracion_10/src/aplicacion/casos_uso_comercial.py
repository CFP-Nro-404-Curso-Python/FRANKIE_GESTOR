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
#   Tanto emitir como anular una factura afectan dos tablas distintas:
#   'facturacion' y 'productos'. El bloque 'with self.uow:' garantiza que ambas
#   operaciones ocurran como una unidad atómica (Commit total o Rollback).
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
         del producto, guarda la factura y decrementa el stock en una sola
         transacción (Commit o Rollback).
        """
        with self.uow:
            producto = self.uow.productos.obtener_por_id(id_producto)

            if not producto:
                raise ErrorEntidadNoEncontrada("El producto que intentás facturar no existe o está inactivo.")

            if not producto.hay_stock_suficiente(cantidad):
                raise ErrorStockInsuficiente(
                    f"Stock insuficiente. Intentás vender {cantidad} pero solo hay {producto.stock_actual} disponibles."
                )

            nueva_factura = Factura(
                id_vendedor=id_vendedor,
                id_cliente=id_cliente,
                id_producto=id_producto,
                cantidad=cantidad,
                valor=producto.precio_venta,
                descuento=descuento
            )

            id_factura = self.uow.ventas.guardar(nueva_factura)
            self.uow.productos.actualizar_stock(id_producto, -cantidad)

            return id_factura

    def anular_factura(self, id_factura: int) -> None:
        """
         Caso de Uso: Anulación atómica de venta (Soft Delete + Restitución de Stock).
         Recupera la factura activa, la da de baja lógicamente y devuelve la
         cantidad vendida al stock del producto dentro de la misma transacción ACID.
        """
        with self.uow:
            factura = self.uow.ventas.obtener_por_id(id_factura)

            if not factura:
                raise ErrorEntidadNoEncontrada(
                    "La factura que intentás anular no existe o ya fue anulada previamente."
                )

            self.uow.ventas.eliminar(id_factura)
            self.uow.productos.actualizar_stock(factura.id_producto, factura.cantidad)

    def listar_facturas(self) -> list[Factura]:
        """
         Caso de Uso: Obtener el historial completo de facturas emitidas y activas.
        """
        with self.uow:
            return self.uow.ventas.listar_todos()