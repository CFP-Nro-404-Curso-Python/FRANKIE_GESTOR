from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from src.dominio.entidades import PerfilUsuario
from src.aplicacion.casos_uso_perfiles import ServicioPerfiles
from src.infraestructura.api.esquemas_validacion import (
    EsquemaLogin,
    EsquemaPerfilCrear,
    EsquemaPerfilModificar,
    EsquemaPerfilRespuesta
)
from src.infraestructura.api.inyector_dependencias import (
    obtener_servicio_perfiles,
    obtener_id_operador
)



# ================================================================================
#  ENRUTADOR DE PERFILES Y AUTENTICACIÓN (CAPA 3 - INFRAESTRUCTURA API)
# ================================================================================
#  DECISIÓN DE DISEÑO (CONTROLADOR LIGERO / THIN CONTROLLER):
#
#   Este módulo solo maneja el protocolo HTTP (rutas, códigos de estado 200, 201, 
#   401, 404 y validación de entrada/salida con DTOs).
# ================================================================================


router = APIRouter(
    prefix="/api/perfiles",
    tags=["Perfiles y Autenticación"]
)


def _serializar_perfil(p: PerfilUsuario) -> EsquemaPerfilRespuesta:
    """Convierte la entidad PerfilUsuario en el DTO de respuesta HTTP completo."""
    return EsquemaPerfilRespuesta(
        id=p.id,
        nombres=p.nombres,
        apellidos=p.apellidos,
        dni=p.dni,
        rol=p.rol,
        usuario=p.usuario,
        telefono=p.telefono,
        email=p.email,
        direccion=p.direccion,
        ciudad=p.ciudad,
        provincia=p.provincia,
        cp=p.cp,
        habilitado=p.habilitado
    )


# --------------------------------------
#  1. ENDPOINT DE AUTENTICACIÓN (LOGIN)
# --------------------------------------

@router.post(
    "/login",
    response_model=EsquemaPerfilRespuesta,
    status_code=status.HTTP_200_OK
)
def iniciar_sesion(
    credenciales: EsquemaLogin,
    servicio: ServicioPerfiles = Depends(obtener_servicio_perfiles)
):
    """
     Recibe usuario y contraseña en texto plano, delega la verificación 
     criptográfica (Bcrypt) al caso de uso y devuelve los datos del perfil activo.
    """
    perfil = servicio.autenticar_usuario(
        usuario=credenciales.usuario,
        password_plana=credenciales.password
    )
    
    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas o usuario inactivo."
        )
        
    return _serializar_perfil(perfil)


# ----------------------------------------------------------------------
#  2. ENDPOINTS ABM DE PERFILES (USUARIOS, RRHH, CLIENTES, PROVEEDORES)
# ----------------------------------------------------------------------

@router.post(
    "",
    status_code=status.HTTP_201_CREATED
)
def crear_perfil(
    datos: EsquemaPerfilCrear,
    id_operador: int = Depends(obtener_id_operador),
    servicio: ServicioPerfiles = Depends(obtener_servicio_perfiles)
):
    """
     Registra un nuevo actor en el sistema (Empleado, Cliente, Proveedor, etc.).
    """
    id_generado = servicio.registrar_perfil(
        id_operador=id_operador,
        datos=datos.model_dump()
    )
    
    return {
        "id": id_generado,
        "mensaje": "Perfil registrado correctamente."
    }


@router.get(
    "",
    response_model=List[EsquemaPerfilRespuesta],
    status_code=status.HTTP_200_OK
)
def listar_todos_los_perfiles(
    servicio: ServicioPerfiles = Depends(obtener_servicio_perfiles)
):
    """
     Devuelve la nómina completa de perfiles activos en el sistema sin importar su rol.
    """
    perfiles = servicio.listar_perfiles()
    return [_serializar_perfil(p) for p in perfiles]


@router.get(
    "/rol/{rol}",
    response_model=List[EsquemaPerfilRespuesta],
    status_code=status.HTTP_200_OK
)
def listar_perfiles_por_rol(
    rol: str,
    servicio: ServicioPerfiles = Depends(obtener_servicio_perfiles)
):
    """
     Devuelve la nómina de perfiles activos filtrados por su rol comercial.
    """
    with servicio.uow:
        perfiles = servicio.uow.perfiles.listar_por_rol(rol)
        return [_serializar_perfil(p) for p in perfiles]


@router.get(
    "/{id_perfil}",
    response_model=EsquemaPerfilRespuesta,
    status_code=status.HTTP_200_OK
)
def obtener_perfil_por_id(
    id_perfil: int,
    servicio: ServicioPerfiles = Depends(obtener_servicio_perfiles)
):
    """
     Busca y retorna un perfil específico por su clave primaria (ID).
    """
    with servicio.uow:
        perfil = servicio.uow.perfiles.obtener_por_id(id_perfil)
        
        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró un perfil activo con ID {id_perfil}."
            )
            
        return _serializar_perfil(perfil)


@router.put(
    "/{id_perfil}",
    status_code=status.HTTP_200_OK
)
def modificar_perfil(
    id_perfil: int,
    datos: EsquemaPerfilModificar,
    id_operador: int = Depends(obtener_id_operador),
    servicio: ServicioPerfiles = Depends(obtener_servicio_perfiles)
):
    """
     Actualiza los datos maestros, de contacto/ubicación o credenciales de un perfil existente.
    """
    servicio.modificar_perfil(
        id_operador=id_operador,
        id_destino=id_perfil,
        datos=datos.model_dump(exclude_unset=True)
    )

    return {"mensaje": "Perfil actualizado correctamente."}


@router.delete(
    "/{id_perfil}",
    status_code=status.HTTP_200_OK
)
def eliminar_perfil(
    id_perfil: int,
    id_operador: int = Depends(obtener_id_operador),
    servicio: ServicioPerfiles = Depends(obtener_servicio_perfiles)
):
    """
     Ejecuta la baja lógica (Soft Delete: habilitado = 0) de un perfil.
    """
    servicio.dar_de_baja_perfil(
        id_operador=id_operador,
        id_destino=id_perfil
    )
    
    return {"mensaje": "Perfil dado de baja correctamente."}