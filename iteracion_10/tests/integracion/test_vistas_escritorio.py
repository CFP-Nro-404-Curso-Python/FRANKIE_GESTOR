import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import pytest
import requests
import bcrypt
from fastapi.testclient import TestClient



# ===========================================================================================================
#  SUITE DE INTEGRACIÓN E2E: VISTAS TKINTER + CLIENTE API + FASTAPI + SQLITE
# ===========================================================================================================
#  UBICACIÓN: tests/integracion/test_vistas_escritorio.py
#
#  DECISIÓN DE DISEÑO:
#   Esta batería de pruebas verifica de punta a punta las 9 ventanas de Tkinter (Panel de Control, Usuarios, 
#   Empleados, Clientes, Proveedores, Stock, Facturación, Consola SQL y Analítica BI) interactuando a través 
#   de 'cliente_http' contra el servidor FastAPI y una base SQLite efímera con el esquema real (3FN, Vistas 
#   y Triggers).
# ===========================================================================================================

# 1. Anclaje de rutas para que los imports internos de las vistas funcionen igual que en producción.
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
from src.presentacion.escritorio.cliente_api import cliente_http

# Importamos los módulos de las vistas de escritorio a auditar.
import src.presentacion.escritorio.vistas.panel_control as mod_panel
import src.presentacion.escritorio.vistas.usuarios as mod_usuarios
import src.presentacion.escritorio.vistas.empleados as mod_empleados
import src.presentacion.escritorio.vistas.clientes as mod_clientes
import src.presentacion.escritorio.vistas.proveedores as mod_proveedores
import src.presentacion.escritorio.vistas.stock as mod_stock
import src.presentacion.escritorio.vistas.facturacion as mod_facturacion
import src.presentacion.escritorio.vistas.consola as mod_consola
import src.presentacion.escritorio.vistas.analitica as mod_analitica


# --------------------------------------------------------------------------
#  ADAPTADOR DE RED EN MEMORIA (PUENTE ENTRE REQUESTS Y FASTAPI TESTCLIENT)
# --------------------------------------------------------------------------

class _PuenteRequestsTestClient:
    """
     Redirige todas las llamadas de la librería 'requests' hechas por cliente_api.py
     hacia el TestClient de FastAPI en memoria, sin necesidad de abrir puertos TCP.
    """
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


# ------------------------------------------------------------
#  HELPERS PARA RECORRER E INTERACTUAR CON WIDGETS DE TKINTER
# ------------------------------------------------------------

def _buscar_widgets(contenedor, clase_objetivo):
    """Recorre recursivamente una ventana y devuelve todos los widgets de un tipo dado."""
    encontrados = []
    for hijo in contenedor.winfo_children():
        if isinstance(hijo, clase_objetivo):
            encontrados.append(hijo)
        encontrados.extend(_buscar_widgets(hijo, clase_objetivo))
    return encontrados

def _buscar_boton_por_texto(contenedor, texto_parcial: str) -> tk.Button:
    """Busca un botón dentro de la ventana cuyo texto contenga la cadena indicada."""
    for boton in _buscar_widgets(contenedor, tk.Button):
        if texto_parcial.lower() in str(boton.cget("text")).lower():
            return boton
    raise AssertionError(f"No se encontró ningún botón con el texto '{texto_parcial}'.")

def _buscar_treeview(contenedor) -> ttk.Treeview:
    """Recupera la grilla Treeview principal de la ventana."""
    tablas = _buscar_widgets(contenedor, ttk.Treeview)
    assert len(tablas) > 0, "No se encontró ningún widget Treeview en la ventana."
    return tablas[0]


# ------------------------------------------------------------------------------
#  FIXTURE PRINCIPAL: ENTORNO AISLADO DE BASE DE DATOS + API + TKINTER HEADLESS
# ------------------------------------------------------------------------------

