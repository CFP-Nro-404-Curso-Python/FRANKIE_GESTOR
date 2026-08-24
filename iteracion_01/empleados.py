# Es necesario exportar tkinter para que tk.Toplevel pueda ser reconocido.
import tkinter as tk
# Necesario para el manejo de tablas mediante Treeview.
from tkinter import ttk



class Empleado(tk.Toplevel):
    def __init__(self, parent):
        # Inicializa la ventana secundaria Toplevel.
        super().__init__(parent)

        self.title("FORMULARIO EMPLEADOS")
        self.geometry("1005x550")



        # ===========================================
        #  FUNCIONES PARA MANEJAR LAS DEMÁS VENTANAS
        # ===========================================
        
        def abrir_clientes():
            # Clientes es la ventana raíz (parent). No se vuelve a instanciar.
            # Simplemente la traemos al frente y le damos el foco.
            parent.lift()
            parent.focus_force()

        def abrir_proveedores():
            """
            IMPORTACIÓN LOCAL (Lazy Import): Se importa la clase Proveedor recién cuando el usuario 
            hace clic en el botón. Si hiciéramos esto al principio del archivo, provocaríamos un
            error de "Importación Circular" (donde clientes importa empleados, y empleados importa
            a los demás, colgando el intérprete de Python antes de arrancar).
            """
            from proveedores import Proveedor
            """
            INSTANCIACIÓN Y JERARQUÍA: Creamos la ventana Proveedor pero le pasamos 'parent' 
            (la ventana tk.Tk() original de Clientes) en lugar de 'self'. Esto asegura que todas 
            las ventanas dependan de la principal. Si usaras 'self', Proveedor sería hija de Empleado, 
            y si cerrás Empleado, se destruiría Proveedor en cascada.
            """
            Proveedor(parent)

        def abrir_stock():
            from stock import Stock
            Stock(parent)

        def abrir_facturacion():
            from facturacion import Facturacion
            Facturacion(parent)



        # =========================================
        #  BOTONES PARA MANEJAR LAS DEMÁS VENTANAS
        # =========================================

        # Botón para volver/enfocar la ventana principal de Clientes.
        boton_clientes = tk.Button(self, text="Clientes", command=abrir_clientes)
        boton_clientes.grid(row=0, column=0, pady=20, padx=10)

        # Crea un botón para abrir la ventana Formulario Proveedores.
        boton_proveedores = tk.Button(self, text="Proveedores", command=abrir_proveedores)
        boton_proveedores.grid(row=0, column=1, pady=20, padx=10)

        # Crea un botón para abrir la ventana Formulario Stock.
        boton_stock = tk.Button(self, text="Stock", command=abrir_stock)
        boton_stock.grid(row=0, column=2, pady=20, padx=10)

        # Crea un botón para abrir la ventana Formulario Facturación.
        boton_facturacion = tk.Button(self, text="Facturación", command=abrir_facturacion)
        boton_facturacion.grid(row=0, column=3, pady=20, padx=10)



        # ===================================
        #  CAMPOS DEL "FORMULARIO EMPLEADOS"
        # ===================================

        tk.Label(self, text="Nombres").grid(row=1, column=0)
        caja_nombres = tk.Entry(self)
        caja_nombres.grid(row=1, column=1)

        tk.Label(self, text="Apellidos").grid(row=2, column=0)
        caja_apellidos = tk.Entry(self)
        caja_apellidos.grid(row=2, column=1)

        tk.Label(self, text="DNI").grid(row=3, column=0)
        caja_dni = tk.Entry(self)
        caja_dni.grid(row=3, column=1)

        tk.Label(self, text="Teléfono").grid(row=4, column=0)
        caja_telefono = tk.Entry(self)
        caja_telefono.grid(row=4, column=1)

        tk.Label(self, text="Email").grid(row=5, column=0)
        caja_email = tk.Entry(self)
        caja_email.grid(row=5, column=1)

        tk.Label(self, text="Domicilio").grid(row=6, column=0)
        caja_domicilio = tk.Entry(self)
        caja_domicilio.grid(row=6, column=1)

        tk.Label(self, text="Legajo").grid(row=7, column=0)
        caja_legajo = tk.Entry(self)
        caja_legajo.grid(row=7, column=1)

        tk.Label(self, text="Cargo").grid(row=8, column=0)
        caja_cargo = tk.Entry(self)
        caja_cargo.grid(row=8, column=1)

        tk.Label(self, text="Sector").grid(row=9, column=0)
        caja_sector = tk.Entry(self)
        caja_sector.grid(row=9, column=1)

        tk.Label(self, text="Sueldo").grid(row=10, column=0)
        caja_sueldo = tk.Entry(self)
        caja_sueldo.grid(row=10, column=1)



        # =========================================================
        #  BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # =========================================================

        boton_guardar = tk.Button(self, text="Guardar Empleado")
        boton_guardar.grid(row=3, column=3)

        boton_modificar = tk.Button(self, text="Modificar Empleado")
        boton_modificar.grid(row=5, column=3)

        boton_eliminar = tk.Button(self, text="Eliminar Empleado")
        boton_eliminar.grid(row=7, column=3)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy)
        boton_cerrar_ventana.grid(row=9, column=3)



        # =============================
        #  TABLA DE DATOS DE EMPLEADOS
        # =============================

        columnas = ("Nombres", "Apellidos", "DNI", "Teléfono", "Email", "Domicilio", "Legajo", "Cargo", "Sector", "Sueldo")

        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=100)

        tabla.grid(row=11, column=0, columnspan=5, pady=20)