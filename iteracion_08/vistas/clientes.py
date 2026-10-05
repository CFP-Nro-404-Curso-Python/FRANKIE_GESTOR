import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os



class Cliente(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("FORMULARIO CLIENTES")
        self.geometry("1005x550")
        


        # =======================================
        #  ANCLAJE DE DIRECTORIO Y BASE DE DATOS
        # =======================================

        # CAMBIO: Adaptación de la ruta a la nueva estructura de carpetas (vistas -> raíz -> db).
        DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
        DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_VISTAS)
        DB_PATH = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")



        # ==========================================
        #  FUNCIONALIDADES DE "FORMULARIO CLIENTES"
        # ==========================================
        
        # CAMBIO: Se eliminó la función "crear_tabla_clientes" porque la base de datos ahora 
        # está centralizada y se construye íntegramente mediante el archivo 'esquema.sql'.

        # CAMBIO HELPER: Función auxiliar para evitar registros duplicados en los catálogos.
        # Si la ciudad o la provincia ya existe, devuelve su ID. Si no, la inserta y devuelve el nuevo ID.
        def obtener_o_crear_catalogo(cursor, tabla, columna, valor):
            cursor.execute(f"SELECT id FROM {tabla} WHERE {columna} = ?", (valor,))
            resultado = cursor.fetchone()
            if resultado:
                return resultado[0]
            cursor.execute(f"INSERT INTO {tabla} ({columna}) VALUES (?)", (valor,))
            return cursor.lastrowid

        def cargar_datos_db():
            for item in tabla.get_children():
                tabla.delete(item)
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # CAMBIO: Consulta monumental para recolectar la información despedazada.
            # Como los clientes ahora son "usuarios", usamos JOINs para unir las tablas maestras, las tablas 
            # puente y extraer únicamente a los que tienen el rol de "Cliente" y están habilitados.
            cursor.execute('''
                SELECT u.id, u.nombres, u.apellidos, u.dni, 
                       t.telefono, m.mail, 
                       d.direccion, c.ciudad, p.provincia, cp.cp
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
                LEFT JOIN ubicacionxlocalidades ul ON uu.id = ul.id_ubicacion
                LEFT JOIN localidadxciudades lc ON ul.id = lc.id_localidad
                LEFT JOIN ciudades c ON lc.id_ciudad = c.id
                LEFT JOIN codigopostales cp ON lc.id_cp = cp.id
                LEFT JOIN localidadxprovincias lp ON ul.id = lp.id_localidad
                LEFT JOIN provincias p ON lp.id_provincia = p.id
                WHERE r.rol = 'Cliente' AND u.habilitado = 1
            ''')
            filas = cursor.fetchall()
            
            for fila in filas:
                tabla.insert("", "end", iid=fila[0], values=fila[1:])
            conexion.close()

        def limpiar_campos():

            # CAMBIO: Se retiró "caja_edad" ya que la cátedra lo eliminó del esquema relacional.
            cajas = [caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email, 
                     caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal]
                     
            for caja in cajas:
                caja.delete(0, tk.END)
            caja_nombres.focus_set()

        def guardar():
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            dni = caja_dni.get().strip()
            telefono = caja_telefono.get().strip()
            email = caja_email.get().strip()
            domicilio = caja_domicilio.get().strip()
            ciudad = caja_ciudad.get().strip()
            provincia = caja_provincia.get().strip()
            codigo_postal = caja_codigo_postal.get().strip()

            if not nombres or not apellidos:
                messagebox.showwarning("Validación", "Nombres y Apellidos son obligatorios.")
                return

            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            try:
                # CAMBIO: Proceso transaccional en cascada (Normalización Extrema).
                
                # 1. Creación del Usuario Central.
                cursor.execute("INSERT INTO usuarios (nombres, apellidos, dni) VALUES (?, ?, ?)", (nombres, apellidos, dni))
                id_usuario = cursor.lastrowid
                
                # 2. Asignación del Rol.
                id_rol = obtener_o_crear_catalogo(cursor, "roles", "rol", "Cliente")
                cursor.execute("INSERT INTO usuxroles (id_usuario, id_rol) VALUES (?, ?)", (id_usuario, id_rol))
                
                # 3. Creación y Vinculación de Contactos.
                cursor.execute("INSERT INTO usuarioxcontactos (id_usuario) VALUES (?)", (id_usuario,))
                id_contacto = cursor.lastrowid
                
                id_tel = obtener_o_crear_catalogo(cursor, "telefonos", "telefono", telefono)
                cursor.execute("INSERT INTO contactoxtelefonos (id_contacto, id_telefono) VALUES (?, ?)", (id_contacto, id_tel))
                
                id_mail = obtener_o_crear_catalogo(cursor, "mails", "mail", email)
                cursor.execute("INSERT INTO contactoxmails (id_contacto, id_mail) VALUES (?, ?)", (id_contacto, id_mail))
                
                # 4. Creación y Vinculación de Ubicaciones.
                cursor.execute("INSERT INTO usuarioxubicaciones (id_usuario) VALUES (?)", (id_usuario,))
                id_ubicacion = cursor.lastrowid
                
                id_dir = obtener_o_crear_catalogo(cursor, "direcciones", "direccion", domicilio)
                cursor.execute("INSERT INTO ubicacionxdireccion (id_ubicacion, id_direccion) VALUES (?, ?)", (id_ubicacion, id_dir))
                
                cursor.execute("INSERT INTO ubicacionxlocalidades (id_ubicacion) VALUES (?)", (id_ubicacion,))
                id_localidad = cursor.lastrowid
                
                id_ciudad = obtener_o_crear_catalogo(cursor, "ciudades", "ciudad", ciudad)
                id_cp = obtener_o_crear_catalogo(cursor, "codigopostales", "cp", codigo_postal)
                cursor.execute("INSERT INTO localidadxciudades (id_localidad, id_ciudad, id_cp) VALUES (?, ?, ?)", (id_localidad, id_ciudad, id_cp))
                
                id_prov = obtener_o_crear_catalogo(cursor, "provincias", "provincia", provincia)
                cursor.execute("INSERT INTO localidadxprovincias (id_localidad, id_provincia) VALUES (?, ?)", (id_localidad, id_prov))
                
                conexion.commit()
            except sqlite3.Error as e:
                messagebox.showerror("Error de Transacción", f"No se pudo guardar el cliente: {e}")
            finally:
                conexion.close()
            
            limpiar_campos()
            cargar_datos_db()

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            valores = tabla.item(seleccion[0], "values")
            
            cajas = [caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email, 
                     caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal]
                     
            for i, caja in enumerate(cajas):
                caja.delete(0, tk.END)
                caja.insert(0, valores[i])

        def modificar():
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            id_usuario = seleccion[0]
            
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            dni = caja_dni.get().strip()
            telefono = caja_telefono.get().strip()
            email = caja_email.get().strip()
            domicilio = caja_domicilio.get().strip()
            ciudad = caja_ciudad.get().strip()
            provincia = caja_provincia.get().strip()
            codigo_postal = caja_codigo_postal.get().strip()

            if not nombres or not apellidos:
                messagebox.showwarning("Validación", "Nombres y Apellidos son obligatorios.")
                return

            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            try:
                # CAMBIO: Modificación Transaccional. En lugar de hacer UPDATE sobre catálogos compartidos
                # (lo que afectaría a otros clientes de la misma ciudad), creamos/buscamos el nuevo catálogo 
                # y reasignamos las claves foráneas en las tablas pivot.
                
                # 1. Actualizamos datos directos del usuario.
                cursor.execute("UPDATE usuarios SET nombres=?, apellidos=?, dni=? WHERE id=?", (nombres, apellidos, dni, id_usuario))
                
                # 2. Actualización de Contactos (Rastreando el ID de contacto).
                cursor.execute("SELECT id FROM usuarioxcontactos WHERE id_usuario=?", (id_usuario,))
                id_contacto = cursor.fetchone()
                if id_contacto:
                    id_contacto = id_contacto[0]
                    id_tel_nuevo = obtener_o_crear_catalogo(cursor, "telefonos", "telefono", telefono)
                    cursor.execute("UPDATE contactoxtelefonos SET id_telefono=? WHERE id_contacto=?", (id_tel_nuevo, id_contacto))
                    
                    id_mail_nuevo = obtener_o_crear_catalogo(cursor, "mails", "mail", email)
                    cursor.execute("UPDATE contactoxmails SET id_mail=? WHERE id_contacto=?", (id_mail_nuevo, id_contacto))
                
                # 3. Actualización de Ubicaciones (Rastreando el ID de ubicación y localidad).
                cursor.execute("SELECT id FROM usuarioxubicaciones WHERE id_usuario=?", (id_usuario,))
                id_ubicacion = cursor.fetchone()
                if id_ubicacion:
                    id_ubicacion = id_ubicacion[0]
                    id_dir_nuevo = obtener_o_crear_catalogo(cursor, "direcciones", "direccion", domicilio)
                    cursor.execute("UPDATE ubicacionxdireccion SET id_direccion=? WHERE id_ubicacion=?", (id_dir_nuevo, id_ubicacion))
                    
                    cursor.execute("SELECT id FROM ubicacionxlocalidades WHERE id_ubicacion=?", (id_ubicacion,))
                    id_localidad = cursor.fetchone()
                    if id_localidad:
                        id_localidad = id_localidad[0]
                        id_ciudad_nueva = obtener_o_crear_catalogo(cursor, "ciudades", "ciudad", ciudad)
                        id_cp_nuevo = obtener_o_crear_catalogo(cursor, "codigopostales", "cp", codigo_postal)
                        cursor.execute("UPDATE localidadxciudades SET id_ciudad=?, id_cp=? WHERE id_localidad=?", (id_ciudad_nueva, id_cp_nuevo, id_localidad))
                        
                        id_prov_nueva = obtener_o_crear_catalogo(cursor, "provincias", "provincia", provincia)
                        cursor.execute("UPDATE localidadxprovincias SET id_provincia=? WHERE id_localidad=?", (id_prov_nueva, id_localidad))
                
                conexion.commit()
            except sqlite3.Error as e:
                messagebox.showerror("Error de Actualización", f"No se pudo modificar el cliente: {e}")
            finally:
                conexion.close()

            limpiar_campos()
            cargar_datos_db()

        def eliminar():
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # CAMBIO: Aplicación de Baja Lógica (UPDATE en lugar de DELETE).
            try:
                for item in seleccion:
                    cursor.execute("UPDATE usuarios SET habilitado = 0 WHERE id = ?", (item,))
                    cursor.execute("UPDATE usuxroles SET habilitado = 0 WHERE id_usuario = ?", (item,))
                conexion.commit()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"No se pudo dar de baja al cliente: {e}")
            finally:
                conexion.close()
            
            limpiar_campos()
            cargar_datos_db()



        # ==================================
        #  CAMPOS DEL "FORMULARIO CLIENTES"
        # ==================================
        
        # CAMBIO: La UI se reorganiza para compensar la eliminación del campo "Edad"
        # y mantener la proporción de la ventana.
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

        tk.Label(self, text="Ciudad").grid(row=7, column=0, pady=5, sticky="e", padx=5)
        caja_ciudad = tk.Entry(self)
        caja_ciudad.grid(row=7, column=1)

        tk.Label(self, text="Provincia").grid(row=8, column=0, pady=5, sticky="e", padx=5)
        caja_provincia = tk.Entry(self)
        caja_provincia.grid(row=8, column=1)

        tk.Label(self, text="Código Postal").grid(row=9, column=0, pady=5, sticky="e", padx=5)
        caja_codigo_postal = tk.Entry(self)
        caja_codigo_postal.grid(row=9, column=1)



        # =========================================================
        #  BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # =========================================================

        boton_guardar = tk.Button(self, text="Guardar Cliente", command=guardar, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_guardar.grid(row=3, column=3, padx=20)

        boton_modificar = tk.Button(self, text="Modificar Cliente", command=modificar, bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_modificar.grid(row=5, column=3, padx=20)

        boton_eliminar = tk.Button(self, text="Eliminar Cliente", command=eliminar, bg="#F44336", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_eliminar.grid(row=7, column=3, padx=20)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy, bg="#9E9E9E", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_cerrar_ventana.grid(row=9, column=3, padx=20)



        # ============================
        #  TABLA DE DATOS DE CLIENTES
        # ============================
        
        # CAMBIO: Columnas sincronizadas con la ausencia del campo Edad.
        columnas = ("Nombres", "Apellidos", "DNI", "Teléfono", "Email", "Domicilio", "Ciudad", "Provincia", "Código Postal")

        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=105) # Ajuste visual leve para compensar la columna eliminada.

        tabla.grid(row=11, column=0, columnspan=5, pady=20, padx=10)
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)



        # ========================
        #  CARGA INICIAL DE DATOS
        # ========================
        
        cargar_datos_db()