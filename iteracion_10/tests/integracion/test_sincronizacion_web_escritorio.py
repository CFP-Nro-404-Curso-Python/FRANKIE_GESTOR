import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import pytest
import requests
import bcrypt
import customtkinter as ctk
from fastapi.testclient import TestClient



# ================================================================================
#  SUITE DE INTEGRACIÓN: CLIENTE WEB SPA Y SINCRONIZACIÓN 3FN CON ESCRITORIO
# ================================================================================
#  UBICACIÓN: tests/integracion/test_sincronizacion_web_escritorio.py
#
#  DECISIÓN DE DISEÑO:
#
#   Verifica la integridad responsive de la SPA Web (paleta Slate/Blue unificada,
#   Modo Oscuro, Alto Contraste WCAG, i18n ES/EN, impresión/PDF @media print,
#   cero localStorage, CORS LAN) y garantiza la sincronización bidireccional
#   real en SQLite 3FN de legajos personales y ubicaciones de stock entre el
#   navegador (PC/Móvil) y CustomTkinter.
# ================================================================================

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
from src.presentacion.escritorio.cliente_api import cliente_http, gestor_ui

import src.presentacion.escritorio.vistas.clientes as mod_clientes
import src.presentacion.escritorio.vistas.empleados as mod_empleados
import src.presentacion.escritorio.vistas.proveedores as mod_proveedores
import src.presentacion.escritorio.vistas.stock as mod_stock
import src.presentacion.escritorio.vistas.facturacion as mod_facturacion
import src.presentacion.escritorio.vistas.usuarios as mod_usuarios


# ----------------------------------------------------------------
#  PUENTE DE RED EN MEMORIA Y HELPERS DE INSPECCIÓN CUSTOMTKINTER
# ----------------------------------------------------------------

class _PuenteRequestsTestClient:
    """Conecta las peticiones de cliente_api.py (CustomTkinter) al TestClient de FastAPI."""

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


def _buscar_boton_por_texto(contenedor, texto_parcial: str) -> ctk.CTkButton:
    for boton in _buscar_widgets(contenedor, ctk.CTkButton):
        if texto_parcial.lower() in str(boton.cget("text")).lower():
            return boton
    raise AssertionError(f"No se encontró el botón CTkButton '{texto_parcial}'.")


def _clicar_boton(boton: ctk.CTkButton):
    comando = boton.cget("command")
    if not callable(comando):
        comando = getattr(boton, "_command", None)
    assert callable(comando), f"El botón '{boton.cget('text')}' no tiene comando ejecutable."
    comando()


def _escribir_entry(entry: ctk.CTkEntry, texto: str):
    entry.delete(0, "end")
    entry.insert(0, str(texto))


# ----------------------------------------------------------------------------
#  FIXTURE DE ENTORNO COMPARTIDO (WEB + CUSTOMTKINTER + FASTAPI + SQLITE 3FN)
# ----------------------------------------------------------------------------

@pytest.fixture
def entorno_multicliente(tmp_path, monkeypatch):
    gestor_ui.resetear_por_defecto()

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
    cursor.execute(
        "INSERT INTO usuxroles (id_usuario, id_rol, habilitado) VALUES (?, ?, 1)",
        (id_admin, id_rol_admin)
    )
    conexion.commit()
    conexion.close()

    app.dependency_overrides[obtener_uow] = lambda: GestorSQLite(ruta_db_test)

    client_fastapi = TestClient(app)
    puente = _PuenteRequestsTestClient(client_fastapi)
    monkeypatch.setattr(requests, "get", puente.get)
    monkeypatch.setattr(requests, "post", puente.post)
    monkeypatch.setattr(requests, "put", puente.put)
    monkeypatch.setattr(requests, "delete", puente.delete)

    cliente_http.id_operador = id_admin

    monkeypatch.setattr(messagebox, "showinfo", lambda t, m: None)
    monkeypatch.setattr(messagebox, "showwarning", lambda t, m: None)
    monkeypatch.setattr(messagebox, "showerror", lambda t, m: None)

    ctk.set_appearance_mode("light")
    root = ctk.CTk()
    root.withdraw()

    yield {
        "root": root,
        "web_client": client_fastapi,
        "ruta_db": ruta_db_test
    }

    gestor_ui.resetear_por_defecto()
    app.dependency_overrides.clear()
    try:
        root.destroy()
    except tk.TclError:
        pass



# ======================================================================
#  CASOS DE PRUEBA: AUDITORÍA WEB SPA, CERO CACHÉS Y SINCRONIZACIÓN 3FN
# ======================================================================

