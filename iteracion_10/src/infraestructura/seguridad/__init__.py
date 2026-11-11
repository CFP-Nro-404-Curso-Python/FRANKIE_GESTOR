# ===========================================================================
#  PAQUETE DE SEGURIDAD Y CRIPTOGRAFÍA (CAPA 3 - INFRAESTRUCTURA)
# ===========================================================================
#  DECISIÓN DE DISEÑO (PATRÓN ADAPTADOR Y DIP):
#
#   Expone la implementación concreta del contrato 'PuertoHashing' (Bcrypt),
#   manteniendo aislada la librería criptográfica del núcleo de Dominio.
# ===========================================================================

from src.infraestructura.seguridad.adaptador_bcrypt import AdaptadorBcrypt

__all__ = [
    "AdaptadorBcrypt",
]