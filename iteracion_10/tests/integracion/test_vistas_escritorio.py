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



# ===============================================================================
#  SUITE DE INTEGRACIÓN E2E: VISTAS DE ESCRITORIO (CUSTOMTKINTER + API REST)
# ===============================================================================
#  UBICACIÓN: tests/integracion/test_vistas_escritorio.py
#
#  DECISIÓN DE DISEÑO:
#
#   Ejecuta pruebas de punta a punta sobre las 9 ventanas reales construidas en
#   CustomTkinter conectadas en memoria al servidor FastAPI (TestClient) y a una
#   base SQLite temporal con el esquema 3FN completo (esquema.sql).
#   Verifica dimensiones (<= 1280x720), matriz RBAC, coexistencia IAM/RRHH,
#   persistencia 3FN sin cachés locales, facturación atómica, impresión/PDF,
#   Sandboxing SQL, BI, Modo Oscuro, Alto Contraste WCAG, Zoom, i18n ES/EN,
#   semáforo y búsqueda en vivo.
# ===============================================================================

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_TESTS = os.path.dirname(DIRECTORIO_ACTUAL)
DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_TESTS)
DIRECTORIO_ESCRITORIO = os.path.join(DIRECTORIO_RAIZ, "src", "presentacion", "escritorio")
DIRECTORIO_VISTAS = os.path.join(DIRECTORIO_ESCRITORIO, "vistas")

for ruta in (DIRECTORIO_RAIZ, DIRECTORIO_ESCRITORIO, DIRECTORIO_VISTAS):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

from src.infraestructura.api.servidor import app
from src.infraestructura.api.inyector_dependencias import obtener_uow
from src.infraestructura.persistencia.gestor_sqlite import GestorSQLite
from src.presentacion.escritorio.cliente_api import cliente_http, gestor_ui

import src.presentacion.escritorio.vistas.panel_control as mod_panel
import src.presentacion.escritorio.vistas.usuarios as mod_usuarios
import src.presentacion.escritorio.vistas.empleados as mod_empleados
import src.presentacion.escritorio.vistas.clientes as mod_clientes
import src.presentacion.escritorio.vistas.proveedores as mod_proveedores
import src.presentacion.escritorio.vistas.stock as mod_stock
import src.presentacion.escritorio.vistas.facturacion as mod_facturacion
import src.presentacion.escritorio.vistas.consola as mod_consola
import src.presentacion.escritorio.vistas.analitica as mod_analitica


# -------------------------------------------------------------------
#  PUENTE HTTP EN MEMORIA Y HELPERS DE INSPECCIÓN PARA CUSTOMTKINTER
# -------------------------------------------------------------------

class _PuenteRequestsTestClient:
    """Redirige las llamadas HTTP de cliente_api.py hacia el TestClient de FastAPI."""

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
    assert len(tablas) > 0, "No se encontró el widget ttk.Treeview en la ventana."
    return tablas[0]


def _buscar_boton_por_texto(contenedor, texto_parcial: str) -> ctk.CTkButton:
    for boton in _buscar_widgets(contenedor, ctk.CTkButton):
        if texto_parcial.lower() in str(boton.cget("text")).lower():
            return boton
    raise AssertionError(f"No se encontró el botón CTkButton '{texto_parcial}'.")


def _clicar_boton(boton: ctk.CTkButton):
    assert boton.cget("state") != "disabled", f"El botón '{boton.cget('text')}' está deshabilitado."
    comando = boton.cget("command")
    if not callable(comando):
        comando = getattr(boton, "_command", None)
    assert callable(comando), f"El botón '{boton.cget('text')}' no posee un comando ejecutable."
    comando()


def _escribir_entry(entry: ctk.CTkEntry, texto: str):
    entry.delete(0, "end")
    entry.insert(0, str(texto))


def _validar_resolucion_maxima(ventana: ctk.CTkToplevel, max_ancho: int = 1280, max_alto: int = 720):
    ventana.update_idletasks()
    geometria = ventana.geometry().split("+")[0]
    ancho, alto = map(int, geometria.split("x"))
    assert ancho <= max_ancho, f"La ventana excede el ancho máximo permitido ({ancho} > {max_ancho})."
    assert alto <= max_alto, f"La ventana excede el alto máximo permitido ({alto} > {max_alto})."


# -------------------------------------------------------------------------------
#  FIXTURE DE ENTORNO ESCRITORIO HEADLESS (CUSTOMTKINTER + FASTAPI + SQLITE 3FN)
# -------------------------------------------------------------------------------

