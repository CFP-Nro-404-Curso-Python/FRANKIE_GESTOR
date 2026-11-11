import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import pytest
import requests
import bcrypt
from fastapi.testclient import TestClient



# ==============================================================================
#  SUITE DE INTEGRACIÓN: CLIENTE WEB SPA Y SINCRONIZACIÓN CON ESCRITORIO
# ==============================================================================
#  UBICACIÓN: tests/integracion/test_sincronizacion_web_escritorio.py
#
#  DECISIÓN DE DISEÑO:
#   Verifica que la interfaz Web (HTML5/CSS3/JS) cumpla con los requisitos de
#   diseño responsive móvil, conectividad LAN dinámica, cabeceras CORS y que
#   cualquier operación realizada desde la Web se refleje inmediatamente en las
#   ventanas de Tkinter (y viceversa) al compartir el mismo Backend FastAPI.
# ==============================================================================

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_TESTS = os.path.dirname(DIRECTORIO_ACTUAL)
DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_TESTS)
DIRECTORIO_ESCRITORIO = os.path.join(DIRECTORIO_RAIZ, "src", "presentacion", "escritorio")
DIRECTORIO_VISTAS = os.path.join(DIRECTORIO_ESCRITORIO, "vistas")
DIRECTORIO_WEB = os.path.join(DIRECTORIO_RAIZ, "src", "presentacion", "web")

for ruta in (DIRECTORIO_RAIZ, DIRECTORIO_ESCRITORIO, DIRECTORIO_VISTAS):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

from src.infraestructura.api.servidor import app
from src.infraestructura.api.inyector_dependencias import obtener_uow
from src.infraestructura.persistencia.gestor_sqlite import GestorSQLite
from src.presentacion.escritorio.cliente_api import cliente_http

import src.presentacion.escritorio.vistas.clientes as mod_clientes
import src.presentacion.escritorio.vistas.proveedores as mod_proveedores
import src.presentacion.escritorio.vistas.stock as mod_stock
import src.presentacion.escritorio.vistas.facturacion as mod_facturacion
import src.presentacion.escritorio.vistas.usuarios as mod_usuarios


# --------------------------------------------------
#  PUENTE DE RED EN MEMORIA Y HELPERS DE INSPECCIÓN
# --------------------------------------------------

class _PuenteRequestsTestClient:
    """Conecta las peticiones de cliente_api.py (Tkinter) al TestClient de FastAPI."""
    def __init__(self, client: TestClient):
        self.client = client

    def _limpiar_ruta(self, url: str) -> str:
        return url.replace("http://127.0.0.1:8000", "")

    def get(self, url: str, headers: dict = None, timeout: float = None):
        return self.client.get(self._limpiar_ruta(url), headers=headers)

    def post(self, url: str, json: dict = None, headers: dict = None, timeout: float = None):
        return self.client.post(self._limpiar_ruta(url), json=json, headers=headers)

    def put(self, url: str, json: dict = None, headers: dict = None, timeout: float = None):
        return self.client.put(self._limpiar_ruta(url), json=json, headers=headers)

    def delete(self, url: str, headers: dict = None, timeout: float = None):
        return self.client.delete(self._limpiar_ruta(url), headers=headers)


def _buscar_widgets(contenedor, clase_objetivo):
    encontrados = []
    for hijo in contenedor.winfo_children():
        if isinstance(hijo, clase_objetivo):
            encontrados.append(hijo)
        encontrados.extend(_buscar_widgets(hijo, clase_objetivo))
    return encontrados


def _buscar_treeview(contenedor) -> ttk.Treeview:
    tablas = _buscar_widgets(contenedor, ttk.Treeview)
    assert len(tablas) > 0, "No se encontró el widget Treeview en la ventana."
    return tablas[0]


def _buscar_boton_por_texto(contenedor, texto_parcial: str) -> tk.Button:
    for boton in _buscar_widgets(contenedor, tk.Button):
        if texto_parcial.lower() in str(boton.cget("text")).lower():
            return boton
    raise AssertionError(f"No se encontró el botón '{texto_parcial}'.")


# ---------------------------------------------------------------------
#  FIXTURE DE ENTORNO COMPARTIDO (WEB + ESCRITORIO + FASTAPI + SQLITE)
# ---------------------------------------------------------------------

