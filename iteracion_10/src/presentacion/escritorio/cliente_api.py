import tkinter as tk
from tkinter import ttk
import requests
import customtkinter as ctk
from typing import Dict, List, Any, Optional, Callable

# =============================================================================
#  CLIENTE HTTP CENTRALIZADO Y GESTOR DE UI (CAPA 4 - PRESENTACIÓN ESCRITORIO)
# =============================================================================
#  DECISIÓN DE DISEÑO (DESACOPLAMIENTO TOTAL Y DRY EN ÁRBOL SELLADO):
#
#   1. ClienteAPI encapsula todas las peticiones HTTP (GET, POST, PUT, DELETE)
#      hacia FastAPI, manteniendo las vistas 100% libres de SQLite y Bcrypt.
#   2. GestorUI centraliza el Design System Slate/Blue (Modo Claro/Oscuro,
#      Alto Contraste WCAG, Escalado Tipográfico e i18n ES/EN) mediante el
#      Patrón Observador, evitando duplicación en las 10 vistas sin alterar
#      la estructura de carpetas sellada del proyecto.
# =============================================================================


class ErrorClienteAPI(Exception):
    """
     Excepción personalizada para que las vistas puedan atrapar cualquier error
     de red o de negocio y mostrarlo fácilmente en un messagebox.
    """
    pass


