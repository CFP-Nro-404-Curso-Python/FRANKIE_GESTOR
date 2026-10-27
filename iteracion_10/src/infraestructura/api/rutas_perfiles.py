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
#  
#   No toma decisiones de negocio ni ejecuta consultas SQL: delega toda la 
#   orquestación al 'ServicioPerfiles' inyectado por FastAPI.
# ================================================================================



router = APIRouter(
    prefix="/api/perfiles",
    tags=["Perfiles y Autenticación"]
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
     Si las credenciales fallan, corta el flujo con un error HTTP 401.
    """
    
    # -----------------------------------------------------------------------------------------
    # CAMBIO APLICADO:
    #  
    #  Se modificó el llamado a 'servicio.autenticar' (que no existía en la Capa 2) 
    #  por el método correcto 'servicio.autenticar_usuario' como define casos_uso_perfiles.py.
    # -----------------------------------------------------------------------------------------

    perfil = servicio.autenticar_usuario(
        usuario=credenciales.usuario,
        password_plana=credenciales.password
    )
    
    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas o usuario inactivo."
        )
        
    return EsquemaPerfilRespuesta(
        id=perfil.id,
        nombres=perfil.nombres,
        apellidos=perfil.apellidos,
        dni=perfil.dni,
        rol=perfil.rol,
        usuario=perfil.usuario,
        habilitado=perfil.habilitado
    )


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
     Extrae el 'X-Operador-Id' de la cabecera HTTP para que la capa de aplicación 
     evalúe si el operador tiene jerarquía suficiente (RBAC) para crear este rol.
    """
    
    # -----------------------------------------------------------------------------------------
    # CAMBIO APLICADO:
    #  
    #  El método 'registrar_perfil' de la Capa 2 NO espera recibir una entidad 'PerfilUsuario' 
    #  armada ni parámetros separados ('nuevo_perfil' y 'password_plana').
    #  
    #  Espera recibir el ID del operador y un diccionario crudo ('datos: dict') 
    #  para armar la entidad por su cuenta. Convertimos el DTO a dict usando '.model_dump()'.
    # -----------------------------------------------------------------------------------------

    id_generado = servicio.registrar_perfil(
        id_operador=id_operador,
        datos=datos.model_dump()
    )
    
    return {
        "id": id_generado,
        "mensaje": "Perfil registrado correctamente."
    }


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
     Devuelve la nómina de perfiles activos filtrados por su rol comercial 
     (ej. 'Cliente', 'Proveedor', 'Gerente').
    """
    # Se actualiza el nombre del método para coincidir con la Capa 2 (asumiendo que era necesario).
    perfiles = servicio.uow.perfiles.listar_por_rol(rol)
    
    return [
        EsquemaPerfilRespuesta(
            id=p.id,
            nombres=p.nombres,
            apellidos=p.apellidos,
            dni=p.dni,
            rol=p.rol,
            usuario=p.usuario,
            habilitado=p.habilitado
        )
        for p in perfiles
    ]


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
     Si no existe o fue dado de baja lógica, retorna HTTP 404.
    """
    # Se actualiza el nombre del método para coincidir con la Capa 2 (asumiendo que era necesario).
    perfil = servicio.uow.perfiles.obtener_por_id(id_perfil)
    
    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró un perfil activo con ID {id_perfil}."
        )
        
    return EsquemaPerfilRespuesta(
        id=perfil.id,
        nombres=perfil.nombres,
        apellidos=perfil.apellidos,
        dni=perfil.dni,
        rol=perfil.rol,
        usuario=perfil.usuario,
        habilitado=perfil.habilitado
    )


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
     Actualiza los datos maestros o credenciales de un perfil existente.
     Valida previamente mediante RBAC si el operador tiene rango para editar al objetivo.
    """


    # --------------------------------------------------------------------------------------------
    # CAMBIO APLICADO:
    #  
    #  El método 'modificar_perfil' de la Capa 2 NO espera recibir una entidad 'PerfilUsuario' 
    #  pre-armada ni un parámetro 'perfil_modificado'.
    #  
    #  Espera recibir (id_operador, id_destino, datos: dict) para buscar la entidad, validar RBAC
    #  y aplicar las modificaciones internamente. Convertimos el DTO a dict excluyendo los nulos.
    # --------------------------------------------------------------------------------------------

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
     Pasa por el filtro RBAC para impedir que un usuario de menor rango 
     elimine a un superior o que un operador se dé de baja a sí mismo.
    """
    
    # --------------------------------------------------------------------------
    # CAMBIO APLICADO:
    #  
    #  Se modificó el llamado para usar el método correcto 'dar_de_baja_perfil'
    #  en lugar de 'eliminar_perfil', tal como define casos_uso_perfiles.py.
    # --------------------------------------------------------------------------
    
    servicio.dar_de_baja_perfil(
        id_operador=id_operador,
        id_destino=id_perfil
    )
    
    return {"mensaje": "Perfil dado de baja correctamente."}