@pytest.fixture
def entorno_multicliente(tmp_path, monkeypatch):
    """
     Levanta una base SQLite temporal compartida por:
     - El cliente Web (simulado con peticiones HTTP directas + cabeceras CORS de LAN).
     - El cliente Escritorio (ventanas reales de Tkinter usando cliente_http).
    """
    ruta_db_test = str(tmp_path / "test_frankie_sync.db")
    ruta_esquema = os.path.join(DIRECTORIO_RAIZ, "db", "esquema.sql")

    conexion = sqlite3.connect(ruta_db_test)
    cursor = conexion.cursor()
    with open(ruta_esquema, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    roles_iniciales = [
        ("Administrador",), ("Gerente",),
        ("Empleado - Ventas",), ("Empleado - Compras",),
        ("Proveedor",), ("Cliente",)
    ]
    cursor.executemany("INSERT INTO roles (rol) VALUES (?)", roles_iniciales)

    hash_admin = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cursor.execute('''
        INSERT INTO usuarios (usuario, password, nombres, apellidos, dni, habilitado)
        VALUES (?, ?, ?, ?, ?, 1)
    ''', ("admin", hash_admin, "David Hernan", "Bravo", "00000000"))
    id_admin = cursor.lastrowid

    cursor.execute("SELECT id FROM roles WHERE rol = 'Administrador'")
    id_rol_admin = cursor.fetchone()[0]
    cursor.execute("INSERT INTO usuxroles (id_usuario, id_rol, habilitado) VALUES (?, ?, 1)", (id_admin, id_rol_admin))
    conexion.commit()
    conexion.close()

    app.dependency_overrides[obtener_uow] = lambda: GestorSQLite(ruta_db_test)

    client_fastapi = TestClient(app)
    puente = _PuenteRequestsTestClient(client_fastapi)
    monkeypatch.setattr(requests, "get", puente.get)
    monkeypatch.setattr(requests, "post", puente.post)
    monkeypatch.setattr(requests, "put", puente.put)
    monkeypatch.setattr(requests, "delete", puente.delete)

    cliente_http.id_operador = 1

    monkeypatch.setattr(messagebox, "showinfo", lambda t, m: None)
    monkeypatch.setattr(messagebox, "showwarning", lambda t, m: None)
    monkeypatch.setattr(messagebox, "showerror", lambda t, m: None)

    root = tk.Tk()
    root.withdraw()

    yield {
        "root": root,
        "web_client": client_fastapi,
        "ruta_db": ruta_db_test
    }

    app.dependency_overrides.clear()
    try:
        root.destroy()
    except tk.TclError:
        pass



# =============================================================================
#  CASOS DE PRUEBA: AUDITORÍA WEB SPA, CORS LAN Y SINCRONIZACIÓN BIDIRECCIONAL
# =============================================================================

def test_1_integridad_archivos_web_spa_y_reglas_responsive_movil():
    """
     Verifica que index.html, estilos.css y app_web.js existan y contengan:
     - Las 10 vistas equivalentes al escritorio.
     - Meta viewport móvil y Media Queries (@media) para pantallas de celulares.
     - Resolución dinámica de IP en red local (window.location.hostname).
    """
    ruta_html = os.path.join(DIRECTORIO_WEB, "index.html")
    ruta_css = os.path.join(DIRECTORIO_WEB, "estilos.css")
    ruta_js = os.path.join(DIRECTORIO_WEB, "app_web.js")

    assert os.path.exists(ruta_html), "Falta el archivo index.html en src/presentacion/web/"
    assert os.path.exists(ruta_css), "Falta el archivo estilos.css en src/presentacion/web/"
    assert os.path.exists(ruta_js), "Falta el archivo app_web.js en src/presentacion/web/"

    with open(ruta_html, "r", encoding="utf-8") as f:
        contenido_html = f.read()

    # Verificamos etiqueta viewport para celulares y las 10 secciones de la SPA.
    assert 'name="viewport"' in contenido_html
    assert "width=device-width" in contenido_html

    vistas_esperadas = [
        "vista-login", "vista-panel", "vista-usuarios", "vista-empleados",
        "vista-clientes", "vista-proveedores", "vista-stock",
        "vista-facturacion", "vista-consola", "vista-analitica"
    ]
    for id_vista in vistas_esperadas:
        assert f'id="{id_vista}"' in contenido_html, f"Falta la sección '{id_vista}' en index.html"

    with open(ruta_css, "r", encoding="utf-8") as f:
        contenido_css = f.read()

    # Verificamos reglas responsive para móviles y paleta de colores corporativa.
    assert "@media (max-width: 640px)" in contenido_css
    assert "#2196F3" in contenido_css
    assert "#4CAF50" in contenido_css

    with open(ruta_js, "r", encoding="utf-8") as f:
        contenido_js = f.read()

    # Verificamos que el JS tome dinámicamente la IP del host LAN y envíe X-Operador-Id.
    assert "window.location.hostname" in contenido_js
    assert "X-Operador-Id" in contenido_js


def test_2_cors_habilitado_para_clientes_moviles_en_red_local(entorno_multicliente):
    """
     Simula una petición HTTP enviada desde el navegador de un teléfono móvil en la
     red WiFi local (Origin: http://192.168.1.45:8080) y verifica que FastAPI
     permita el tráfico Cross-Origin (CORS) incluyendo la cabecera X-Operador-Id.
    """
    web_client = entorno_multicliente["web_client"]
    origen_movil_lan = "http://192.168.1.45:8080"

    # Petición Preflight OPTIONS que envía cualquier navegador móvil antes de un POST/PUT/DELETE.
    respuesta_options = web_client.options(
        "/api/perfiles",
        headers={
            "Origin": origen_movil_lan,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, X-Operador-Id"
        }
    )
    assert respuesta_options.status_code == 200
    assert respuesta_options.headers.get("access-control-allow-origin") in ("*", origen_movil_lan)


def test_3_sincronizacion_alta_en_web_se_refleja_en_escritorio_tkinter(entorno_multicliente):
    """
     Verifica que si un operador carga un Proveedor, un Cliente y un Producto desde
     la Vista Web (Móvil/PC), al abrir las ventanas de Tkinter en la PC los datos
     aparezcan inmediatamente en sus tablas Treeview.
    """
    root = entorno_multicliente["root"]
    web = entorno_multicliente["web_client"]
    cabeceras_web = {"X-Operador-Id": "1"}

    # 1. El usuario desde el navegador Web da de alta un Proveedor.
    res_prov = web.post("/api/perfiles", headers=cabeceras_web, json={
        "nombres": "Distribuidora Atlántica Web",
        "apellidos": "Lucía Méndez",
        "dni": "30-99887766-1",
        "rol": "Proveedor"
    })
    assert res_prov.status_code == 201
    id_prov_web = res_prov.json()["id"]

    # 2. Desde el navegador Web da de alta un Cliente.
    res_cli = web.post("/api/perfiles", headers=cabeceras_web, json={
        "nombres": "Sofía",
        "apellidos": "Alonso",
        "dni": "40111222",
        "rol": "Cliente"
    })
    assert res_cli.status_code == 201

    # 3. Desde el navegador Web registra un Producto asociado a ese Proveedor.
    res_prod = web.post("/api/productos", headers=cabeceras_web, json={
        "codigo": "WEB-TEC-01",
        "descripcion": "Teclado Mecánico Inalámbrico",
        "categoria": "Perifericos",
        "id_proveedor": id_prov_web,
        "precio_costo": 35000.0,
        "precio_venta": 55000.0,
        "stock_actual": 25.0,
        "stock_minimo": 5.0,
        "vencimiento": "S/D"
    })
    assert res_prod.status_code == 201

    # 4. Abrimos las ventanas de Escritorio (Tkinter) y verificamos que muestren los registros creados en la Web.
    win_proveedores = mod_proveedores.Proveedor(root)
    tabla_prov = _buscar_treeview(win_proveedores)
    razones_sociales_tk = [tabla_prov.item(i, "values")[0] for i in tabla_prov.get_children()]
    assert "Distribuidora Atlántica Web" in razones_sociales_tk

    win_clientes = mod_clientes.Cliente(root)
    tabla_cli = _buscar_treeview(win_clientes)
    apellidos_cli_tk = [tabla_cli.item(i, "values")[1] for i in tabla_cli.get_children()]
    assert "Alonso" in apellidos_cli_tk

    win_stock = mod_stock.Stock(root)
    tabla_stk = _buscar_treeview(win_stock)
    codigos_stk_tk = [tabla_stk.item(i, "values")[0] for i in tabla_stk.get_children()]
    assert "WEB-TEC-01" in codigos_stk_tk

    win_proveedores.destroy()
    win_clientes.destroy()
    win_stock.destroy()


def test_4_sincronizacion_venta_en_escritorio_actualiza_stock_y_bi_en_web(entorno_multicliente):
    """
     Verifica el camino inverso: se emite una factura desde la ventana de Facturación
     de Tkinter en la PC, y cuando el teléfono móvil consulta la API para renderizar
     Stock y el Tablero BI, recibe el stock descontado y la nueva factura al instante.
    """
    root = entorno_multicliente["root"]
    web = entorno_multicliente["web_client"]

    # 1. Preparamos catálogo base.
    id_prov = cliente_http.crear_perfil({"nombres": "Prov Sync", "apellidos": "SA", "dni": "1", "rol": "Proveedor"})["id"]
    id_vend = cliente_http.crear_perfil({"nombres": "Vendedor", "apellidos": "PC", "dni": "2", "rol": "Empleado - Ventas"})["id"]
    id_cli = cliente_http.crear_perfil({"nombres": "Cliente", "apellidos": "Móvil", "dni": "3", "rol": "Cliente"})["id"]
    id_prod = cliente_http.crear_producto({
        "codigo": "SYNC-MOUSE-99",
        "descripcion": "Mouse Gamer Óptico",
        "categoria": "Perifericos",
        "id_proveedor": id_prov,
        "precio_costo": 15000.0,
        "precio_venta": 25000.0,
        "stock_actual": 10.0,
        "stock_minimo": 2.0
    })["id"]

    # 2. Emitimos una venta de 4 unidades desde la ventana Tkinter de Facturación.
    win_fac = mod_facturacion.Facturacion(root)
    combos = _buscar_widgets(win_fac, ttk.Combobox)
    cajas = [w for w in _buscar_widgets(win_fac, tk.Entry) if not isinstance(w, ttk.Combobox)]

    combos[0].set(f"Vendedor PC (ID: {id_vend})")
    combos[1].set(f"Cliente Móvil (ID: {id_cli})")
    combos[2].set("SYNC-MOUSE-99 - Mouse Gamer Óptico")
    combos[2].event_generate("<<ComboboxSelected>>")

    cajas[0].insert(0, "4")  # Cantidad vendida: 4.
    cajas[2].insert(0, "0")  # Sin descuento.

    _buscar_boton_por_texto(win_fac, "Guardar Facturación").invoke()
    win_fac.destroy()

    # 3. El cliente Web en el celular consulta GET /api/productos y GET /api/facturas.
    productos_web = web.get("/api/productos").json()
    prod_sincronizado = next(p for p in productos_web if p["id"] == id_prod)
    assert prod_sincronizado["stock_actual"] == 6.0, "El stock en la vista Web no reflejó el descuento hecho en Tkinter."

    facturas_web = web.get("/api/facturas").json()
    assert len(facturas_web) == 1
    assert float(facturas_web[0]["total"]) == 100000.0


def test_5_sincronizacion_credenciales_entre_web_y_escritorio(entorno_multicliente):
    """
     Verifica que si un Administrador crea un nuevo usuario desde la interfaz Web,
     ese usuario pueda iniciar sesión inmediatamente desde el cliente de Escritorio.
    """
    root = entorno_multicliente["root"]
    web = entorno_multicliente["web_client"]

    # 1. Alta de un Gerente desde el cliente Web.
    res_alta = web.post(
        "/api/perfiles",
        headers={"X-Operador-Id": "1"},
        json={
            "nombres": "Valeria",
            "apellidos": "Lynch",
            "dni": "25666777",
            "rol": "Gerente",
            "usuario": "vlynch",
            "password_plana": "ClaveSeguraWeb123"
        }
    )
    assert res_alta.status_code == 201

    # 2. El nuevo usuario inicia sesión desde el cliente de Escritorio (cliente_http).
    sesion_escritorio = cliente_http.iniciar_sesion("vlynch", "ClaveSeguraWeb123")
    assert sesion_escritorio["rol"] == "Gerente"
    assert sesion_escritorio["nombres"] == "Valeria"

    # 3. Además aparece listado en la grilla de Gestión de Usuarios de Tkinter.
    win_usu = mod_usuarios.Usuario(root, id_actual=1, rol_actual="Administrador")
    tabla_usu = _buscar_treeview(win_usu)
    usuarios_en_grilla = [tabla_usu.item(i, "values")[0] for i in tabla_usu.get_children()]
    assert "vlynch" in usuarios_en_grilla
    win_usu.destroy()