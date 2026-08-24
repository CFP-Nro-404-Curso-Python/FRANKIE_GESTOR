import tkinter as tk
from tkinter import ttk



class Stock(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("FORMULARIO STOCK")
        self.geometry("1005x550")

    

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

        boton_proveedores = tk.Button(self, text="Proveedores", command=abrir_proveedores)
        boton_proveedores.grid(row=0, column=2, pady=20, padx=10)

        boton_facturacion = tk.Button(self, text="Facturación", command=abrir_facturacion)
        boton_facturacion.grid(row=0, column=3, pady=20, padx=10)



        # =======================================
        #  FUNCIONALIDADES DE "FORMULARIO STOCK"
        # =======================================

        def limpiar_campos():
            cajas = [caja_codigo, caja_descripcion, caja_categoria, caja_proveedor, caja_stock_actual, caja_stock_minimo, caja_precio_costo, 
                     caja_precio_venta, caja_ubicacion, caja_vencimiento]
                     
            for caja in cajas:
                caja.delete(0, tk.END)
            
            caja_codigo.focus_set()
        
        def guardar():
            codigo = caja_codigo.get()
            descripcion = caja_descripcion.get()
            categoria = caja_categoria.get()
            proveedor = caja_proveedor.get()
            stock_actual = caja_stock_actual.get()
            stock_minimo = caja_stock_minimo.get()
            precio_costo = caja_precio_costo.get()
            precio_venta = caja_precio_venta.get()
            ubicacion = caja_ubicacion.get()
            vencimiento = caja_vencimiento.get()

            tabla.insert("","end",values=(codigo, descripcion, categoria, proveedor, stock_actual, stock_minimo, precio_costo, precio_venta, 
                                          ubicacion, vencimiento))

            limpiar_campos()

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            
            if not seleccion:
                return
                
            valores = tabla.item(seleccion[0], "values")
            
            cajas = [caja_codigo, caja_descripcion, caja_categoria, caja_proveedor, caja_stock_actual, caja_stock_minimo, caja_precio_costo, 
                     caja_precio_venta, caja_ubicacion, caja_vencimiento]
                     
            for i, caja in enumerate(cajas):
                caja.delete(0, tk.END)
                caja.insert(0, valores[i])
        
        def modificar():
            seleccion = tabla.selection()
            
            if not seleccion:
                return
            
            codigo = caja_codigo.get()
            descripcion = caja_descripcion.get()
            categoria = caja_categoria.get()
            proveedor = caja_proveedor.get()
            stock_actual = caja_stock_actual.get()
            stock_minimo = caja_stock_minimo.get()
            precio_costo = caja_precio_costo.get()
            precio_venta = caja_precio_venta.get()
            ubicacion = caja_ubicacion.get()
            vencimiento = caja_vencimiento.get()

            tabla.item(seleccion[0], values=(codigo, descripcion, categoria, proveedor, stock_actual, stock_minimo, precio_costo, precio_venta, 
                                             ubicacion, vencimiento))

            limpiar_campos()
        
        def eliminar():
            seleccion = tabla.selection()
            
            if not seleccion:
                return
                
            for item in seleccion:
                tabla.delete(item)
            
            limpiar_campos()
        


        # ===============================
        #  CAMPOS DEL "FORMULARIO STOCK"
        # ===============================

        tk.Label(self, text="Código").grid(row=1, column=0)
        caja_codigo = tk.Entry(self)
        caja_codigo.grid(row=1, column=1)

        tk.Label(self, text="Descripción").grid(row=2, column=0)
        caja_descripcion = tk.Entry(self)
        caja_descripcion.grid(row=2, column=1)

        tk.Label(self, text="Categoría").grid(row=3, column=0)
        caja_categoria = tk.Entry(self)
        caja_categoria.grid(row=3, column=1)

        tk.Label(self, text="Proveedor").grid(row=4, column=0)
        caja_proveedor = tk.Entry(self)
        caja_proveedor.grid(row=4, column=1)

        tk.Label(self, text="Stock Actual").grid(row=5, column=0)
        caja_stock_actual = tk.Entry(self)
        caja_stock_actual.grid(row=5, column=1)

        tk.Label(self, text="Stock Mínimo").grid(row=6, column=0)
        caja_stock_minimo = tk.Entry(self)
        caja_stock_minimo.grid(row=6, column=1)

        tk.Label(self, text="Precio Costo").grid(row=7, column=0)
        caja_precio_costo = tk.Entry(self)
        caja_precio_costo.grid(row=7, column=1)

        tk.Label(self, text="Precio Venta").grid(row=8, column=0)
        caja_precio_venta = tk.Entry(self)
        caja_precio_venta.grid(row=8, column=1)

        tk.Label(self, text="Ubicación").grid(row=9, column=0)
        caja_ubicacion = tk.Entry(self)
        caja_ubicacion.grid(row=9, column=1)

        tk.Label(self, text="Vencimiento").grid(row=10, column=0)
        caja_vencimiento = tk.Entry(self)
        caja_vencimiento.grid(row=10, column=1)



        # =========================================================
        #  BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # =========================================================

        boton_guardar = tk.Button(self, text="Guardar Producto", command=guardar)
        boton_guardar.grid(row=3, column=3)

        boton_modificar = tk.Button(self, text="Modificar Producto", command=modificar)
        boton_modificar.grid(row=5, column=3)

        boton_eliminar = tk.Button(self, text="Eliminar Producto", command=eliminar)
        boton_eliminar.grid(row=7, column=3)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy)
        boton_cerrar_ventana.grid(row=9, column=3)



        # =========================
        #  TABLA DE DATOS DE STOCK
        # =========================

        columnas = ("Código", "Descripción", "Categoría", "Proveedor", "Stock Actual", "Stock Mínimo", "Precio Costo", "Precio Venta", "Ubicación", 
                    "Vencimiento")

        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=100)

        tabla.grid(row=11, column=0, columnspan=5, pady=20)

        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)