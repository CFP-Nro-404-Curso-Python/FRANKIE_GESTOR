from typing import Optional
from pydantic import BaseModel

# ==============================================================================
#  ESQUEMAS DE VALIDACIÓN / DTOs (CAPA 3 - INFRAESTRUCTURA API)
# ==============================================================================
#  DECISIÓN DE DISEÑO (PATRÓN DTO Y BARRERA DE ENTRADA):
#
#  Usamos Pydantic para definir los Objetos de Transferencia de Datos (DTOs).
#
#  Su único trabajo es validar que el JSON que llega por la red tenga los tipos 
#  de datos correctos (int, float, str) antes de tocar los Casos de Uso.
#
#  Si alguien envía texto donde iba un número, FastAPI rechaza la petición 
#  automáticamente con un error HTTP 422 sin ensuciar el Dominio.
# ==============================================================================



# -----------------------------------------------------------------------------
#  1. ESQUEMAS PARA PERFILES Y AUTENTICACIÓN (USUARIOS, RRHH, CLIENTES, PROV.)
# -----------------------------------------------------------------------------

class EsquemaLogin(BaseModel):
    """Estructura exigida para iniciar sesión."""
    usuario: str
    password: str


class EsquemaPerfilCrear(BaseModel):
    """
     Datos requeridos para dar de alta cualquier perfil humano/comercial.
     'usuario' y 'password_plana' son opcionales porque un Cliente o Proveedor 
     no necesita credenciales para operar en el sistema.
    """
    nombres: str
    apellidos: str
    dni: str
    rol: str
    usuario: Optional[str] = None
    password_plana: Optional[str] = None


class EsquemaPerfilModificar(BaseModel):
    """
     Campos permitidos al editar un perfil existente. 
     Todos son opcionales para permitir actualizaciones parciales.
    """
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    dni: Optional[str] = None
    rol: Optional[str] = None
    usuario: Optional[str] = None
    password_plana: Optional[str] = None


class EsquemaPerfilRespuesta(BaseModel):
    """
     Molde de salida para devolver datos de un usuario hacia el frontend.
    
     NOTA DE SEGURIDAD: Omitimos intencionalmente el campo 'password_hash' 
     para garantizar que jamás viaje una clave encriptada por la red.
    """
    id: int
    nombres: str
    apellidos: str
    dni: str
    rol: str
    usuario: Optional[str] = None
    habilitado: int = 1


# -----------------------------------------
#  2. ESQUEMAS PARA INVENTARIO Y PRODUCTOS
# -----------------------------------------

class EsquemaProductoCrear(BaseModel):
    """Datos requeridos para registrar un nuevo artículo en el catálogo."""
    codigo: str
    descripcion: str
    categoria: str
    id_proveedor: int
    precio_costo: float
    precio_venta: float
    stock_actual: float = 0.0
    stock_minimo: float = 0.0
    vencimiento: str = "S/D"


class EsquemaProductoModificar(BaseModel):
    """
     Datos permitidos para actualizar detalles comerciales de un producto.
     No incluye 'stock_actual' porque el inventario solo debe moverse 
     mediante operaciones atómicas de ingreso o facturación.
    """
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    id_proveedor: Optional[int] = None
    precio_costo: Optional[float] = None
    precio_venta: Optional[float] = None
    stock_minimo: Optional[float] = None
    vencimiento: Optional[str] = None


class EsquemaIngresoStock(BaseModel):
    """Payload simple para sumar mercadería a un producto existente."""
    cantidad: float


class EsquemaProductoRespuesta(BaseModel):
    """Molde de salida con el estado completo de un producto en catálogo."""
    id: int
    codigo: str
    descripcion: str
    categoria: str
    id_proveedor: int
    precio_costo: float
    precio_venta: float
    stock_actual: float
    stock_minimo: float
    vencimiento: str
    habilitado: int = 1


# --------------------------------------------------------
#  3. ESQUEMAS PARA OPERACIONES COMERCIALES (FACTURACIÓN)
# --------------------------------------------------------

class EsquemaFacturaCrear(BaseModel):
    """Datos necesarios para emitir un comprobante de venta."""
    id_vendedor: int
    id_cliente: int
    id_producto: int
    cantidad: float
    descuento: float = 0.0