@pytest.fixture
def entorno_gui(tmp_path, monkeypatch):
    """
     Prepara para cada test:
     1. Una base SQLite temporal inicializada con db/esquema.sql y el usuario 'admin'.
     2. La inyección de dependencias de FastAPI apuntando a esa base temporal.
     3. El puente entre 'requests' (cliente_http) y TestClient(app).
     4. Una ventana raíz tk.Tk() oculta (withdraw) y espías para messagebox.
    """
    ruta_db_test = str(tmp_path / "test_frankie_gui.db")
    ruta_esquema = os.path.join(DIRECTORIO_RAIZ, "db", "esquema.sql")

    # 1. Inicializamos la base temporal con el esquema oficial y el Administrador maestro.
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

    # 2. Redirigimos FastAPI y la Consola SQL hacia la base temporal.
    app.dependency_overrides[obtener_uow] = lambda: GestorSQLite(ruta_db_test)
    monkeypatch.setattr(mod_consola, "DB_PATH", ruta_db_test)

    # 3. Conectamos requests de cliente_api.py al TestClient de FastAPI.
    client_fastapi = TestClient(app)
    puente = _PuenteRequestsTestClient(client_fastapi)
    monkeypatch.setattr(requests, "get", puente.get)
    monkeypatch.setattr(requests, "post", puente.post)
    monkeypatch.setattr(requests, "put", puente.put)
    monkeypatch.setattr(requests, "delete", puente.delete)

    # Configuramos el operador activo por defecto como el Admin (ID 1).
    cliente_http.id_operador = 1

    # 4. Interceptamos messagebox para que no abra ventanas modales bloqueantes.
    historial_alertas = {"info": [], "warning": [], "error": []}
    monkeypatch.setattr(messagebox, "showinfo", lambda t, m: historial_alertas["info"].append((t, m)))
    monkeypatch.setattr(messagebox, "showwarning", lambda t, m: historial_alertas["warning"].append((t, m)))
    monkeypatch.setattr(messagebox, "showerror", lambda t, m: historial_alertas["error"].append((t, m)))

    # 5. Creamos la raíz de Tkinter oculta (modo Headless).
    root = tk.Tk()
    root.withdraw()

    yield {
        "root": root,
        "ruta_db": ruta_db_test,
        "alertas": historial_alertas
    }

    # Limpieza al terminar cada test.
    app.dependency_overrides.clear()
    try:
        root.destroy()
    except tk.TclError:
        pass



# ==========================================================
#  CASOS DE PRUEBA DE INTEGRACIÓN EN INTERFAZ DE ESCRITORIO
# ==========================================================

def test_1_cambio_password_admin_en_gui_mantiene_rol_y_acceso_al_panel(entorno_gui):
    """
     Prueba de regresión crítica:
     Verifica que al cambiar la contraseña de 'admin' desde la ventana de Usuarios,
     el rol no se corrompa a mayúsculas ('ADMINISTRADOR') y que al volver a iniciar
     sesión conserve acceso total (botones en estado NORMAL) en el Panel de Control.
    """
    root = entorno_gui["root"]

    # 1. Login inicial con la clave por defecto.
    perfil_inicial = cliente_http.iniciar_sesion("admin", "admin123")
    assert perfil_inicial["rol"] == "Administrador"

    # 2. Abrimos la ventana de Gestión de Usuarios y seleccionamos la fila del Admin (ID "1").
    win_usuarios = mod_usuarios.Usuario(root, id_actual=1, rol_actual="Administrador")
    tabla = _buscar_treeview(win_usuarios)
    assert "1" in tabla.get_children()

    tabla.selection_set("1")
    tabla.event_generate("<<TreeviewSelect>>")
    root.update_idletasks()

    # 3. Escribimos una nueva contraseña en la caja de password (4to Entry del formulario).
    cajas_texto = [w for w in _buscar_widgets(win_usuarios, tk.Entry) if not isinstance(w, ttk.Combobox)]
    caja_password = cajas_texto[3]
    caja_password.delete(0, tk.END)
    caja_password.insert(0, "NuevaClaveAdmin2026!")

    # Invocamos el botón "Modificar" de la interfaz gráfica.
    btn_modificar = _buscar_boton_por_texto(win_usuarios, "Modificar")
    btn_modificar.invoke()
    assert len(entorno_gui["alertas"]["error"]) == 0

    # 4. Re-autenticamos con la nueva contraseña y verificamos que el rol siga siendo 'Administrador'.
    perfil_reingreso = cliente_http.iniciar_sesion("admin", "NuevaClaveAdmin2026!")
    assert perfil_reingreso["rol"] == "Administrador"

    # 5. Abrimos el Panel de Control con los datos devueltos por el login y verificamos que todo esté habilitado.
    win_panel = mod_panel.PanelControl(
        root,
        perfil_reingreso["id"],
        perfil_reingreso["rol"],
        perfil_reingreso["nombres"],
        perfil_reingreso["apellidos"]
    )
    botones_panel = [
        b for b in _buscar_widgets(win_panel, tk.Button)
        if b.cget("text") != "Cerrar Sesión"
    ]
    assert len(botones_panel) == 9
    for boton in botones_panel:
        assert str(boton.cget("state")) == "normal", f"El botón '{boton.cget('text')}' quedó deshabilitado."

    win_usuarios.destroy()
    win_panel.destroy()