@pytest.fixture
def entorno_escritorio(tmp_path, monkeypatch):
    """
     Prepara una base SQLite temporal con esquema 3FN, roles base y usuario 'admin',
     conecta cliente_http a TestClient, restaura gestor_ui y captura messagebox.
    """
    gestor_ui.resetear_por_defecto()

    ruta_db_test = str(tmp_path / "test_frankie_escritorio.db")
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

    alertas = {"info": [], "warning": [], "error": []}
    monkeypatch.setattr(messagebox, "showinfo", lambda t, m: alertas["info"].append((t, m)))
    monkeypatch.setattr(messagebox, "showwarning", lambda t, m: alertas["warning"].append((t, m)))
    monkeypatch.setattr(messagebox, "showerror", lambda t, m: alertas["error"].append((t, m)))

    ctk.set_appearance_mode("light")
    root = ctk.CTk()
    root.withdraw()

    yield {
        "root": root,
        "client": client_fastapi,
        "alertas": alertas,
        "id_admin": id_admin,
        "ruta_db": ruta_db_test
    }

    gestor_ui.resetear_por_defecto()
    app.dependency_overrides.clear()
    try:
        root.destroy()
    except tk.TclError:
        pass



# ==========================================================
#  CASOS DE PRUEBA E2E PARA LAS 9 VENTANAS DE CUSTOMTKINTER
# ==========================================================

def test_1_panel_control_matriz_rbac_y_resolucion(entorno_escritorio):
    """
     Verifica que PanelControl habilite/deshabilite exactamente los módulos
     correspondientes al rol activo y respete la cota máxima de 1280x720.
    """
    root = entorno_escritorio["root"]

    # 1. Perfil Empleado - Ventas: solo Clientes y Facturación habilitados.
    panel_ventas = mod_panel.PanelControl(root, 2, "Empleado - Ventas", "Lucas", "Vendedor")
    _validar_resolucion_maxima(panel_ventas)

    assert _buscar_boton_por_texto(panel_ventas, "Clientes").cget("state") == "normal"
    assert _buscar_boton_por_texto(panel_ventas, "Facturación").cget("state") == "normal"
    assert _buscar_boton_por_texto(panel_ventas, "Proveedores").cget("state") == "disabled"
    assert _buscar_boton_por_texto(panel_ventas, "Stock").cget("state") == "disabled"
    assert _buscar_boton_por_texto(panel_ventas, "Recursos Humanos").cget("state") == "disabled"
    assert _buscar_boton_por_texto(panel_ventas, "Usuarios").cget("state") == "disabled"
    assert _buscar_boton_por_texto(panel_ventas, "Consola SQL").cget("state") == "disabled"
    assert _buscar_boton_por_texto(panel_ventas, "Backup").cget("state") == "disabled"
    assert _buscar_boton_por_texto(panel_ventas, "Analítica").cget("state") == "disabled"
    panel_ventas.destroy()

    # 2. Perfil Gerente: opera módulos comerciales, RRHH, IAM y BI; bloquea ROOT.
    panel_gerente = mod_panel.PanelControl(root, 3, "Gerente", "María", "Gerencia")
    assert _buscar_boton_por_texto(panel_gerente, "Recursos Humanos").cget("state") == "normal"
    assert _buscar_boton_por_texto(panel_gerente, "Analítica").cget("state") == "normal"
    assert _buscar_boton_por_texto(panel_gerente, "Consola SQL").cget("state") == "disabled"
    assert _buscar_boton_por_texto(panel_gerente, "Backup").cget("state") == "disabled"
    panel_gerente.destroy()

    # 3. Perfil Administrador: acceso irrestricto a todos los módulos.
    panel_admin = mod_panel.PanelControl(root, 1, "Administrador", "David", "Bravo")
    assert _buscar_boton_por_texto(panel_admin, "Consola SQL").cget("state") == "normal"
    assert _buscar_boton_por_texto(panel_admin, "Backup").cget("state") == "normal"
    panel_admin.destroy()


