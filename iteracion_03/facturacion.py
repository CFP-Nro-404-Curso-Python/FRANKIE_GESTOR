# Es necesario exportar tkinter para que tk.Toplevel pueda ser reconocido.
import tkinter as tk
from tkinter import ttk
# Importa módulos nativos para el manejo de persistencia en archivos CSV.
import csv
import os



class Facturacion(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("FORMULARIO FACTURACIÓN")
        self.geometry("570x650")



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



        # =============================================
        #  FUNCIONALIDADES DE "FORMULARIO FACTURACIÓN"
        # =============================================

        # Definimos la constante con el nombre del archivo de persistencia.
        ARCHIVO_CSV = "datos_facturacion.csv"

        # Esta función lee el CSV y carga los datos en la tabla al iniciar la ventana.
        def cargar_datos_csv():
            # Se verifica si el archivo existe usando el módulo os para evitar errores en la primera ejecución.
            if os.path.exists(ARCHIVO_CSV):
                with open(ARCHIVO_CSV, mode="r", encoding="utf-8") as archivo:
                    lector = csv.reader(archivo)
                    for fila in lector:
                        # Inserta cada fila recuperada del archivo CSV en el Treeview.
                        tabla.insert("", "end", values=fila)
                # Recalculamos el total general luego de cargar las líneas de facturación guardadas.
                actualizar_total_factura()

        # Esta función sobrescribe el archivo CSV con los datos actuales de la tabla.
        def sobrescribir_csv():
            with open(ARCHIVO_CSV, mode="w", newline="", encoding="utf-8") as archivo:
                escritor = csv.writer(archivo)
                # Se itera sobre todos los elementos visibles en la tabla.
                for item in tabla.get_children():
                    valores = tabla.item(item, "values")
                    escritor.writerow(valores)

        def limpiar_campos():
            # No limpiamos vendedor ni cliente para agilizar la carga repetitiva de productos en la misma factura.
            cajas = [caja_producto, caja_cantidad, caja_valor, caja_descuento]
            for caja in cajas:
                caja.delete(0, tk.END)
            caja_producto.focus_set()

        # Esta función lee la tabla entera y recalcula el Gran Total. Previene la desincronización de estados.
        def actualizar_total_factura():
            gran_total = 0.0
            # get_children() devuelve los IDs de todas las filas en el Treeview.
            for item in tabla.get_children():
                # Extraemos la tupla de valores de cada fila.
                valores = tabla.item(item, "values")
                # Sumamos el valor del índice 4 (Total en $).
                gran_total += float(valores[4])
            
            # Actualizamos la etiqueta global.
            label_total_factura.config(text=f"TOTAL FACTURA: $ {gran_total:.2f}")

        def guardar():
            # Manejo de excepciones básico por si el usuario ingresa letras en campos numéricos o deja vacíos.
            try:
                producto = caja_producto.get()
                cantidad = float(caja_cantidad.get())
                valor = float(caja_valor.get())
                descuento = float(caja_descuento.get())

                # Validación de Límites: El descuento no puede ser negativo ni mayor a 100.
                if descuento < 0 or descuento > 100:
                    print("Error: El descuento por producto debe estar entre 0 y 100%.")
                    return # Cortamos la ejecución para no guardar datos anómalos.
                
                # Aplicación de la regla de negocio.
                total_linea = (cantidad * valor) * (1 - (descuento / 100))
                
                # Formateamos el total a 2 decimales para que se vea prolijo.
                tabla.insert("", "end", values=(producto, cantidad, valor, descuento, f"{total_linea:.2f}"))

                limpiar_campos()
                actualizar_total_factura()
                # Persistencia: Se guarda el estado actualizado de la tabla en el archivo CSV.
                sobrescribir_csv()
                
            except ValueError:
                # Acá lo ideal a futuro es lanzar un tk.messagebox de error.
                print("Error: Ingrese valores numéricos válidos.")

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            valores = tabla.item(seleccion[0], "values")
            cajas = [caja_producto, caja_cantidad, caja_valor, caja_descuento]
            
            for i, caja in enumerate(cajas):
                caja.delete(0, tk.END)
                caja.insert(0, valores[i])

        def modificar():
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            try:
                producto = caja_producto.get()
                cantidad = float(caja_cantidad.get())
                valor = float(caja_valor.get())
                descuento = float(caja_descuento.get())

                # Se evalúa la variable local "descuento".
                if descuento < 0 or descuento > 100:
                    print("Error: El descuento por producto debe estar entre 0 y 100%.")
                    return
                
                total_linea = (cantidad * valor) * (1 - (descuento / 100))

                tabla.item(seleccion[0], values=(producto, cantidad, valor, descuento, f"{total_linea:.2f}"))

                limpiar_campos()
                actualizar_total_factura()
                # Persistencia: Se guarda el estado actualizado de la tabla en el archivo CSV.
                sobrescribir_csv()
                
            except ValueError:
                print("Error: Ingrese valores numéricos válidos.")

        def eliminar():
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            for item in seleccion:
                tabla.delete(item)
            
            limpiar_campos()
            actualizar_total_factura()
            # Persistencia: Se guarda el estado actualizado de la tabla en el archivo CSV.
            sobrescribir_csv()



        # =====================================
        #  DESCUENTO SOBRE EL TOTAL DE FACTURA
        # =====================================

        def calcular_descuento_final():
            try:
                # 1. Calculamos el total actual leyendo la tabla (Fuente de Verdad).
                gran_total = 0.0
                for item in tabla.get_children():
                    valores = tabla.item(item, "values")
                    gran_total += float(valores[4])
                
                # 2. Tomamos solo el porcentaje ingresado por el usuario.
                desc_porcentaje = float(caja_calc_descuento.get())

                # Validación del límite sobre el total global.
                if desc_porcentaje < 0 or desc_porcentaje > 100:
                    label_resultado_desc.config(text="Error: El descuento debe estar entre 0 y 100%.")
                    return
                
                # 3. Calculamos el precio final.
                resultado = gran_total * (1 - (desc_porcentaje / 100))
                
                # 4. Actualizamos la vista.
                label_resultado_desc.config(text=f"Total con descuento ({desc_porcentaje}%): $ {resultado:.2f}")
            except ValueError:
                label_resultado_desc.config(text="Error: Ingrese un porcentaje válido.")



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

        boton_guardar = tk.Button(self, text="Guardar Facturación", command=guardar)
        boton_guardar.grid(row=4, column=3, padx=20)

        boton_modificar = tk.Button(self, text="Modificar Facturación", command=modificar)
        boton_modificar.grid(row=5, column=3, padx=20)

        boton_eliminar = tk.Button(self, text="Eliminar Facturación", command=eliminar)
        boton_eliminar.grid(row=6, column=3, padx=20)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy)
        boton_cerrar_ventana.grid(row=7, column=3, padx=20)



        # ===============================
        #  TABLA DE DATOS DE FACTURACIÓN
        # ===============================

        columnas = ("Producto", "Cantidad", "Valor en $", "Descuento en %", "Total en $")

        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=100)

        tabla.grid(row=8, column=0, columnspan=5, pady=20)
        
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)



        # ===================================
        #  ETIQUETA GLOBAL: TOTAL DE FACTURA
        # ===================================

        label_total_factura = tk.Label(self, text="TOTAL FACTURA: $ 0.00", font=("Arial", 10, "bold"))
        label_total_factura.grid(row=9, column=0, columnspan=2, sticky="w", padx=10)



        # ======================================
        #  SECCIÓN: DESCUENTO GLOBAL DE FACTURA
        # ======================================
        
        tk.Label(self, text="APLICAR DESCUENTO GLOBAL", font=("Arial", 9, "bold")).grid(row=10, column=0, pady=10, columnspan=2)

        # Se eliminó la petición del subtotal. Solo pedimos el porcentaje.
        tk.Label(self, text="Descuento Global en %").grid(row=11, column=0)
        caja_calc_descuento = tk.Entry(self)
        caja_calc_descuento.grid(row=11, column=1)

        boton_calcular_desc = tk.Button(self, text="Calcular Descuento Final", command=calcular_descuento_final)
        boton_calcular_desc.grid(row=11, column=3)



        # ==============================================
        #  ETIQUETA QUE MUESTRA RESULTANTE DE DESCUENTO
        # ==============================================
        
        label_resultado_desc = tk.Label(self, text="TOTAL CON DESCUENTO: $ 0.00", font=("Arial", 9, "bold"))
        label_resultado_desc.grid(row=12, column=0, columnspan=4, pady=15)


        # ========================
        #  CARGA INICIAL DE DATOS
        # ========================

        # Se invoca a la función que recupera los datos del CSV y los plasma en la tabla.
        # Debe ser llamada al final, luego de que label_total_factura esté inicializada.
        cargar_datos_csv()