def test_2_panel_control_aplica_matriz_rbac_segun_rol(entorno_gui):
    """
     Verifica que el Panel de Control habilite y deshabilite correctamente los botones
     según el rol operativo del usuario logueado (Gerente vs Empleado - Ventas).
    """
    root = entorno_gui["root"]

    # Caso A: Empleado - Ventas (solo puede acceder a Clientes y Facturación).
    panel_ventas = mod_panel.PanelControl(root, 2, "Empleado - Ventas", "Juan", "Perez")
    assert str(_buscar_boton_por_texto(panel_ventas, "Gestión de Clientes").cget("state")) == "normal"
    assert str(_buscar_boton_por_texto(panel_ventas, "Facturación").cget("state")) == "normal"
    assert str(_buscar_boton_por_texto(panel_ventas, "Control de Stock").cget("state")) == "disabled"
    assert str(_buscar_boton_por_texto(panel_ventas, "Gestión de Usuarios").cget("state")) == "disabled"
    assert str(_buscar_boton_por_texto(panel_ventas, "Consola SQL").cget("state")) == "disabled"
    assert str(_buscar_boton_por_texto(panel_ventas, "Analítica de Ventas").cget("state")) == "disabled"
    panel_ventas.destroy()

    # Caso B: Gerente (accede a todo incluido BI, excepto a Consola SQL y Backup que son ROOT).
    panel_gerente = mod_panel.PanelControl(root, 3, "Gerente", "Laura", "Gomez")
    assert str(_buscar_boton_por_texto(panel_gerente, "Recursos Humanos").cget("state")) == "normal"
    assert str(_buscar_boton_por_texto(panel_gerente, "Analítica de Ventas").cget("state")) == "normal"
    assert str(_buscar_boton_por_texto(panel_gerente, "Consola SQL").cget("state")) == "disabled"
    assert str(_buscar_boton_por_texto(panel_gerente, "Generar Backup").cget("state")) == "disabled"
    panel_gerente.destroy()