def test_2_usuarios_iam_y_rrhh_coexistencia_sin_pisar_datos_3fn(entorno_escritorio):
    """
     Verifica el flujo real entre Gestión de Usuarios (IAM) y RRHH:
     1. Se crea una cuenta en Usuarios con credenciales de acceso.
     2. Se completa su legajo personal 3FN (DNI, teléfono, email, domicilio) en RRHH.
     3. Se reabre RRHH y se verifica persistencia real desde SQLite + login vigente.
    """
    root = entorno_escritorio["root"]

    # Paso 1: Alta rápida de credenciales en Usuarios (IAM).
    win_usu = mod_usuarios.Usuario(root, id_actual=1, rol_actual="Administrador")
    _validar_resolucion_maxima(win_usu)

    cajas_usu = _buscar_widgets(win_usu, ctk.CTkEntry)
    combo_usu = _buscar_widgets(win_usu, ctk.CTkComboBox)[0]

    _escribir_entry(cajas_usu[0], "Martín")
    _escribir_entry(cajas_usu[1], "Gómez")
    _escribir_entry(cajas_usu[2], "mgomez")
    _escribir_entry(cajas_usu[3], "ClaveVentas2026")
    combo_usu.set("Empleado - Ventas")

    _clicar_boton(_buscar_boton_por_texto(win_usu, "Guardar"))
    tabla_usu = _buscar_treeview(win_usu)
    iids_mgomez = [
        iid for iid in tabla_usu.get_children()
        if tabla_usu.item(iid, "values")[0] == "mgomez"
    ]
    assert len(iids_mgomez) == 1
    id_mgomez = iids_mgomez[0]
    win_usu.destroy()

    # Paso 2: Completar legajo personal en RRHH sin tocar credenciales.
    win_emp = mod_empleados.Empleado(root, id_actual=1, rol_actual="Administrador")
    _validar_resolucion_maxima(win_emp)
    tabla_emp = _buscar_treeview(win_emp)
    tabla_emp.selection_set(id_mgomez)
    tabla_emp.event_generate("<<TreeviewSelect>>")
    win_emp.update()

    cajas_emp = _buscar_widgets(win_emp, ctk.CTkEntry)
    _escribir_entry(cajas_emp[2], "35123456")
    _escribir_entry(cajas_emp[3], "223-555-9999")
    _escribir_entry(cajas_emp[4], "martin.gomez@frankie.com")
    _escribir_entry(cajas_emp[5], "Av. Colón 2500")
    _escribir_entry(cajas_emp[6], "Mar del Plata")
    _escribir_entry(cajas_emp[7], "Buenos Aires")
    _escribir_entry(cajas_emp[8], "7600")

    _clicar_boton(_buscar_boton_por_texto(win_emp, "Modificar Perfil"))
    win_emp.destroy()

    # Paso 3: Reabrir RRHH (ventana fresca, cero caché) y comprobar persistencia real.
    win_emp_2 = mod_empleados.Empleado(root, id_actual=1, rol_actual="Administrador")
    tabla_emp_2 = _buscar_treeview(win_emp_2)
    valores = tabla_emp_2.item(id_mgomez, "values")
    assert valores[2] == "35123456"
    assert valores[3] == "223-555-9999"
    assert valores[4] == "martin.gomez@frankie.com"
    assert valores[5] == "Av. Colón 2500"
    assert valores[6] == "Mar del Plata"
    assert valores[7] == "Buenos Aires"
    assert valores[8] == "7600"
    win_emp_2.destroy()

    # Paso 4: Confirmar que las credenciales IAM no fueron sobrescritas por RRHH.
    sesion = cliente_http.iniciar_sesion("mgomez", "ClaveVentas2026")
    assert sesion["rol"] == "Empleado - Ventas"
    assert sesion["email"] == "martin.gomez@frankie.com"


def test_3_clientes_abm_completo_con_persistencia_3fn(entorno_escritorio):
    """
     Verifica Alta, Modificación y Baja Lógica de un Cliente en CustomTkinter
     confirmando que sus datos de contacto y domicilio persisten en SQLite 3FN.
    """
    root = entorno_escritorio["root"]
    win_cli = mod_clientes.Cliente(root)
    _validar_resolucion_maxima(win_cli)

    cajas = _buscar_widgets(win_cli, ctk.CTkEntry)
    _escribir_entry(cajas[0], "Laura")
    _escribir_entry(cajas[1], "Fernández")
    _escribir_entry(cajas[2], "30999888")
    _escribir_entry(cajas[3], "223-411-2233")
    _escribir_entry(cajas[4], "laura@correo.com")
    _escribir_entry(cajas[5], "San Martín 1234")
    _escribir_entry(cajas[6], "Mar del Plata")
    _escribir_entry(cajas[7], "Buenos Aires")
    _escribir_entry(cajas[8], "7600")

    _clicar_boton(_buscar_boton_por_texto(win_cli, "Guardar Cliente"))

    tabla = _buscar_treeview(win_cli)
    assert len(tabla.get_children()) == 1
    iid_cli = tabla.get_children()[0]
    vals = tabla.item(iid_cli, "values")
    assert vals[0] == "Laura"
    assert vals[3] == "223-411-2233"
    assert vals[5] == "San Martín 1234"

    # Modificar domicilio y verificar tras reabrir.
    tabla.selection_set(iid_cli)
    tabla.event_generate("<<TreeviewSelect>>")
    win_cli.update()
    _escribir_entry(cajas[5], "Av. Independencia 800")
    _clicar_boton(_buscar_boton_por_texto(win_cli, "Modificar Cliente"))
    assert tabla.item(iid_cli, "values")[5] == "Av. Independencia 800"

    # Eliminar cliente (baja lógica).
    tabla.selection_set(iid_cli)
    _clicar_boton(_buscar_boton_por_texto(win_cli, "Eliminar Cliente"))
    assert len(tabla.get_children()) == 0
    win_cli.destroy()