def test_1_integridad_web_spa_paleta_unificada_y_cero_localstorage():
    """
     Verifica que index.html, estilos.css y app_web.js cumplan:
     - 10 vistas equivalentes y meta viewport móvil.
     - Paleta Slate/Blue unificada con CustomTkinter y Media Queries móviles.
     - Resolución LAN dinámica (window.location.hostname) y CERO uso de localStorage.
    """
    ruta_html = os.path.join(DIRECTORIO_WEB, "index.html")
    ruta_css = os.path.join(DIRECTORIO_WEB, "estilos.css")
    ruta_js = os.path.join(DIRECTORIO_WEB, "app_web.js")

    assert os.path.exists(ruta_html)
    assert os.path.exists(ruta_css)
    assert os.path.exists(ruta_js)

    with open(ruta_html, "r", encoding="utf-8") as f:
        contenido_html = f.read()

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

    assert "@media (max-width: 640px)" in contenido_css
    assert "#2563EB" in contenido_css
    assert "#16A34A" in contenido_css
    assert "#1E293B" in contenido_css

    with open(ruta_js, "r", encoding="utf-8") as f:
        contenido_js = f.read()

    assert "window.location.hostname" in contenido_js
    assert "X-Operador-Id" in contenido_js
    assert "localStorage." not in contenido_js, "app_web.js no debe invocar localStorage para datos de negocio."


def test_2_cors_habilitado_para_clientes_moviles_en_red_local(entorno_multicliente):
    """
     Simula una petición Preflight OPTIONS enviada desde un móvil en red WiFi local
     y verifica que FastAPI permita el tráfico Cross-Origin incluyendo X-Operador-Id.
    """
    web_client = entorno_multicliente["web_client"]
    origen_movil_lan = "http://192.168.1.38:8080"

    respuesta_options = web_client.options(
        "/api/perfiles",
        headers={
            "Origin": origen_movil_lan,
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "Content-Type, X-Operador-Id"
        }
    )
    assert respuesta_options.status_code == 200
    assert respuesta_options.headers.get("access-control-allow-origin") in ("*", origen_movil_lan)


def test_3_sincronizacion_alta_3fn_en_web_se_refleja_en_customtkinter(entorno_multicliente):
    """
     Verifica que los datos completos (contacto, domicilio y ubicación de stock)
     cargados desde la Web aparezcan íntegramente en las grillas de CustomTkinter.
    """
    root = entorno_multicliente["root"]
    web = entorno_multicliente["web_client"]
    cabeceras_web = {"X-Operador-Id": "1"}

    # 1. Alta de Proveedor con legajo 3FN desde la Web.
    res_prov = web.post("/api/perfiles", headers=cabeceras_web, json={
        "nombres": "Distribuidora Atlántica Web",
        "apellidos": "Lucía Méndez",
        "dni": "30-99887766-1",
        "rol": "Proveedor",
        "telefono": "223-490-1000",
        "email": "contacto@atlantica.com",
        "direccion": "Av. Luro 4100",
        "ciudad": "Mar del Plata",
        "provincia": "Buenos Aires",
        "cp": "7600"
    })
    assert res_prov.status_code == 201
    id_prov_web = res_prov.json()["id"]

    # 2. Alta de Cliente con legajo 3FN desde la Web.
    res_cli = web.post("/api/perfiles", headers=cabeceras_web, json={
        "nombres": "Sofía",
        "apellidos": "Alonso",
        "dni": "40111222",
        "rol": "Cliente",
        "telefono": "223-600-7788",
        "email": "sofia@mail.com",
        "direccion": "Güemes 2900",
        "ciudad": "Mar del Plata",
        "provincia": "Buenos Aires",
        "cp": "7600"
    })
    assert res_cli.status_code == 201

    # 3. Alta de Producto con ubicación en depósito desde la Web.
    res_prod = web.post("/api/productos", headers=cabeceras_web, json={
        "codigo": "WEB-TEC-01",
        "descripcion": "Teclado Mecánico Inalámbrico",
        "categoria": "Perifericos",
        "id_proveedor": id_prov_web,
        "precio_costo": 35000.0,
        "precio_venta": 55000.0,
        "stock_actual": 25.0,
        "stock_minimo": 5.0,
        "ubicacion": "Estantería B-12",
        "vencimiento": "S/D"
    })
    assert res_prod.status_code == 201

    # 4. Abrimos las vistas de CustomTkinter y verificamos TODOS los campos 3FN.
    win_proveedores = mod_proveedores.Proveedor(root)
    tabla_prov = _buscar_treeview(win_proveedores)
    vals_prov = tabla_prov.item(str(id_prov_web), "values")
    assert vals_prov[0] == "Distribuidora Atlántica Web"
    assert vals_prov[2] == "223-490-1000"
    assert vals_prov[3] == "contacto@atlantica.com"
    assert vals_prov[4] == "Av. Luro 4100"

    win_clientes = mod_clientes.Cliente(root)
    tabla_cli = _buscar_treeview(win_clientes)
    vals_cli = tabla_cli.item(tabla_cli.get_children()[0], "values")
    assert vals_cli[1] == "Alonso"
    assert vals_cli[3] == "223-600-7788"
    assert vals_cli[5] == "Güemes 2900"

    win_stock = mod_stock.Stock(root)
    tabla_stk = _buscar_treeview(win_stock)
    vals_stk = tabla_stk.item(tabla_stk.get_children()[0], "values")
    assert vals_stk[0] == "WEB-TEC-01"
    assert vals_stk[8] == "Estantería B-12"

    win_proveedores.destroy()
    win_clientes.destroy()
    win_stock.destroy()