def test_3_flujo_gui_proveedores_y_stock_sincronizados(entorno_gui):
    """
     Verifica que al dar de alta un Proveedor en su ventana, aparezca inmediatamente
     en el desplegable de la ventana de Stock, permitiendo crear y modificar productos.
    """
    root = entorno_gui["root"]

    # 1. Abrimos el formulario de Proveedores y cargamos un proveedor nuevo.
    win_prov = mod_proveedores.Proveedor(root)
    cajas_prov = [w for w in _buscar_widgets(win_prov, tk.Entry) if not isinstance(w, ttk.Combobox)]
    cajas_prov[0].insert(0, "Mayorista Informático MDP")  # Razón Social
    cajas_prov[1].insert(0, "30-71122334-9")              # CUIT
    cajas_prov[8].insert(0, "Roberto Gómez")              # Contacto

    _buscar_boton_por_texto(win_prov, "Guardar Proveedor").invoke()

    tabla_prov = _buscar_treeview(win_prov)
    assert len(tabla_prov.get_children()) == 1
    valores_prov = tabla_prov.item(tabla_prov.get_children()[0], "values")
    assert valores_prov[0] == "Mayorista Informático MDP"

    # 2. Abrimos la ventana de Stock y verificamos que el proveedor esté en el Combobox.
    win_stock = mod_stock.Stock(root)
    combo_prov = _buscar_widgets(win_stock, ttk.Combobox)[0]
    assert "Mayorista Informático MDP" in combo_prov["values"]

    # 3. Damos de alta un producto desde la interfaz de Stock.
    cajas_stock = [w for w in _buscar_widgets(win_stock, tk.Entry) if not isinstance(w, ttk.Combobox)]
    cajas_stock[0].insert(0, "MON-24-FHD")       # Código.
    cajas_stock[1].insert(0, "Monitor 24 IPS")   # Descripción.
    cajas_stock[2].insert(0, "Monitores")        # Categoría.
    combo_prov.set("Mayorista Informático MDP")  # Proveedor.
    cajas_stock[3].insert(0, "20")               # Stock Actual.
    cajas_stock[4].insert(0, "5")                # Stock Mínimo.
    cajas_stock[5].insert(0, "100000")           # Precio Costo.
    cajas_stock[6].insert(0, "150000")           # Precio Venta.
    cajas_stock[7].insert(0, "Depósito Central") # Ubicación.

    _buscar_boton_por_texto(win_stock, "Guardar Producto").invoke()

    tabla_stock = _buscar_treeview(win_stock)
    assert len(tabla_stock.get_children()) == 1
    id_fila_prod = tabla_stock.get_children()[0]
    assert tabla_stock.item(id_fila_prod, "values")[0] == "MON-24-FHD"
    assert float(tabla_stock.item(id_fila_prod, "values")[4]) == 20.0

    # 4. Seleccionamos el producto, modificamos su stock a 30 y su precio de venta a 165000.
    tabla_stock.selection_set(id_fila_prod)
    win_stock.nametowidget(tabla_stock).event_generate("<<TreeviewSelect>>")
    cajas_stock[3].delete(0, tk.END)
    cajas_stock[3].insert(0, "30")
    cajas_stock[6].delete(0, tk.END)
    cajas_stock[6].insert(0, "165000")

    _buscar_boton_por_texto(win_stock, "Modificar Producto").invoke()
    assert float(tabla_stock.item(id_fila_prod, "values")[4]) == 30.0
    assert float(tabla_stock.item(id_fila_prod, "values")[7]) == 165000.0

    win_prov.destroy()
    win_stock.destroy()

