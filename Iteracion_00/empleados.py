# Es necesario exportar tkinter para que tk.Toplevel pueda ser reconocido.
import tkinter as tk



class Empleado(tk.Toplevel):
    def __init__(self, parent):
        # Inicializa la ventana secundaria Toplevel.
        super().__init__(parent)

        self.title("FORMULARIO EMPLEADOS")
        self.geometry("550x550")



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