def test_4_flujo_gerente_web_edita_vendedor_3fn_y_se_refleja_en_tk_rrhh(entorno_multicliente):
    """
     Reproduce el escenario crítico real:
     1. Admin crea un Gerente en Escritorio (CustomTkinter).
     2. El Gerente se loguea en la Web, crea un Vendedor y luego completa todos
        sus datos personales (DNI, teléfono, email, dirección, ciudad, provincia, CP).
     3. Al abrir RRHH en CustomTkinter se reflejan TODOS los campos actualizados,
        y el vendedor conserva intactas sus credenciales de acceso.
    """
    root = entorno_multicliente["root"]
    web = entorno_multicliente["web_client"]

    # 1. Admin crea al Gerente desde CustomTkinter (Usuarios).
    win_usu = mod_usuarios.Usuario(root, id_actual=1, rol_actual="Administrador")
    cajas_usu = _buscar_widgets(win_usu, ctk.CTkEntry)
    combo_rol = _buscar_widgets(win_usu, ctk.CTkComboBox)[0]

    _escribir_entry(cajas_usu[0], "Roberto")
    _escribir_entry(cajas_usu[1], "Gerente")
    _escribir_entry(cajas_usu[2], "rgerente")
    _escribir_entry(cajas_usu[3], "GerentePass123")
    combo_rol.set("Gerente")
    _clicar_boton(_buscar_boton_por_texto(win_usu, "Guardar"))
    win_usu.destroy()

    # 2. El Gerente inicia sesión desde el cliente Web.
    res_login_ger = web.post("/api/perfiles/login", json={
        "usuario": "rgerente",
        "password": "GerentePass123"
    })
    assert res_login_ger.status_code == 200
    id_gerente = res_login_ger.json()["id"]
    cabeceras_gerente = {"X-Operador-Id": str(id_gerente)}

    # 3. El Gerente crea un Vendedor en la Web (módulo Usuarios).
    res_vend = web.post("/api/perfiles", headers=cabeceras_gerente, json={
        "nombres": "Julián",
        "apellidos": "Álvarez",
        "dni": "00000000",
        "rol": "Empleado - Ventas",
        "usuario": "jalvarez",
        "password_plana": "Ventas2026"
    })
    assert res_vend.status_code == 201
    id_vendedor = res_vend.json()["id"]

    # 4. El Gerente completa los datos personales del Vendedor en la Web (módulo RRHH).
    res_edit = web.put(f"/api/perfiles/{id_vendedor}", headers=cabeceras_gerente, json={
        "nombres": "Julián",
        "apellidos": "Álvarez",
        "dni": "42555666",
        "rol": "Empleado - Ventas",
        "telefono": "223-512-3456",
        "email": "julian.alvarez@frankie.com",
        "direccion": "Av. Constitución 5100",
        "ciudad": "Mar del Plata",
        "provincia": "Buenos Aires",
        "cp": "7600"
    })
    assert res_edit.status_code == 200

    # 5. En CustomTkinter (RRHH) deben aparecer TODOS los datos personales, no solo el DNI.
    win_rrhh = mod_empleados.Empleado(root, id_actual=1, rol_actual="Administrador")
    tabla_rrhh = _buscar_treeview(win_rrhh)
    valores_tk = tabla_rrhh.item(str(id_vendedor), "values")

    assert valores_tk[0] == "Julián"
    assert valores_tk[1] == "Álvarez"
    assert valores_tk[2] == "42555666"
    assert valores_tk[3] == "223-512-3456"
    assert valores_tk[4] == "julian.alvarez@frankie.com"
    assert valores_tk[5] == "Av. Constitución 5100"
    assert valores_tk[6] == "Mar del Plata"
    assert valores_tk[7] == "Buenos Aires"
    assert valores_tk[8] == "7600"
    assert valores_tk[9] == "Empleado - Ventas"
    win_rrhh.destroy()

    # 6. El Vendedor sigue pudiendo loguearse porque RRHH no pisó sus credenciales.
    res_login_vend = web.post("/api/perfiles/login", json={
        "usuario": "jalvarez",
        "password": "Ventas2026"
    })
    assert res_login_vend.status_code == 200
    assert res_login_vend.json()["direccion"] == "Av. Constitución 5100"


