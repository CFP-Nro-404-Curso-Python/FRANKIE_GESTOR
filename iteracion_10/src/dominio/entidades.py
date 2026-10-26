# ========================================================================================
#  ENTIDADES DE DOMINIO (CAPA 1 - NÚCLEO DE NEGOCIO)
# ========================================================================================
#  DECISIÓN DE DISEÑO (KISS / YAGNI / DIP):

#   Usamos 'dataclasses' nativas de Python para evitar el código repetitivo (boilerplate) 
#   de los constructores __init__. Estas clases son Puras (POJOs/POCOs): no saben 
#   absolutamente nada de bases de datos, diccionarios JSON, ni validaciones web.
#  
#   Su único propósito es modelar los conceptos del negocio en la memoria RAM.
# ========================================================================================



from dataclasses import dataclass
from typing import Optional

@dataclass
class PerfilUsuario:
    """
     Entidad polimórfica que representa a cualquier actor del sistema.
     Abstrae a Administradores, Gerentes, Empleados, Clientes y Proveedores.
    """
    nombres: str
    apellidos: str
    dni: str
    rol: str
    # Opcionales porque un Cliente o Proveedor se crea sin credenciales de acceso.
    usuario: Optional[str] = None
    password_hash: Optional[str] = None
    # El ID es opcional al instanciar porque un usuario nuevo aún no fue persistido.
    id: Optional[int] = None
    habilitado: int = 1


@dataclass
class Producto:
    """
     Entidad que representa un artículo en el inventario.
     Contiene la lógica base comercial (precios y stock).
    """
    codigo: str
    descripcion: str
    categoria: str
    id_proveedor: int
    precio_costo: float
    precio_venta: float
    stock_actual: float
    stock_minimo: float = 0.0
    vencimiento: str = "S/D"
    id: Optional[int] = None
    habilitado: int = 1

    def hay_stock_suficiente(self, cantidad_requerida: float) -> bool:
        """
         Regla de negocio encapsulada (Alta Cohesión): 
         Es el propio producto quien sabe si puede satisfacer una demanda, 
         no la base de datos ni el controlador de la API.
        """
        return self.stock_actual >= cantidad_requerida


@dataclass
class Factura:
    """
     Entidad transaccional que representa un comprobante de venta.
     Vincula a los actores (vendedor, cliente) con el inventario (producto).
    """
    id_vendedor: int
    id_cliente: int
    id_producto: int
    cantidad: float
    valor: float  # Precio congelado al momento exacto de la operación.
    descuento: float = 0.0
    # La fecha y el total se delegan por defecto al motor de base de datos, 
    # pero la entidad puede recibirlos para reconstruir el historial en RAM.
    fecha: Optional[str] = None
    total: Optional[float] = None
    id: Optional[int] = None
    habilitado: int = 1

    def calcular_total_estimado(self) -> float:
        """
         Regla de negocio encapsulada:
         Calcula cómo debería dar el total antes de delegar la persistencia física.
        """
        subtotal = self.cantidad * self.valor
        return subtotal * (1 - (self.descuento / 100.0))