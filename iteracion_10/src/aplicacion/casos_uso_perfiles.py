from src.dominio.entidades import PerfilUsuario
from src.dominio.excepciones import ErrorCredencialesInvalidas, ErrorEntidadNoEncontrada
from src.dominio.politicas_rbac import obtener_estrategia_rbac
from src.dominio.puertos import PuertoUnidadDeTrabajo, PuertoHashing



# ================================================================================
#  CASOS DE USO: GESTIÓN DE PERFILES Y AUTENTICACIÓN (CAPA 2 - APLICACIÓN)
# ================================================================================
#  DECISIÓN DE DISEÑO (ORQUESTACIÓN Y DIP):
#
#   Esta capa no toma decisiones de negocio ni ejecuta SQL. Su único trabajo es 
#   coordinar: busca la política de seguridad (RBAC), encripta la clave usando el 
#   puerto de hashing, y le dice a la Unidad de Trabajo que guarde los cambios.
# ================================================================================

class ServicioPerfiles:
    """
     Servicio de aplicación que orquesta todas las operaciones de usuarios, 
     empleados, clientes y proveedores.
    """

    def __init__(self, uow: PuertoUnidadDeTrabajo, hasher: PuertoHashing):
        """
         Inyección de Dependencias. El servicio exige un UoW y un Hasher, 
         pero no sabe (ni le importa) si son SQLite, PostgreSQL o Bcrypt.
        """
        self.uow = uow
        self.hasher = hasher

    def autenticar_usuario(self, usuario: str, password_plana: str) -> PerfilUsuario:
        """
         Caso de Uso: Login.
         Busca al usuario y verifica criptográficamente su contraseña.
        """
        with self.uow:
            perfil = self.uow.perfiles.obtener_por_usuario(usuario)
            
            # Si el perfil no existe, o existe pero no tiene password (ej. es Cliente).
            if not perfil or not perfil.password_hash:
                raise ErrorCredencialesInvalidas("Usuario inexistente o credenciales inválidas.")
                
            # Delega la verificación matemática al puerto de seguridad.
            if not self.hasher.verificar_password(password_plana, perfil.password_hash):
                raise ErrorCredencialesInvalidas("Usuario inexistente o credenciales inválidas.")
                
            return perfil

    def registrar_perfil(self, id_operador: int, datos: dict) -> int:
        """
         Caso de Uso: Alta de un nuevo actor (Usuario, Empleado, Cliente, Proveedor).
         Aplica RBAC antes de hacer cualquier mutación e incluye su legajo 3FN.
        """
        with self.uow:
            # 1. Identificar quién hace la operación y qué permisos tiene.
            rol_operador = self.uow.perfiles.obtener_rol_por_id(id_operador)
            estrategia_rbac = obtener_estrategia_rbac(rol_operador)
            
            # 2. Validar si el operador tiene jerarquía para crear el rol destino.
            rol_destino = datos.get("rol")
            estrategia_rbac.validar_creacion(rol_destino)
            
            # 3. Preparar credenciales si corresponde (clientes/proveedores no usan).
            password_hash = None
            if datos.get("password_plana"):
                password_hash = self.hasher.hashear_password(datos["password_plana"])
                
            # 4. Construir la entidad pura incluyendo datos de contacto y ubicación.
            nuevo_perfil = PerfilUsuario(
                nombres=datos["nombres"],
                apellidos=datos["apellidos"],
                dni=datos.get("dni") or "S/D",
                rol=rol_destino,
                usuario=datos.get("usuario"),
                password_hash=password_hash,
                telefono=datos.get("telefono") or "S/D",
                email=datos.get("email") or "S/D",
                direccion=datos.get("direccion") or "S/D",
                ciudad=datos.get("ciudad") or "S/D",
                provincia=datos.get("provincia") or "S/D",
                cp=datos.get("cp") or "S/D"
            )
            
            # 5. Persistir usando la Unidad de Trabajo (ACID).
            return self.uow.perfiles.guardar(nuevo_perfil)

    def modificar_perfil(self, id_operador: int, id_destino: int, datos: dict) -> None:
        """
         Caso de Uso: Modificación de actor. 
         Revisa permisos, actualiza campos maestros/contacto y, opcionalmente, re-hashea la clave.
         Permite actualizaciones parciales (desde Usuarios o desde RRHH) sin pisar datos ajenos.
        """
        with self.uow:
            rol_operador = self.uow.perfiles.obtener_rol_por_id(id_operador)
            perfil_destino = self.uow.perfiles.obtener_por_id(id_destino)
            
            if not perfil_destino:
                raise ErrorEntidadNoEncontrada("El perfil que intentás modificar no existe.")

            estrategia_rbac = obtener_estrategia_rbac(rol_operador)
            
            # Validamos que pueda modificar el rol actual de la entidad.
            estrategia_rbac.validar_modificacion(perfil_destino.rol, id_destino, id_operador)
            # También validamos que tenga permisos si intenta cambiarle el rol a uno superior.
            if datos.get("rol") and datos.get("rol") != perfil_destino.rol:
                estrategia_rbac.validar_creacion(datos["rol"])

            # Actualizamos el objeto en memoria conservando los valores previos si no se enviaron.
            perfil_destino.nombres = datos.get("nombres", perfil_destino.nombres)
            perfil_destino.apellidos = datos.get("apellidos", perfil_destino.apellidos)
            perfil_destino.dni = datos.get("dni", perfil_destino.dni)
            perfil_destino.rol = datos.get("rol", perfil_destino.rol)
            perfil_destino.usuario = datos.get("usuario", perfil_destino.usuario)
            perfil_destino.telefono = datos.get("telefono", perfil_destino.telefono)
            perfil_destino.email = datos.get("email", perfil_destino.email)
            perfil_destino.direccion = datos.get("direccion", perfil_destino.direccion)
            perfil_destino.ciudad = datos.get("ciudad", perfil_destino.ciudad)
            perfil_destino.provincia = datos.get("provincia", perfil_destino.provincia)
            perfil_destino.cp = datos.get("cp", perfil_destino.cp)
            
            # Si mandaron clave nueva, calculamos el nuevo hash.
            if datos.get("password_plana"):
                perfil_destino.password_hash = self.hasher.hashear_password(datos["password_plana"])

            self.uow.perfiles.modificar(perfil_destino)

    def dar_de_baja_perfil(self, id_operador: int, id_destino: int) -> None:
        """
         Caso de Uso: Baja lógica de un actor.
        """
        with self.uow:
            rol_operador = self.uow.perfiles.obtener_rol_por_id(id_operador)
            perfil_destino = self.uow.perfiles.obtener_por_id(id_destino)
            
            if not perfil_destino:
                raise ErrorEntidadNoEncontrada("El perfil que intentás eliminar no existe.")
                
            estrategia_rbac = obtener_estrategia_rbac(rol_operador)
            
            # Validar que la jerarquía permita el borrado (y evitar auto-baja de gerentes).
            estrategia_rbac.validar_baja(perfil_destino.rol, id_destino, id_operador)
            
            # Ejecutar borrado lógico.
            self.uow.perfiles.eliminar(id_destino)

    def listar_perfiles(self) -> list[PerfilUsuario]:
        """
         Caso de Uso: Obtener el catálogo completo de perfiles activos en el sistema
         sin filtrar por rol. Necesario para poblar las grillas principales.
        """
        with self.uow:
            return self.uow.perfiles.listar_todos()