def test_4_proveedores_y_stock_con_ubicacion_3fn(entorno_escritorio):
    """
     Verifica el alta de un Proveedor (con contacto/domicilio 3FN) y la creación
     y modificación de un Producto con ubicación física ('ubicaciones_stock').
    """
    root = entorno_escritorio["root"]

    # 1. Crear Proveedor en CustomTkinter.
    win_prov = mod_proveedores.Proveedor(root)
    _validar_resolucion_maxima(win_prov)
    cajas_prov = _buscar_widgets(win_prov, ctk.CTkEntry)

    # Orden en proveedores.py: RazonSocial, CUIT, Tel, Email, Contacto, Dir, Ciudad, Prov, CP.
    _escribir_entry(cajas_prov[0], "TecnoSur SRL")
    _escribir_entry(cajas_prov[1], "30-71122334-9")
    _escribir_entry(cajas_prov[2], "011-4444-5555")
    _escribir_entry(cajas_prov[3], "ventas@tecnosur.com")
    _escribir_entry(cajas_prov[4], "Carlos Ruiz")
    _escribir_entry(cajas_prov[5], "Parque Industrial Lote 4")
    _escribir_entry(cajas_prov[6], "Batán")
    _escribir_entry(cajas_prov[7], "Buenos Aires")
    _escribir_entry(cajas_prov[8], "7601")

    _clicar_boton(_buscar_boton_por_texto(win_prov, "Guardar Proveedor"))
    tabla_prov = _buscar_treeview(win_prov)
    vals_prov = tabla_prov.item(tabla_prov.get_children()[0], "values")
    assert vals_prov[0] == "TecnoSur SRL"
    assert vals_prov[3] == "ventas@tecnosur.com"
    assert vals_prov[8] == "Carlos Ruiz"
    win_prov.destroy()

    # 2. Crear Producto en Stock asociado al proveedor con ubicación física.
    win_stk = mod_stock.Stock(root)
    _validar_resolucion_maxima(win_stk)
    cajas_stk = _buscar_widgets(win_stk, ctk.CTkEntry)
    combo_prov = _buscar_widgets(win_stk, ctk.CTkComboBox)[0]

    # Orden en stock.py: Codigo, Desc, Cat, Ubicacion, StkAct, StkMin, Costo, Venta, Venc.
    _escribir_entry(cajas_stk[0], "MON-24-IPS")
    _escribir_entry(cajas_stk[1], "Monitor LED 24 IPS")
    _escribir_entry(cajas_stk[2], "Monitores")
    combo_prov.set("TecnoSur SRL")
    _escribir_entry(cajas_stk[3], "Depósito Central - Rack 3")
    _escribir_entry(cajas_stk[4], "15")
    _escribir_entry(cajas_stk[5], "3")
    _escribir_entry(cajas_stk[6], "120000")
    _escribir_entry(cajas_stk[7], "185000")
    _escribir_entry(cajas_stk[8], "S/D")

    _clicar_boton(_buscar_boton_por_texto(win_stk, "Guardar Producto"))
    win_stk.destroy()

    # 3. Reabrir Stock y confirmar que la ubicación persistió en SQLite 3FN.
    win_stk_2 = mod_stock.Stock(root)
    tabla_stk = _buscar_treeview(win_stk_2)
    assert len(tabla_stk.get_children()) == 1
    vals_stk = tabla_stk.item(tabla_stk.get_children()[0], "values")
    assert vals_stk[0] == "MON-24-IPS"
    assert vals_stk[8] == "Depósito Central - Rack 3"
    win_stk_2.destroy()