def test_4_visibilidad_vendedor_bi_semilla_y_alta_rrhh_clientes(entorno_gui):
    """
     Verifica que tanto un empleado creado desde RRHH ('empleados.py') como el
     'vendedor_bi' de la semilla aparezcan disponibles en la ventana de Facturación.
    """
    root = entorno_gui["root"]
    ruta_db = entorno_gui["ruta_db"]

    # 1. Simulamos la inserción de 'vendedor_bi' con el rol 'EMPLEADO' tal como en la semilla BI.
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO roles (rol) VALUES ('EMPLEADO')")
    id_rol_semilla = cursor.lastrowid
    cursor.execute('''
        INSERT INTO usuarios (id, nombres, apellidos, dni, usuario, password, habilitado)
        VALUES (888, 'Vendedor', 'BI', '88888888', 'vendedor_bi', 'hash', 1)
    ''')
    cursor.execute("INSERT INTO usuxroles (id_usuario, id_rol) VALUES (888, ?)", (id_rol_semilla,))
    conexion.commit()
    conexion.close()

    # 2. Damos de alta un vendedor adicional desde la ventana de RRHH (empleados.py).
    win_emp = mod_empleados.Empleado(root, id_actual=1, rol_actual="Administrador")
    cajas_emp = [w for w in _buscar_widgets(win_emp, tk.Entry) if not isinstance(w, ttk.Combobox)]
    combo_rol_emp = _buscar_widgets(win_emp, ttk.Combobox)[0]

    cajas_emp[0].insert(0, "Martín")
    cajas_emp[1].insert(0, "Palermo")
    cajas_emp[2].insert(0, "22333444")
    combo_rol_emp.set("Empleado - Ventas")
    _buscar_boton_por_texto(win_emp, "Guardar Perfil").invoke()

    # 3. Damos de alta un cliente desde la ventana de Clientes (clientes.py).
    win_cli = mod_clientes.Cliente(root)
    cajas_cli = [w for w in _buscar_widgets(win_cli, tk.Entry) if not isinstance(w, ttk.Combobox)]
    cajas_cli[0].insert(0, "Ana")
    cajas_cli[1].insert(0, "belleza")
    cajas_cli[2].insert(0, "33444555")
    _buscar_boton_por_texto(win_cli, "Guardar Cliente").invoke()

    # 4. Abrimos Facturación y comprobamos que ambos vendedores y el cliente estén en los Combobox.
    win_fac = mod_facturacion.Facturacion(root)
    combos_fac = _buscar_widgets(win_fac, ttk.Combobox)
    vendedores_disponibles = combos_fac[0]["values"]
    clientes_disponibles = combos_fac[1]["values"]

    assert any("Vendedor BI" in v for v in vendedores_disponibles), "No apareció vendedor_bi en Facturación."
    assert any("Martín Palermo" in v for v in vendedores_disponibles), "No apareció el empleado de RRHH."
    assert any("Ana belleza" in c for c in clientes_disponibles), "No apareció el cliente registrado."

    win_emp.destroy()
    win_cli.destroy()
    win_fac.destroy()

def test_5_flujo_gui_facturacion_y_analitica_bi_completo(entorno_gui):
    """
     Prueba el circuito comercial completo desde las ventanas:
     Emisión de factura en 'facturacion.py' -> Descuento de stock -> Visualización
     de KPIs y gráficos en 'analitica.py' -> Anulación y restitución de inventario.
    """
    root = entorno_gui["root"]

    # 1. Preparamos los datos base mediante el cliente HTTP (Proveedor, Vendedor, Cliente y Producto).
    id_prov = cliente_http.crear_perfil({"nombres": "Prov", "apellidos": "SA", "dni": "1", "rol": "Proveedor"})["id"]
    id_vend = cliente_http.crear_perfil({"nombres": "Vend", "apellidos": "Uno", "dni": "2", "rol": "Empleado - Ventas"})["id"]
    id_cli = cliente_http.crear_perfil({"nombres": "Cli", "apellidos": "Final", "dni": "3", "rol": "Cliente"})["id"]
    id_prod = cliente_http.crear_producto({
        "codigo": "SSD-1TB",
        "descripcion": "Disco SSD 1TB NVMe",
        "categoria": "Almacenamiento",
        "id_proveedor": id_prov,
        "precio_costo": 50000.0,
        "precio_venta": 80000.0,
        "stock_actual": 10.0,
        "stock_minimo": 2.0
    })["id"]

    # 2. Abrimos la ventana de Facturación y emitimos una venta de 3 unidades con 10% de descuento.
    win_fac = mod_facturacion.Facturacion(root)
    combos_fac = _buscar_widgets(win_fac, ttk.Combobox)
    cajas_fac = [w for w in _buscar_widgets(win_fac, tk.Entry) if not isinstance(w, ttk.Combobox)]

    combos_fac[0].set(f"Vend Uno (ID: {id_vend})")
    combos_fac[1].set(f"Cli Final (ID: {id_cli})")
    combos_fac[2].set("SSD-1TB - Disco SSD 1TB NVMe")
    combos_fac[2].event_generate("<<ComboboxSelected>>")

    cajas_fac[0].insert(0, "3")   # Cantidad: 3
    cajas_fac[2].insert(0, "10")  # Descuento: 10%

    _buscar_boton_por_texto(win_fac, "Guardar Facturación").invoke()

    tabla_fac = _buscar_treeview(win_fac)
    assert len(tabla_fac.get_children()) == 1
    id_factura_emitida = tabla_fac.get_children()[0]
    # Total esperado: (3 * 80000) * 0.90 = 216000.0
    assert float(tabla_fac.item(id_factura_emitida, "values")[4]) == 216000.0

    # Verificamos que el stock físico bajó de 10 a 7 unidades.
    assert cliente_http.obtener_producto(id_prod)["stock_actual"] == 7.0

    # 3. Abrimos el Tablero de Analítica BI (analitica.py) y verificamos KPIs y DataFrame.
    win_bi = mod_analitica.AnaliticaBI(root)
    assert not win_bi.df.empty
    assert win_bi.indicadores["Facturación Total"].cget("text") == "$ 216,000.00"
    assert win_bi.indicadores["Operaciones"].cget("text") == "1"
    assert win_bi.indicadores["Unidades Vendidas"].cget("text") == "3"
    assert len(win_bi.tabla.get_children()) == 1
    win_bi.cerrar_ventana()

    # 4. Seleccionamos la factura en Facturación y la eliminamos (anulación), verificando restitución de stock.
    tabla_fac.selection_set(id_factura_emitida)
    _buscar_boton_por_texto(win_fac, "Eliminar Facturación").invoke()
    assert len(tabla_fac.get_children()) == 0
    assert cliente_http.obtener_producto(id_prod)["stock_actual"] == 10.0

    win_fac.destroy()

