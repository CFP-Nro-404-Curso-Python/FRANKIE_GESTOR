import os
import sys
import time
import socket
import subprocess
import atexit
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk


# =======================================================
#  1. ANCLAJE DE DIRECTORIOS E INYECCIÓN DE RUTAS (PATH)
# =======================================================

DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_ESCRITORIO = os.path.dirname(DIRECTORIO_VISTAS)
DIRECTORIO_PRESENTACION = os.path.dirname(DIRECTORIO_ESCRITORIO)
DIRECTORIO_SRC = os.path.dirname(DIRECTORIO_PRESENTACION)
DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_SRC)

for ruta in (DIRECTORIO_RAIZ, DIRECTORIO_ESCRITORIO, DIRECTORIO_VISTAS):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

from src.presentacion.escritorio.cliente_api import cliente_http, ErrorClienteAPI, gestor_ui
from src.infraestructura.persistencia.gestor_sqlite import GestorSQLite
from src.infraestructura.seguridad.adaptador_bcrypt import AdaptadorBcrypt

CARPETA_DB = os.path.join(DIRECTORIO_RAIZ, "db")
os.makedirs(CARPETA_DB, exist_ok=True)

DB_PATH = os.path.join(CARPETA_DB, "frankie_gestor.db")
ESQUEMA_PATH = os.path.join(CARPETA_DB, "esquema.sql")

DIRECTORIO_WEB = os.path.join(DIRECTORIO_PRESENTACION, "web")
os.makedirs(DIRECTORIO_WEB, exist_ok=True)


# =============================================================
#  2. AUTO-INICIALIZACIÓN DE BASE DE DATOS Y SERVIDORES EN RED
# =============================================================

procesos_activos = []