class ClienteAPI:
    """
     Encapsula todas las llamadas a la librería 'requests' hacia la API REST.
    """

    def __init__(self, url_base: str = "http://127.0.0.1:8000", id_operador: int = 1):
        self.url_base = url_base.rstrip("/")
        self.id_operador = id_operador
        self.datos_sesion: Optional[Dict[str, Any]] = None

    def _obtener_cabeceras(self, id_operador_override: Optional[int] = None) -> Dict[str, str]:
        """Arma las cabeceras HTTP e inyecta 'X-Operador-Id' para validación RBAC."""
        operador = id_operador_override if id_operador_override is not None else self.id_operador
        return {
            "Content-Type": "application/json",
            "X-Operador-Id": str(operador)
        }

    def _procesar_respuesta(self, respuesta: requests.Response) -> Any:
        """Valida códigos HTTP 200/201 y extrae mensajes limpios de error ante fallos."""
        if respuesta.status_code in (200, 201):
            return respuesta.json()

        try:
            datos_error = respuesta.json()
            mensaje = datos_error.get("detalle") or datos_error.get("detail") or "Error desconocido en el servidor."
            if isinstance(mensaje, list):
                mensaje = "; ".join([f"{err.get('loc', [''])[-1]}: {err.get('msg', '')}" for err in mensaje])
        except ValueError:
            mensaje = f"Error HTTP {respuesta.status_code}: {respuesta.text}"

        raise ErrorClienteAPI(str(mensaje))

    def verificar_servidor_activo(self) -> bool:
        """Comprueba si el servidor FastAPI ya está escuchando peticiones."""
        try:
            respuesta = requests.get(f"{self.url_base}/docs", timeout=1.5)
            return respuesta.status_code == 200
        except requests.RequestException:
            return False

    # --------------------------------------------------------------------------
    #  1. MÉTODOS DE AUTENTICACIÓN Y PERFILES (USUARIOS, RRHH, CLIENTES, PROV.)
    # --------------------------------------------------------------------------

    def iniciar_sesion(self, usuario: str, password_plana: str) -> Dict[str, Any]:
        """Envía las credenciales a POST /api/perfiles/login."""
        try:
            respuesta = requests.post(
                f"{self.url_base}/api/perfiles/login",
                json={"usuario": usuario, "password": password_plana},
                timeout=5
            )
            datos = self._procesar_respuesta(respuesta)
            self.id_operador = datos["id"]
            self.datos_sesion = datos
            return datos
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"No se pudo conectar con el servidor Backend: {e}")

    def listar_perfiles(self) -> List[Dict[str, Any]]:
        """Obtiene todos los perfiles activos del sistema (GET /api/perfiles)."""
        try:
            respuesta = requests.get(
                f"{self.url_base}/api/perfiles",
                headers=self._obtener_cabeceras(),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al listar perfiles: {e}")

    def listar_perfiles_por_rol(self, rol: str) -> List[Dict[str, Any]]:
        """Obtiene los perfiles activos filtrados por rol (GET /api/perfiles/rol/{rol})."""
        try:
            respuesta = requests.get(
                f"{self.url_base}/api/perfiles/rol/{rol}",
                headers=self._obtener_cabeceras(),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al filtrar perfiles por rol: {e}")

    def obtener_perfil(self, id_perfil: int) -> Dict[str, Any]:
        """Busca un perfil puntual por su ID (GET /api/perfiles/{id})."""
        try:
            respuesta = requests.get(
                f"{self.url_base}/api/perfiles/{id_perfil}",
                headers=self._obtener_cabeceras(),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al obtener el perfil: {e}")

    def crear_perfil(self, datos: Dict[str, Any], id_operador: Optional[int] = None) -> Dict[str, Any]:
        """Da de alta un nuevo perfil validando RBAC (POST /api/perfiles)."""
        try:
            respuesta = requests.post(
                f"{self.url_base}/api/perfiles",
                json=datos,
                headers=self._obtener_cabeceras(id_operador),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al crear perfil: {e}")

    def modificar_perfil(self, id_perfil: int, datos: Dict[str, Any], id_operador: Optional[int] = None) -> Dict[str, Any]:
        """Actualiza un perfil existente validando RBAC (PUT /api/perfiles/{id})."""
        try:
            respuesta = requests.put(
                f"{self.url_base}/api/perfiles/{id_perfil}",
                json=datos,
                headers=self._obtener_cabeceras(id_operador),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al modificar perfil: {e}")

    def eliminar_perfil(self, id_perfil: int, id_operador: Optional[int] = None) -> Dict[str, Any]:
        """Ejecuta la baja lógica de un perfil validando RBAC (DELETE /api/perfiles/{id})."""
        try:
            respuesta = requests.delete(
                f"{self.url_base}/api/perfiles/{id_perfil}",
                headers=self._obtener_cabeceras(id_operador),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al eliminar perfil: {e}")

    # --------------------------------------
    #  2. MÉTODOS DE INVENTARIO Y PRODUCTOS
    # --------------------------------------

    def listar_productos(self) -> List[Dict[str, Any]]:
        """Recupera todo el catálogo activo de productos (GET /api/productos)."""
        try:
            respuesta = requests.get(
                f"{self.url_base}/api/productos",
                headers=self._obtener_cabeceras(),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al listar productos: {e}")

    def obtener_producto(self, id_producto: int) -> Dict[str, Any]:
        """Recupera un producto puntual por su ID (GET /api/productos/{id})."""
        try:
            respuesta = requests.get(
                f"{self.url_base}/api/productos/{id_producto}",
                headers=self._obtener_cabeceras(),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al obtener producto: {e}")

    def crear_producto(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Registra un producto nuevo en el catálogo (POST /api/productos)."""
        try:
            respuesta = requests.post(
                f"{self.url_base}/api/productos",
                json=datos,
                headers=self._obtener_cabeceras(),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al crear producto: {e}")

    def modificar_producto(self, id_producto: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Modifica los datos comerciales de un producto (PUT /api/productos/{id})."""
        try:
            respuesta = requests.put(
                f"{self.url_base}/api/productos/{id_producto}",
                json=datos,
                headers=self._obtener_cabeceras(),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al modificar producto: {e}")

    def ingresar_stock(self, id_producto: int, cantidad: float) -> Dict[str, Any]:
        """Suma stock de manera atómica a un producto (POST /api/productos/{id}/stock)."""
        try:
            respuesta = requests.post(
                f"{self.url_base}/api/productos/{id_producto}/stock",
                json={"cantidad": cantidad},
                headers=self._obtener_cabeceras(),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al ingresar stock: {e}")

    def eliminar_producto(self, id_producto: int) -> Dict[str, Any]:
        """Realiza la baja lógica de un producto (DELETE /api/productos/{id})."""
        try:
            respuesta = requests.delete(
                f"{self.url_base}/api/productos/{id_producto}",
                headers=self._obtener_cabeceras(),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al eliminar producto: {e}")

    # ----------------------------------------------------------
    #  3. MÉTODOS DE OPERACIONES COMERCIALES (FACTURACIÓN Y BI)
    # ----------------------------------------------------------

    def listar_facturas(self) -> List[Dict[str, Any]]:
        """Obtiene el historial de facturas activas (GET /api/facturas)."""
        try:
            respuesta = requests.get(
                f"{self.url_base}/api/facturas",
                headers=self._obtener_cabeceras(),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al listar facturas: {e}")

    def emitir_factura(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Emite una factura y descuenta stock atómicamente (POST /api/facturas)."""
        try:
            respuesta = requests.post(
                f"{self.url_base}/api/facturas",
                json=datos,
                headers=self._obtener_cabeceras(),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al emitir factura: {e}")

    def anular_factura(self, id_factura: int) -> Dict[str, Any]:
        """Anula una factura emitida (DELETE /api/facturas/{id})."""
        try:
            respuesta = requests.delete(
                f"{self.url_base}/api/facturas/{id_factura}",
                headers=self._obtener_cabeceras(),
                timeout=5
            )
            return self._procesar_respuesta(respuesta)
        except requests.RequestException as e:
            raise ErrorClienteAPI(f"Error de red al anular factura: {e}")


# =============================================================================
#  GESTOR CENTRALIZADO DE TEMAS, I18N (ES/EN) Y ACCESIBILIDAD (WCAG)
# =============================================================================

_PALETAS = {
    ("light", False): {
        "bg_app": "#F1F5F9",
        "bg_card": "#FFFFFF",
        "bg_header": "#1E293B",
        "bg_input": "#FFFFFF",
        "bg_input_ro": "#F1F5F9",
        "fg_text": "#0F172A",
        "fg_label": "#334155",
        "fg_muted": "#64748B",
        "fg_header": "#FFFFFF",
        "fg_header_sub": "#CBD5E1",
        "border": "#CBD5E1",
        "border_width": 1,
        "focus_border": "#2563EB",
        "tree_bg": "#FFFFFF",
        "tree_alt": "#F8FAFC",
        "tree_fg": "#0F172A",
        "tree_head_bg": "#E2E8F0",
        "tree_head_fg": "#1E293B",
        "tree_sel_bg": "#DBEAFE",
        "tree_sel_fg": "#0F172A",
        "stock_warn_bg": "#FEF3C7",
        "stock_warn_fg": "#92400E",
        "stock_crit_bg": "#FEE2E2",
        "stock_crit_fg": "#991B1B",
        "btn_dis_bg": "#E2E8F0",
        "btn_dis_fg": "#94A3B8",
        "chip_bg": "#E2E8F0",
        "chip_hover": "#CBD5E1",
        "chip_fg": "#1E293B",
        "consola_bg": "#0F172A",
        "consola_fg": "#E2E8F0",
        "canvas_bg": "#FFFFFF",
        "canvas_grid": "#E2E8F0",
        "canvas_axis": "#CBD5E1",
        "canvas_text": "#334155",
        "canvas_muted": "#64748B",
    },
    ("dark", False): {
        "bg_app": "#0F172A",
        "bg_card": "#1E293B",
        "bg_header": "#020617",
        "bg_input": "#0F172A",
        "bg_input_ro": "#334155",
        "fg_text": "#F8FAFC",
        "fg_label": "#E2E8F0",
        "fg_muted": "#94A3B8",
        "fg_header": "#F8FAFC",
        "fg_header_sub": "#94A3B8",
        "border": "#334155",
        "border_width": 1,
        "focus_border": "#38BDF8",
        "tree_bg": "#1E293B",
        "tree_alt": "#162033",
        "tree_fg": "#F8FAFC",
        "tree_head_bg": "#0F172A",
        "tree_head_fg": "#E2E8F0",
        "tree_sel_bg": "#1D4ED8",
        "tree_sel_fg": "#FFFFFF",
        "stock_warn_bg": "#451A03",
        "stock_warn_fg": "#FDE68A",
        "stock_crit_bg": "#450A0A",
        "stock_crit_fg": "#FECACA",
        "btn_dis_bg": "#334155",
        "btn_dis_fg": "#64748B",
        "chip_bg": "#334155",
        "chip_hover": "#475569",
        "chip_fg": "#F8FAFC",
        "consola_bg": "#020617",
        "consola_fg": "#E2E8F0",
        "canvas_bg": "#1E293B",
        "canvas_grid": "#334155",
        "canvas_axis": "#475569",
        "canvas_text": "#E2E8F0",
        "canvas_muted": "#94A3B8",
    },
    ("light", True): {
        "bg_app": "#FFFFFF",
        "bg_card": "#FFFFFF",
        "bg_header": "#000000",
        "bg_input": "#FFFFFF",
        "bg_input_ro": "#E5E7EB",
        "fg_text": "#000000",
        "fg_label": "#000000",
        "fg_muted": "#1F2937",
        "fg_header": "#FFFFFF",
        "fg_header_sub": "#FACC15",
        "border": "#000000",
        "border_width": 2,
        "focus_border": "#1D4ED8",
        "tree_bg": "#FFFFFF",
        "tree_alt": "#F3F4F6",
        "tree_fg": "#000000",
        "tree_head_bg": "#000000",
        "tree_head_fg": "#FFFFFF",
        "tree_sel_bg": "#1D4ED8",
        "tree_sel_fg": "#FFFFFF",
        "stock_warn_bg": "#FEF08A",
        "stock_warn_fg": "#000000",
        "stock_crit_bg": "#FCA5A5",
        "stock_crit_fg": "#000000",
        "btn_dis_bg": "#D1D5DB",
        "btn_dis_fg": "#374151",
        "chip_bg": "#E5E7EB",
        "chip_hover": "#D1D5DB",
        "chip_fg": "#000000",
        "consola_bg": "#000000",
        "consola_fg": "#FFFFFF",
        "canvas_bg": "#FFFFFF",
        "canvas_grid": "#9CA3AF",
        "canvas_axis": "#000000",
        "canvas_text": "#000000",
        "canvas_muted": "#111827",
    },
    ("dark", True): {
        "bg_app": "#000000",
        "bg_card": "#0A0A0A",
        "bg_header": "#000000",
        "bg_input": "#000000",
        "bg_input_ro": "#1F2937",
        "fg_text": "#FFFFFF",
        "fg_label": "#FFFFFF",
        "fg_muted": "#FDE047",
        "fg_header": "#FFFFFF",
        "fg_header_sub": "#FACC15",
        "border": "#FACC15",
        "border_width": 2,
        "focus_border": "#38BDF8",
        "tree_bg": "#000000",
        "tree_alt": "#111827",
        "tree_fg": "#FFFFFF",
        "tree_head_bg": "#1F2937",
        "tree_head_fg": "#FACC15",
        "tree_sel_bg": "#FACC15",
        "tree_sel_fg": "#000000",
        "stock_warn_bg": "#713F12",
        "stock_warn_fg": "#FFFFFF",
        "stock_crit_bg": "#7F1D1D",
        "stock_crit_fg": "#FFFFFF",
        "btn_dis_bg": "#1F2937",
        "btn_dis_fg": "#9CA3AF",
        "chip_bg": "#1F2937",
        "chip_hover": "#374151",
        "chip_fg": "#FACC15",
        "consola_bg": "#000000",
        "consola_fg": "#FACC15",
        "canvas_bg": "#000000",
        "canvas_grid": "#4B5563",
        "canvas_axis": "#FACC15",
        "canvas_text": "#FFFFFF",
        "canvas_muted": "#FDE047",
    },
}

_ROLES_A_EN = {
    "Administrador": "Administrator",
    "Gerente": "Manager",
    "Empleado - Ventas": "Sales Employee",
    "Empleado - Compras": "Purchasing Employee",
    "Proveedor": "Supplier",
    "Cliente": "Customer",
}

_ROLES_A_CANONICO = {v: k for k, v in _ROLES_A_EN.items()}
for _r in _ROLES_A_EN:
    _ROLES_A_CANONICO[_r] = _r

_TRADUCCIONES = {
    "es": {
        # Comunes y preferencias
        "app_titulo": "FRANKIE GESTOR",
        "app_subtitulo": "Sistema de Gestión Comercial",
        "btn_cerrar": "Cerrar",
        "btn_actualizar": "Actualizar",
        "btn_limpiar": "Limpiar",
        "btn_guardar": "Guardar",
        "btn_modificar": "Modificar",
        "btn_eliminar": "Eliminar",
        "buscar_ph": "Buscar en la tabla (Ctrl+F)...",
        "contador_filas": "Mostrando {visibles} de {total} registros",
        "sin_dato": "S/D",
        "sin_cred": "[Sin Credenciales]",
        "sel_rol": "Seleccione un rol...",
        "btn_tema_oscuro": "Oscuro",
        "btn_tema_claro": "Claro",
        "btn_hc": "HC",
        "btn_idioma": "EN",
        "atajos_hint": "Atajos: F5 Actualizar | Ctrl+F Buscar | Esc Cerrar",

        # Alertas comunes
        "val_tit": "Validación",
        "err_com_tit": "Error de Comunicación",
        "err_tx_tit": "Error de Transacción",
        "err_act_tit": "Error al Actualizar",
        "err_gua_tit": "Error al Guardar",
        "err_acc_tit": "Acceso Denegado",
        "err_acc_err_tit": "Acceso Denegado / Error",
        "err_bloq_tit": "Operación Bloqueada",
        "err_fmt_tit": "Error de Formato",
        "err_sel_tit": "Selección Requerida",

        # Login
        "login_win": "FRANKIE GESTOR - Acceso al Sistema",
        "login_usu": "Usuario",
        "login_usu_ph": "Ej: admin",
        "login_pass": "Contraseña",
        "login_btn": "Ingresar al Sistema",
        "login_intentos": "Intentos disponibles: {n}",
        "login_bloqueado": "Acceso bloqueado por seguridad.",
        "login_completar": "Completá todos los campos.",
        "login_ok_tit": "Acceso Concedido",
        "login_ok_msg": "Bienvenido/a, {nombre} {apellido}.\nRol: {rol}",
        "login_err_tit": "Error de Autenticación",
        "login_err_msg": "Credenciales incorrectas o usuario inhabilitado. Intentos restantes: {n}",
        "login_bloq_tit": "Bloqueo de Seguridad",
        "login_bloq_msg": "Superaste el límite de intentos fallidos. El sistema se cerrará.",

        # Panel de Control
        "panel_win": "FRANKIE GESTOR - Panel de Control",
        "panel_op": "Operador: {nombre} {apellido}  |  Rol: {rol}",
        "panel_bienv": "BIENVENIDO/A, {nombre} {apellido}",
        "panel_sub": "Panel Operativo — Permisos habilitados para: {rol}",
        "panel_clientes": "Gestión de Clientes",
        "panel_facturacion": "Facturación",
        "panel_proveedores": "Gestión de Proveedores",
        "panel_stock": "Control de Stock",
        "panel_empleados": "Recursos Humanos (RRHH)",
        "panel_usuarios": "Gestión de Usuarios (IAM)",
        "panel_consola": "Consola SQL (Auditoría)",
        "panel_backup": "Generar Backup JSON",
        "panel_analitica": "Analítica de Ventas (Tablero BI / OLAP)",
        "panel_salir": "Cerrar Sesión",
        "bkp_ok_tit": "Backup Exitoso",
        "bkp_ok_msg": "Copia de seguridad guardada correctamente en:\n{ruta}",
        "bkp_err_tit": "Error de Backup",
        "bkp_err_msg": "No se pudo generar el respaldo:\n{err}",

        # Usuarios (IAM)
        "usu_win": "GESTIÓN DE USUARIOS",
        "usu_header": "GESTIÓN DE USUARIOS Y CREDENCIALES (IAM)",
        "usu_nombres": "Nombres *",
        "usu_nombres_ph": "Nombre del usuario",
        "usu_apellidos": "Apellidos *",
        "usu_apellidos_ph": "Apellido del usuario",
        "usu_login": "Usuario (Login) *",
        "usu_login_ph": "Cuenta de acceso",
        "usu_pass": "Contraseña",
        "usu_pass_ph": "Vacío al editar para conservar",
        "usu_rol": "Rol Asignado *",
        "usu_ayuda": "Seleccioná una fila para editar credenciales o cambiar el rol asignado.",
        "usu_todos_req": "Todos los campos son obligatorios en este módulo.",
        "usu_priv_err": "Privilegios insuficientes para crear perfiles de esta jerarquía.",
        "usu_sel_req": "Seleccioná primero un usuario de la tabla.",
        "usu_mod_req": "Nombres, Apellidos, Usuario y Rol son obligatorios.",
        "col_usuario": "Usuario",
        "col_rol_sis": "Rol del Sistema",
        "col_nombres": "Nombres",
        "col_apellidos": "Apellidos",

        # Empleados (RRHH)
        "emp_win": "FORMULARIO EMPLEADOS (RRHH)",
        "emp_header": "RECURSOS HUMANOS — LEGAJOS DE EMPLEADOS",
        "emp_dni": "DNI",
        "emp_tel": "Teléfono",
        "emp_email": "Email",
        "emp_dir": "Dirección",
        "emp_ciudad": "Ciudad",
        "emp_prov": "Provincia",
        "emp_cp": "Cód. Postal",
        "emp_rol": "Rol Organizacional *",
        "emp_btn_guardar": "Guardar Perfil",
        "emp_btn_modificar": "Modificar Perfil",
        "emp_btn_eliminar": "Eliminar Perfil",
        "emp_req": "Nombres, Apellidos y Rol Organizacional son obligatorios.",
        "emp_priv_err": "Privilegios insuficientes para crear perfiles de esta jerarquía organizativa.",
        "emp_sel_req": "Seleccioná primero un empleado de la nómina.",
        "col_dni": "DNI",
        "col_tel": "Teléfono",
        "col_email": "Email",
        "col_dir": "Dirección",
        "col_ciudad": "Ciudad",
        "col_prov": "Provincia",
        "col_cp": "CP",
        "col_rol": "Rol",

        # Clientes
        "cli_win": "FORMULARIO CLIENTES",
        "cli_header": "GESTIÓN DE CLIENTES",
        "cli_cp": "Código Postal",
        "cli_btn_guardar": "Guardar Cliente",
        "cli_btn_modificar": "Modificar Cliente",
        "cli_btn_eliminar": "Eliminar Cliente",
        "cli_req": "Nombres y Apellidos son obligatorios.",
        "cli_sel_req": "Seleccioná primero un cliente de la tabla.",

        # Proveedores
        "prov_win": "FORMULARIO PROVEEDORES",
        "prov_header": "GESTIÓN DE PROVEEDORES",
        "prov_razon": "Razón Social *",
        "prov_cuit": "CUIT",
        "prov_contacto": "Contacto (Rep.)",
        "prov_btn_guardar": "Guardar Proveedor",
        "prov_btn_modificar": "Modificar Proveedor",
        "prov_btn_eliminar": "Eliminar Proveedor",
        "prov_req": "La Razón Social es obligatoria.",
        "prov_sel_req": "Seleccioná primero un proveedor de la tabla.",
        "col_razon": "Razón Social",
        "col_cuit": "CUIT",
        "col_contacto": "Contacto",

        # Stock
        "stk_win": "FORMULARIO STOCK E INVENTARIO",
        "stk_header": "CONTROL DE STOCK E INVENTARIO",
        "stk_codigo": "Código *",
        "stk_desc": "Descripción *",
        "stk_cat": "Categoría",
        "stk_prov": "Proveedor *",
        "stk_ubic": "Ubicación",
        "stk_act": "Stock Actual",
        "stk_min": "Stock Mínimo",
        "stk_costo": "Precio Costo ($)",
        "stk_venta": "Precio Venta ($)",
        "stk_venc": "Vencimiento",
        "stk_sel_prov": "Seleccione proveedor...",
        "stk_sin_prov": "Sin proveedores",
        "stk_btn_guardar": "Guardar Producto",
        "stk_btn_modificar": "Modificar Producto",
        "stk_btn_eliminar": "Eliminar Producto",
        "stk_req": "Código, Descripción y Proveedor son campos obligatorios.",
        "stk_prov_inv": "El proveedor seleccionado no es válido o fue dado de baja.",
        "stk_nums_err": "Asegúrese de ingresar valores numéricos válidos en precios y stock.",
        "stk_sel_req": "Seleccioná primero un producto de la tabla.",
        "stk_semaforo": "Referencias: Amarillo = Stock Bajo (<= Mínimo)  |  Rojo = Agotado (0)",
        "col_codigo": "Código",
        "col_desc": "Descripción",
        "col_cat": "Categoría",
        "col_prov_col": "Proveedor",
        "col_stk_act": "Stock Actual",
        "col_stk_min": "Stock Mínimo",
        "col_costo": "Precio Costo",
        "col_venta": "Precio Venta",
        "col_ubic": "Ubicación",
        "col_venc": "Vencimiento",

        # Facturación
        "fac_win": "FORMULARIO FACTURACIÓN",
        "fac_header": "FACTURACIÓN Y OPERACIONES COMERCIALES",
        "fac_vendedor": "Datos del Vendedor *",
        "fac_cliente": "Datos del Cliente *",
        "fac_producto": "Producto *",
        "fac_cantidad": "Cantidad *",
        "fac_valor": "Valor Unitario ($)",
        "fac_desc_item": "Descuento por Ítem (%)",
        "fac_sel_vend": "Seleccione vendedor...",
        "fac_sel_cli": "Seleccione cliente...",
        "fac_sel_prod": "Seleccione producto...",
        "fac_sin_vend": "Sin vendedores",
        "fac_sin_cli": "Sin clientes",
        "fac_sin_prod": "Sin productos",
        "fac_btn_guardar": "Guardar Facturación",
        "fac_btn_modificar": "Modificar Facturación",
        "fac_btn_eliminar": "Eliminar Facturación",
        "fac_total": "TOTAL FACTURA: $ {monto}",
        "fac_total_desc": "Total con descuento ({pct}%): $ {monto}",
        "fac_desc_global": "Descuento Global (%):",
        "fac_btn_calc": "Calcular Descuento Final",
        "fac_req": "Vendedor, Cliente y Producto son obligatorios.",
        "fac_nums_err": "Ingresá valores numéricos válidos en Cantidad y Descuento.",
        "fac_rango_err": "La cantidad debe ser > 0 y el descuento debe estar entre 0 y 100%.",
        "fac_asoc_err": "Seleccioná un vendedor, cliente y producto válidos.",
        "fac_sel_req": "Seleccioná primero una factura de la tabla.",
        "fac_rep_tit": "Alerta de Reposición",
        "fac_rep_msg": "El producto llegó a su stock mínimo. Quedan {u} unidades.",
        "fac_desc_num": "Ingresá un porcentaje numérico válido.",
        "fac_desc_rango": "El descuento global debe estar entre 0 y 100%.",
        "col_prod": "Producto",
        "col_cant": "Cantidad",
        "col_valor": "Valor en $",
        "col_desc_pct": "Descuento en %",
        "col_total": "Total en $",

        # Consola SQL
        "sql_win": "CONSOLA SQL - AUDITORÍA (SOLO LECTURA)",
        "sql_header": "CONSOLA SQL — AUDITORÍA EN SANDBOX (SOLO LECTURA)",
        "sql_rapidas": "Consultas rápidas:",
        "sql_btn_ejec": "Ejecutar Consulta",
        "sql_btn_limp": "Limpiar Consola",
        "sql_est_esp": "Estado: Esperando consulta...",
        "sql_est_rbac": "Estado: Bloqueado por falta de privilegios RBAC.",
        "sql_est_sbx": "Estado: Query bloqueada por Sandboxing.",
        "sql_est_ok": "Estado: Ejecución exitosa. Filas recuperadas: {n}",
        "sql_solo_admin": "Solo un Administrador activo puede ejecutar auditorías SQL.",
        "sql_bloq_tit": "Bloqueo de Seguridad",
        "sql_bloq_msg": "Transacción abortada. Operación destructiva detectada.\nEsta consola es de Solo Lectura (SELECT).",
        "sql_solo_sel": "Error SQL: Solo se admiten sentencias que comiencen con SELECT.",

        # Analítica BI
        "bi_win": "ANALÍTICA DE VENTAS - TABLERO BI / OLAP",
        "bi_header": "TABLERO DE CONTROL — ANALÍTICA BI / OLAP",
        "bi_sub_ini": "Análisis estadístico en tiempo real",
        "bi_sub_vacio": "Sin ventas registradas para analizar",
        "bi_sub_top": "Más Vendido: {prod}  |  Categoría Top: {cat}",
        "bi_btn_act": "Actualizar Análisis",
        "bi_kpi_fac": "FACTURACIÓN TOTAL",
        "bi_kpi_ops": "OPERACIONES",
        "bi_kpi_uni": "UNIDADES VENDIDAS",
        "bi_kpi_tkt": "TICKET PROMEDIO",
        "bi_graf_top10": "Top 10 Productos (Facturación)",
        "bi_graf_mensual": "Evolución Mensual",
        "bi_graf_cat": "Facturación por Categoría",
        "bi_sin_datos": "Sin datos",
        "col_id_venta": "ID Venta",
        "col_precio_cong": "Precio Congelado",
        "col_fecha": "Fecha",
        "col_total_cob": "Total Cobrado",
    },
    "en": {
        # Common & preferences
        "app_titulo": "FRANKIE GESTOR",
        "app_subtitulo": "Commercial Management System",
        "btn_cerrar": "Close",
        "btn_actualizar": "Refresh",
        "btn_limpiar": "Clear",
        "btn_guardar": "Save",
        "btn_modificar": "Update",
        "btn_eliminar": "Delete",
        "buscar_ph": "Filter table (Ctrl+F)...",
        "contador_filas": "Showing {visibles} of {total} records",
        "sin_dato": "N/A",
        "sin_cred": "[No Credentials]",
        "sel_rol": "Select a role...",
        "btn_tema_oscuro": "Dark",
        "btn_tema_claro": "Light",
        "btn_hc": "HC",
        "btn_idioma": "ES",
        "atajos_hint": "Shortcuts: F5 Refresh | Ctrl+F Search | Esc Close",

        # Common alerts
        "val_tit": "Validation",
        "err_com_tit": "Communication Error",
        "err_tx_tit": "Transaction Error",
        "err_act_tit": "Update Error",
        "err_gua_tit": "Save Error",
        "err_acc_tit": "Access Denied",
        "err_acc_err_tit": "Access Denied / Error",
        "err_bloq_tit": "Operation Blocked",
        "err_fmt_tit": "Format Error",
        "err_sel_tit": "Selection Required",

        # Login
        "login_win": "FRANKIE GESTOR - System Sign In",
        "login_usu": "Username",
        "login_usu_ph": "e.g. admin",
        "login_pass": "Password",
        "login_btn": "Sign In",
        "login_intentos": "Remaining attempts: {n}",
        "login_bloqueado": "Access locked for security.",
        "login_completar": "Please fill in all fields.",
        "login_ok_tit": "Access Granted",
        "login_ok_msg": "Welcome, {nombre} {apellido}.\nRole: {rol}",
        "login_err_tit": "Authentication Error",
        "login_err_msg": "Invalid credentials or disabled account. Remaining attempts: {n}",
        "login_bloq_tit": "Security Lockout",
        "login_bloq_msg": "Maximum failed attempts exceeded. The application will close.",

        # Dashboard
        "panel_win": "FRANKIE GESTOR - Control Panel",
        "panel_op": "Operator: {nombre} {apellido}  |  Role: {rol}",
        "panel_bienv": "WELCOME, {nombre} {apellido}",
        "panel_sub": "Operations Dashboard — Enabled permissions for: {rol}",
        "panel_clientes": "Customer Management",
        "panel_facturacion": "Invoicing",
        "panel_proveedores": "Supplier Management",
        "panel_stock": "Inventory Control",
        "panel_empleados": "Human Resources (HR)",
        "panel_usuarios": "User Management (IAM)",
        "panel_consola": "SQL Console (Audit)",
        "panel_backup": "Generate JSON Backup",
        "panel_analitica": "Sales Analytics (BI / OLAP Dashboard)",
        "panel_salir": "Sign Out",
        "bkp_ok_tit": "Backup Successful",
        "bkp_ok_msg": "Backup file saved successfully at:\n{ruta}",
        "bkp_err_tit": "Backup Error",
        "bkp_err_msg": "Could not generate backup:\n{err}",

        # Users (IAM)
        "usu_win": "USER MANAGEMENT",
        "usu_header": "USER & CREDENTIALS MANAGEMENT (IAM)",
        "usu_nombres": "First Name *",
        "usu_nombres_ph": "User first name",
        "usu_apellidos": "Last Name *",
        "usu_apellidos_ph": "User last name",
        "usu_login": "Username (Login) *",
        "usu_login_ph": "Account username",
        "usu_pass": "Password",
        "usu_pass_ph": "Leave empty on edit to keep",
        "usu_rol": "Assigned Role *",
        "usu_ayuda": "Select a row to edit credentials or update the assigned role.",
        "usu_todos_req": "All fields are required in this module.",
        "usu_priv_err": "Insufficient privileges to create profiles at this hierarchy level.",
        "usu_sel_req": "Please select a user from the table first.",
        "usu_mod_req": "First Name, Last Name, Username and Role are required.",
        "col_usuario": "Username",
        "col_rol_sis": "System Role",
        "col_nombres": "First Name",
        "col_apellidos": "Last Name",

        # Employees (HR)
        "emp_win": "EMPLOYEES FORM (HR)",
        "emp_header": "HUMAN RESOURCES — EMPLOYEE RECORDS",
        "emp_dni": "ID / DNI",
        "emp_tel": "Phone",
        "emp_email": "Email",
        "emp_dir": "Address",
        "emp_ciudad": "City",
        "emp_prov": "State / Province",
        "emp_cp": "Postal Code",
        "emp_rol": "Organizational Role *",
        "emp_btn_guardar": "Save Profile",
        "emp_btn_modificar": "Update Profile",
        "emp_btn_eliminar": "Delete Profile",
        "emp_req": "First Name, Last Name and Organizational Role are required.",
        "emp_priv_err": "Insufficient privileges to create profiles at this hierarchy level.",
        "emp_sel_req": "Please select an employee from the table first.",
        "col_dni": "DNI",
        "col_tel": "Phone",
        "col_email": "Email",
        "col_dir": "Address",
        "col_ciudad": "City",
        "col_prov": "Province",
        "col_cp": "ZIP",
        "col_rol": "Role",

        # Customers
        "cli_win": "CUSTOMERS FORM",
        "cli_header": "CUSTOMER MANAGEMENT",
        "cli_cp": "Postal Code",
        "cli_btn_guardar": "Save Customer",
        "cli_btn_modificar": "Update Customer",
        "cli_btn_eliminar": "Delete Customer",
        "cli_req": "First Name and Last Name are required.",
        "cli_sel_req": "Please select a customer from the table first.",

        # Suppliers
        "prov_win": "SUPPLIERS FORM",
        "prov_header": "SUPPLIER MANAGEMENT",
        "prov_razon": "Company Name *",
        "prov_cuit": "Tax ID (CUIT)",
        "prov_contacto": "Contact Rep.",
        "prov_btn_guardar": "Save Supplier",
        "prov_btn_modificar": "Update Supplier",
        "prov_btn_eliminar": "Delete Supplier",
        "prov_req": "Company Name is required.",
        "prov_sel_req": "Please select a supplier from the table first.",
        "col_razon": "Company Name",
        "col_cuit": "CUIT",
        "col_contacto": "Contact",

        # Stock
        "stk_win": "INVENTORY & STOCK FORM",
        "stk_header": "INVENTORY & STOCK CONTROL",
        "stk_codigo": "SKU / Code *",
        "stk_desc": "Description *",
        "stk_cat": "Category",
        "stk_prov": "Supplier *",
        "stk_ubic": "Location",
        "stk_act": "Current Stock",
        "stk_min": "Minimum Stock",
        "stk_costo": "Cost Price ($)",
        "stk_venta": "Sale Price ($)",
        "stk_venc": "Expiration",
        "stk_sel_prov": "Select supplier...",
        "stk_sin_prov": "No suppliers",
        "stk_btn_guardar": "Save Product",
        "stk_btn_modificar": "Update Product",
        "stk_btn_eliminar": "Delete Product",
        "stk_req": "Code, Description and Supplier are required.",
        "stk_prov_inv": "Selected supplier is invalid or inactive.",
        "stk_nums_err": "Please enter valid numeric values for prices and stock.",
        "stk_sel_req": "Please select a product from the table first.",
        "stk_semaforo": "Legend: Amber = Low Stock (<= Min)  |  Red = Out of Stock (0)",
        "col_codigo": "Code",
        "col_desc": "Description",
        "col_cat": "Category",
        "col_prov_col": "Supplier",
        "col_stk_act": "Stock",
        "col_stk_min": "Min Stock",
        "col_costo": "Cost Price",
        "col_venta": "Sale Price",
        "col_ubic": "Location",
        "col_venc": "Expiration",

        # Invoicing
        "fac_win": "INVOICING FORM",
        "fac_header": "INVOICING & COMMERCIAL OPERATIONS",
        "fac_vendedor": "Salesperson *",
        "fac_cliente": "Customer *",
        "fac_producto": "Product *",
        "fac_cantidad": "Quantity *",
        "fac_valor": "Unit Price ($)",
        "fac_desc_item": "Item Discount (%)",
        "fac_sel_vend": "Select salesperson...",
        "fac_sel_cli": "Select customer...",
        "fac_sel_prod": "Select product...",
        "fac_sin_vend": "No salespeople",
        "fac_sin_cli": "No customers",
        "fac_sin_prod": "No products",
        "fac_btn_guardar": "Save Invoice",
        "fac_btn_modificar": "Update Invoice",
        "fac_btn_eliminar": "Delete Invoice",
        "fac_total": "INVOICE TOTAL: $ {monto}",
        "fac_total_desc": "Total with discount ({pct}%): $ {monto}",
        "fac_desc_global": "Global Discount (%):",
        "fac_btn_calc": "Calculate Final Total",
        "fac_req": "Salesperson, Customer and Product are required.",
        "fac_nums_err": "Enter valid numeric values for Quantity and Discount.",
        "fac_rango_err": "Quantity must be > 0 and Discount between 0 and 100%.",
        "fac_asoc_err": "Please select a valid salesperson, customer and product.",
        "fac_sel_req": "Please select an invoice from the table first.",
        "fac_rep_tit": "Restock Alert",
        "fac_rep_msg": "Product reached minimum stock level. {u} units remaining.",
        "fac_desc_num": "Please enter a valid numeric percentage.",
        "fac_desc_rango": "Global discount must be between 0 and 100%.",
        "col_prod": "Product",
        "col_cant": "Qty",
        "col_valor": "Unit Price $",
        "col_desc_pct": "Discount %",
        "col_total": "Total $",

        # SQL Console
        "sql_win": "SQL CONSOLE - AUDIT (READ-ONLY)",
        "sql_header": "SQL CONSOLE — SANDBOX AUDIT (READ-ONLY)",
        "sql_rapidas": "Quick queries:",
        "sql_btn_ejec": "Run Query",
        "sql_btn_limp": "Clear Console",
        "sql_est_esp": "Status: Waiting for query...",
        "sql_est_rbac": "Status: Blocked due to insufficient RBAC privileges.",
        "sql_est_sbx": "Status: Query blocked by Sandbox policy.",
        "sql_est_ok": "Status: Query executed successfully. Rows returned: {n}",
        "sql_solo_admin": "Only an active Administrator can run SQL audit queries.",
        "sql_bloq_tit": "Security Block",
        "sql_bloq_msg": "Transaction aborted. Destructive operation detected.\nThis console is Read-Only (SELECT).",
        "sql_solo_sel": "SQL Error: Only SELECT statements are allowed.",

        # BI Analytics
        "bi_win": "SALES ANALYTICS - BI / OLAP DASHBOARD",
        "bi_header": "CONTROL DASHBOARD — BI / OLAP ANALYTICS",
        "bi_sub_ini": "Real-time statistical analysis",
        "bi_sub_vacio": "No sales records available for analysis",
        "bi_sub_top": "Top Seller: {prod}  |  Top Category: {cat}",
        "bi_btn_act": "Refresh Analytics",
        "bi_kpi_fac": "TOTAL REVENUE",
        "bi_kpi_ops": "TRANSACTIONS",
        "bi_kpi_uni": "UNITS SOLD",
        "bi_kpi_tkt": "AVERAGE TICKET",
        "bi_graf_top10": "Top 10 Products (Revenue)",
        "bi_graf_mensual": "Monthly Trend",
        "bi_graf_cat": "Revenue by Category",
        "bi_sin_datos": "No data",
        "col_id_venta": "Sale ID",
        "col_precio_cong": "Frozen Price",
        "col_fecha": "Date",
        "col_total_cob": "Total Charged",
    },
}


class GestorUI:
    """
     Controlador reactivo de presentación (Patrón Observador).
     Sincroniza Modo Claro/Oscuro, Alto Contraste WCAG, Escalado Tipográfico
     e Internacionalización (ES/EN) entre todas las ventanas abiertas.
    """

    ESCALAS_DISPONIBLES = (1.0, 1.15, 1.25)

    def __init__(self):
        self.tema: str = "light"
        self.alto_contraste: bool = False
        self.idioma: str = "es"
        self.escala: float = 1.0
        self._observadores: List[Callable[[], None]] = []

    def paleta(self) -> Dict[str, Any]:
        return _PALETAS[(self.tema, self.alto_contraste)]

    def tam(self, base: int) -> int:
        return max(8, int(round(base * self.escala)))

    def fuente(self, base: int = 12, weight: str = "normal", slant: str = "roman", family: str = "Segoe UI") -> ctk.CTkFont:
        return ctk.CTkFont(family=family, size=self.tam(base), weight=weight, slant=slant)

    def t(self, clave: str, **kwargs) -> str:
        dic = _TRADUCCIONES.get(self.idioma, _TRADUCCIONES["es"])
        texto = dic.get(clave, _TRADUCCIONES["es"].get(clave, clave))
        if kwargs:
            try:
                return texto.format(**kwargs)
            except KeyError:
                return texto
        return texto

    def rol_a_ui(self, rol_canonico: Optional[str]) -> str:
        """Traduce un rol canónico del Backend a su etiqueta visual según idioma."""
        if not rol_canonico:
            return self.t("sin_dato")
        if self.idioma == "en":
            return _ROLES_A_EN.get(rol_canonico, rol_canonico)
        return rol_canonico

    def rol_a_canonico(self, valor_ui: str) -> str:
        """Convierte cualquier etiqueta de rol (ES/EN) al valor canónico exigido por la API."""
        limpio = (valor_ui or "").strip()
        if limpio in ("", _TRADUCCIONES["es"]["sel_rol"], _TRADUCCIONES["en"]["sel_rol"]):
            return ""
        return _ROLES_A_CANONICO.get(limpio, limpio)

    def es_sin_dato(self, valor: Optional[str]) -> bool:
        return (valor or "").strip() in ("", "S/D", "N/A")

    def suscribir(self, ventana: tk.Misc, callback: Callable[[], None]) -> None:
        """Registra una vista para actualizarse en vivo y limpia la suscripción al cerrarse."""
        if callback not in self._observadores:
            self._observadores.append(callback)

        def _al_cerrar(event):
            if event.widget is ventana and callback in self._observadores:
                self._observadores.remove(callback)

        ventana.bind("<Destroy>", _al_cerrar, add="+")

    def _notificar(self) -> None:
        vivos = []
        for cb in list(self._observadores):
            try:
                cb()
                vivos.append(cb)
            except tk.TclError:
                continue
        self._observadores = vivos

    def alternar_tema(self) -> None:
        self.tema = "dark" if self.tema == "light" else "light"
        ctk.set_appearance_mode(self.tema)
        self._notificar()

    def alternar_idioma(self) -> None:
        self.idioma = "en" if self.idioma == "es" else "es"
        self._notificar()

    def alternar_alto_contraste(self) -> None:
        self.alto_contraste = not self.alto_contraste
        self._notificar()

    def ajustar_escala(self, delta: int) -> None:
        idx = self.ESCALAS_DISPONIBLES.index(self.escala)
        nuevo_idx = max(0, min(len(self.ESCALAS_DISPONIBLES) - 1, idx + delta))
        if nuevo_idx != idx:
            self.escala = self.ESCALAS_DISPONIBLES[nuevo_idx]
            self._notificar()

    def resetear_por_defecto(self) -> None:
        """Restaura el estado inicial (Claro, ES, 100%, Contraste estándar)."""
        self.tema = "light"
        self.alto_contraste = False
        self.idioma = "es"
        self.escala = 1.0
        ctk.set_appearance_mode("light")
        self._notificar()

    def aplicar_estilo_treeview(self, ventana: tk.Misc) -> None:
        """Actualiza el tema ttk.Treeview para que acompañe el modo oscuro y el zoom."""
        p = self.paleta()
        estilo = ttk.Style(ventana)
        estilo.theme_use("clam")
        estilo.configure(
            "Frankie.Treeview",
            background=p["tree_bg"],
            foreground=p["tree_fg"],
            fieldbackground=p["tree_bg"],
            rowheight=int(28 * self.escala),
            font=("Segoe UI", self.tam(10)),
            borderwidth=0
        )
        estilo.configure(
            "Frankie.Treeview.Heading",
            background=p["tree_head_bg"],
            foreground=p["tree_head_fg"],
            font=("Segoe UI", self.tam(10), "bold"),
            relief="flat",
            padding=(8, 6)
        )
        estilo.map(
            "Frankie.Treeview",
            background=[("selected", p["tree_sel_bg"])],
            foreground=[("selected", p["tree_sel_fg"])]
        )

    def aplicar_tags_tabla(self, tabla: ttk.Treeview) -> None:
        """Configura zebra striping y semáforo de stock en cualquier Treeview."""
        p = self.paleta()
        tabla.tag_configure("par", background=p["tree_bg"], foreground=p["tree_fg"])
        tabla.tag_configure("impar", background=p["tree_alt"], foreground=p["tree_fg"])
        tabla.tag_configure("stock_bajo", background=p["stock_warn_bg"], foreground=p["stock_warn_fg"])
        tabla.tag_configure("stock_agotado", background=p["stock_crit_bg"], foreground=p["stock_crit_fg"])

    def estilizar_entry(self, entry: ctk.CTkEntry, readonly: bool = False) -> None:
        """Aplica tokens de tema y anillo de foco accesible a un CTkEntry."""
        p = self.paleta()
        entry.configure(
            fg_color=p["bg_input_ro"] if readonly else p["bg_input"],
            text_color=p["fg_muted"] if readonly else p["fg_text"],
            border_color=p["border"],
            border_width=p["border_width"],
            placeholder_text_color=p["fg_muted"],
            font=self.fuente(12)
        )
        if not getattr(entry, "_frankie_foco_bind", False):
            entry.bind("<FocusIn>", lambda e, w=entry: w.configure(border_color=self.paleta()["focus_border"], border_width=2), add="+")
            entry.bind("<FocusOut>", lambda e, w=entry: w.configure(border_color=self.paleta()["border"], border_width=self.paleta()["border_width"]), add="+")
            entry._frankie_foco_bind = True

    def estilizar_combo(self, combo: ctk.CTkComboBox) -> None:
        """Aplica tokens de tema y contraste a un CTkComboBox."""
        p = self.paleta()
        combo.configure(
            fg_color=p["bg_input"],
            text_color=p["fg_text"],
            border_color=p["border"],
            border_width=p["border_width"],
            dropdown_fg_color=p["bg_card"],
            dropdown_text_color=p["fg_text"],
            dropdown_hover_color=p["tree_sel_bg"],
            button_color="#334155" if self.tema == "dark" else "#94A3B8",
            button_hover_color="#475569" if self.tema == "dark" else "#64748B",
            font=self.fuente(12),
            dropdown_font=self.fuente(11)
        )

    def crear_barra_preferencias(self, padre: ctk.CTkFrame) -> Dict[str, ctk.CTkButton]:
        """
         Construye controles compactos de Tema, Idioma (ES/EN), Zoom (A-/A+)
         y Alto Contraste (HC) usando únicamente CTkButton para no alterar el
         orden de CTkEntry/CTkComboBox en la suite E2E.
        """
        barra = ctk.CTkFrame(padre, fg_color="transparent")
        barra.pack(side="right", padx=(0, 8))

        btn_idioma = ctk.CTkButton(
            barra, text=self.t("btn_idioma"), command=self.alternar_idioma,
            width=40, height=28, corner_radius=6,
            fg_color="#334155", hover_color="#475569", text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        btn_idioma.pack(side="left", padx=2)

        btn_tema = ctk.CTkButton(
            barra,
            text=self.t("btn_tema_oscuro") if self.tema == "light" else self.t("btn_tema_claro"),
            command=self.alternar_tema,
            width=64, height=28, corner_radius=6,
            fg_color="#334155", hover_color="#475569", text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        btn_tema.pack(side="left", padx=2)

        btn_zoom_menos = ctk.CTkButton(
            barra, text="A-", command=lambda: self.ajustar_escala(-1),
            width=32, height=28, corner_radius=6,
            fg_color="#334155", hover_color="#475569", text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        btn_zoom_menos.pack(side="left", padx=2)

        btn_zoom_mas = ctk.CTkButton(
            barra, text="A+", command=lambda: self.ajustar_escala(1),
            width=32, height=28, corner_radius=6,
            fg_color="#334155", hover_color="#475569", text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        btn_zoom_mas.pack(side="left", padx=2)

        btn_hc = ctk.CTkButton(
            barra, text="HC", command=self.alternar_alto_contraste,
            width=36, height=28, corner_radius=6,
            fg_color="#FACC15" if self.alto_contraste else "#334155",
            hover_color="#EAB308" if self.alto_contraste else "#475569",
            text_color="#000000" if self.alto_contraste else "#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        btn_hc.pack(side="left", padx=2)

        return {
            "idioma": btn_idioma,
            "tema": btn_tema,
            "zoom_menos": btn_zoom_menos,
            "zoom_mas": btn_zoom_mas,
            "hc": btn_hc,
        }

    def actualizar_barra_preferencias(self, botones: Dict[str, ctk.CTkButton]) -> None:
        """Sincroniza el texto y resaltado de la barra de preferencias."""
        botones["idioma"].configure(text=self.t("btn_idioma"))
        botones["tema"].configure(
            text=self.t("btn_tema_oscuro") if self.tema == "light" else self.t("btn_tema_claro")
        )
        botones["hc"].configure(
            fg_color="#FACC15" if self.alto_contraste else "#334155",
            hover_color="#EAB308" if self.alto_contraste else "#475569",
            text_color="#000000" if self.alto_contraste else "#FFFFFF",
        )


# Instancias globales compartidas para todas las vistas de Escritorio.
cliente_http = ClienteAPI()
gestor_ui = GestorUI()