def test_5_facturacion_descuento_y_anulacion_sin_duplicar_stock(entorno_escritorio):
    """
     Verifica que emitir una factura descuente stock y que anularla desde la vista
     restituya exactamente las unidades originales sin duplicar inventario.
    """
    root = entorno_escritorio["root"]

    id_prov = cliente_http.crear_perfil({"nombres": "Prov Fac", "apellidos": "SA", "dni": "1", "rol": "Proveedor"})["id"]
    id_vend = cliente_http.crear_perfil({"nombres": "Ana", "apellidos": "Ventas", "dni": "2", "rol": "Empleado - Ventas"})["id"]
    id_cli = cliente_http.crear_perfil({"nombres": "Pedro", "apellidos": "Cliente", "dni": "3", "rol": "Cliente"})["id"]
    id_prod = cliente_http.crear_producto({
        "codigo": "SSD-1TB",
        "descripcion": "Disco SSD 1TB NVMe",
        "categoria": "Almacenamiento",
        "id_proveedor": id_prov,
        "precio_costo": 50000.0,
        "precio_venta": 80000.0,
        "stock_actual": 10.0,
        "stock_minimo": 2.0,
        "ubicacion": "Vitrina B"
    })["id"]

    win_fac = mod_facturacion.Facturacion(root)
    _validar_resolucion_maxima(win_fac)

    combos = _buscar_widgets(win_fac, ctk.CTkComboBox)
    cajas = _buscar_widgets(win_fac, ctk.CTkEntry)

    combos[0].set(f"Ana Ventas (ID: {id_vend})")
    combos[1].set(f"Pedro Cliente (ID: {id_cli})")
    combos[2].set("SSD-1TB - Disco SSD 1TB NVMe")
    win_fac.autocompletar_precio("SSD-1TB - Disco SSD 1TB NVMe")

    _escribir_entry(cajas[0], "4")   # Cantidad vendida.
    _escribir_entry(cajas[2], "10")  # 10% descuento.

    _clicar_boton(_buscar_boton_por_texto(win_fac, "Guardar Facturación"))

    # Verificamos stock descontado (10 - 4 = 6).
    assert cliente_http.obtener_producto(id_prod)["stock_actual"] == 6.0

    tabla_fac = _buscar_treeview(win_fac)
    assert len(tabla_fac.get_children()) == 1
    iid_fac = tabla_fac.get_children()[0]

    # Anulamos la factura y verificamos que el stock vuelva exactamente a 10.0 (no a 14.0).
    tabla_fac.selection_set(iid_fac)
    tabla_fac.event_generate("<<TreeviewSelect>>")
    win_fac.update()
    _clicar_boton(_buscar_boton_por_texto(win_fac, "Eliminar Facturación"))

    assert len(tabla_fac.get_children()) == 0
    assert cliente_http.obtener_producto(id_prod)["stock_actual"] == 10.0
    win_fac.destroy()


def test_6_consola_sql_sandboxing_y_consulta_select(entorno_escritorio):
    """
     Verifica que ConsolaSQL ejecute consultas SELECT sobre la API REST
     y bloquee cualquier sentencia destructiva (DELETE/DROP/UPDATE).
    """
    root = entorno_escritorio["root"]
    alertas = entorno_escritorio["alertas"]

    win_sql = mod_consola.ConsolaSQL(root, id_actual=1)
    _validar_resolucion_maxima(win_sql)

    editor = _buscar_widgets(win_sql, ctk.CTkTextbox)[0]
    btn_ejecutar = _buscar_boton_por_texto(win_sql, "Ejecutar Consulta")
    tabla_sql = _buscar_treeview(win_sql)

    # 1. Consulta SELECT válida.
    editor.delete("1.0", "end")
    editor.insert("1.0", "SELECT * FROM usuarios")
    _clicar_boton(btn_ejecutar)
    assert len(tabla_sql.get_children()) >= 1

    # 2. Intento de inyección destructiva bloqueado por Sandboxing.
    editor.delete("1.0", "end")
    editor.insert("1.0", "DELETE FROM usuarios;")
    _clicar_boton(btn_ejecutar)
    assert any("Bloqueo de Seguridad" in titulo for titulo, _ in alertas["error"])
    win_sql.destroy()


