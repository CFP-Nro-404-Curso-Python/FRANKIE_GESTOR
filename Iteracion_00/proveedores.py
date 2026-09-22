import tkinter as tk



class Proveedor(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("FORMULARIO PROVEEDORES")
        self.geometry("400x300")

    

        # ===========================================
        #  FUNCIONES PARA MANEJAR LAS DEMÁS VENTANAS
        # ===========================================
        
        def abrir_clientes():
            parent.lift()
            parent.focus_force()

        def abrir_empleados():
            from empleados import Empleado
            Empleado(parent)

        def abrir_stock():
            from stock import Stock
            Stock(parent)

        def abrir_facturacion():
            from facturacion import Facturacion
            Facturacion(parent)



        # =========================================
        #  BOTONES PARA MANEJAR LAS DEMÁS VENTANAS
        # =========================================

        boton_clientes = tk.Button(self, text="Clientes", command=abrir_clientes)
        boton_clientes.grid(row=0, column=0, pady=20, padx=10)

        boton_empleados = tk.Button(self, text="Empleados", command=abrir_empleados)
        boton_empleados.grid(row=0, column=1, pady=20, padx=10)

        boton_stock = tk.Button(self, text="Stock", command=abrir_stock)
        boton_stock.grid(row=0, column=2, pady=20, padx=10)

        boton_facturacion = tk.Button(self, text="Facturación", command=abrir_facturacion)
        boton_facturacion.grid(row=0, column=3, pady=20, padx=10)