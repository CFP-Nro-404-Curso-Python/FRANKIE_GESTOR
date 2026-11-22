import sqlite3
from typing import List, Optional
from src.dominio.entidades import PerfilUsuario
from src.dominio.puertos import PuertoRepositorioPerfiles
from src.infraestructura.persistencia.utilidades_sql import obtener_o_crear



# =============================================================================
#  REPOSITORIO DE PERFILES SQL (CAPA 3 - INFRAESTRUCTURA)
# =============================================================================
#  DECISIÓN DE DISEÑO (PATRÓN REPOSITORIO Y 3FN COMPLETA):
#
#   Esta clase esconde la complejidad de las consultas SQL y las relaciones en 
#   Tercera Forma Normal (3FN). La Capa de Casos de Uso le envía un objeto 
#   'PerfilUsuario' limpio, y el repositorio se encarga de desarmarlo y 
#   distribuirlo en 'usuarios', 'roles', 'usuxroles' y los árboles satélites
#   de contacto y ubicación geográfica.
# =============================================================================

class RepositorioPerfilesSQL(PuertoRepositorioPerfiles):
    
    # Consulta base unificada que reconstruye el perfil con sus tablas puente 3FN activas.
    _SELECT_PERFIL_3FN = '''
        SELECT u.id, u.nombres, u.apellidos, u.dni, r.rol, u.usuario, u.password, u.habilitado,
               COALESCE(t.telefono, 'S/D') AS telefono,
               COALESCE(m.mail, 'S/D') AS email,
               COALESCE(d.direccion, 'S/D') AS direccion,
               COALESCE(c.ciudad, 'S/D') AS ciudad,
               COALESCE(p.provincia, 'S/D') AS provincia,
               COALESCE(cp.cp, 'S/D') AS cp
        FROM usuarios u
        LEFT JOIN usuxroles uxr ON u.id = uxr.id_usuario AND uxr.habilitado = 1
        LEFT JOIN roles r ON uxr.id_rol = r.id
        LEFT JOIN usuarioxcontactos uc ON u.id = uc.id_usuario AND uc.habilitado = 1
        LEFT JOIN contactoxtelefonos ct ON uc.id = ct.id_contacto AND ct.habilitado = 1
        LEFT JOIN telefonos t ON ct.id_telefono = t.id
        LEFT JOIN contactoxmails cm ON uc.id = cm.id_contacto AND cm.habilitado = 1
        LEFT JOIN mails m ON cm.id_mail = m.id
        LEFT JOIN usuarioxubicaciones uu ON u.id = uu.id_usuario AND uu.habilitado = 1
        LEFT JOIN ubicacionxdireccion ud ON uu.id = ud.id_ubicacion AND ud.habilitado = 1
        LEFT JOIN direcciones d ON ud.id_direccion = d.id
        LEFT JOIN ubicacionxlocalidades ul ON uu.id = ul.id_ubicacion AND ul.habilitado = 1
        LEFT JOIN localidadxciudades lc ON ul.id = lc.id_localidad AND lc.habilitado = 1
        LEFT JOIN ciudades c ON lc.id_ciudad = c.id
        LEFT JOIN codigopostales cp ON lc.id_cp = cp.id
        LEFT JOIN localidadxprovincias lp ON ul.id = lp.id_localidad AND lp.habilitado = 1
        LEFT JOIN provincias p ON lp.id_provincia = p.id
    '''

    # Mapa de traducción entre las mayúsculas físicas de SQLite y los nombres de rol del Dominio/UI.
    _MAPA_ROLES = {
        "ADMINISTRADOR": "Administrador",
        "GERENTE": "Gerente",
        "EMPLEADO - VENTAS": "Empleado - Ventas",
        "EMPLEADO - COMPRAS": "Empleado - Compras",
        "EMPLEADO": "Empleado - Ventas",
        "PROVEEDOR": "Proveedor",
        "CLIENTE": "Cliente",
    }

    def __init__(self, conexion: sqlite3.Connection):
        """
         Recibe la conexión a la base de datos inyectada por el GestorSQLite 
         (Unidad de Trabajo). No abre ni cierra conexiones por su cuenta.
        """
        self.conexion = conexion

    def _obtener_o_crear_literal(self, cursor: sqlite3.Cursor, tabla: str, columna: str, valor: str) -> int:
        """
         Resuelve catálogos de contacto y domicilio preservando mayúsculas/minúsculas 
         originales (ej. emails en minúscula o nombres de calles/ciudades).
        """
        valor_limpio = str(valor).strip() if valor and str(valor).strip() else "S/D"
        cursor.execute(f"SELECT id FROM {tabla} WHERE {columna} = ?", (valor_limpio,))
        fila = cursor.fetchone()
        if fila:
            return fila[0]
        cursor.execute(f"INSERT INTO {tabla} ({columna}, habilitado) VALUES (?, 1)", (valor_limpio,))
        return cursor.lastrowid

    def _sincronizar_contacto_y_ubicacion(self, cursor: sqlite3.Cursor, id_usuario: int, perfil: PerfilUsuario) -> None:
        """
         Desactiva los vínculos puente anteriores (Soft Delete) e inserta los 
         nodos actualizados del árbol de contacto y ubicación en 3FN.
        """
        # 1. Desactivar árboles intermedios previos para evitar duplicación en los LEFT JOIN.
        cursor.execute("UPDATE usuarioxcontactos SET habilitado = 0 WHERE id_usuario = ?", (id_usuario,))
        cursor.execute("UPDATE usuarioxubicaciones SET habilitado = 0 WHERE id_usuario = ?", (id_usuario,))

        # 2. Árbol de Contactos (Teléfono y Email).
        cursor.execute("INSERT INTO usuarioxcontactos (id_usuario, habilitado) VALUES (?, 1)", (id_usuario,))
        id_contacto = cursor.lastrowid

        id_telefono = self._obtener_o_crear_literal(cursor, "telefonos", "telefono", perfil.telefono)
        cursor.execute(
            "INSERT INTO contactoxtelefonos (id_contacto, id_telefono, habilitado) VALUES (?, ?, 1)",
            (id_contacto, id_telefono)
        )

        id_mail = self._obtener_o_crear_literal(cursor, "mails", "mail", perfil.email)
        cursor.execute(
            "INSERT INTO contactoxmails (id_contacto, id_mail, habilitado) VALUES (?, ?, 1)",
            (id_contacto, id_mail)
        )

        # 3. Árbol Geográfico (Dirección, Ciudad, Código Postal, Provincia y País).
        cursor.execute("INSERT INTO usuarioxubicaciones (id_usuario, habilitado) VALUES (?, 1)", (id_usuario,))
        id_ubicacion = cursor.lastrowid

        id_direccion = self._obtener_o_crear_literal(cursor, "direcciones", "direccion", perfil.direccion)
        cursor.execute(
            "INSERT INTO ubicacionxdireccion (id_ubicacion, id_direccion, habilitado) VALUES (?, ?, 1)",
            (id_ubicacion, id_direccion)
        )

        cursor.execute("INSERT INTO ubicacionxlocalidades (id_ubicacion, habilitado) VALUES (?, 1)", (id_ubicacion,))
        id_localidad = cursor.lastrowid

        id_ciudad = self._obtener_o_crear_literal(cursor, "ciudades", "ciudad", perfil.ciudad)
        id_cp = self._obtener_o_crear_literal(cursor, "codigopostales", "cp", perfil.cp)
        cursor.execute(
            "INSERT INTO localidadxciudades (id_localidad, id_ciudad, id_cp, habilitado) VALUES (?, ?, ?, 1)",
            (id_localidad, id_ciudad, id_cp)
        )

        id_provincia = self._obtener_o_crear_literal(cursor, "provincias", "provincia", perfil.provincia)
        cursor.execute(
            "INSERT INTO localidadxprovincias (id_localidad, id_provincia, habilitado) VALUES (?, ?, 1)",
            (id_localidad, id_provincia)
        )

        id_pais = self._obtener_o_crear_literal(cursor, "paises", "pais", "Argentina")
        cursor.execute(
            "INSERT INTO localidadxpaises (id_localidad, id_pais, habilitado) VALUES (?, ?, 1)",
            (id_localidad, id_pais)
        )

    def guardar(self, perfil: PerfilUsuario) -> int:
        """
         Inserta un nuevo actor en el sistema ejecutando una transacción escalonada 3FN.
        """
        cursor = self.conexion.cursor()
        
        # 1. Insertar datos maestros en la tabla central (columna física: password).
        cursor.execute('''
            INSERT INTO usuarios (nombres, apellidos, dni, usuario, password, habilitado)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (perfil.nombres, perfil.apellidos, perfil.dni, perfil.usuario, perfil.password_hash))
        
        id_nuevo_usuario = cursor.lastrowid
        
        # 2. Resolver catálogo satélite (Roles) usando el helper DRY en mayúsculas.
        id_rol = obtener_o_crear(cursor, "roles", "rol", perfil.rol)
        
        # 3. Vincular usuario y rol en la tabla puente.
        cursor.execute('''
            INSERT INTO usuxroles (id_usuario, id_rol, habilitado)
            VALUES (?, ?, 1)
        ''', (id_nuevo_usuario, id_rol))

        # 4. Persistir árboles de contacto y ubicación en 3FN.
        self._sincronizar_contacto_y_ubicacion(cursor, id_nuevo_usuario, perfil)
        
        return id_nuevo_usuario

    def modificar(self, perfil: PerfilUsuario) -> None:
        """
         Actualiza los datos maestros, reasigna el rol y sincroniza contactos y domicilio en 3FN.
        """
        cursor = self.conexion.cursor()
        
        # 1. Actualizar datos en tabla central.
        cursor.execute('''
            UPDATE usuarios 
            SET nombres = ?, apellidos = ?, dni = ?, usuario = ?, password = ?
            WHERE id = ?
        ''', (perfil.nombres, perfil.apellidos, perfil.dni, perfil.usuario, perfil.password_hash, perfil.id))
        
        # 2. Actualizar tabla puente de roles.
        id_rol = obtener_o_crear(cursor, "roles", "rol", perfil.rol)
        cursor.execute("DELETE FROM usuxroles WHERE id_usuario = ?", (perfil.id,))
        cursor.execute("INSERT INTO usuxroles (id_usuario, id_rol, habilitado) VALUES (?, ?, 1)", (perfil.id, id_rol))

        # 3. Sincronizar árboles de contacto y ubicación en 3FN.
        self._sincronizar_contacto_y_ubicacion(cursor, perfil.id, perfil)

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
        cursor.execute(
            f"{self._SELECT_PERFIL_3FN} WHERE u.usuario = ? AND u.habilitado = 1 GROUP BY u.id",
            (usuario,)
        )
        fila = cursor.fetchone()
        return self._mapear_a_entidad(fila) if fila else None

    def obtener_por_id(self, id_perfil: int) -> Optional[PerfilUsuario]:
        """
         Recupera el objeto PerfilUsuario reconstruido con su legajo 3FN a partir de su ID.
        """
        cursor = self.conexion.cursor()
        cursor.execute(
            f"{self._SELECT_PERFIL_3FN} WHERE u.id = ? AND u.habilitado = 1 GROUP BY u.id",
            (id_perfil,)
        )
        fila = cursor.fetchone()
        return self._mapear_a_entidad(fila) if fila else None

    def _normalizar_rol(self, rol_db: Optional[str]) -> Optional[str]:
        """Convierte el rol almacenado en mayúsculas en SQLite al formato esperado por el Dominio y la UI."""
        if not rol_db:
            return None
        return self._MAPA_ROLES.get(str(rol_db).strip().upper(), rol_db)

    def listar_por_rol(self, rol: str) -> List[PerfilUsuario]:
        """
         Devuelve una lista de perfiles que coincidan con un rol específico 
         (ej. todos los Clientes, o todos los Empleados de Ventas).
        """
        cursor = self.conexion.cursor()
        cursor.execute(f'''
            {self._SELECT_PERFIL_3FN}
            WHERE (UPPER(r.rol) = UPPER(?) OR (UPPER(?) = 'EMPLEADO - VENTAS' AND UPPER(r.rol) = 'EMPLEADO'))
              AND u.habilitado = 1
            GROUP BY u.id
        ''', (rol, rol))
        
        return [self._mapear_a_entidad(fila) for fila in cursor.fetchall()]

    def listar_todos(self) -> List[PerfilUsuario]:
        """
         Devuelve la lista completa de todos los perfiles activos en el sistema con su legajo 3FN.
        """
        cursor = self.conexion.cursor()
        cursor.execute(f"{self._SELECT_PERFIL_3FN} WHERE u.habilitado = 1 GROUP BY u.id")
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
            WHERE uxr.id_usuario = ? AND uxr.habilitado = 1
        ''', (id_perfil,))
        
        resultado = cursor.fetchone()
        return self._normalizar_rol(resultado[0]) if resultado else None

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
            rol=self._normalizar_rol(fila[4]),
            usuario=fila[5],
            password_hash=fila[6],
            habilitado=fila[7],
            telefono=fila[8] if len(fila) > 8 and fila[8] else "S/D",
            email=fila[9] if len(fila) > 9 and fila[9] else "S/D",
            direccion=fila[10] if len(fila) > 10 and fila[10] else "S/D",
            ciudad=fila[11] if len(fila) > 11 and fila[11] else "S/D",
            provincia=fila[12] if len(fila) > 12 and fila[12] else "S/D",
            cp=fila[13] if len(fila) > 13 and fila[13] else "S/D"
        )