def test_7_analitica_bi_calcula_kpis_y_puebla_grilla(entorno_escritorio):
    """
     Verifica que el Tablero BI procese facturas emitidas desde el Backend,
     renderice los 3 Canvas estadísticos y cargue el detalle histórico en tabla.
    """
    root = entorno_escritorio["root"]

    id_prov = cliente_http.crear_perfil({"nombres": "Prov BI", "apellidos": "SA", "dni": "1", "rol": "Proveedor"})["id"]
    id_vend = cliente_http.crear_perfil({"nombres": "Vendedor", "apellidos": "BI", "dni": "2", "rol": "Empleado - Ventas"})["id"]
    id_cli = cliente_http.crear_perfil({"nombres": "Cliente", "apellidos": "BI", "dni": "3", "rol": "Cliente"})["id"]
    id_prod = cliente_http.crear_producto({
        "codigo": "BI-NOTE-01",
        "descripcion": "Notebook 15 Pulgadas",
        "categoria": "Computación",
        "id_proveedor": id_prov,
        "precio_costo": 400000.0,
        "precio_venta": 600000.0,
        "stock_actual": 5.0,
        "stock_minimo": 1.0
    })["id"]

    cliente_http.emitir_factura({
        "id_vendedor": id_vend,
        "id_cliente": id_cli,
        "id_producto": id_prod,
        "cantidad": 2.0,
        "descuento": 0.0
    })

    win_bi = mod_analitica.Analitica(root)
    _validar_resolucion_maxima(win_bi)

    tabla_bi = _buscar_treeview(win_bi)
    assert len(tabla_bi.get_children()) == 1
    fila = tabla_bi.item(tabla_bi.get_children()[0], "values")
    assert fila[1] == "Notebook 15 Pulgadas"
    assert fila[2] == "Computación"

    canvases_bi = [w for w in _buscar_widgets(win_bi, tk.Canvas) if type(w) is tk.Canvas]
    assert len(canvases_bi) == 3
    win_bi.destroy()


def test_8_modo_oscuro_bilingue_accesibilidad_semaforo_y_buscador(entorno_escritorio):
    """
     Verifica de punta a punta las mejoras profesionales de la Capa 4:
     1. Cambio reactivo a Modo Oscuro, Alto Contraste WCAG y Zoom 125% sin exceder 1280x720.
     2. Traducción en vivo a Inglés (EN) manteniendo roles canónicos en español hacia FastAPI.
     3. Semáforo visual de inventario ('stock_agotado' y 'stock_bajo') y filtro en vivo.
     4. Redibujado reactivo de los 3 Canvas en Analítica BI al alternar tema.
    """
    root = entorno_escritorio["root"]

    # 1. PanelControl: Modo Oscuro + Alto Contraste + Escala máxima (125%) + Inglés.
    panel = mod_panel.PanelControl(root, 1, "Administrador", "David", "Bravo")
    gestor_ui.alternar_tema()
    assert gestor_ui.tema == "dark"
    assert panel.cget("fg_color") == "#0F172A"

    gestor_ui.alternar_alto_contraste()
    assert gestor_ui.alto_contraste is True
    assert panel.cget("fg_color") == "#000000"

    gestor_ui.ajustar_escala(1)
    gestor_ui.ajustar_escala(1)
    assert gestor_ui.escala == 1.25
    _validar_resolucion_maxima(panel)

    gestor_ui.alternar_idioma()
    assert gestor_ui.idioma == "en"
    assert _buscar_boton_por_texto(panel, "Customer Management").cget("state") == "normal"
    assert _buscar_boton_por_texto(panel, "Sign Out").cget("state") == "normal"
    panel.destroy()

    # 2. Usuarios (IAM) operando en Inglés: el Backend debe recibir el rol canónico español.
    win_usu = mod_usuarios.Usuario(root, id_actual=1, rol_actual="Administrador")
    _validar_resolucion_maxima(win_usu)

    cajas_usu = _buscar_widgets(win_usu, ctk.CTkEntry)
    combo_usu = _buscar_widgets(win_usu, ctk.CTkComboBox)[0]

    _escribir_entry(cajas_usu[0], "Elena")
    _escribir_entry(cajas_usu[1], "Vega")
    _escribir_entry(cajas_usu[2], "evega")
    _escribir_entry(cajas_usu[3], "SalesPass2026")
    combo_usu.set("Sales Employee")

    _clicar_boton(_buscar_boton_por_texto(win_usu, "Save"))

    perfiles_api = cliente_http.listar_perfiles()
    perfil_elena = next(p for p in perfiles_api if p.get("usuario") == "evega")
    assert perfil_elena["rol"] == "Empleado - Ventas"

    tabla_usu = _buscar_treeview(win_usu)
    assert tabla_usu.item(str(perfil_elena["id"]), "values")[1] == "Sales Employee"

    # Al volver a Español con la ventana abierta, el Patrón Observador actualiza la grilla en vivo.
    gestor_ui.alternar_idioma()
    assert gestor_ui.idioma == "es"
    assert tabla_usu.item(str(perfil_elena["id"]), "values")[1] == "Empleado - Ventas"
    win_usu.destroy()

    # 3. Stock: Semáforo visual (agotado / bajo / normal) y buscador instantáneo.
    id_prov = cliente_http.crear_perfil({"nombres": "Prov Semaforo", "apellidos": "SA", "dni": "9", "rol": "Proveedor"})["id"]
    id_agotado = cliente_http.crear_producto({
        "codigo": "SEM-000", "descripcion": "Cable HDMI Agotado", "categoria": "Cables",
        "id_proveedor": id_prov, "precio_costo": 1000.0, "precio_venta": 2000.0,
        "stock_actual": 0.0, "stock_minimo": 5.0
    })["id"]
    id_bajo = cliente_http.crear_producto({
        "codigo": "SEM-LOW", "descripcion": "Mouse Stock Bajo", "categoria": "Perifericos",
        "id_proveedor": id_prov, "precio_costo": 5000.0, "precio_venta": 9000.0,
        "stock_actual": 3.0, "stock_minimo": 5.0
    })["id"]
    id_ok = cliente_http.crear_producto({
        "codigo": "SEM-OK", "descripcion": "Teclado Stock Normal", "categoria": "Perifericos",
        "id_proveedor": id_prov, "precio_costo": 10000.0, "precio_venta": 18000.0,
        "stock_actual": 25.0, "stock_minimo": 5.0
    })["id"]

    win_stk = mod_stock.Stock(root)
    _validar_resolucion_maxima(win_stk)
    tabla_stk = _buscar_treeview(win_stk)

    assert "stock_agotado" in tabla_stk.item(str(id_agotado), "tags")
    assert "stock_bajo" in tabla_stk.item(str(id_bajo), "tags")
    assert any(t in ("par", "impar") for t in tabla_stk.item(str(id_ok), "tags"))

    # Verificamos el enlace de teclado y ejecutamos el filtro de forma determinista en headless.
    caja_busqueda = _buscar_widgets(win_stk, ctk.CTkEntry)[-1]
    assert caja_busqueda._entry.bind("<KeyRelease>"), "El buscador debe tener enlazado el evento <KeyRelease>."
    _escribir_entry(caja_busqueda, "SEM-LOW")
    win_stk.filtrar_tabla()
    assert len(tabla_stk.get_children()) == 1
    assert tabla_stk.item(tabla_stk.get_children()[0], "values")[0] == "SEM-LOW"
    win_stk.destroy()

    # 4. Analítica BI: redibujado reactivo de los 3 Canvas puros al cambiar tema y contraste.
    win_bi = mod_analitica.Analitica(root)
    _validar_resolucion_maxima(win_bi)
    canvases_bi = [w for w in _buscar_widgets(win_bi, tk.Canvas) if type(w) is tk.Canvas]
    assert len(canvases_bi) == 3
    assert canvases_bi[0].cget("bg") == gestor_ui.paleta()["canvas_bg"]

    gestor_ui.alternar_alto_contraste()
    gestor_ui.alternar_tema()
    assert canvases_bi[0].cget("bg") == gestor_ui.paleta()["canvas_bg"]
    win_bi.destroy()


