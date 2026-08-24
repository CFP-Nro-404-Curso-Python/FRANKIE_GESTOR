# Importa tkinter para crear interfaces gráficas.
import tkinter as tk



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
ventana.geometry("550x550")
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



# Mantiene abierta la ventana y maneja eventos de botones.
ventana.mainloop()