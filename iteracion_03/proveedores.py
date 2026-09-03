# Es necesario exportar tkinter para que tk.Toplevel pueda ser reconocido.
import tkinter as tk
from tkinter import ttk
# Importa módulos nativos para el manejo de persistencia en archivos CSV.
import csv
import os



class Proveedor(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("FORMULARIO PROVEEDORES")
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


        # =============================================
        #  FUNCIONALIDADES DE "FORMULARIO PROVEEDORES"
        # =============================================

        # Definimos el nombre de la carpeta contenedora.
        CARPETA_PERSISTENCIA = "persistencia"

        # Aseguramos que la carpeta exista antes de operar. exist_ok=True evita errores si ya fue creada.
        os.makedirs(CARPETA_PERSISTENCIA, exist_ok=True)

        # Definimos la constante uniendo la carpeta con el nombre del archivo de persistencia.
        ARCHIVO_CSV = os.path.join(CARPETA_PERSISTENCIA, "datos_proveedores.csv")

        # Esta función lee el CSV y carga los datos en la tabla al iniciar la ventana.
        def cargar_datos_csv():
            # Se verifica si el archivo existe usando el módulo os para evitar errores en la primera ejecución.
            if os.path.exists(ARCHIVO_CSV):
                with open(ARCHIVO_CSV, mode="r", encoding="utf-8") as archivo:
                    lector = csv.reader(archivo)
                    for fila in lector:
                        # Inserta cada fila recuperada del archivo CSV en el Treeview.
                        tabla.insert("", "end", values=fila)

        # Esta función sobrescribe el archivo CSV con los datos actuales de la tabla.
        def sobrescribir_csv():
            with open(ARCHIVO_CSV, mode="w", newline="", encoding="utf-8") as archivo:
                escritor = csv.writer(archivo)
                # Se itera sobre todos los elementos visibles en la tabla.
                for item in tabla.get_children():
                    valores = tabla.item(item, "values")
                    escritor.writerow(valores)

        def limpiar_campos():
            cajas = [caja_razon_social, caja_cuit, caja_telefono, caja_email, caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal, 
                     caja_rubro, caja_contacto]
                     
            for caja in cajas:
                caja.delete(0, tk.END)
            
            caja_razon_social.focus_set()

        def guardar():
            razon_social = caja_razon_social.get()
            cuit = caja_cuit.get()
            telefono = caja_telefono.get()
            email = caja_email.get()
            domicilio = caja_domicilio.get()
            ciudad = caja_ciudad.get()
            provincia = caja_provincia.get()
            codigo_postal = caja_codigo_postal.get()
            rubro = caja_rubro.get()
            contacto = caja_contacto.get()

            tabla.insert("","end",values=(razon_social, cuit, telefono, email, domicilio, ciudad, provincia, codigo_postal, rubro, contacto))

            limpiar_campos()
            # PERSISTENCIA: Se guarda el estado actualizado de la tabla en el archivo CSV.
            sobrescribir_csv()

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            
            if not seleccion:
                return
                
            valores = tabla.item(seleccion[0], "values")
            
            cajas = [caja_razon_social, caja_cuit, caja_telefono, caja_email, caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal, 
                     caja_rubro, caja_contacto]
                     
            for i, caja in enumerate(cajas):
                caja.delete(0, tk.END)
                caja.insert(0, valores[i])
        
        def modificar():
            seleccion = tabla.selection()
            
            if not seleccion:
                return
            
            razon_social = caja_razon_social.get()
            cuit = caja_cuit.get()
            telefono = caja_telefono.get()
            email = caja_email.get()
            domicilio = caja_domicilio.get()
            ciudad = caja_ciudad.get()
            provincia = caja_provincia.get()
            codigo_postal = caja_codigo_postal.get()
            rubro = caja_rubro.get()
            contacto = caja_contacto.get()

            tabla.item(seleccion[0], values=(razon_social, cuit, telefono, email, domicilio, ciudad, provincia, codigo_postal, rubro, contacto))

            limpiar_campos()
            # PERSISTENCIA: Se guarda el estado actualizado de la tabla en el archivo CSV.
            sobrescribir_csv()

        def eliminar():
            seleccion = tabla.selection()
            
            if not seleccion:
                return
                
            for item in seleccion:
                tabla.delete(item)
            
            limpiar_campos()
            # PERSISTENCIA: Se guarda el estado actualizado de la tabla en el archivo CSV.
            sobrescribir_csv()

        

        # =====================================
        #  CAMPOS DEL "FORMULARIO PROVEEDORES"
        # =====================================

        tk.Label(self, text="Razón Social").grid(row=1, column=0)
        caja_razon_social = tk.Entry(self)
        caja_razon_social.grid(row=1, column=1)

        tk.Label(self, text="CUIT").grid(row=2, column=0)
        caja_cuit = tk.Entry(self)
        caja_cuit.grid(row=2, column=1)

        tk.Label(self, text="Teléfono").grid(row=3, column=0)
        caja_telefono = tk.Entry(self)
        caja_telefono.grid(row=3, column=1)

        tk.Label(self, text="Email").grid(row=4, column=0)
        caja_email = tk.Entry(self)
        caja_email.grid(row=4, column=1)

        tk.Label(self, text="Domicilio").grid(row=5, column=0)
        caja_domicilio = tk.Entry(self)
        caja_domicilio.grid(row=5, column=1)

        tk.Label(self, text="Ciudad").grid(row=6, column=0)
        caja_ciudad = tk.Entry(self)
        caja_ciudad.grid(row=6, column=1)

        tk.Label(self, text="Provincia").grid(row=7, column=0)
        caja_provincia = tk.Entry(self)
        caja_provincia.grid(row=7, column=1)

        tk.Label(self, text="Código Postal").grid(row=8, column=0)
        caja_codigo_postal = tk.Entry(self)
        caja_codigo_postal.grid(row=8, column=1)

        tk.Label(self, text="Rubro").grid(row=9, column=0)
        caja_rubro = tk.Entry(self)
        caja_rubro.grid(row=9, column=1)

        tk.Label(self, text="Contacto").grid(row=10, column=0)
        caja_contacto = tk.Entry(self)
        caja_contacto.grid(row=10, column=1)



        # =========================================================
        #  BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # =========================================================

        boton_guardar = tk.Button(self, text="Guardar Proveedor", command=guardar)
        boton_guardar.grid(row=3, column=3)

        boton_modificar = tk.Button(self, text="Modificar Proveedor", command=modificar)
        boton_modificar.grid(row=5, column=3)

        boton_eliminar = tk.Button(self, text="Eliminar Proveedor", command=eliminar)
        boton_eliminar.grid(row=7, column=3)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy)
        boton_cerrar_ventana.grid(row=9, column=3)



        # ===============================
        #  TABLA DE DATOS DE PROVEEDORES
        # ===============================

        columnas = ("Razón Social", "CUIT", "Teléfono", "Email", "Domicilio", "Ciudad", "Provincia", "Código Postal", "Rubro", "Contacto")

        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=100)

        tabla.grid(row=11, column=0, columnspan=5, pady=20)

        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)


        # ============================
        #  CARGA INICIAL DE DATOS
        # ============================

        # Se invoca a la función que recupera los datos del CSV y los plasma en la tabla.
        cargar_datos_csv()