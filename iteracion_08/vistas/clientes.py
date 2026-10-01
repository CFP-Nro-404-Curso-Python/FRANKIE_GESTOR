import tkinter as tk
from tkinter import ttk
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

        # CAMBIO ARQUITECTÓNICO: Como el archivo .py ahora vive dentro de la carpeta /vistas, necesitamos subir 
        # un nivel en el árbol de directorios para encontrar la carpeta /db.

        DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
        DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_VISTAS)
        DB_PATH = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")



        # ==========================================
        #  FUNCIONALIDADES DE "FORMULARIO CLIENTES"
        # ==========================================
        
        # CAMBIO: Se eliminó la función crear_tabla_clientes(). 
        # La generación de la base de datos ahora está delegada y centralizada en login.py mediante esquema.sql.

        def cargar_datos_db():
            for item in tabla.get_children():
                tabla.delete(item)
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # CAMBIO - VISTAS FILTRADAS (JOIN): 
            # Reconstruimos la información del cliente esparcida en la arquitectura altamente normalizada.
            # Solo traemos los usuarios que tienen el rol 'Cliente' y no están dados de baja (habilitado = 1).

            consulta_sql = '''
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
            '''
            cursor.execute(consulta_sql)
            filas = cursor.fetchall()
            
            for fila in filas:
                tabla.insert("", "end", iid=fila[0], values=fila[1:])
            conexion.close()

        def limpiar_campos():
            # CAMBIO: Se removió caja_edad porque el campo 'edad' no existe en el nuevo modelo unificado de usuarios.
            cajas = [caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email, 
                     caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal]
                     
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
            ciudad = caja_ciudad.get()
            provincia = caja_provincia.get()
            codigo_postal = caja_codigo_postal.get()

            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # FUNCION HELPER: Evita repetir 20 líneas de código. Busca si un valor maestro existe, sino lo crea y 
            # retorna su ID.

            def obtener_o_crear(tabla_db, columna_db, valor):
                cursor.execute(f"SELECT id FROM {tabla_db} WHERE {columna_db} = ?", (valor,))
                res = cursor.fetchone()
                if res: return res[0]
                cursor.execute(f"INSERT INTO {tabla_db} ({columna_db}) VALUES (?)", (valor,))
                return cursor.lastrowid

            # 1. TABLA CENTRAL (Usuarios).
            
            cursor.execute("INSERT INTO usuarios (nombres, apellidos, dni) VALUES (?, ?, ?)", (nombres, apellidos, dni))
            id_usuario = cursor.lastrowid
            
            # 2. ROL (Garantizamos que sea catalogado como Cliente).

            id_rol = obtener_o_crear('roles', 'rol', 'Cliente')
            cursor.execute("INSERT INTO usuxroles (id_usuario, id_rol) VALUES (?, ?)", (id_usuario, id_rol))

            # 3. CONTACTOS (Atomización).

            cursor.execute("INSERT INTO usuarioxcontactos (id_usuario) VALUES (?)", (id_usuario,))
            id_contacto = cursor.lastrowid
            
            id_telefono = obtener_o_crear('telefonos', 'telefono', telefono)
            cursor.execute("INSERT INTO contactoxtelefonos (id_contacto, id_telefono) VALUES (?, ?)", (id_contacto, id_telefono))
            
            id_mail = obtener_o_crear('mails', 'mail', email)
            cursor.execute("INSERT INTO contactoxmails (id_contacto, id_mail) VALUES (?, ?)", (id_contacto, id_mail))

            # 4. UBICACIONES (Árbol Geográfico).

            cursor.execute("INSERT INTO usuarioxubicaciones (id_usuario) VALUES (?)", (id_usuario,))
            id_ubicacion = cursor.lastrowid
            
            id_direccion = obtener_o_crear('direcciones', 'direccion', domicilio)
            cursor.execute("INSERT INTO ubicacionxdireccion (id_ubicacion, id_direccion) VALUES (?, ?)", (id_ubicacion, id_direccion))
            
            cursor.execute("INSERT INTO ubicacionxlocalidades (id_ubicacion) VALUES (?)", (id_ubicacion,))
            id_localidad = cursor.lastrowid
            
            id_pais = obtener_o_crear('paises', 'pais', 'Argentina') # Dato por defecto
            cursor.execute("INSERT INTO localidadxpaises (id_localidad, id_pais) VALUES (?, ?)", (id_localidad, id_pais))
            
            id_provincia = obtener_o_crear('provincias', 'provincia', provincia)
            cursor.execute("INSERT INTO localidadxprovincias (id_localidad, id_provincia) VALUES (?, ?)", (id_localidad, id_provincia))
            
            id_ciudad = obtener_o_crear('ciudades', 'ciudad', ciudad)
            id_cp = obtener_o_crear('codigopostales', 'cp', codigo_postal)
            cursor.execute("INSERT INTO localidadxciudades (id_localidad, id_ciudad, id_cp) VALUES (?, ?, ?)", (id_localidad, id_ciudad, id_cp))

            conexion.commit()
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
            
            id_cliente = seleccion[0]
            nombres = caja_nombres.get()
            apellidos = caja_apellidos.get()
            dni = caja_dni.get()
            telefono = caja_telefono.get()
            email = caja_email.get()
            domicilio = caja_domicilio.get()
            ciudad = caja_ciudad.get()
            provincia = caja_provincia.get()
            codigo_postal = caja_codigo_postal.get()

            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            def obtener_o_crear(tabla_db, columna_db, valor):
                cursor.execute(f"SELECT id FROM {tabla_db} WHERE {columna_db} = ?", (valor,))
                res = cursor.fetchone()
                if res: return res[0]
                cursor.execute(f"INSERT INTO {tabla_db} ({columna_db}) VALUES (?)", (valor,))
                return cursor.lastrowid

            # 1. Actualizamos datos principales.

            cursor.execute("UPDATE usuarios SET nombres=?, apellidos=?, dni=? WHERE id=?", (nombres, apellidos, dni, id_cliente))
            
            # 2. Actualizamos mapeo de Contactos.

            id_telefono = obtener_o_crear('telefonos', 'telefono', telefono)
            cursor.execute('''
                UPDATE contactoxtelefonos SET id_telefono = ? 
                WHERE id_contacto = (SELECT id FROM usuarioxcontactos WHERE id_usuario = ?)
            ''', (id_telefono, id_cliente))

            id_mail = obtener_o_crear('mails', 'mail', email)
            cursor.execute('''
                UPDATE contactoxmails SET id_mail = ? 
                WHERE id_contacto = (SELECT id FROM usuarioxcontactos WHERE id_usuario = ?)
            ''', (id_mail, id_cliente))

            # 3. Actualizamos mapeo de Ubicaciones.

            id_direccion = obtener_o_crear('direcciones', 'direccion', domicilio)
            cursor.execute('''
                UPDATE ubicacionxdireccion SET id_direccion = ? 
                WHERE id_ubicacion = (SELECT id FROM usuarioxubicaciones WHERE id_usuario = ?)
            ''', (id_direccion, id_cliente))

            id_provincia = obtener_o_crear('provincias', 'provincia', provincia)
            cursor.execute('''
                UPDATE localidadxprovincias SET id_provincia = ? 
                WHERE id_localidad = (
                    SELECT ul.id FROM ubicacionxlocalidades ul 
                    JOIN usuarioxubicaciones uu ON ul.id_ubicacion = uu.id WHERE uu.id_usuario = ?
                )
            ''', (id_provincia, id_cliente))

            id_ciudad = obtener_o_crear('ciudades', 'ciudad', ciudad)
            id_cp = obtener_o_crear('codigopostales', 'cp', codigo_postal)
            cursor.execute('''
                UPDATE localidadxciudades SET id_ciudad = ?, id_cp = ? 
                WHERE id_localidad = (
                    SELECT ul.id FROM ubicacionxlocalidades ul 
                    JOIN usuarioxubicaciones uu ON ul.id_ubicacion = uu.id WHERE uu.id_usuario = ?
                )
            ''', (id_ciudad, id_cp, id_cliente))

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
            # Ahora la función elimina modificando el parámetro de habilitación. No usa sentencias DELETE.

            for item in seleccion:
                cursor.execute("UPDATE usuarios SET habilitado = 0 WHERE id = ?", (item,))
                
            conexion.commit()
            conexion.close()
            
            limpiar_campos()
            cargar_datos_db()



        # ==================================
        #  CAMPOS DEL "FORMULARIO CLIENTES"
        # ==================================

        # CAMBIO: Se eliminó el Entry de 'Edad' para alinearse al esquema unificado. Se reordenaron las filas.

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

        # CAMBIO: Se eliminó la columna "Edad" del Treeview.

        columnas = ("Nombres", "Apellidos", "DNI", "Teléfono", "Email", "Domicilio", "Ciudad", "Provincia", "Código Postal")

        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=100)

        tabla.grid(row=11, column=0, columnspan=5, pady=20, padx=10)
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)



        # ========================
        #  CARGA INICIAL DE DATOS
        # ========================
        
        cargar_datos_db()