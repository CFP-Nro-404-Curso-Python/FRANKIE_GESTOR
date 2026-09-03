# Importa tkinter para crear interfaces gráficas.
import tkinter as tk
# Importa ttk que contiene componentes avanzados como tablas (Treeview).
from tkinter import ttk
# Importa módulos nativos para manejo de directorios y SQLite.
import sqlite3
import os



# ===================================
#  IMPORTACIÓN DE LOS DEMÁS ARCHIVOS
# ===================================

# Importa la clase Empleado de empleados.py
from empleados import Empleado
# Importa la clase Proveedor de proveedores.py
from proveedores import Proveedor
# Importa la clase Stock de stock.py
from stock import Stock
# Importa la clase Facturacion de facturacion.py
from facturacion import Facturacion



# ==============================================
#  CREACIÓN DE LA VENTANA "FORMULARIO CLIENTES"
# ==============================================

# Crea la ventana principal.
ventana = tk.Tk()
# Define tamaño ancho y alto.
ventana.geometry("1005x550")
# Cambia el título.
ventana.title("FORMULARIO CLIENTES")



# ===========================================
#  FUNCIONES PARA MANEJAR LAS DEMÁS VENTANAS
# ===========================================

def abrir_empleados():
    Empleado(ventana)

def abrir_proveedores():
    Proveedor(ventana)

def abrir_stock():
    Stock(ventana)

def abrir_facturacion():
    Facturacion(ventana)



# =========================================
#  BOTONES PARA MANEJAR LAS DEMÁS VENTANAS
# =========================================

boton_empleados = tk.Button(ventana, text="Empleados", command=abrir_empleados)
boton_empleados.grid(row=0, column=0, pady=20, padx=10)

boton_proveedores = tk.Button(ventana, text="Proveedores", command=abrir_proveedores)
boton_proveedores.grid(row=0, column=1, pady=20, padx=10)

boton_stock = tk.Button(ventana, text="Stock", command=abrir_stock)
boton_stock.grid(row=0, column=2, pady=20, padx=10)

boton_facturacion = tk.Button(ventana, text="Facturación", command=abrir_facturacion)
boton_facturacion.grid(row=0, column=3, pady=20, padx=10)



# ==========================================
#  FUNCIONALIDADES DE "FORMULARIO CLIENTES"
# ==========================================

#  Migración a SQLite y Anclaje de Directorio
# --------------------------------------------
# Obtenemos la ruta absoluta de donde está alojado este script (.py)
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))

# Construimos la ruta absoluta hacia la carpeta "db"
CARPETA_DB = os.path.join(DIRECTORIO_ACTUAL, "db")
os.makedirs(CARPETA_DB, exist_ok=True)

# Construimos la ruta absoluta hacia la base de datos
DB_PATH = os.path.join(CARPETA_DB, "frankie_gestor.db")

