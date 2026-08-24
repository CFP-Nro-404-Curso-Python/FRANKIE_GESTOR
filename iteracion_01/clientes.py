# Importa tkinter para crear interfaces gráficas.
import tkinter as tk
# Importa ttk que contiene componentes avanzados como tablas (Treeview).
from tkinter import ttk



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



# ==================================
#  CAMPOS DEL "FORMULARIO CLIENTES"
# ==================================

# Etiqueta con una caja de entrada asociada para el campo correspondiente.
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
boton_guardar = tk.Button(ventana, text="Guardar Cliente")
boton_guardar.grid(row=3, column=3)

# Botón "Modificar Cliente".
boton_modificar = tk.Button(ventana, text="Modificar Cliente")
boton_modificar.grid(row=5, column=3)

# Botón "Eliminar Cliente".
boton_eliminar = tk.Button(ventana, text="Eliminar Cliente")
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



# Mantiene abierta la ventana y maneja eventos de botones.
ventana.mainloop()