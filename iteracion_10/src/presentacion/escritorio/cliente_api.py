import requests
from typing import Dict, List, Any, Optional

# =============================================================================
#  CLIENTE HTTP CENTRALIZADO (CAPA 4 - PRESENTACIÓN ESCRITORIO)
# =============================================================================
#  DECISIÓN DE DISEÑO (DESACOPLAMIENTO TOTAL):
#
#   Las ventanas de Tkinter ya no tocan SQLite ni Bcrypt. Todas las pantallas 
#   usan este cliente para hablar con el servidor FastAPI mediante peticiones 
#   HTTP (GET, POST, PUT, DELETE), garantizando que Escritorio y Web usen 
#   exactamente las mismas reglas de negocio.
# =============================================================================



class ErrorClienteAPI(Exception):
    """
     Excepción personalizada para que las vistas de Tkinter puedan atrapar 
     cualquier error de red o de negocio y mostrarlo fácilmente en un messagebox.
    """
    pass


class ClienteAPI:
    """
     Encapsula todas las llamadas a la librería 'requests' hacia la API REST.
    """

    def __init__(self, url_base: str = "http://127.0.0.1:8000", id_operador: int = 1):

        # Dirección donde corre nuestro servidor local FastAPI.
        self.url_base = url_base.rstrip("/")

        # Guardamos el ID del usuario logueado para enviarlo en la cabecera RBAC.
        self.id_operador = id_operador
        self.datos_sesion: Optional[Dict[str, Any]] = None

    def _obtener_cabeceras(self, id_operador_override: Optional[int] = None) -> Dict[str, str]:
        """
         Arma las cabeceras HTTP necesarias. Inyecta 'X-Operador-Id' para que 
         el backend sepa qué usuario está haciendo la operación y valide su rol.
        """
        operador = id_operador_override if id_operador_override is not None else self.id_operador
        return {
            "Content-Type": "application/json",
            "X-Operador-Id": str(operador)
        }

    def _procesar_respuesta(self, respuesta: requests.Response) -> Any:
        """
         Revisa si la petición HTTP salió bien (códigos 200 o 201).
         Si hubo un error (400, 401, 403, 404, 422, 500), extrae el mensaje 
         claro que envió el backend y lanza ErrorClienteAPI.
        """
        if respuesta.status_code in (200, 201):
            return respuesta.json()

        # Intentamos leer el mensaje de error que envía FastAPI o el Dominio.
        try:
            datos_error = respuesta.json()

            # 'detalle' viene de nuestras excepciones de Dominio (servidor.py).
            # 'detail' viene de HTTPException o errores de validación de Pydantic.
            mensaje = datos_error.get("detalle") or datos_error.get("detail") or "Error desconocido en el servidor."
            if isinstance(mensaje, list):

                # Si Pydantic devuelve una lista de errores de formato (422), los unimos.
                mensaje = "; ".join([f"{err.get('loc', [''])[-1]}: {err.get('msg', '')}" for err in mensaje])
        except ValueError:
            mensaje = f"Error HTTP {respuesta.status_code}: {respuesta.text}"

        raise ErrorClienteAPI(str(mensaje))

    def verificar_servidor_activo(self) -> bool:
        """
         Comprueba rápidamente si el servidor FastAPI ya está escuchando peticiones.
        """
        try:
            respuesta = requests.get(f"{self.url_base}/docs", timeout=1.5)
            return respuesta.status_code == 200
        except requests.RequestException:
            return False


    # --------------------------------------------------------------------------
    #  1. MÉTODOS DE AUTENTICACIÓN Y PERFILES (USUARIOS, RRHH, CLIENTES, PROV.)
    # --------------------------------------------------------------------------

    def iniciar_sesion(self, usuario: str, password_plana: str) -> Dict[str, Any]:
        """
         Envía las credenciales a POST /api/perfiles/login.
         Si son válidas, guarda el ID del operador en sesión y devuelve sus datos.
        """
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


# Instancia global compartida para que todas las vistas de Tkinter puedan usarla directamente.
cliente_http = ClienteAPI()