def test_5_sincronizacion_venta_en_escritorio_actualiza_stock_y_bi_en_web(entorno_multicliente):
    """
     Verifica el camino inverso: una venta emitida desde CustomTkinter actualiza
     inmediatamente el stock y el historial BI consumido por la interfaz Web.
    """
    root = entorno_multicliente["root"]
    web = entorno_multicliente["web_client"]

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
        "stock_minimo": 2.0,
        "ubicacion": "Mostrador 1"
    })["id"]

    win_fac = mod_facturacion.Facturacion(root)
    combos = _buscar_widgets(win_fac, ctk.CTkComboBox)
    cajas = _buscar_widgets(win_fac, ctk.CTkEntry)

    combos[0].set(f"Vendedor PC (ID: {id_vend})")
    combos[1].set(f"Cliente Móvil (ID: {id_cli})")
    combos[2].set("SYNC-MOUSE-99 - Mouse Gamer Óptico")
    win_fac.autocompletar_precio("SYNC-MOUSE-99 - Mouse Gamer Óptico")

    _escribir_entry(cajas[0], "4")
    _escribir_entry(cajas[2], "0")

    _clicar_boton(_buscar_boton_por_texto(win_fac, "Guardar Facturación"))
    win_fac.destroy()

    productos_web = web.get("/api/productos").json()
    prod_sincronizado = next(p for p in productos_web if p["id"] == id_prod)
    assert prod_sincronizado["stock_actual"] == 6.0
    assert prod_sincronizado["ubicacion"] == "Mostrador 1"

    facturas_web = web.get("/api/facturas").json()
    assert len(facturas_web) == 1
    assert float(facturas_web[0]["total"]) == 100000.0


def test_6_sincronizacion_credenciales_entre_web_y_customtkinter(entorno_multicliente):
    """
     Verifica que un usuario creado desde la Web pueda iniciar sesión en el
     cliente de Escritorio y figure inmediatamente en la grilla de Usuarios.
    """
    root = entorno_multicliente["root"]
    web = entorno_multicliente["web_client"]

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

    sesion_escritorio = cliente_http.iniciar_sesion("vlynch", "ClaveSeguraWeb123")
    assert sesion_escritorio["rol"] == "Gerente"
    assert sesion_escritorio["nombres"] == "Valeria"

    win_usu = mod_usuarios.Usuario(root, id_actual=1, rol_actual="Administrador")
    tabla_usu = _buscar_treeview(win_usu)
    usuarios_en_grilla = [tabla_usu.item(i, "values")[0] for i in tabla_usu.get_children()]
    assert "vlynch" in usuarios_en_grilla
    win_usu.destroy()