# DDL (Data Definition Language): Inicializa la tabla si no existe.
def crear_tabla_clientes():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres TEXT,
            apellidos TEXT,
            dni TEXT,
            edad TEXT,
            telefono TEXT,
            email TEXT,
            domicilio TEXT,
            ciudad TEXT,
            provincia TEXT,
            codigo_postal TEXT
        )
    ''')
    conexion.commit()
    conexion.close()

# DML (Data Manipulation Language): Lectura de datos.
def cargar_datos_db():
    # Limpiamos la tabla visual antes de recargar para evitar duplicados.
    for item in tabla.get_children():
        tabla.delete(item)
        
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM clientes")
    filas = cursor.fetchall()
    
    for fila in filas:
        # fila[0] contiene el 'id'. Lo usamos como 'iid' interno del Treeview.
        # fila[1:] contiene el resto de los datos que sí son visibles.
        tabla.insert("", "end", iid=fila[0], values=fila[1:])
    conexion.close()

def limpiar_campos():
    cajas = [caja_nombres, caja_apellidos, caja_dni, caja_edad, caja_telefono, caja_email, 
             caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal]
             
    for caja in cajas:
        caja.delete(0, tk.END)
    caja_nombres.focus_set()

def guardar():
    nombres = caja_nombres.get()
    apellidos = caja_apellidos.get()
    dni = caja_dni.get()
    edad = caja_edad.get()
    telefono = caja_telefono.get()
    email = caja_email.get()
    domicilio = caja_domicilio.get()
    ciudad = caja_ciudad.get()
    provincia = caja_provincia.get()
    codigo_postal = caja_codigo_postal.get()

    #  Operación INSERT
    # ------------------
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT INTO clientes (nombres, apellidos, dni, edad, telefono, email, domicilio, ciudad, provincia, codigo_postal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nombres, apellidos, dni, edad, telefono, email, domicilio, ciudad, provincia, codigo_postal))
    conexion.commit()
    conexion.close()
    
    limpiar_campos()
    # Recargamos la grilla para que SQLite le asigne el ID correcto en la interfaz.
    cargar_datos_db()

def seleccionar_fila(event):
    seleccion = tabla.selection()
    
    if not seleccion:
        return
        
    valores = tabla.item(seleccion[0], "values")
    
    cajas = [caja_nombres, caja_apellidos, caja_dni, caja_edad, caja_telefono, caja_email, 
             caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal]
             
    for i, caja in enumerate(cajas):
        caja.delete(0, tk.END)
        caja.insert(0, valores[i])

def modificar():
    seleccion = tabla.selection()
    
    if not seleccion:
        return
    
    # Extraemos el ID oculto que asignamos a la fila.
    id_cliente = seleccion[0]
    
    nombres = caja_nombres.get()
    apellidos = caja_apellidos.get()
    dni = caja_dni.get()
    edad = caja_edad.get()
    telefono = caja_telefono.get()
    email = caja_email.get()
    domicilio = caja_domicilio.get()
    ciudad = caja_ciudad.get()
    provincia = caja_provincia.get()
    codigo_postal = caja_codigo_postal.get()

    #  Operación UPDATE
    # ------------------
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute('''
        UPDATE clientes SET 
        nombres=?, apellidos=?, dni=?, edad=?, telefono=?, email=?, domicilio=?, ciudad=?, provincia=?, codigo_postal=?
        WHERE id=?
    ''', (nombres, apellidos, dni, edad, telefono, email, domicilio, ciudad, provincia, codigo_postal, id_cliente))
    conexion.commit()
    conexion.close()

    limpiar_campos()
    cargar_datos_db()

def eliminar():
    seleccion = tabla.selection()
    
    if not seleccion:
        return
        
    #  Operación DELETE
    # ------------------
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    for item in seleccion:
        # El 'item' contiene el ID de la base de datos.
        cursor.execute("DELETE FROM clientes WHERE id=?", (item,))
        
    conexion.commit()
    conexion.close()
    
    limpiar_campos()
    cargar_datos_db()



# ==================================
#  CAMPOS DEL "FORMULARIO CLIENTES"
# ==================================

tk.Label(ventana, text="Nombres").grid(row=1, column=0)
caja_nombres = tk.Entry(ventana)
caja_nombres.grid(row=1, column=1)

tk.Label(ventana, text="Apellidos").grid(row=2, column=0)
caja_apellidos = tk.Entry(ventana)
caja_apellidos.grid(row=2, column=1)

tk.Label(ventana, text="DNI").grid(row=3, column=0)
caja_dni = tk.Entry(ventana)
caja_dni.grid(row=3, column=1)

tk.Label(ventana, text="Edad").grid(row=4, column=0)
caja_edad = tk.Entry(ventana)
caja_edad.grid(row=4, column=1)

tk.Label(ventana, text="Teléfono").grid(row=5, column=0)
caja_telefono = tk.Entry(ventana)
caja_telefono.grid(row=5, column=1)

tk.Label(ventana,text="Email").grid(row=6, column=0)
caja_email = tk.Entry(ventana)
caja_email.grid(row=6, column=1)

tk.Label(ventana,text="Domicilio").grid(row=7, column=0)
caja_domicilio = tk.Entry(ventana)
caja_domicilio.grid(row=7, column=1)

tk.Label(ventana, text="Ciudad").grid(row=8, column=0)
caja_ciudad = tk.Entry(ventana)
caja_ciudad.grid(row=8, column=1)

tk.Label(ventana,text="Provincia").grid(row=9, column=0)
caja_provincia = tk.Entry(ventana)
caja_provincia.grid(row=9, column=1)

tk.Label(ventana, text="Código Postal").grid(row=10, column=0)
caja_codigo_postal = tk.Entry(ventana)
caja_codigo_postal.grid(row=10, column=1)



# =========================================================
#  BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
# =========================================================

boton_guardar = tk.Button(ventana, text="Guardar Cliente", command=guardar)
boton_guardar.grid(row=3, column=3)

boton_modificar = tk.Button(ventana, text="Modificar Cliente", command=modificar)
boton_modificar.grid(row=5, column=3)

boton_eliminar = tk.Button(ventana, text="Eliminar Cliente", command=eliminar)
boton_eliminar.grid(row=7, column=3)

boton_cerrar_ventana = tk.Button(ventana, text="Cerrar Ventana", command=ventana.destroy)
boton_cerrar_ventana.grid(row=9, column=3)



# ============================
#  TABLA DE DATOS DE CLIENTES
# ============================

columnas = ("Nombres", "Apellidos", "DNI", "Edad", "Teléfono", "Email", "Domicilio", "Ciudad", "Provincia", "Código Postal")

tabla = ttk.Treeview(ventana, columns=columnas, show="headings", height=10)

for col in columnas:
    tabla.heading(col, text=col)
    tabla.column(col, width=100)

tabla.grid(row=11, column=0, columnspan=5, pady=20)
tabla.bind("<<TreeviewSelect>>", seleccionar_fila)



# ========================
#  CARGA INICIAL DE DATOS
# ========================

# Se crea la tabla si no existe y luego se leen los datos a la grilla.
crear_tabla_clientes()
cargar_datos_db()

ventana.mainloop()