import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import bcrypt



# =======================================================================
#  ANCLAJE DE DIRECTORIO Y BASE DE DATOS (REFACTORIZACIÓN DE ESTRUCTURA)
# =======================================================================

# CAMBIO: Como login.py ahora vive dentro de la carpeta "vistas", necesitamos retroceder un nivel en el árbol de 
# directorios para encontrar la carpeta "db".

DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_VISTAS)

CARPETA_DB = os.path.join(DIRECTORIO_RAIZ, "db")
os.makedirs(CARPETA_DB, exist_ok=True)

DB_PATH = os.path.join(CARPETA_DB, "frankie_gestor.db")
ESQUEMA_PATH = os.path.join(CARPETA_DB, "esquema.sql")

def inicializar_seguridad():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    


    # ======================================================
    #  FASE 1: CONSTRUCCIÓN DEL MOTOR RELACIONAL VÍA SCRIPT
    # ======================================================

    # CAMBIO: Se elimina todo el DDL hardcodeado en Python. 
    # El sistema ahora lee y ejecuta el archivo 'esquema.sql' completo, lo que garantiza que todas las tablas 
    # y triggers se creen en el orden jerárquico correcto.

    if os.path.exists(ESQUEMA_PATH):
        with open(ESQUEMA_PATH, 'r', encoding='utf-8') as archivo_sql:
            script_sql = archivo_sql.read()

            # executescript permite correr múltiples sentencias SQL de un tirón.
            cursor.executescript(script_sql)
    else:
        messagebox.showerror("Error Crítico", "No se encontró 'esquema.sql' en la carpeta db. El sistema no puede inicializarse.")
        return
    


    # =========================================================
    #  FASE 2: SIEMBRA DE DATOS MAESTROS (SEEDING NORMALIZADO)
    # =========================================================

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        
        # 1. Al no existir más la columna 'rol' en usuarios, primero debemos poblar el catálogo maestro de roles 
        # y capturar su ID generado.
        cursor.execute("INSERT INTO roles (rol) VALUES ('Administrador')")
        id_rol_admin = cursor.lastrowid

        # 2. Generación del hash criptográfico para el usuario matriz.
        password_plana = "admin123".encode('utf-8')
        sal = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_plana, sal).decode('utf-8')
        
        # 3. Inserción en la tabla central de usuarios (notar que ya no se pasa el rol acá).
        cursor.execute('''
            INSERT INTO usuarios (usuario, password, nombres, apellidos, dni) 
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'David Hernan', 'Bravo', '00000000'))
        id_usuario_admin = cursor.lastrowid

        # 4. Inserción en la tabla puente (usuxroles) conectando al usuario con su rol.
        cursor.execute('''
            INSERT INTO usuxroles (id_usuario, id_rol)
            VALUES (?, ?)
        ''', (id_usuario_admin, id_rol_admin))
    
    conexion.commit()
    conexion.close()

# Ejecutamos la inicialización al arrancar.
inicializar_seguridad()



# =====================================
#  CREACIÓN DE LA VENTANA RAÍZ "LOGIN"
# =====================================

ventana = tk.Tk()
ventana.title("FRANKIE GESTOR - ACCESO AL SISTEMA")
ventana.geometry("400x250")
ventana.eval('tk::PlaceWindow . center')
ventana.resizable(False, False)



# ===============================================
#  INYECCIÓN GLOBAL DE EVENTOS (USABILIDAD Y UX)
# ===============================================

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



# =======================================
#  FUNCIONALIDADES Y VALIDACIÓN DE LOGIN
# =======================================

intentos_fallidos = 0

def validar_ingreso():
    global intentos_fallidos
    
    usuario_ingresado = caja_usuario.get()
    password_ingresada = caja_password.get().encode('utf-8')
    
    if not usuario_ingresado or not password_ingresada:
        messagebox.showwarning("Validación", "Completá todos los campos.")
        return
        
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    


    # ===============================================================================
    #  FALLA DE SEGURIDAD CORREGIDA: PREVENCIÓN DE INGRESO DE USUARIOS DADOS DE BAJA
    # ===============================================================================

    # CAMBIO: Como la cátedra implementó Bajas Lógicas, si un usuario fue "eliminado" (habilitado = 0), no debe poder 
    # loguearse. Además, la consulta ahora requiere operaciones JOIN para ir a buscar el rol a las tablas maestras.
    
    cursor.execute('''
        SELECT u.password, r.rol, u.nombres, u.apellidos 
        FROM usuarios u
        JOIN usuxroles ur ON u.id = ur.id_usuario
        JOIN roles r ON ur.id_rol = r.id
        WHERE u.usuario = ? 
          AND u.habilitado = 1 
          AND ur.habilitado = 1
    ''', (usuario_ingresado,))
    
    resultado = cursor.fetchone()
    conexion.close()
    
    if resultado and bcrypt.checkpw(password_ingresada, resultado[0].encode('utf-8')):
        rol_usuario = resultado[1]
        nombres_usuario = resultado[2]
        apellidos_usuario = resultado[3]

        messagebox.showinfo("Acceso Concedido", f"Bienvenido/a, {nombres_usuario} {apellidos_usuario}.\nRol: {rol_usuario}")

        caja_usuario.delete(0, tk.END)
        caja_password.delete(0, tk.END)
        caja_usuario.focus_set()
        
        ventana.withdraw()
        
        # Invocamos el panel (que también deberá adaptarse a la nueva estructura de carpetas).
        from panel_control import PanelControl
        PanelControl(ventana, rol_usuario, nombres_usuario, apellidos_usuario)
    else:
        intentos_fallidos += 1
        intentos_restantes = 3 - intentos_fallidos
        
        caja_usuario.delete(0, tk.END)
        caja_password.delete(0, tk.END)
        caja_usuario.focus_set()
        
        if intentos_restantes > 0:
            messagebox.showerror("Error de Autenticación", f"Credenciales incorrectas o usuario deshabilitado.\nIntentos restantes: {intentos_restantes}")
        else:
            messagebox.showerror("Bloqueo de Seguridad", "Superaste el límite de intentos fallidos. El sistema se cerrará.")
            ventana.destroy()



# ===================
#  INTERFAZ DE LOGIN
# ===================

tk.Label(ventana, text="SISTEMA DE GESTIÓN", font=("Arial", 12, "bold")).pack(pady=15)

tk.Label(ventana, text="Usuario:").pack()
caja_usuario = tk.Entry(ventana, width=30)
caja_usuario.pack(pady=5)

tk.Label(ventana, text="Contraseña:").pack()
caja_password = tk.Entry(ventana, width=30, show="*")
caja_password.pack(pady=5)

boton_ingresar = tk.Button(ventana, text="Ingresar al Sistema", command=validar_ingreso, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
boton_ingresar.pack(pady=20)

ventana.bind('<Return>', lambda event: validar_ingreso())

ventana.mainloop()