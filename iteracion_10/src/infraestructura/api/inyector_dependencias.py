import os
from fastapi import Depends, Header
from src.dominio.puertos import PuertoUnidadDeTrabajo, PuertoHashing
from src.infraestructura.persistencia.gestor_sqlite import GestorSQLite
from src.infraestructura.seguridad.adaptador_bcrypt import AdaptadorBcrypt
from src.aplicacion.casos_uso_perfiles import ServicioPerfiles
from src.aplicacion.casos_uso_inventario import ServicioInventario
from src.aplicacion.casos_uso_comercial import ServicioComercial

# ================================================================================
#  INYECTOR DE DEPENDENCIAS Y FÁBRICA DE SERVICIOS (CAPA 3 - INFRAESTRUCTURA)
# ================================================================================
#  DECISIÓN DE DISEÑO (INVERSIÓN DE CONTROL Y PATRÓN FÁBRICA):
#
#   Las rutas HTTP (endpoints) no deben saber cómo se instancia una base de datos 
#   ni qué librería encripta las claves. Este módulo centraliza la creación y el 
#   "cableado" (wiring) de todas las piezas.
#  
#   Además, separar 'obtener_uow' nos permite interceptarla fácilmente en Pytest 
#   para desviar el tráfico hacia una base de datos temporal sin tocar el código.
# ================================================================================



# 1. Resolución dinámica de la ruta hacia la base de datos física de producción.
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(DIRECTORIO_ACTUAL)))
RUTA_DB_OFICIAL = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")


# ---------------------------------------------------
#  PROVEEDORES DE ADAPTADORES BASE (INFRAESTRUCTURA)
# ---------------------------------------------------

def obtener_uow() -> PuertoUnidadDeTrabajo:
    """
     Provee una instancia limpia de la Unidad de Trabajo apuntando a SQLite.
     En los tests de integración, FastAPI reemplaza esta función al vuelo 
     mediante 'dependency_overrides' para usar una base efímera aislada.
    """
    return GestorSQLite(RUTA_DB_OFICIAL)


def obtener_hasher() -> PuertoHashing:
    """
     Provee el adaptador criptográfico concreto (Bcrypt).
    """
    return AdaptadorBcrypt()


def obtener_id_operador(
    x_operador_id: int = Header(default=1, alias="X-Operador-Id")
) -> int:
    """
     Intercepta la cabecera HTTP 'X-Operador-Id' enviada por el cliente 
     (Tkinter o Web) para identificar quién está ejecutando la acción y 
     aplicar las políticas jerárquicas RBAC correspondientes.
    """
    return x_operador_id


# -----------------------------------------------
#  FÁBRICAS DE CASOS DE USO (CAPA DE APLICACIÓN)
# -----------------------------------------------

def obtener_servicio_perfiles(
    uow: PuertoUnidadDeTrabajo = Depends(obtener_uow),
    hasher: PuertoHashing = Depends(obtener_hasher)
) -> ServicioPerfiles:
    """
     Ensambla y entrega el Servicio de Perfiles con su Unidad de Trabajo 
     y su motor de hashing ya inyectados.
    """
    return ServicioPerfiles(uow=uow, hasher=hasher)


def obtener_servicio_inventario(
    uow: PuertoUnidadDeTrabajo = Depends(obtener_uow)
) -> ServicioInventario:
    """
     Ensambla y entrega el Servicio de Inventario listo para operar.
    """
    return ServicioInventario(uow=uow)


def obtener_servicio_comercial(
    uow: PuertoUnidadDeTrabajo = Depends(obtener_uow)
) -> ServicioComercial:
    """
     Ensambla y entrega el Servicio Comercial para facturación y anulaciones.
    """
    return ServicioComercial(uow=uow)