# Importa tkinter para crear interfaces gráficas.
import tkinter as tk
# Importa ttk que contiene componentes avanzados como tablas (Treeview).
from tkinter import ttk
# Importa módulos nativos para el manejo de persistencia en archivos CSV.
import csv
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

# Función para abrir la ventana de "Formulario Empleados" desde el módulo importado
# (from empleados import Empleado).
def abrir_empleados():
    # Instancia la clase definida en empleados.py pasándole la ventana principal.
    Empleado(ventana)

# Función para abrir la ventana de "Formulario Proveedores" desde el módulo importado
# (from proveedores import Proveedor).
def abrir_proveedores():
    # Instancia la clase definida en proveedores.py pasándole la ventana principal.
    Proveedor(ventana)

# Función para abrir la ventana de "Formulario Stock" desde el módulo importado
# (from stock import Stock).
def abrir_stock():
    # Instancia la clase definida en stock.py pasándole la ventana principal.
    Stock(ventana)

# Función para abrir la ventana de "Formulario Facturación" desde el módulo importado
# (from facturacion import Facturacion).
def abrir_facturacion():
    # Instancia la clase definida en facturacion.py pasándole la ventana principal.
    Facturacion(ventana)



# =========================================
#  BOTONES PARA MANEJAR LAS DEMÁS VENTANAS
# =========================================

# Crea un botón para abrir la ventana Formulario Empleados.
boton_empleados = tk.Button(ventana, text="Empleados", command=abrir_empleados)
boton_empleados.grid(row=0, column=0, pady=20, padx=10)

# Crea un botón para abrir la ventana Formulario Proveedores.
boton_proveedores = tk.Button(ventana, text="Proveedores", command=abrir_proveedores)
boton_proveedores.grid(row=0, column=1, pady=20, padx=10)

# Crea un botón para abrir la ventana Formulario Stock.
boton_stock = tk.Button(ventana, text="Stock", command=abrir_stock)
boton_stock.grid(row=0, column=2, pady=20, padx=10)

# Crea un botón para abrir la ventana Formulario Facturación.
boton_facturacion = tk.Button(ventana, text="Facturación", command=abrir_facturacion)
boton_facturacion.grid(row=0, column=3, pady=20, padx=10)



# ==========================================
#  FUNCIONALIDADES DE "FORMULARIO CLIENTES"
# ==========================================

# Obtenemos la ruta absoluta del directorio exacto donde está alojado este script (.py).
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))

# Definimos el nombre de la carpeta contenedora y unimos esa ruta absoluta con el nombre de la carpeta contenedora.
CARPETA_PERSISTENCIA = os.path.join(DIRECTORIO_ACTUAL, "persistencia")

# Aseguramos que la carpeta exista antes de operar. exist_ok=True evita errores si ya fue creada.
os.makedirs(CARPETA_PERSISTENCIA, exist_ok=True)

# Definimos la constante uniendo la carpeta con el nombre del archivo de persistencia.
ARCHIVO_CSV = os.path.join(CARPETA_PERSISTENCIA, "datos_clientes.csv")

# Esta función lee el CSV y carga los datos en la tabla al iniciar el programa.
def cargar_datos_csv():
    # Se verifica si el archivo existe usando el módulo os para evitar errores en la primera ejecución.
    if os.path.exists(ARCHIVO_CSV):
        with open(ARCHIVO_CSV, mode="r", encoding="utf-8") as archivo:
            lector = csv.reader(archivo)
            for fila in lector:
                # Inserta cada fila recuperada del archivo CSV en el Treeview.
                tabla.insert("", "end", values=fila)