def test_9_facturacion_vista_previa_impresion_popup_y_pdf(entorno_escritorio, monkeypatch, tmp_path):
    """
     Verifica la funcionalidad de Impresión / PDF de Factura (Opción B - Dual)
     100% en Capa 4 sin modificar el Backend:
     1. Alerta preventiva cuando la tabla está vacía.
     2. Pop-up CTkToplevel inicia por defecto en modo 'Tabla Completa + Descuento Global'.
     3. Conmutador dual hacia 'Ítem Seleccionado' cuando hay una fila marcada.
     4. Exportación de comprobante HTML imprimible (@media print + window.print) vía navegador.
    """
    root = entorno_escritorio["root"]
    alertas = entorno_escritorio["alertas"]

    win_fac = mod_facturacion.Facturacion(root)
    _validar_resolucion_maxima(win_fac)

    # 1. Sin facturas cargadas debe advertir y no abrir el pop-up.
    _clicar_boton(_buscar_boton_por_texto(win_fac, "Imprimir Factura"))
    assert len(alertas["warning"]) >= 1
    assert win_fac._ventana_impresion is None

    # 2. Creamos actores (con legajo 3FN completo) y 2 facturas en el Backend.
    id_prov = cliente_http.crear_perfil({"nombres": "Prov Imp", "apellidos": "SA", "dni": "30-11111111-9", "rol": "Proveedor"})["id"]
    id_vend = cliente_http.crear_perfil({"nombres": "Sofía", "apellidos": "Ventas", "dni": "29111222", "rol": "Empleado - Ventas"})["id"]
    id_cli = cliente_http.crear_perfil({
        "nombres": "Carla",
        "apellidos": "Méndez",
        "dni": "33444555",
        "rol": "Cliente",
        "direccion": "Av. Colón 1500",
        "ciudad": "Mar del Plata",
        "provincia": "Buenos Aires",
        "cp": "7600"
    })["id"]
    id_prod_1 = cliente_http.crear_producto({
        "codigo": "IMP-01",
        "descripcion": "Mouse Inalámbrico",
        "categoria": "Perifericos",
        "id_proveedor": id_prov,
        "precio_costo": 6000.0,
        "precio_venta": 10000.0,
        "stock_actual": 20.0,
        "stock_minimo": 2.0
    })["id"]
    id_prod_2 = cliente_http.crear_producto({
        "codigo": "IMP-02",
        "descripcion": "Pad Gamer XL",
        "categoria": "Accesorios",
        "id_proveedor": id_prov,
        "precio_costo": 2500.0,
        "precio_venta": 5000.0,
        "stock_actual": 15.0,
        "stock_minimo": 2.0
    })["id"]

    cliente_http.emitir_factura({
        "id_vendedor": id_vend,
        "id_cliente": id_cli,
        "id_producto": id_prod_1,
        "cantidad": 2.0,
        "descuento": 0.0
    })
    cliente_http.emitir_factura({
        "id_vendedor": id_vend,
        "id_cliente": id_cli,
        "id_producto": id_prod_2,
        "cantidad": 1.0,
        "descuento": 0.0
    })

    # Refrescamos la vista y aplicamos 10% de descuento global (25,000 -> 22,500).
    _clicar_boton(_buscar_boton_por_texto(win_fac, "Actualizar"))
    tabla_fac = _buscar_treeview(win_fac)
    assert len(tabla_fac.get_children()) == 2

    cajas_fac = _buscar_widgets(win_fac, ctk.CTkEntry)
    _escribir_entry(cajas_fac[-1], "10")
    _clicar_boton(_buscar_boton_por_texto(win_fac, "Calcular Descuento Final"))
    assert win_fac._porcentaje_global_activo == 10.0

    # Marcamos una fila para verificar que el pop-up habilite el selector dual pero abra en 'Tabla Completa'.
    iid_primera = tabla_fac.get_children()[0]
    tabla_fac.selection_set(iid_primera)
    tabla_fac.event_generate("<<TreeviewSelect>>")
    win_fac.update()

    _clicar_boton(_buscar_boton_por_texto(win_fac, "Imprimir Factura"))
    popup = win_fac._ventana_impresion
    assert popup is not None and popup.winfo_exists()
    _validar_resolucion_maxima(popup)

    tabla_pop = _buscar_treeview(popup)
    assert len(tabla_pop.get_children()) == 2

    textos_pop = " | ".join(str(lbl.cget("text")) for lbl in _buscar_widgets(popup, ctk.CTkLabel))
    assert "25,000.00" in textos_pop
    assert "10%" in textos_pop
    assert "22,500.00" in textos_pop
    assert "33444555" in textos_pop
    assert "Av. Colón 1500" in textos_pop

    # 3. Alternar a 'Ítem Seleccionado' y volver a 'Tabla Completa'.
    _clicar_boton(_buscar_boton_por_texto(popup, "Ítem Seleccionado"))
    assert len(tabla_pop.get_children()) == 1

    _clicar_boton(_buscar_boton_por_texto(popup, "Tabla Completa"))
    assert len(tabla_pop.get_children()) == 2

    # 4. Exportación a vista imprimible HTML / PDF interceptando el navegador del SO.
    uris_abiertas = []
    monkeypatch.setattr(mod_facturacion.webbrowser, "open", lambda uri: uris_abiertas.append(uri) or True)
    monkeypatch.setattr(mod_facturacion.tempfile, "gettempdir", lambda: str(tmp_path))

    _clicar_boton(_buscar_boton_por_texto(popup, "Imprimir / Guardar PDF"))
    assert len(uris_abiertas) == 1
    assert uris_abiertas[0].startswith("file://")
    assert uris_abiertas[0].endswith(".html")

    archivos_html = list(tmp_path.glob("frankie_factura_*.html"))
    assert len(archivos_html) == 1
    html_generado = archivos_html[0].read_text(encoding="utf-8")
    assert "@media print" in html_generado
    assert "window.print()" in html_generado
    assert "IMP-01 - Mouse Inalámbrico" in html_generado
    assert "IMP-02 - Pad Gamer XL" in html_generado
    assert "22,500.00" in html_generado
    assert "33444555" in html_generado
    assert "Av. Colón 1500" in html_generado

    popup.destroy()
    win_fac.destroy()