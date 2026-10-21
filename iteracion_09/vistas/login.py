import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import bcrypt



# ======================================================
#  ANCLAJE DE DIRECTORIOS (ADAPTADO A NUEVA ESTRUCTURA)
# ======================================================

# login.py ahora está dentro de /vistas, por lo que el directorio raíz está un nivel arriba.
DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_VISTAS)
CARPETA_DB = os.path.join(DIRECTORIO_RAIZ, "db")
os.makedirs(CARPETA_DB, exist_ok=True)

DB_PATH = os.path.join(CARPETA_DB, "frankie_gestor.db")
ESQUEMA_PATH = os.path.join(CARPETA_DB, "esquema.sql")

def inicializar_seguridad():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    # 1. EJECUCIÓN DEL DDL EXTERNO (esquema.sql)
    # Se delega la creación de tablas al script de SQLite garantizando normalización extrema.
    if os.path.exists(ESQUEMA_PATH):
        with open(ESQUEMA_PATH, 'r', encoding='utf-8') as archivo_sql:
            script = archivo_sql.read()
            cursor.executescript(script)
    else:
        messagebox.showerror("Error Crítico", f"No se encontró el archivo de estructura:\n{ESQUEMA_PATH}")
        conexion.close()
        return
        
    # 2. INYECCIÓN DE CATÁLOGO DE ROLES (Si la base está vacía)
    cursor.execute("SELECT COUNT(*) FROM roles")
    if cursor.fetchone()[0] == 0:
        roles_basicos = [
            ('Administrador',), ('Gerente',), 
            ('Empleado - Ventas',), ('Empleado - Compras',), 
            ('Proveedor',), ('Cliente',)
        ]
        cursor.executemany("INSERT INTO roles (rol) VALUES (?)", roles_basicos)
    
    # 3. SEMILLA DEL SISTEMA (Creación del Administrador Maestro con relaciones intermedias)
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:

        # Encriptación de contraseña.
        password_plana = "admin123".encode('utf-8')
        sal = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_plana, sal).decode('utf-8')
        
        # Inserción en tabla central.
        cursor.execute('''
            INSERT INTO usuarios (usuario, password, nombres, apellidos, dni) 
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'David Hernan', 'Bravo', '00000000'))
        
        id_nuevo_admin = cursor.lastrowid # Capturamos el ID del usuario recién creado.
        
        # Rescatamos el ID del rol Administrador.
        cursor.execute("SELECT id FROM roles WHERE rol = 'Administrador'")
        id_rol_admin = cursor.fetchone()[0]
        
        # Inserción en la tabla intermedia (Resolución N:M).
        cursor.execute('''
            INSERT INTO usuxroles (id_usuario, id_rol) VALUES (?, ?)
        ''', (id_nuevo_admin, id_rol_admin))
    
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
ventana.eval('tk::PlaceWindow . center') # Centramos la ventana de login.
ventana.resizable(False, False)



# ===============================================
#  INYECCIÓN GLOBAL DE EVENTOS (USABILIDAD Y UX)
# ===============================================

# 1. Construcción del Menú Contextual en memoria.
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

# 2. Refuerzo de Atajos de Teclado.
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
    
    # REFACTORIZACIÓN SQL: Extraemos los datos cruzando las tablas mediante JOIN y asegurándonos 
    # de que ni el usuario ni la asignación del rol estén dados de baja.
    # CAMBIO: Agregamos u.id a la cláusula SELECT para capturar la identidad física del usuario.
    cursor.execute('''
        SELECT u.id, u.password, r.rol, u.nombres, u.apellidos 
        FROM usuarios u
        JOIN usuxroles ur ON u.id = ur.id_usuario
        JOIN roles r ON ur.id_rol = r.id
        WHERE u.usuario = ? AND u.habilitado = 1 AND ur.habilitado = 1
        LIMIT 1
    ''', (usuario_ingresado,))
    
    resultado = cursor.fetchone()
    conexion.close()
    
    # CAMBIO: Ajustamos el índice de resultado[] porque ahora u.id es la posición 0 y password la 1.
    if resultado and bcrypt.checkpw(password_ingresada, resultado[1].encode('utf-8')):
        id_usuario = resultado[0]
        rol_usuario = resultado[2]
        nombres_usuario = resultado[3]
        apellidos_usuario = resultado[4]

        messagebox.showinfo("Acceso Concedido", f"Bienvenido/a, {nombres_usuario} {apellidos_usuario}.\nRol: {rol_usuario}")

        caja_usuario.delete(0, tk.END)
        caja_password.delete(0, tk.END)
        caja_usuario.focus_set()
        
        ventana.withdraw()
        
        from panel_control import PanelControl
        # CAMBIO: Propagamos el id_usuario hacia el Panel de Control.
        PanelControl(ventana, id_usuario, rol_usuario, nombres_usuario, apellidos_usuario)
    else:
        intentos_fallidos += 1
        intentos_restantes = 3 - intentos_fallidos
        
        caja_usuario.delete(0, tk.END)
        caja_password.delete(0, tk.END)
        caja_usuario.focus_set()
        
        if intentos_restantes > 0:
            messagebox.showerror("Error de Autenticación", f"Credenciales incorrectas o usuario inhabilitado. Intentos restantes: {intentos_restantes}")
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