def _puerto_en_uso(puerto: int) -> bool:
    """Verifica si un puerto TCP local ya está ocupado por un servidor activo."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", puerto)) == 0


def _detener_servidores():
    """Cierra limpiamente los subprocesos al salir de la aplicación de escritorio."""
    for proc in procesos_activos:
        if proc.poll() is None:
            proc.terminate()


atexit.register(_detener_servidores)


def inicializar_seguridad_y_servicios():
    """
     Garantiza que la base de datos exista usando los adaptadores del Backend,
     y levanta automáticamente FastAPI (8000) y el servidor Web LAN (8080).
    """
    if not os.path.exists(ESQUEMA_PATH):
        messagebox.showerror("Error Crítico", f"No se encontró el archivo de estructura:\n{ESQUEMA_PATH}")
        return

    with GestorSQLite(DB_PATH) as uow:
        cursor = uow.conexion.cursor()

        with open(ESQUEMA_PATH, "r", encoding="utf-8") as archivo_sql:
            cursor.executescript(archivo_sql.read())

        cursor.execute("SELECT COUNT(*) FROM roles")
        if cursor.fetchone()[0] == 0:
            roles_basicos = [
                ("Administrador",), ("Gerente",),
                ("Empleado - Ventas",), ("Empleado - Compras",),
                ("Proveedor",), ("Cliente",)
            ]
            cursor.executemany("INSERT INTO roles (rol) VALUES (?)", roles_basicos)

        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            hasher = AdaptadorBcrypt()
            password_hash = hasher.hashear_password("admin123")

            cursor.execute('''
                INSERT INTO usuarios (usuario, password, nombres, apellidos, dni, habilitado)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', ("admin", password_hash, "David Hernan", "Bravo", "00000000"))

            id_nuevo_admin = cursor.lastrowid
            cursor.execute("SELECT id FROM roles WHERE rol = 'Administrador'")
            id_rol_admin = cursor.fetchone()[0]

            cursor.execute('''
                INSERT INTO usuxroles (id_usuario, id_rol, habilitado) VALUES (?, ?, 1)
            ''', (id_nuevo_admin, id_rol_admin))

    if not _puerto_en_uso(8000):
        proc_api = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.infraestructura.api.servidor:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=DIRECTORIO_RAIZ,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        procesos_activos.append(proc_api)

        for _ in range(25):
            if cliente_http.verificar_servidor_activo():
                break
            time.sleep(0.2)

    if not _puerto_en_uso(8080):
        proc_web = subprocess.Popen(
            [sys.executable, "-m", "http.server", "8080", "--bind", "0.0.0.0", "--directory", DIRECTORIO_WEB],
            cwd=DIRECTORIO_RAIZ,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        procesos_activos.append(proc_web)


inicializar_seguridad_y_servicios()


# ===================================
#  3. CREACIÓN DE LA VENTANA "LOGIN"
# ===================================

ctk.set_appearance_mode(gestor_ui.tema)
ctk.set_default_color_theme("blue")

ventana = ctk.CTk()
ventana.title(gestor_ui.t("login_win"))
ventana.resizable(False, False)

ANCHO_WIN, ALTO_WIN = 460, 470
pos_x = max((ventana.winfo_screenwidth() - ANCHO_WIN) // 2, 0)
pos_y = max((ventana.winfo_screenheight() - ALTO_WIN) // 2, 0)
ventana.geometry(f"{ANCHO_WIN}x{ALTO_WIN}+{pos_x}+{pos_y}")


# ================================================
#  4. INYECCIÓN GLOBAL DE EVENTOS (USABILIDAD UX)
# ================================================

menu_contextual = tk.Menu(ventana, tearoff=0)
menu_contextual.add_command(label="Copiar", command=lambda: ventana.focus_get().event_generate("<<Copy>>"))
menu_contextual.add_command(label="Cortar", command=lambda: ventana.focus_get().event_generate("<<Cut>>"))
menu_contextual.add_command(label="Pegar", command=lambda: ventana.focus_get().event_generate("<<Paste>>"))
menu_contextual.add_separator()
menu_contextual.add_command(label="Seleccionar Todo", command=lambda: ventana.focus_get().event_generate("<<SelectAll>>"))


def desplegar_menu(event):
    if isinstance(event.widget, (tk.Entry, tk.Text, ttk.Combobox)):
        event.widget.focus_set()
        menu_contextual.tk_popup(event.x_root, event.y_root)


for clase in ("Entry", "TCombobox", "Text"):
    ventana.bind_class(clase, "<Button-3>", desplegar_menu)


def forzar_atajo(evento, evento_virtual):
    evento.widget.event_generate(evento_virtual)
    return "break"


atajos_globales = {
    "<Control-c>": "<<Copy>>", "<Control-C>": "<<Copy>>",
    "<Control-x>": "<<Cut>>", "<Control-X>": "<<Cut>>",
    "<Control-v>": "<<Paste>>", "<Control-V>": "<<Paste>>",
    "<Control-a>": "<<SelectAll>>", "<Control-A>": "<<SelectAll>>"
}

for clase in ("Entry", "TCombobox", "Text"):
    for combinacion_teclas, accion_virtual in atajos_globales.items():
        ventana.bind_class(clase, combinacion_teclas, lambda e, ev=accion_virtual: forzar_atajo(e, ev))


# ================================================
#  5. VALIDACIÓN DE LOGIN CONSUMIENDO LA API REST
# ================================================

intentos_fallidos = 0


def validar_ingreso():
    """Envía el usuario y contraseña al endpoint /api/perfiles/login."""
    global intentos_fallidos

    usuario_ingresado = caja_usuario.get().strip()
    password_ingresada = caja_password.get()

    if not usuario_ingresado or not password_ingresada:
        messagebox.showwarning(gestor_ui.t("val_tit"), gestor_ui.t("login_completar"))
        return

    try:
        datos_perfil = cliente_http.iniciar_sesion(usuario_ingresado, password_ingresada)

        intentos_fallidos = 0
        lbl_intentos.configure(
            text=gestor_ui.t("login_intentos", n=3),
            text_color=gestor_ui.paleta()["fg_muted"]
        )

        id_usuario = datos_perfil["id"]
        rol_usuario = datos_perfil["rol"]
        nombres_usuario = datos_perfil["nombres"]
        apellidos_usuario = datos_perfil["apellidos"]

        messagebox.showinfo(
            gestor_ui.t("login_ok_tit"),
            gestor_ui.t(
                "login_ok_msg",
                nombre=nombres_usuario,
                apellido=apellidos_usuario,
                rol=gestor_ui.rol_a_ui(rol_usuario)
            )
        )

        caja_usuario.delete(0, "end")
        caja_password.delete(0, "end")
        caja_usuario.focus_set()

        ventana.withdraw()

        from panel_control import PanelControl
        PanelControl(ventana, id_usuario, rol_usuario, nombres_usuario, apellidos_usuario)

    except ErrorClienteAPI:
        intentos_fallidos += 1
        intentos_restantes = 3 - intentos_fallidos

        caja_usuario.delete(0, "end")
        caja_password.delete(0, "end")
        caja_usuario.focus_set()

        if intentos_restantes > 0:
            lbl_intentos.configure(
                text=gestor_ui.t("login_intentos", n=intentos_restantes),
                text_color="#DC2626"
            )
            messagebox.showerror(
                gestor_ui.t("login_err_tit"),
                gestor_ui.t("login_err_msg", n=intentos_restantes)
            )
        else:
            lbl_intentos.configure(text=gestor_ui.t("login_bloqueado"), text_color="#DC2626")
            messagebox.showerror(gestor_ui.t("login_bloq_tit"), gestor_ui.t("login_bloq_msg"))
            ventana.destroy()


# ==============================
#  6. INTERFAZ GRÁFICA DE LOGIN
# ==============================

barra_top = ctk.CTkFrame(ventana, corner_radius=0, height=44)
barra_top.pack(fill="x")
barra_top.pack_propagate(False)

lbl_marca_top = ctk.CTkLabel(barra_top, text="FRANKIE GESTOR", anchor="w")
lbl_marca_top.pack(side="left", padx=14)

botones_pref = gestor_ui.crear_barra_preferencias(barra_top)

tarjeta = ctk.CTkFrame(ventana, corner_radius=14)
tarjeta.pack(fill="both", expand=True, padx=24, pady=20)

lbl_titulo = ctk.CTkLabel(tarjeta, text=gestor_ui.t("app_titulo"))
lbl_titulo.pack(pady=(22, 2))

lbl_subtitulo = ctk.CTkLabel(tarjeta, text=gestor_ui.t("app_subtitulo"))
lbl_subtitulo.pack(pady=(0, 18))

contenedor_campos = ctk.CTkFrame(tarjeta, fg_color="transparent")
contenedor_campos.pack(fill="x", padx=28)

lbl_usu = ctk.CTkLabel(contenedor_campos, text=gestor_ui.t("login_usu"), anchor="w")
lbl_usu.pack(fill="x", pady=(0, 4))

caja_usuario = ctk.CTkEntry(
    contenedor_campos,
    height=38,
    corner_radius=8,
    placeholder_text=gestor_ui.t("login_usu_ph")
)
caja_usuario.pack(fill="x", pady=(0, 14))
caja_usuario.focus_set()

lbl_pass = ctk.CTkLabel(contenedor_campos, text=gestor_ui.t("login_pass"), anchor="w")
lbl_pass.pack(fill="x", pady=(0, 4))

caja_password = ctk.CTkEntry(
    contenedor_campos,
    height=38,
    corner_radius=8,
    placeholder_text="••••••••",
    show="*"
)
caja_password.pack(fill="x", pady=(0, 18))

boton_ingresar = ctk.CTkButton(
    contenedor_campos,
    text=gestor_ui.t("login_btn"),
    command=validar_ingreso,
    height=40,
    corner_radius=8,
    fg_color="#16A34A",
    hover_color="#15803D"
)
boton_ingresar.pack(fill="x")

lbl_intentos = ctk.CTkLabel(tarjeta, text=gestor_ui.t("login_intentos", n=3))
lbl_intentos.pack(pady=(14, 10))


def _aplicar_ui_login():
    p = gestor_ui.paleta()
    ventana.title(gestor_ui.t("login_win"))
    ventana.configure(fg_color=p["bg_app"])
    barra_top.configure(fg_color=p["bg_header"])
    lbl_marca_top.configure(text_color=p["fg_header"], font=gestor_ui.fuente(12, "bold"))
    gestor_ui.actualizar_barra_preferencias(botones_pref)

    tarjeta.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])
    lbl_titulo.configure(text=gestor_ui.t("app_titulo"), text_color=p["fg_text"], font=gestor_ui.fuente(20, "bold"))
    lbl_subtitulo.configure(text=gestor_ui.t("app_subtitulo"), text_color=p["fg_muted"], font=gestor_ui.fuente(11))
    lbl_usu.configure(text=gestor_ui.t("login_usu"), text_color=p["fg_label"], font=gestor_ui.fuente(12, "bold"))
    lbl_pass.configure(text=gestor_ui.t("login_pass"), text_color=p["fg_label"], font=gestor_ui.fuente(12, "bold"))

    gestor_ui.estilizar_entry(caja_usuario)
    gestor_ui.estilizar_entry(caja_password)
    if not caja_usuario.get():
        caja_usuario.configure(placeholder_text=gestor_ui.t("login_usu_ph"))

    boton_ingresar.configure(text=gestor_ui.t("login_btn"), font=gestor_ui.fuente(13, "bold"))

    restantes = 3 - intentos_fallidos
    if restantes > 0:
        lbl_intentos.configure(
            text=gestor_ui.t("login_intentos", n=restantes),
            text_color="#DC2626" if intentos_fallidos > 0 else p["fg_muted"],
            font=gestor_ui.fuente(11)
        )
    else:
        lbl_intentos.configure(text=gestor_ui.t("login_bloqueado"), text_color="#DC2626", font=gestor_ui.fuente(11))


gestor_ui.suscribir(ventana, _aplicar_ui_login)
_aplicar_ui_login()

ventana.bind("<Return>", lambda event: validar_ingreso())

ventana.mainloop()