# Esta función sobrescribe el archivo CSV con los datos actuales de la tabla.
# Al usar mode="w", se reemplaza el contenido viejo por la foto actual de la tabla, garantizando sincronización.
def sobrescribir_csv():
    with open(ARCHIVO_CSV, mode="w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        # Se itera sobre todos los elementos visibles en la tabla.
        for item in tabla.get_children():
            valores = tabla.item(item, "values")
            escritor.writerow(valores)

# Esta función limpia los campos Entry, y vuelve el cursor a la primera caja de texto.
def limpiar_campos():
    cajas = [caja_nombres, caja_apellidos, caja_dni, caja_edad, caja_telefono, caja_email, 
             caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal]
             
    for caja in cajas:
        caja.delete(0, tk.END)
    # el método focus_set() devuelve el foco a la caja de texto indicada.
    caja_nombres.focus_set()

# Esta función se ejecuta al hacer clic en el botón "Guardar Cliente", mediante el método get().
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

    # Inserta una nueva fila dentro de la tabla.
    tabla.insert("","end",values=(nombres, apellidos, dni, edad, telefono, email, domicilio, ciudad, provincia, codigo_postal))

    limpiar_campos()
    # PERSISTENCIA: Se guarda el estado actualizado de la tabla en el archivo CSV.
    sobrescribir_csv()

# Esta función se dispara automáticamente al hacer clic en una fila.
def seleccionar_fila(event):
    seleccion = tabla.selection()
    
    if not seleccion:
        return
        
    # Obtenemos la tupla de datos de la fila marcada.
    valores = tabla.item(seleccion[0], "values")
    
    # Agrupamos los Entries en el mismo orden que las columnas.
    cajas = [caja_nombres, caja_apellidos, caja_dni, caja_edad, caja_telefono, caja_email, 
             caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal]
             
    # Iteramos para limpiar las cajas y llenarlas con el dato correspondiente.
    for i, caja in enumerate(cajas):
        caja.delete(0, tk.END)
        caja.insert(0, valores[i])

# Esta función se ejecuta al tocar el botón Modificar.
def modificar():
    # Obtiene la tupla con los identificadores de las filas seleccionadas.
    seleccion = tabla.selection()
    
    # Validación: si no hay nada seleccionado, cortamos la ejecución para evitar errores.
    if not seleccion:
        return
    
    # Se toman los valores actuales de los Entry
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

    # Se actualiza el primer elemento seleccionado (índice 0).
    tabla.item(seleccion[0], values=(nombres, apellidos, dni, edad, telefono, email, domicilio, ciudad, provincia, codigo_postal))

    limpiar_campos()
    # PERSISTENCIA: Se guarda el estado actualizado de la tabla en el archivo CSV.
    sobrescribir_csv()

# Esta función se ejecuta al tocar el botón Eliminar.
def eliminar():
    seleccion = tabla.selection()
    
    if not seleccion:
        return
        
    # Se itera sobre la selección por si el usuario seleccionó múltiples filas.
    for item in seleccion:
        tabla.delete(item)
    
    limpiar_campos()
    # PERSISTENCIA: Se guarda el estado actualizado de la tabla en el archivo CSV.
    sobrescribir_csv()



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

# Botón "Guardar Cliente".
boton_guardar = tk.Button(ventana, text="Guardar Cliente", command=guardar)
boton_guardar.grid(row=3, column=3)

# Botón "Modificar Cliente".
boton_modificar = tk.Button(ventana, text="Modificar Cliente", command=modificar)
boton_modificar.grid(row=5, column=3)

# Botón "Eliminar Cliente".
boton_eliminar = tk.Button(ventana, text="Eliminar Cliente", command=eliminar)
boton_eliminar.grid(row=7, column=3)

# Botón "Cerrar Ventana".
boton_cerrar_ventana = tk.Button(ventana, text="Cerrar Ventana", command=ventana.destroy)
boton_cerrar_ventana.grid(row=9, column=3)



# ============================
#  TABLA DE DATOS DE CLIENTES
# ============================

# Configuración de la tabla Treeview.
columnas = ("Nombres", "Apellidos", "DNI", "Edad", "Teléfono", "Email", "Domicilio", "Ciudad", "Provincia", "Código Postal")

tabla = ttk.Treeview(ventana, columns=columnas, show="headings", height=10)

for col in columnas:
    tabla.heading(col, text=col)
    tabla.column(col, width=100)

tabla.grid(row=11, column=0, columnspan=5, pady=20)

# Enlazamos el evento de selección de la tabla con tu función.
# <<TreeviewSelect>> es el evento nativo que detecta cuando cambia la fila remarcada.
tabla.bind("<<TreeviewSelect>>", seleccionar_fila)



# ============================
#  CARGA INICIAL DE DATOS
# ============================

# Se invoca a la función que recupera los datos del CSV y los plasma en la tabla.
cargar_datos_csv()

# Mantiene abierta la ventana y maneja eventos de botones.
ventana.mainloop()