def test_6_consola_sql_bloquea_escritura_y_permite_lectura_select(entorno_gui):
    """
     Verifica que la Consola SQL de auditoría ('consola.py') bloquee cualquier
     intento destructivo (Sandboxing Regex) y ejecute correctamente consultas SELECT.
    """
    root = entorno_gui["root"]
    win_consola = mod_consola.ConsolaSQL(root)

    caja_query = _buscar_widgets(win_consola, tk.Text)[0]
    btn_ejecutar = _buscar_boton_por_texto(win_consola, "Ejecutar Consulta")
    tabla_sql = _buscar_treeview(win_consola)

    # 1. Intento de inyección destructiva (DELETE).
    caja_query.insert("1.0", "DELETE FROM usuarios WHERE id = 1;")
    btn_ejecutar.invoke()
    assert len(entorno_gui["alertas"]["error"]) == 1
    assert "Solo Lectura" in entorno_gui["alertas"]["error"][0][1]

    # 2. Consulta SELECT legítima de auditoría.
    caja_query.delete("1.0", tk.END)
    caja_query.insert("1.0", "SELECT usuario, nombres, apellidos FROM usuarios WHERE habilitado = 1")
    btn_ejecutar.invoke()

    filas_recuperadas = tabla_sql.get_children()
    assert len(filas_recuperadas) >= 1
    valores_primera_fila = tabla_sql.item(filas_recuperadas[0], "values")
    assert valores_primera_fila[0] == "admin"

    win_consola.destroy()

def test_7_bloqueo_baja_ultimo_admin_desde_gui_usuarios(entorno_gui):
    """
     Verifica que si desde la ventana de Usuarios se intenta eliminar al único
     Administrador activo, el Trigger de SQLite ('trg_proteger_ultimo_admin')
     aborte la operación y la ventana muestre el alerta sin borrar al usuario.
    """
    root = entorno_gui["root"]
    win_usuarios = mod_usuarios.Usuario(root, id_actual=1, rol_actual="Administrador")
    tabla = _buscar_treeview(win_usuarios)

    # Seleccionamos al único Administrador (ID "1") e invocamos el botón "Eliminar".
    tabla.selection_set("1")
    _buscar_boton_por_texto(win_usuarios, "Eliminar").invoke()

    # Debe haberse disparado un messagebox.showerror y el Admin debe seguir en la tabla.
    assert len(entorno_gui["alertas"]["error"]) == 1
    assert "1" in tabla.get_children()

    win_usuarios.destroy()