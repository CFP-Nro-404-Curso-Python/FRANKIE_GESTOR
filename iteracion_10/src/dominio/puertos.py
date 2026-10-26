# ===============================================================================
#  PUERTOS (CAPA 1 - NÚCLEO DE NEGOCIO / ARQUITECTURA HEXAGONAL)
# ===============================================================================
#  DECISIÓN DE DISEÑO (PRINCIPIO DE INVERSIÓN DE DEPENDENCIAS - DIP):

#   Los "Puertos" son simplemente Interfaces (Clases Base Abstractas en Python).

#   El dominio define aquí QUÉ necesita (guardar un usuario, hashear una clave),
#   pero no le importa CÓMO se hace. Las capas externas (Infraestructura) 
#   están obligadas a implementar estos contratos.

#   Gracias a esto, el negocio no depende de SQLite ni de Bcrypt.
# ===============================================================================



from abc import ABC, abstractmethod
from typing import List, Optional
from src.dominio.entidades import PerfilUsuario, Producto, Factura

class PuertoHashing(ABC):
    """
     Contrato para cualquier sistema de encriptación de contraseñas.
     Mañana podemos cambiar Bcrypt por Argon2 sin tocar la lógica de negocio.
    """
    @abstractmethod
    def hashear_password(self, password_plana: str) -> str:
        pass

    @abstractmethod
    def verificar_password(self, password_plana: str, password_hash: str) -> bool:
        pass


class PuertoRepositorioPerfiles(ABC):
    """
     Contrato para la persistencia de actores del sistema (Usuarios, Empleados, etc.).
    """
    @abstractmethod
    def guardar(self, perfil: PerfilUsuario) -> int:
        pass

    @abstractmethod
    def modificar(self, perfil: PerfilUsuario) -> None:
        pass

    @abstractmethod
    def eliminar(self, id_perfil: int) -> None:
        pass

    @abstractmethod
    def obtener_por_usuario(self, usuario: str) -> Optional[PerfilUsuario]:
        pass

    @abstractmethod
    def obtener_por_id(self, id_perfil: int) -> Optional[PerfilUsuario]:
        pass

    @abstractmethod
    def listar_por_rol(self, rol: str) -> List[PerfilUsuario]:
        pass

    @abstractmethod
    def obtener_rol_por_id(self, id_perfil: int) -> Optional[str]:
        pass


class PuertoRepositorioProductos(ABC):
    """
     Contrato para la persistencia y gestión de inventario.
    """
    @abstractmethod
    def guardar(self, producto: Producto) -> int:
        pass

    @abstractmethod
    def modificar(self, producto: Producto) -> None:
        pass

    @abstractmethod
    def eliminar(self, id_producto: int) -> None:
        pass

    @abstractmethod
    def obtener_por_codigo(self, codigo: str) -> Optional[Producto]:
        pass

    @abstractmethod
    def obtener_por_id(self, id_producto: int) -> Optional[Producto]:
        pass

    @abstractmethod
    def actualizar_stock(self, id_producto: int, variacion: float) -> None:
        pass


class PuertoRepositorioVentas(ABC):
    """
     Contrato para el registro transaccional de facturación.
    """
    @abstractmethod
    def guardar(self, factura: Factura) -> int:
        pass

    @abstractmethod
    def eliminar(self, id_factura: int) -> None:
        pass


class PuertoUnidadDeTrabajo(ABC):
    """
     Contrato para el Patrón Unidad de Trabajo (Unit of Work).
     Garantiza que las operaciones de los repositorios se ejecuten en bloque (ACID).
     Si algo falla, debe permitir deshacer (rollback) todos los cambios.
     Utiliza los métodos mágicos __enter__ y __exit__ para funcionar con 'with'.
    """
    perfiles: PuertoRepositorioPerfiles
    productos: PuertoRepositorioProductos
    ventas: PuertoRepositorioVentas

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, traceback):
        pass

    @abstractmethod
    def commit(self) -> None:
        pass

    @abstractmethod
    def rollback(self) -> None:
        pass