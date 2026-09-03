# Es necesario exportar tkinter para que tk.Toplevel pueda ser reconocido.
import tkinter as tk
# Necesario para el manejo de tablas mediante Treeview.
from tkinter import ttk
# Importa módulos nativos para manejo de directorios y SQLite.
import sqlite3
import os



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


        # ===========================================
        #  FUNCIONALIDADES DE "FORMULARIO EMPLEADOS"
        # ===========================================

        #  Migración a SQLite y Anclaje de Directorio
        # --------------------------------------------
        # Obtenemos la ruta absoluta de donde está alojado este script (.py)
        DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))

        # Construimos la ruta absoluta hacia la carpeta "db"
        CARPETA_DB = os.path.join(DIRECTORIO_ACTUAL, "db")
        os.makedirs(CARPETA_DB, exist_ok=True)

        # Construimos la ruta absoluta hacia la base de datos
        DB_PATH = os.path.join(CARPETA_DB, "frankie_gestor.db")

        # DDL (Data Definition Language): Inicializa la tabla si no existe.
        def crear_tabla_empleados():
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS empleados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombres TEXT,
                    apellidos TEXT,
                    dni TEXT,
                    telefono TEXT,
                    email TEXT,
                    domicilio TEXT,
                    legajo TEXT,
                    cargo TEXT,
                    sector TEXT,
                    sueldo TEXT
                )
            ''')
            conexion.commit()
            conexion.close()

        # DML (Data Manipulation Language): Lectura de datos.
        def cargar_datos_db():
            # Limpiamos la tabla visual antes de recargar para evitar duplicados.
            for item in tabla.get_children():
                tabla.delete(item)
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM empleados")
            filas = cursor.fetchall()
            
            for fila in filas:
                # fila[0] contiene el 'id'. Lo usamos como 'iid' interno del Treeview.
                # fila[1:] contiene el resto de los datos visibles.
                tabla.insert("", "end", iid=fila[0], values=fila[1:])
            conexion.close()

        def limpiar_campos():
            cajas = [caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email, caja_domicilio, caja_legajo, caja_cargo, caja_sector, 
                     caja_sueldo]
                     
            for caja in cajas:
                caja.delete(0, tk.END)
            
            caja_nombres.focus_set()

        def guardar():
            nombres = caja_nombres.get()
            apellidos = caja_apellidos.get()
            dni = caja_dni.get()
            telefono = caja_telefono.get()
            email = caja_email.get()
            domicilio = caja_domicilio.get()
            legajo = caja_legajo.get()
            cargo = caja_cargo.get()
            sector = caja_sector.get()
            sueldo = caja_sueldo.get()

            #  Operación INSERT
            # ------------------
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            cursor.execute('''
                INSERT INTO empleados (nombres, apellidos, dni, telefono, email, domicilio, legajo, cargo, sector, sueldo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nombres, apellidos, dni, telefono, email, domicilio, legajo, cargo, sector, sueldo))
            conexion.commit()
            conexion.close()

            limpiar_campos()
            cargar_datos_db()

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            
            if not seleccion:
                return
                
            valores = tabla.item(seleccion[0], "values")
            
            cajas = [caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email, caja_domicilio, caja_legajo, caja_cargo, caja_sector, 
                     caja_sueldo]
                     
            for i, caja in enumerate(cajas):
                caja.delete(0, tk.END)
                caja.insert(0, valores[i])

        def modificar():
            seleccion = tabla.selection()
            
            if not seleccion:
                return
            
            # Extraemos el ID oculto que asignamos a la fila.
            id_empleado = seleccion[0]
            
            nombres = caja_nombres.get()
            apellidos = caja_apellidos.get()
            dni = caja_dni.get()
            telefono = caja_telefono.get()
            email = caja_email.get()
            domicilio = caja_domicilio.get()
            legajo = caja_legajo.get()
            cargo = caja_cargo.get()
            sector = caja_sector.get()
            sueldo = caja_sueldo.get()

            #  Operación UPDATE
            # ------------------
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            cursor.execute('''
                UPDATE empleados SET 
                nombres=?, apellidos=?, dni=?, telefono=?, email=?, domicilio=?, legajo=?, cargo=?, sector=?, sueldo=?
                WHERE id=?
            ''', (nombres, apellidos, dni, telefono, email, domicilio, legajo, cargo, sector, sueldo, id_empleado))
            conexion.commit()
            conexion.close()

            limpiar_campos()
            cargar_datos_db()

        def eliminar():
            seleccion = tabla.selection()
            
            if not seleccion:
                return
                
            #  Operación DELETE
            # ------------------
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            for item in seleccion:
                # El 'item' contiene el ID de la base de datos.
                cursor.execute("DELETE FROM empleados WHERE id=?", (item,))
                
            conexion.commit()
            conexion.close()
            
            limpiar_campos()
            cargar_datos_db()



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

        boton_guardar = tk.Button(self, text="Guardar Empleado", command=guardar)
        boton_guardar.grid(row=3, column=3)

        boton_modificar = tk.Button(self, text="Modificar Empleado", command=modificar)
        boton_modificar.grid(row=5, column=3)

        boton_eliminar = tk.Button(self, text="Eliminar Empleado", command=eliminar)
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

        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)



        # ========================
        #  CARGA INICIAL DE DATOS
        # ========================

        # Se crea la tabla si no existe y luego se leen los datos a la grilla.
        crear_tabla_empleados()
        cargar_datos_db()