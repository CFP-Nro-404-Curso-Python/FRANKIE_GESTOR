# ===================================================================================
#  PAQUETE DE PERSISTENCIA FÍSICA SQLITE (CAPA 3 - INFRAESTRUCTURA)
# ===================================================================================
#  DECISIÓN DE DISEÑO (PATRÓN UNIDAD DE TRABAJO Y REPOSITORIO):
#
#   Centraliza el acceso a los adaptadores SQLite en Tercera Forma Normal (3FN).
#   El orden de importación respeta la jerarquía interna (utilidades -> repositorios
#   -> gestor transaccional) previniendo referencias circulares.
# ===================================================================================

from src.infraestructura.persistencia.utilidades_sql import obtener_o_crear
from src.infraestructura.persistencia.repositorio_perfiles_sql import RepositorioPerfilesSQL
from src.infraestructura.persistencia.repositorio_productos_sql import RepositorioProductosSQL
from src.infraestructura.persistencia.repositorio_ventas_sql import RepositorioVentasSQL
from src.infraestructura.persistencia.gestor_sqlite import GestorSQLite

__all__ = [
    "obtener_o_crear",
    "RepositorioPerfilesSQL",
    "RepositorioProductosSQL",
    "RepositorioVentasSQL",
    "GestorSQLite",
]