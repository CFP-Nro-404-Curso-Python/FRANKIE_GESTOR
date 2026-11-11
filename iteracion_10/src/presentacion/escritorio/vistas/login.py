import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import time
import socket
import subprocess
import atexit



# =======================================================
#  1. ANCLAJE DE DIRECTORIOS E INYECCIÓN DE RUTAS (PATH)
# =======================================================

# Calculamos las rutas subiendo desde src/presentacion/escritorio/vistas/ hasta la raíz del proyecto.
DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_ESCRITORIO = os.path.dirname(DIRECTORIO_VISTAS)
DIRECTORIO_PRESENTACION = os.path.dirname(DIRECTORIO_ESCRITORIO)
DIRECTORIO_SRC = os.path.dirname(DIRECTORIO_PRESENTACION)
DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_SRC)

# Agregamos las carpetas clave al path de Python para que los imports funcionen desde cualquier consola.
for ruta in (DIRECTORIO_RAIZ, DIRECTORIO_ESCRITORIO, DIRECTORIO_VISTAS):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

from src.presentacion.escritorio.cliente_api import cliente_http, ErrorClienteAPI
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
     Garantiza que la base de datos exista (con o sin semillas previas) usando los 
     adaptadores del Backend, y levanta automáticamente la API REST (puerto 8000) 
     y el servidor Web para la red local (puerto 8080).
    """
    # 1. Verificación e inicialización de la base de datos a través de la Unidad de Trabajo.
    if not os.path.exists(ESQUEMA_PATH):
        messagebox.showerror("Error Crítico", f"No se encontró el archivo de estructura:\n{ESQUEMA_PATH}")
        return

    with GestorSQLite(DB_PATH) as uow:
        cursor = uow.conexion.cursor()
        
        # Ejecutamos el esquema DDL (crea tablas, vistas y triggers si no existen).
        with open(ESQUEMA_PATH, "r", encoding="utf-8") as archivo_sql:
            cursor.executescript(archivo_sql.read())

        # Si la tabla de roles está vacía, cargamos los roles básicos del sistema.
        cursor.execute("SELECT COUNT(*) FROM roles")
        if cursor.fetchone()[0] == 0:
            roles_basicos = [
                ("Administrador",), ("Gerente",),
                ("Empleado - Ventas",), ("Empleado - Compras",),
                ("Proveedor",), ("Cliente",)
            ]
            cursor.executemany("INSERT INTO roles (rol) VALUES (?)", roles_basicos)

        # Si no hay usuarios (ejecución sin semillas), creamos el Administrador por defecto.
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

    # 2. Arranque automático del servidor FastAPI en 0.0.0.0:8000 (accesible en LAN).
    if not _puerto_en_uso(8000):
        proc_api = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.infraestructura.api.servidor:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=DIRECTORIO_RAIZ,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        procesos_activos.append(proc_api)

        # Esperamos brevemente a que FastAPI termine de levantar antes de habilitar el login.
        for _ in range(25):
            if cliente_http.verificar_servidor_activo():
                break
            time.sleep(0.2)

    # 3. Arranque automático del servidor Web en 0.0.0.0:8080 para dispositivos de la red local.
    if not _puerto_en_uso(8080):
        proc_web = subprocess.Popen(
            [sys.executable, "-m", "http.server", "8080", "--bind", "0.0.0.0", "--directory", DIRECTORIO_WEB],
            cwd=DIRECTORIO_RAIZ,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        procesos_activos.append(proc_web)

# Ejecutamos la preparación del entorno al arrancar.
inicializar_seguridad_y_servicios()



# ===================================
#  3. CREACIÓN DE LA VENTANA "LOGIN"
# ===================================

ventana = tk.Tk()
ventana.title("FRANKIE GESTOR - ACCESO AL SISTEMA")
ventana.geometry("400x250")
ventana.eval('tk::PlaceWindow . center')
ventana.resizable(False, False)



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

ventana.bind_class("Entry", "<Button-3>", desplegar_menu)
ventana.bind_class("TCombobox", "<Button-3>", desplegar_menu)
ventana.bind_class("Text", "<Button-3>", desplegar_menu)

def forzar_atajo(evento, evento_virtual):
    evento.widget.event_generate(evento_virtual)
    return "break"

atajos_globales = {
    "<Control-c>": "<<Copy>>", "<Control-C>": "<<Copy>>",
    "<Control-x>": "<<Cut>>", "<Control-X>": "<<Cut>>",
    "<Control-v>": "<<Paste>>", "<Control-V>": "<<Paste>>",
    "<Control-a>": "<<SelectAll>>", "<Control-A>": "<<SelectAll>>"
}

for clase in ["Entry", "TCombobox", "Text"]:
    for combinacion_teclas, accion_virtual in atajos_globales.items():
        ventana.bind_class(clase, combinacion_teclas, lambda e, ev=accion_virtual: forzar_atajo(e, ev))



# ================================================
#  5. VALIDACIÓN DE LOGIN CONSUMIENDO LA API REST
# ================================================

intentos_fallidos = 0

def validar_ingreso():
    """
     Envía el usuario y contraseña al endpoint /api/perfiles/login a través de cliente_http.
     No toca la base de datos ni desencripta claves localmente.
    """
    global intentos_fallidos
    
    usuario_ingresado = caja_usuario.get().strip()
    password_ingresada = caja_password.get()
    
    if not usuario_ingresado or not password_ingresada:
        messagebox.showwarning("Validación", "Completá todos los campos.")
        return

    try:
        # Petición HTTP POST al Backend para autenticar credenciales.
        datos_perfil = cliente_http.iniciar_sesion(usuario_ingresado, password_ingresada)
        
        intentos_fallidos = 0
        id_usuario = datos_perfil["id"]
        rol_usuario = datos_perfil["rol"]
        nombres_usuario = datos_perfil["nombres"]
        apellidos_usuario = datos_perfil["apellidos"]

        messagebox.showinfo("Acceso Concedido", f"Bienvenido/a, {nombres_usuario} {apellidos_usuario}.\nRol: {rol_usuario}")

        caja_usuario.delete(0, tk.END)
        caja_password.delete(0, tk.END)
        caja_usuario.focus_set()
        
        ventana.withdraw()
        
        from panel_control import PanelControl
        PanelControl(ventana, id_usuario, rol_usuario, nombres_usuario, apellidos_usuario)

    except ErrorClienteAPI:
        intentos_fallidos += 1
        intentos_restantes = 3 - intentos_fallidos
        
        caja_usuario.delete(0, tk.END)
        caja_password.delete(0, tk.END)
        caja_usuario.focus_set()
        
        if intentos_restantes > 0:
            messagebox.showerror(
                "Error de Autenticación",
                f"Credenciales incorrectas o usuario inhabilitado. Intentos restantes: {intentos_restantes}"
            )
        else:
            messagebox.showerror(
                "Bloqueo de Seguridad",
                "Superaste el límite de intentos fallidos. El sistema se cerrará."
            )
            ventana.destroy()



# ==============================
#  6. INTERFAZ GRÁFICA DE LOGIN
# ==============================

tk.Label(ventana, text="SISTEMA DE GESTIÓN", font=("Arial", 12, "bold")).pack(pady=15)

tk.Label(ventana, text="Usuario:").pack()
caja_usuario = tk.Entry(ventana, width=30)
caja_usuario.pack(pady=5)
caja_usuario.focus_set()

tk.Label(ventana, text="Contraseña:").pack()
caja_password = tk.Entry(ventana, width=30, show="*")
caja_password.pack(pady=5)

boton_ingresar = tk.Button(
    ventana,
    text="Ingresar al Sistema",
    command=validar_ingreso,
    bg="#4CAF50",
    fg="white",
    font=("Arial", 10, "bold")
)
boton_ingresar.pack(pady=20)

ventana.bind('<Return>', lambda event: validar_ingreso())

ventana.mainloop()