def test_7_paridad_web_spa_temas_bilingue_wcag_buscadores_y_bi():
    """
     Verifica la paridad 1:1 de la interfaz Web SPA respecto a CustomTkinter:
     - Barra de preferencias (ES/EN, Claro/Oscuro, A-/A+, Alto Contraste).
     - Atributos semánticos WCAG 2.1 AA (aria-live, aria-pressed, :focus-visible).
     - Buscadores instantáneos en las 7 grillas y semáforo de stock.
     - Gráficos BI con anti-superposición y persistencia de preferencias solo en sessionStorage.
    """
    ruta_html = os.path.join(DIRECTORIO_WEB, "index.html")
    ruta_css = os.path.join(DIRECTORIO_WEB, "estilos.css")
    ruta_js = os.path.join(DIRECTORIO_WEB, "app_web.js")

    with open(ruta_html, "r", encoding="utf-8") as f:
        html = f.read()
    with open(ruta_css, "r", encoding="utf-8") as f:
        css = f.read()
    with open(ruta_js, "r", encoding="utf-8") as f:
        js = f.read()

    # Controles de preferencias y accesibilidad WCAG en HTML.
    for id_ctrl in (
        "btn-pref-idioma", "btn-pref-tema",
        "btn-pref-zoom-menos", "btn-pref-zoom-mas", "btn-pref-hc"
    ):
        assert f'id="{id_ctrl}"' in html

    assert 'role="toolbar"' in html
    assert 'aria-live="polite"' in html
    assert 'aria-pressed=' in html
    assert 'data-i18n=' in html

    # Buscadores instantáneos presentes en las 7 grillas.
    for id_busq in (
        "buscar-usuarios", "buscar-empleados", "buscar-clientes",
        "buscar-proveedores", "buscar-stock", "buscar-facturacion", "buscar-bi"
    ):
        assert f'id="{id_busq}"' in html

    # Perfiles visuales, escalado WCAG y semáforo en CSS.
    assert 'html[data-theme="dark"]' in css
    assert 'html[data-contrast="high"]' in css
    assert 'html[data-theme="dark"][data-contrast="high"]' in css
    assert 'html[data-scale="1.15"]' in css
    assert 'html[data-scale="1.25"]' in css
    assert ":focus-visible" in css
    assert ".fila-stock-bajo" in css
    assert ".fila-stock-agotado" in css

    # Motor i18n, preferencias en sessionStorage, atajos y BI anti-superposición en JS.
    assert "TRADUCCIONES_WEB" in js
    assert "ROLES_A_EN" in js
    assert "alternarIdiomaWeb" in js
    assert "alternarTemaWeb" in js
    assert "alternarAltoContrasteWeb" in js
    assert "ajustarEscalaWeb" in js
    assert "sessionStorage" in js
    assert "localStorage." not in js
    assert "acortarEtiquetaBI" in js
    assert "obtenerTokensCanvas" in js
    assert 'evento.key === "Escape"' in js


def test_8_paridad_impresion_factura_web_modal_y_media_print():
    """
     Verifica que la SPA Web implemente en paridad 1:1 la vista previa e
     impresión / PDF de facturas (Opción B - Dual, por defecto Tabla Completa +
     Descuento Global) sin modificar el Backend ni usar localStorage.
    """
    ruta_html = os.path.join(DIRECTORIO_WEB, "index.html")
    ruta_css = os.path.join(DIRECTORIO_WEB, "estilos.css")
    ruta_js = os.path.join(DIRECTORIO_WEB, "app_web.js")

    with open(ruta_html, "r", encoding="utf-8") as f:
        html = f.read()
    with open(ruta_css, "r", encoding="utf-8") as f:
        css = f.read()
    with open(ruta_js, "r", encoding="utf-8") as f:
        js = f.read()

    # Botón, modal de vista previa y elementos del comprobante en HTML.
    for id_imp in (
        "btn-fac-imprimir",
        "modal-impresion-factura",
        "area-impresion-factura",
        "imp-barra-modo",
        "btn-imp-modo-todo",
        "btn-imp-modo-sel",
        "btn-imp-web-print",
        "tabla-impresion-factura",
        "imp-nro",
        "imp-cliente",
        "imp-vendedor",
        "imp-dni",
        "imp-domicilio",
        "imp-subtotal",
        "imp-fila-desc-global",
        "imp-total-final",
    ):
        assert f'id="{id_imp}"' in html, f"Falta '{id_imp}' en index.html"

    assert "abrirVistaPreviaFacturaWeb()" in html
    assert "imprimirFacturaWeb()" in html
    assert "no-print" in html

    # Reglas de maquetado e impresión PDF limpia en CSS.
    assert "@media print" in css
    assert ".no-print" in css
    assert ".hoja-comprobante" in css
    assert ".tabla-comprobante" in css
    assert "print-color-adjust: exact" in css

    # Lógica de comprobante dual (por defecto 'todo') e i18n en JS.
    assert "abrirVistaPreviaFacturaWeb" in js
    assert "construirDatosComprobanteWeb" in js
    assert "renderizarVistaPreviaFacturaWeb" in js
    assert "cambiarModoImpresionWeb" in js
    assert "cerrarVistaPreviaFacturaWeb" in js
    assert "imprimirFacturaWeb" in js
    assert "window.print()" in js
    assert 'modoImpresionWeb = "todo"' in js
    assert "mapaClientesIdAObj" in js
    assert "mapaVendedoresIdAObj" in js
    assert "fac_btn_imprimir" in js
    assert "fac_imp_modo_todo" in js
    assert "fac_imp_modo_sel" in js
    assert "localStorage." not in js