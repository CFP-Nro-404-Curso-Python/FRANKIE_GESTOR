import sqlite3
from typing import List, Optional
from src.dominio.entidades import PerfilUsuario
from src.dominio.puertos import PuertoRepositorioPerfiles
from src.infraestructura.persistencia.utilidades_sql import obtener_o_crear

# =============================================================================
#  REPOSITORIO DE PERFILES SQL (CAPA 3 - INFRAESTRUCTURA)
# =============================================================================
#  DECISIÓN DE DISEÑO (PATRÓN REPOSITORIO Y 3FN):
#
#   Esta clase esconde la complejidad de las consultas SQL y las relaciones en 
#   Tercera Forma Normal (3FN). La Capa de Casos de Uso le envía un objeto 
#   'PerfilUsuario' limpio, y el repositorio se encarga de desarmarlo y 
#   distribuirlo en las tablas 'usuarios', 'roles' y 'usuxroles'.
# =============================================================================



class RepositorioPerfilesSQL(PuertoRepositorioPerfiles):
    
    def __init__(self, conexion: sqlite3.Connection):
        """
         Recibe la conexión a la base de datos inyectada por el GestorSQLite 
         (Unidad de Trabajo). No abre ni cierra conexiones por su cuenta.
        """
        self.conexion = conexion

    def guardar(self, perfil: PerfilUsuario) -> int:
        """
         Inserta un nuevo actor en el sistema ejecutando una transacción escalonada.
        """
        cursor = self.conexion.cursor()
        
        # 1. Insertar datos maestros en la tabla central (columna física: password).
        cursor.execute('''
            INSERT INTO usuarios (nombres, apellidos, dni, usuario, password, habilitado)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (perfil.nombres, perfil.apellidos, perfil.dni, perfil.usuario, perfil.password_hash))
        
        id_nuevo_usuario = cursor.lastrowid
        
        # 2. Resolver catálogo satélite (Roles) usando el helper DRY.
        id_rol = obtener_o_crear(cursor, "roles", "rol", perfil.rol)
        
        # 3. Vincular usuario y rol en la tabla puente (Muchos a Muchos).
        cursor.execute('''
            INSERT INTO usuxroles (id_usuario, id_rol)
            VALUES (?, ?)
        ''', (id_nuevo_usuario, id_rol))
        
        return id_nuevo_usuario

    def modificar(self, perfil: PerfilUsuario) -> None:
        """
         Actualiza los datos maestros y reasigna el rol si hubo cambios.
        """
        cursor = self.conexion.cursor()
        
        # 1. Actualizar datos en tabla central (columna física: password).
        cursor.execute('''
            UPDATE usuarios 
            SET nombres = ?, apellidos = ?, dni = ?, usuario = ?, password = ?
            WHERE id = ?
        ''', (perfil.nombres, perfil.apellidos, perfil.dni, perfil.usuario, perfil.password_hash, perfil.id))
        
        # 2. Actualizar tabla puente de roles.
        id_rol = obtener_o_crear(cursor, "roles", "rol", perfil.rol)
        
        # Borramos el rol viejo y ponemos el nuevo para evitar duplicidad de privilegios.
        cursor.execute("DELETE FROM usuxroles WHERE id_usuario = ?", (perfil.id,))
        cursor.execute("INSERT INTO usuxroles (id_usuario, id_rol) VALUES (?, ?)", (perfil.id, id_rol))

    def eliminar(self, id_perfil: int) -> None:
        """
         Aplica el Borrado Lógico (Soft Delete) cambiando el estado habilitado a 0.
         Gracias a esto preservamos el historial contable de auditoría.
        """
        cursor = self.conexion.cursor()
        cursor.execute("UPDATE usuarios SET habilitado = 0 WHERE id = ?", (id_perfil,))

    def obtener_por_usuario(self, usuario: str) -> Optional[PerfilUsuario]:
        """
         Busca un perfil usando el nombre de usuario (credencial de login).
         Retorna None si no existe o si fue dado de baja.
        """
        cursor = self.conexion.cursor()
        cursor.execute('''
            SELECT u.id, u.nombres, u.apellidos, u.dni, r.rol, u.usuario, u.password, u.habilitado
            FROM usuarios u
            LEFT JOIN usuxroles uxr ON u.id = uxr.id_usuario
            LEFT JOIN roles r ON uxr.id_rol = r.id
            WHERE u.usuario = ? AND u.habilitado = 1
        ''', (usuario,))
        
        fila = cursor.fetchone()
        return self._mapear_a_entidad(fila) if fila else None

    def obtener_por_id(self, id_perfil: int) -> Optional[PerfilUsuario]:
        """
         Recupera el objeto PerfilUsuario reconstruido a partir de su ID.
        """
        cursor = self.conexion.cursor()
        cursor.execute('''
            SELECT u.id, u.nombres, u.apellidos, u.dni, r.rol, u.usuario, u.password, u.habilitado
            FROM usuarios u
            LEFT JOIN usuxroles uxr ON u.id = uxr.id_usuario
            LEFT JOIN roles r ON uxr.id_rol = r.id
            WHERE u.id = ? AND u.habilitado = 1
        ''', (id_perfil,))
        
        fila = cursor.fetchone()
        return self._mapear_a_entidad(fila) if fila else None

    def listar_por_rol(self, rol: str) -> List[PerfilUsuario]:
        """
         Devuelve una lista de perfiles que coincidan con un rol específico 
         (ej. todos los Clientes, o todos los Empleados de Ventas).
        """
        cursor = self.conexion.cursor()
        cursor.execute('''
            SELECT u.id, u.nombres, u.apellidos, u.dni, r.rol, u.usuario, u.password, u.habilitado
            FROM usuarios u
            JOIN usuxroles uxr ON u.id = uxr.id_usuario
            JOIN roles r ON uxr.id_rol = r.id
            WHERE r.rol = ? AND u.habilitado = 1
        ''', (rol,))
        
        return [self._mapear_a_entidad(fila) for fila in cursor.fetchall()]

    # --------------------------------------------------------------------------------------
    # CAMBIO APLICADO:
    #  
    # Se implementó el método 'listar_todos' exigido por el puerto actualizado.
    # Obtiene todos los perfiles activos (habilitado = 1) resolviendo su rol mediante JOIN,
    # ideal para poblar la grilla general de la interfaz de usuario.
    # --------------------------------------------------------------------------------------
    def listar_todos(self) -> List[PerfilUsuario]:
        """
         Devuelve la lista completa de todos los perfiles activos en el sistema.
        """
        cursor = self.conexion.cursor()
        cursor.execute('''
            SELECT u.id, u.nombres, u.apellidos, u.dni, r.rol, u.usuario, u.password, u.habilitado
            FROM usuarios u
            LEFT JOIN usuxroles uxr ON u.id = uxr.id_usuario
            LEFT JOIN roles r ON uxr.id_rol = r.id
            WHERE u.habilitado = 1
        ''')
        
        return [self._mapear_a_entidad(fila) for fila in cursor.fetchall()]

    def obtener_rol_por_id(self, id_perfil: int) -> Optional[str]:
        """
         Método ultra-ligero utilizado por el inyector de dependencias (RBAC) 
         para consultar velozmente la jerarquía de un usuario sin armar todo el objeto.
        """
        cursor = self.conexion.cursor()
        cursor.execute('''
            SELECT r.rol 
            FROM usuxroles uxr
            JOIN roles r ON uxr.id_rol = r.id
            WHERE uxr.id_usuario = ?
        ''', (id_perfil,))
        
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None

    def _mapear_a_entidad(self, fila: tuple) -> PerfilUsuario:
        """
         Función privada auxiliar. Convierte la tupla cruda de SQLite en 
         una entidad pura de Dominio (PerfilUsuario).
        """
        return PerfilUsuario(
            id=fila[0],
            nombres=fila[1],
            apellidos=fila[2],
            dni=fila[3],
            rol=fila[4],
            usuario=fila[5],
            password_hash=fila[6],
            habilitado=fila[7]
        )