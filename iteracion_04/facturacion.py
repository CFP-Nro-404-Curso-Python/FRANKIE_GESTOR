# Es necesario exportar tkinter para que tk.Toplevel pueda ser reconocido.
import tkinter as tk
from tkinter import ttk
# Importamos messagebox para mostrar los avisos y errores de forma gráfica.
from tkinter import messagebox
# Importa módulos nativos para el manejo de persistencia en archivos CSV.
import csv
import os



class Facturacion(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("FORMULARIO FACTURACIÓN")
        self.geometry("600x680")



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



        # =========================================================
        #  FUNCIONES DE EXTRACCIÓN DE DATOS MAESTROS (INTEGRACIÓN)
        # =========================================================

        # Nueva función que permite obtener la lista de vendedores desde el archivo CSV de empleados.
        def obtener_vendedores():
            lista = []
            if os.path.exists("datos_empleados.csv"):
                with open("datos_empleados.csv", mode="r", encoding="utf-8") as f:
                    for fila in csv.reader(f):
                        if fila and len(fila) >= 2:
                            # Concatenamos Apellido y Nombre.
                            lista.append(f"{fila[1]}, {fila[0]}")
            return lista

        # Nueva función que permite obtener la lista de clientes desde el archivo CSV de clientes.
        def obtener_clientes():
            lista = []
            if os.path.exists("datos_clientes.csv"):
                with open("datos_clientes.csv", mode="r", encoding="utf-8") as f:
                    for fila in csv.reader(f):
                        if fila and len(fila) >= 2:
                            lista.append(f"{fila[1]}, {fila[0]}")
            return lista

        # Nueva función que permite obtener la lista de productos desde el archivo CSV de stock.
        def obtener_productos():
            lista = []
            if os.path.exists("datos_stock.csv"):
                with open("datos_stock.csv", mode="r", encoding="utf-8") as f:
                    for fila in csv.reader(f):
                        if fila and len(fila) >= 2:
                            # Concatenamos Código y Descripción
                            lista.append(f"{fila[0]} - {fila[1]}")
            return lista

        # Función de evento: Se dispara al seleccionar un producto para autocompletar el precio oficial.
        def autocompletar_precio(event):
            seleccion = caja_producto.get()
            if not seleccion: return

            # Extraemos el código real separando la cadena por el guión.
            codigo_prod = seleccion.split(" - ")[0]
            
            if os.path.exists("datos_stock.csv"):
                with open("datos_stock.csv", mode="r", encoding="utf-8") as archivo:
                    for fila in csv.reader(archivo):
                        if fila and fila[0] == codigo_prod:
                            precio_venta = fila[7] # Índice 7 es Precio Venta en stock.py.
                            
                            # Desbloqueamos la caja temporalmente para inyectar el valor.
                            caja_valor.config(state="normal")
                            caja_valor.delete(0, tk.END)
                            caja_valor.insert(0, precio_venta)
                            caja_valor.config(state="readonly")
                            break
        


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
        
        # CONTROLADOR DE TRANSACCIÓN: Lee, valida y actualiza el archivo de stock físico.
        # Ahora devuelve una tupla (booleano_exito, mensaje_advertencia), que permmite procesar
        # advertencias de límite mínimo sin frenar la transacción principal.
        def gestionar_stock(codigo_buscado, variacion):
            if not os.path.exists("datos_stock.csv"):
                return False, "El archivo de sotck maestro no existe."
            
            filas = []
            exito = False
            advertencia = ""

            with open("datos_stock.csv", mode="r", encoding="utf-8") as f:
                lector = csv.reader(f)
                for fila in lector:
                    if fila and fila[0] == codigo_buscado:
                        stock_actual = float(fila[4]) # Índice 4 es Stock Actual.
                        stock_minimo = float(fila[5]) # Leemos el límite crítico.
                        nuevo_stock = stock_actual + variacion
                        
                        # Barrera estricta: Falta de stock.
                        if nuevo_stock < 0:
                            return False, f"Stock insuficiente. Quedan {int(stock_actual)} unidades."

                        # Barrera preventiva: Se alcanzó el límite mínimo de inventario (sólo disparamos
                        # advertencias cuando estamos decontando mercadería).
                        if variacion < 0 and nuevo_stock <= stock_minimo:
                            advertencia = f"El producto llegó a su stock mínimo. Quedan {int(nuevo_stock)} unidades."
                        
                        fila[4] = str(nuevo_stock)
                        exito = True
                    filas.append(fila)
            
            # Si validó correctamente, reescribimos el archivo maestro de stock.
            if exito:
                with open("datos_stock.csv", mode="w", newline="", encoding="utf-8") as f:
                    escritor = csv.writer(f)
                    escritor.writerows(filas)
            
            return exito, advertencia

        # Función refactorizada para limpiar los campos del formulario y preparar la interfaz para un nuevo ingreso.
        def limpiar_campos():
            # Desbloqueamos el valor para poder vaciarlo.
            caja_valor.config(state="normal")

            caja_producto.set("")
            caja_cantidad.delete(0, tk.END)
            caja_valor.delete(0, tk.END)
            caja_descuento.delete(0, tk.END)

            # Volvemos a bloquear el precio
            caja_valor.config(state="readonly")
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

        # Función refactorizada para guardar una nueva línea de facturación en la tabla y persistirla en el CSV.
        def guardar():
            try:
                producto = caja_producto.get()
                # Validación de Producto: No se permite guardar una línea sin producto.
                if not producto:
                    print("Error: Seleccione un producto de la lista.")
                    return

                cantidad = float(caja_cantidad.get())
                valor = float(caja_valor.get())
                descuento = float(caja_descuento.get())

                # Validación de Límites: El descuento no puede ser negativo ni mayor a 100.
                if descuento < 0 or descuento > 100:
                    # Utilizamos messagebox para mostrar un error gráfico al usuario en lugar de solo imprimirlo en consola.
                    messagebox.showerror("Validación", "El descuento por producto debe estar entre 0 y 100%.")
                    return # Cortamos la ejecución para no guardar datos anómalos.

                # INTEGRACIÓN: Verificamos y descontamos stock antes de guardar.
                codigo_prod = producto.split(" - ")[0]
                exito, msj_stock = gestionar_stock(codigo_prod, -cantidad)

                # Si falló la transacción (ej.: Stock negativo).
                if not exito:
                    messagebox.showerror("Transacción Rechazada", msj_stock)
                    return

                # Aplicación de la regla de negocio.
                total_linea = (cantidad * valor) * (1 - (descuento / 100))
                
                # Formateamos el total a 2 decimales para que se vea prolijo.
                tabla.insert("", "end", values=(producto, cantidad, valor, descuento, f"{total_linea:.2f}"))

                limpiar_campos()
                actualizar_total_factura()
                # Persistencia: Se guarda el estado actualizado de la tabla en el archivo CSV.
                sobrescribir_csv()

                # Si pasó la transacción pero arrojó una advertencia de stock crítico.
                if msj_stock:
                    messagebox.showwarning("Alerta de Reposición", msj_stock)
                
            except ValueError:
                # Mensaje de error gráfico para el usuario en caso de ingresar datos no numéricos en Cantidad o Descuento.
                messagebox.showerror("Error de Formato", "Ingrese valores numéricos válidos en Cantidad y Descuento.")

        # Refactorización de la función que permite seleccionar una fila de la tabla y autocompletar los campos del formulario.
        def seleccionar_fila(event):
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            valores = tabla.item(seleccion[0], "values")

            # Desbloqueamos, rellenamos y bloqueamos para no romper el readonly
            caja_valor.config(state="normal")

            caja_producto.set(valores[0])
            caja_cantidad.delete(0, tk.END)
            caja_cantidad.insert(0, valores[1])
            caja_valor.delete(0, tk.END)
            caja_valor.insert(0, valores[2])
            caja_descuento.delete(0, tk.END)
            caja_descuento.insert(0, valores[3])
            
            # Bloqueamos nuevamente el precio para respetar el dato del maestro de stock.
            caja_valor.config(state="readonly")
            
        # Refactorización de la función que permite modificar una línea de facturación seleccionada en la tabla y persistir los cambios en el CSV.
        def modificar():
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            try:
                producto_nuevo = caja_producto.get()
                # Validación de Producto: No se permite modificar una línea sin producto.
                if not producto_nuevo:
                    # Mensaje de error gráfico para el usuario en caso de intentar modificar sin seleccionar un producto.
                    messagebox.showerror("Error de Carga", "Seleccione un producto de la lista.")
                    return

                cantidad_nueva = float(caja_cantidad.get())
                valor_nuevo = float(caja_valor.get())
                descuento = float(caja_descuento.get())

                # Se evalúa la variable local "descuento".
                if descuento < 0 or descuento > 100:
                    messagebox.showerror("Validación", "El descuento por producto debe estar entre 0 y 100%.")
                    return

                # Datos del registro antes de modificar.
                valores_viejos = tabla.item(seleccion[0], "values")
                producto_viejo = valores_viejos[0]
                codigo_viejo = producto_viejo.split(" - ")[0]
                cantidad_vieja = float(valores_viejos[1])

                codigo_nuevo = producto_nuevo.split(" - ")[0]

                # INTEGRACIÓN (Transacción manual en 2 pasos):
                # 1. Restituimos el stock viejo.
                gestionar_stock(codigo_viejo, +cantidad_vieja)

                # 2. Intentamos deducir el stock nuevo.
                exito, msj_stock = gestionar_stock(codigo_nuevo, -cantidad_nueva)

                if not exito:
                    # Rollback de seguridad.
                    gestionar_stock(codigo_viejo, -cantidad_vieja)
                    # Mensaje de error gráfico para el usuario en caso de intentar modificar con stock insuficiente.
                    messagebox.showerror("Transacción Rechazada", "Stock insuficiente para la nueva cantidad. Se ha deshecho el cambio.")
                    return

                total_linea = (cantidad_nueva * valor_nuevo) * (1 - (descuento / 100))

                tabla.item(seleccion[0], values=(producto_nuevo, cantidad_nueva, valor_nuevo, descuento, f"{total_linea:.2f}"))

                limpiar_campos()
                actualizar_total_factura()
                # Persistencia: Se guarda el estado actualizado de la tabla en el archivo CSV.
                sobrescribir_csv()

                if msj_stock:
                    # Mensaje de advertencia gráfico para el usuario en caso de alcanzar el stock mínimo.
                    messagebox.showwarning("Alerta de Reposición", msj_stock)
                
            except ValueError:
                # Mensaje de error gráfico para el usuario en caso de ingresar datos no numéricos en Cantidad o Descuento.
                messagebox.showerror("Error de Formato",  "Ingrese valores numéricos válidos en Cantidad y Descuento.")

        # Refactorización de la función que permite eliminar una línea de facturación seleccionada en la tabla y persistir los cambios en el CSV.
        def eliminar():
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            for item in seleccion:
                valores = tabla.item(item, "values")
                codigo_prod = valores[0].split(" - ")[0]
                cantidad_a_devolver = float(valores[1])

                # INTEGRACIÓN: Devolvemos el stock eliminado al inventario físico.
                gestionar_stock(codigo_prod, +cantidad_a_devolver)

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
                    messagebox.showerror("Validación", "El descuento global debe estar entre 0 y 100%.")
                    return
                
                # 3. Calculamos el precio final.
                resultado = gran_total * (1 - (desc_porcentaje / 100))
                
                # 4. Actualizamos la vista.
                label_resultado_desc.config(text=f"Total con descuento ({desc_porcentaje}%): $ {resultado:.2f}")
            except ValueError:
                messagebox.showerror("Error", "Ingrese un porcentaje global válido.")



        # =====================================
        #  CAMPOS DEL "FORMULARIO FACTURACIÓN"
        # =====================================

        tk.Label(self, text="Datos del Vendedor").grid(row=1, column=0)
        # Reemplazado por Combobox vinculado a empleados.
        caja_datos_vendedor = ttk.Combobox(self, values=obtener_vendedores(), state="readonly", width=25)
        caja_datos_vendedor.grid(row=1, column=1)

        tk.Label(self, text="Datos del Cliente").grid(row=2, column=0)
        # Reemplazado por Combobox vinculado a clientes.
        caja_datos_cliente = ttk.Combobox(self, values=obtener_clientes(), state="readonly", width=25)
        caja_datos_cliente.grid(row=2, column=1)

        tk.Label(self, text="").grid(row=3, column=0)
        
        tk.Label(self, text="Producto").grid(row=4, column=0)
        # Reemplazado por Combobox vinculado a stock
        caja_producto = ttk.Combobox(self, values=obtener_productos(), state="readonly", width=25)
        caja_producto.grid(row=4, column=1)

        # Binding del evento de autocompletado de precio al elegir un producto
        caja_producto.bind("<<ComboboxSelected>>", autocompletar_precio)

        tk.Label(self, text="Cantidad").grid(row=5, column=0)
        caja_cantidad = tk.Entry(self)
        caja_cantidad.grid(row=5, column=1)
        
        tk.Label(self, text="Valor en $").grid(row=6, column=0)
        caja_valor = tk.Entry(self)
        caja_valor.grid(row=6, column=1)
        
        # Bloqueamos la edición manual del precio para respetar el dato del maestro de stock
        caja_valor.config(state="readonly")

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