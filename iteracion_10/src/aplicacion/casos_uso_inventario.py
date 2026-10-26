from src.dominio.entidades import Producto
from src.dominio.excepciones import ErrorEntidadNoEncontrada
from src.dominio.puertos import PuertoUnidadDeTrabajo

# ==============================================================================
#  CASOS DE USO: GESTIÓN DE INVENTARIO (CAPA 2 - APLICACIÓN)
# ==============================================================================
#  DECISIÓN DE DISEÑO (ORQUESTACIÓN Y PROTECCIÓN DE CONCURRENCIA):
#
#   El Servicio de Inventario coordina la creación y edición del catálogo.
#  
#   Nota clave: La modificación general de un producto excluye intencionalmente 
#   al 'stock_actual' para evitar Condiciones de Carrera. El stock solo se 
#   toca de manera atómica (sumando o restando) mediante actualizar_stock.
# ==============================================================================



class ServicioInventario:
    """
     Orquesta los flujos de trabajo relacionados con el catálogo de artículos
     y el control de stock base.
    """

    def __init__(self, uow: PuertoUnidadDeTrabajo):
        """
         Inyección de Dependencias. El servicio interactúa con las interfaces (puertos), 
         desconociendo si por detrás corre SQLite o cualquier otro motor.
        """
        self.uow = uow

    def registrar_producto(self, datos: dict) -> int:
        """
         Caso de Uso: Alta de un nuevo producto en el catálogo.
         Convierte el diccionario crudo de entrada en una entidad validada y la persiste.
        """
        with self.uow:
            nuevo_producto = Producto(
                codigo=datos["codigo"],
                descripcion=datos["descripcion"],
                categoria=datos["categoria"],
                id_proveedor=datos["id_proveedor"],
                precio_costo=datos["precio_costo"],
                precio_venta=datos["precio_venta"],
                stock_actual=datos.get("stock_actual", 0.0),
                stock_minimo=datos.get("stock_minimo", 0.0),
                vencimiento=datos.get("vencimiento", "S/D")
            )
            return self.uow.productos.guardar(nuevo_producto)

    def modificar_producto(self, id_producto: int, datos: dict) -> None:
        """
         Caso de Uso: Edición de datos maestros del producto (precios, descripciones).
        """
        with self.uow:
            producto = self.uow.productos.obtener_por_id(id_producto)
            
            if not producto:
                raise ErrorEntidadNoEncontrada("El producto que intentás modificar no existe.")

            # Actualizamos los atributos en memoria.
            producto.codigo = datos.get("codigo", producto.codigo)
            producto.descripcion = datos.get("descripcion", producto.descripcion)
            producto.categoria = datos.get("categoria", producto.categoria)
            producto.id_proveedor = datos.get("id_proveedor", producto.id_proveedor)
            producto.precio_costo = datos.get("precio_costo", producto.precio_costo)
            producto.precio_venta = datos.get("precio_venta", producto.precio_venta)
            producto.stock_minimo = datos.get("stock_minimo", producto.stock_minimo)
            producto.vencimiento = datos.get("vencimiento", producto.vencimiento)
            
            # Persistimos los cambios usando la Unidad de Trabajo (ACID).
            self.uow.productos.modificar(producto)

    def dar_de_baja_producto(self, id_producto: int) -> None:
        """
         Caso de Uso: Borrado lógico de un producto (Soft Delete).
         Mantiene intacto el historial contable de facturas pasadas.
        """
        with self.uow:
            producto = self.uow.productos.obtener_por_id(id_producto)
            
            if not producto:
                raise ErrorEntidadNoEncontrada("El producto que intentás eliminar no existe.")
                
            self.uow.productos.eliminar(id_producto)

    def registrar_ingreso_stock(self, id_producto: int, cantidad: float) -> None:
        """
         Caso de Uso: Ingreso manual de mercadería (ej. llega pedido del proveedor).
         Utiliza el método de actualización atómica en base de datos.
        """
        with self.uow:
            producto = self.uow.productos.obtener_por_id(id_producto)
            
            if not producto:
                raise ErrorEntidadNoEncontrada("El producto al que intentás sumarle stock no existe.")
                
            self.uow.productos.actualizar_stock(id_producto, cantidad)