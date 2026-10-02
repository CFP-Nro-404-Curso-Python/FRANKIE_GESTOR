import tkinter as tk
from tkinter import ttk
import sqlite3
import os



class Empleado(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("FORMULARIO EMPLEADOS")
        self.geometry("1005x550")



        # =======================================
        #  ANCLAJE DE DIRECTORIO Y BASE DE DATOS
        # =======================================
        
        # CAMBIO ARQUITECTÓNICO: Subimos un nivel en el árbol de directorios para encontrar la carpeta /db.

        DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
        DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_VISTAS)
        DB_PATH = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")



        # ===========================================
        #  FUNCIONALIDADES DE "FORMULARIO EMPLEADOS"
        # ===========================================

        # CAMBIO: Se eliminó la función crear_tabla_empleados().
        # La generación de la base de datos ahora está delegada y centralizada en login.py mediante esquema.sql.

        def cargar_datos_db():
            for item in tabla.get_children():
                tabla.delete(item)
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # CAMBIO - VISTAS FILTRADAS (JOIN):
            # Reconstruimos la información del empleado utilizando UNION para traer tanto a Vendedores como Compradores.
            # Los campos exclusivos como Legajo, Sueldo y Sector ya no existen en el esquema unificado de usuarios.

            consulta_sql = '''
                SELECT u.id, u.nombres, u.apellidos, u.dni, 
                       t.telefono, m.mail, 
                       d.direccion, r.rol
                FROM usuarios u
                JOIN usuxroles ur ON u.id = ur.id_usuario
                JOIN roles r ON ur.id_rol = r.id
                LEFT JOIN usuarioxcontactos uc ON u.id = uc.id_usuario
                LEFT JOIN contactoxtelefonos ct ON uc.id = ct.id_contacto
                LEFT JOIN telefonos t ON ct.id_telefono = t.id
                LEFT JOIN contactoxmails cm ON uc.id = cm.id_contacto
                LEFT JOIN mails m ON cm.id_mail = m.id
                LEFT JOIN usuarioxubicaciones uu ON u.id = uu.id_usuario
                LEFT JOIN ubicacionxdireccion ud ON uu.id = ud.id_ubicacion
                LEFT JOIN direcciones d ON ud.id_direccion = d.id
                WHERE r.rol IN ('Empleado - Ventas', 'Empleado - Compras') AND u.habilitado = 1
            '''
            cursor.execute(consulta_sql)
            filas = cursor.fetchall()
            
            for fila in filas:
                tabla.insert("", "end", iid=fila[0], values=fila[1:])
            conexion.close()

        def limpiar_campos():

            # CAMBIO: Se removieron caja_legajo, caja_sueldo, caja_sector y caja_cargo por incompatibilidad de esquema.
            # Se agregó caja_rol para poder seleccionar el tipo de empleado.

            cajas = [caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email, caja_domicilio]
            for caja in cajas:
                caja.delete(0, tk.END)
            caja_rol.set("")
            caja_nombres.focus_set()

        def guardar():
            nombres = caja_nombres.get()
            apellidos = caja_apellidos.get()
            dni = caja_dni.get()
            telefono = caja_telefono.get()
            email = caja_email.get()
            domicilio = caja_domicilio.get()
            rol_seleccionado = caja_rol.get()

            if not rol_seleccionado:
                print("Error: Debe asignar un rol al empleado.")
                return

            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # FUNCION HELPER para normalización extrema.

            def obtener_o_crear(tabla_db, columna_db, valor):
                cursor.execute(f"SELECT id FROM {tabla_db} WHERE {columna_db} = ?", (valor,))
                res = cursor.fetchone()
                if res: return res[0]
                cursor.execute(f"INSERT INTO {tabla_db} ({columna_db}) VALUES (?)", (valor,))
                return cursor.lastrowid

            # 1. TABLA CENTRAL (Usuarios).

            cursor.execute("INSERT INTO usuarios (nombres, apellidos, dni) VALUES (?, ?, ?)", (nombres, apellidos, dni))
            id_usuario = cursor.lastrowid
            
            # 2. ROL (Garantizamos que sea catalogado como el rol seleccionado en la interfaz).

            id_rol = obtener_o_crear('roles', 'rol', rol_seleccionado)
            cursor.execute("INSERT INTO usuxroles (id_usuario, id_rol) VALUES (?, ?)", (id_usuario, id_rol))

            # 3. CONTACTOS (Atomización).

            cursor.execute("INSERT INTO usuarioxcontactos (id_usuario) VALUES (?)", (id_usuario,))
            id_contacto = cursor.lastrowid
            
            id_telefono = obtener_o_crear('telefonos', 'telefono', telefono)
            cursor.execute("INSERT INTO contactoxtelefonos (id_contacto, id_telefono) VALUES (?, ?)", (id_contacto, id_telefono))
            
            id_mail = obtener_o_crear('mails', 'mail', email)
            cursor.execute("INSERT INTO contactoxmails (id_contacto, id_mail) VALUES (?, ?)", (id_contacto, id_mail))

            # 4. UBICACIONES (Solo dirección, ya que en el diagrama de cátedra no se exigen siempre datos geográficos completos).
            cursor.execute("INSERT INTO usuarioxubicaciones (id_usuario) VALUES (?)", (id_usuario,))
            id_ubicacion = cursor.lastrowid
            
            id_direccion = obtener_o_crear('direcciones', 'direccion', domicilio)
            cursor.execute("INSERT INTO ubicacionxdireccion (id_ubicacion, id_direccion) VALUES (?, ?)", (id_ubicacion, id_direccion))

            conexion.commit()
            conexion.close()

            limpiar_campos()
            cargar_datos_db()

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            valores = tabla.item(seleccion[0], "values")
            
            cajas = [caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email, caja_domicilio]
            for i, caja in enumerate(cajas):
                caja.delete(0, tk.END)
                caja.insert(0, valores[i])
                
            caja_rol.set(valores[6]) # El índice 6 del Treeview ahora contiene el Rol.

        def modificar():
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            id_empleado = seleccion[0]
            
            nombres = caja_nombres.get()
            apellidos = caja_apellidos.get()
            dni = caja_dni.get()
            telefono = caja_telefono.get()
            email = caja_email.get()
            domicilio = caja_domicilio.get()
            rol_seleccionado = caja_rol.get()

            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            def obtener_o_crear(tabla_db, columna_db, valor):
                cursor.execute(f"SELECT id FROM {tabla_db} WHERE {columna_db} = ?", (valor,))
                res = cursor.fetchone()
                if res: return res[0]
                cursor.execute(f"INSERT INTO {tabla_db} ({columna_db}) VALUES (?)", (valor,))
                return cursor.lastrowid

            # 1. Actualizamos datos principales.

            cursor.execute("UPDATE usuarios SET nombres=?, apellidos=?, dni=? WHERE id=?", (nombres, apellidos, dni, id_empleado))
            
            # 2. Actualizamos Rol.

            id_rol = obtener_o_crear('roles', 'rol', rol_seleccionado)
            cursor.execute("UPDATE usuxroles SET id_rol = ? WHERE id_usuario = ?", (id_rol, id_empleado))
            
            # 3. Actualizamos mapeo de Contactos.

            id_telefono = obtener_o_crear('telefonos', 'telefono', telefono)
            cursor.execute('''
                UPDATE contactoxtelefonos SET id_telefono = ? 
                WHERE id_contacto = (SELECT id FROM usuarioxcontactos WHERE id_usuario = ?)
            ''', (id_telefono, id_empleado))

            id_mail = obtener_o_crear('mails', 'mail', email)
            cursor.execute('''
                UPDATE contactoxmails SET id_mail = ? 
                WHERE id_contacto = (SELECT id FROM usuarioxcontactos WHERE id_usuario = ?)
            ''', (id_mail, id_empleado))

            # 4. Actualizamos mapeo de Ubicaciones.

            id_direccion = obtener_o_crear('direcciones', 'direccion', domicilio)
            cursor.execute('''
                UPDATE ubicacionxdireccion SET id_direccion = ? 
                WHERE id_ubicacion = (SELECT id FROM usuarioxubicaciones WHERE id_usuario = ?)
            ''', (id_direccion, id_empleado))

            conexion.commit()
            conexion.close()

            limpiar_campos()
            cargar_datos_db()

        def eliminar():
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # CAMBIO: Aplicación estricta de Baja Lógica (Soft Delete).

            for item in seleccion:
                cursor.execute("UPDATE usuarios SET habilitado = 0 WHERE id=?", (item,))
                
            conexion.commit()
            conexion.close()
            
            limpiar_campos()
            cargar_datos_db()



        # ===================================
        #  CAMPOS DEL "FORMULARIO EMPLEADOS"
        # ===================================

        # CAMBIO: UI Refactorizada para adaptarse a la unificación de entidades del Esquema 08.
        
        tk.Label(self, text="Nombres").grid(row=1, column=0, pady=5, sticky="e", padx=5)
        caja_nombres = tk.Entry(self)
        caja_nombres.grid(row=1, column=1)

        tk.Label(self, text="Apellidos").grid(row=2, column=0, pady=5, sticky="e", padx=5)
        caja_apellidos = tk.Entry(self)
        caja_apellidos.grid(row=2, column=1)

        tk.Label(self, text="DNI").grid(row=3, column=0, pady=5, sticky="e", padx=5)
        caja_dni = tk.Entry(self)
        caja_dni.grid(row=3, column=1)

        tk.Label(self, text="Teléfono").grid(row=4, column=0, pady=5, sticky="e", padx=5)
        caja_telefono = tk.Entry(self)
        caja_telefono.grid(row=4, column=1)

        tk.Label(self, text="Email").grid(row=5, column=0, pady=5, sticky="e", padx=5)
        caja_email = tk.Entry(self)
        caja_email.grid(row=5, column=1)

        tk.Label(self, text="Domicilio").grid(row=6, column=0, pady=5, sticky="e", padx=5)
        caja_domicilio = tk.Entry(self)
        caja_domicilio.grid(row=6, column=1)

        tk.Label(self, text="Sector / Área").grid(row=7, column=0, pady=5, sticky="e", padx=5)
        caja_rol = ttk.Combobox(self, values=["Empleado - Ventas", "Empleado - Compras"], state="readonly", width=17)
        caja_rol.grid(row=7, column=1)



        # =========================================================
        #  BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # =========================================================

        boton_guardar = tk.Button(self, text="Guardar Empleado", command=guardar, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_guardar.grid(row=3, column=3, padx=20)

        boton_modificar = tk.Button(self, text="Modificar Empleado", command=modificar, bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_modificar.grid(row=5, column=3, padx=20)

        boton_eliminar = tk.Button(self, text="Eliminar Empleado", command=eliminar, bg="#F44336", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_eliminar.grid(row=7, column=3, padx=20)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy, bg="#9E9E9E", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_cerrar_ventana.grid(row=9, column=3, padx=20)



        # =============================
        #  TABLA DE DATOS DE EMPLEADOS
        # =============================

        # CAMBIO: Adaptamos las columnas del Treeview para reflejar la eliminación de Legajo, Sector, Cargo y Sueldo.
        
        columnas = ("Nombres", "Apellidos", "DNI", "Teléfono", "Email", "Domicilio", "Área Asignada")

        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=120)

        tabla.grid(row=11, column=0, columnspan=5, pady=20, padx=10)
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)



        # ========================
        #  CARGA INICIAL DE DATOS
        # ========================
        cargar_datos_db()