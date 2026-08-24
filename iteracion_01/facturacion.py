import tkinter as tk
from tkinter import ttk



class Facturacion(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("FORMULARIO FACTURACIÓN")
        self.geometry("550x600")

    

        # ===========================================
        #  FUNCIONES PARA MANEJAR LAS DEMÁS VENTANAS
        # ===========================================
        
        def abrir_clientes():
            parent.lift()
            parent.focus_force()

        def abrir_empleados():
            from empleados import Empleado
            Empleado(parent)

        def abrir_proveedores():
            from proveedores import Proveedor
            Proveedor(parent)

        def abrir_stock():
            from stock import Stock
            Stock(parent)



        # =========================================
        #  BOTONES PARA MANEJAR LAS DEMÁS VENTANAS
        # =========================================

        boton_clientes = tk.Button(self, text="Clientes", command=abrir_clientes)
        boton_clientes.grid(row=0, column=0, pady=10, padx=10)

        boton_empleados = tk.Button(self, text="Empleados", command=abrir_empleados)
        boton_empleados.grid(row=0, column=1, pady=10, padx=10)

        boton_proveedores = tk.Button(self, text="Proveedores", command=abrir_proveedores)
        boton_proveedores.grid(row=0, column=2, pady=10, padx=10)

        boton_stock = tk.Button(self, text="Stock", command=abrir_stock)
        boton_stock.grid(row=0, column=3, pady=10, padx=10)



        # =====================================
        #  CAMPOS DEL "FORMULARIO FACTURACIÓN"
        # =====================================

        tk.Label(self, text="Datos del Vendedor").grid(row=1, column=0)
        caja_datos_vendedor = tk.Entry(self)
        caja_datos_vendedor.grid(row=1, column=1)

        tk.Label(self, text="Datos del Cliente").grid(row=2, column=0)
        caja_datos_cliente = tk.Entry(self)
        caja_datos_cliente.grid(row=2, column=1)

        tk.Label(self, text="").grid(row=3, column=0)
        
        tk.Label(self, text="Producto").grid(row=4, column=0)
        caja_producto = tk.Entry(self)
        caja_producto.grid(row=4, column=1)

        tk.Label(self, text="Cantidad").grid(row=5, column=0)
        caja_cantidad = tk.Entry(self)
        caja_cantidad.grid(row=5, column=1)

        tk.Label(self, text="Valor en $").grid(row=6, column=0)
        caja_valor = tk.Entry(self)
        caja_valor.grid(row=6, column=1)

        tk.Label(self, text="Descuento en %").grid(row=7, column=0)
        caja_descuento = tk.Entry(self)
        caja_descuento.grid(row=7, column=1)



        # =========================================================
        #  BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # =========================================================

        boton_guardar = tk.Button(self, text="Guardar Facturación")
        boton_guardar.grid(row=4, column=3)

        boton_modificar = tk.Button(self, text="Modificar Facturación")
        boton_modificar.grid(row=5, column=3)

        boton_eliminar = tk.Button(self, text="Eliminar Facturación")
        boton_eliminar.grid(row=6, column=3)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy)
        boton_cerrar_ventana.grid(row=7, column=3)



        # ===============================
        #  TABLA DE DATOS DE FACTURACIÓN
        # ===============================

        columnas = ("Producto", "Cantidad", "Valor en $", "Descuento en %", "Total en $")

        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=100)

        tabla.grid(row=8, column=0, columnspan=5, pady=20)



        # =================================================================
        #  CAMPOS QUE MUESTRAN DESCUENTO DE LA "CALCULADORA DE DESCUENTOS"
        # =================================================================
        tk.Label(self, text="CALCULADORA DE DESCUENTOS").grid(row=9, column=0, pady=10)
        tk.Label(self, text="Subtotal en $").grid(row=10, column=0)
        caja_desc = tk.Entry(self)
        caja_desc.grid(row=10, column=1)

        tk.Label(self, text="Descuento en %").grid(row=11, column=0)
        caja_desc = tk.Entry(self)
        caja_desc.grid(row=11, column=1)



        # ============================
        #  BOTÓN "CALCULAR DESCUENTO"
        # ============================

        boton_calcular_desc = tk.Button(self, text="Calcular Descuento")
        boton_calcular_desc.grid(row=11, column=3)



        # ==============================================
        #  ETIQUETA QUE MUESTRA RESULTANTE DE DESCUENTO
        # ==============================================

        tk.Label(self, text="").grid(row=12, column=0)
        tk.Label(self, text="El Precio Aplicando el Descuento es de $ ").grid(row=13, column=0)