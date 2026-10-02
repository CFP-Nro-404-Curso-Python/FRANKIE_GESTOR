import tkinter as tk
from tkinter import ttk
import sqlite3
import os



class Proveedor(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("FORMULARIO PROVEEDORES")
        self.geometry("1005x550")



        # =======================================
        #  ANCLAJE DE DIRECTORIO Y BASE DE DATOS
        # =======================================
        
        # CAMBIO ARQUITECTÓNICO: Subimos un nivel en el árbol de directorios para encontrar la carpeta /db.

        DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
        DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_VISTAS)
        DB_PATH = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")



        # =============================================
        #  FUNCIONALIDADES DE "FORMULARIO PROVEEDORES"
        # =============================================

        # CAMBIO: Se eliminó la función crear_tabla_proveedores().
        # La generación de la base de datos ahora está delegada y centralizada en login.py mediante esquema.sql.

        def cargar_datos_db():
            for item in tabla.get_children():
                tabla.delete(item)
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # CAMBIO - VISTAS FILTRADAS (JOIN):
            # Reconstruimos la información del proveedor. 
            # Atención: En el modelo unificado, la 'razon_social' se guarda en 'apellidos' 
            # y el 'rubro' no existe nativamente, por lo que usamos 'nombres' para el contacto o fantasía.

            consulta_sql = '''
                SELECT u.id, u.apellidos, u.dni, 
                       t.telefono, m.mail, 
                       d.direccion, c.ciudad, p.provincia, cp.cp, u.nombres
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
                WHERE r.rol = 'Proveedor' AND u.habilitado = 1
            '''
            cursor.execute(consulta_sql)
            filas = cursor.fetchall()
            
            for fila in filas:
                tabla.insert("", "end", iid=fila[0], values=fila[1:])
            conexion.close()

        def limpiar_campos():

            # CAMBIO: Se removió caja_rubro por incompatibilidad de esquema.

            cajas = [caja_razon_social, caja_cuit, caja_telefono, caja_email, 
                     caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal, caja_contacto]
                     
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
            contacto = caja_contacto.get()

            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # FUNCION HELPER para normalización extrema.

            def obtener_o_crear(tabla_db, columna_db, valor):
                cursor.execute(f"SELECT id FROM {tabla_db} WHERE {columna_db} = ?", (valor,))
                res = cursor.fetchone()
                if res: return res[0]
                cursor.execute(f"INSERT INTO {tabla_db} ({columna_db}) VALUES (?)", (valor,))
                return cursor.lastrowid

            # 1. TABLA CENTRAL (Usuarios - Mapeando Razón Social a Apellidos y Contacto a Nombres).

            cursor.execute("INSERT INTO usuarios (nombres, apellidos, dni) VALUES (?, ?, ?)", (contacto, razon_social, cuit))
            id_usuario = cursor.lastrowid
            
            # 2. ROL (Garantizamos que sea catalogado como Proveedor).

            id_rol = obtener_o_crear('roles', 'rol', 'Proveedor')
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
            
            cajas = [caja_razon_social, caja_cuit, caja_telefono, caja_email, caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal, caja_contacto]

            # Mapeamos los índices del Treeview a las cajas, saltando el índice 8 que era 'Rubro'.

            indices = [0, 1, 2, 3, 4, 5, 6, 7, 9]
                     
            for caja, idx in zip(cajas, indices):
                caja.delete(0, tk.END)
                caja.insert(0, valores[idx])
        
        def modificar():
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            id_proveedor = seleccion[0]
            
            razon_social = caja_razon_social.get()
            cuit = caja_cuit.get()
            telefono = caja_telefono.get()
            email = caja_email.get()
            domicilio = caja_domicilio.get()
            ciudad = caja_ciudad.get()
            provincia = caja_provincia.get()
            codigo_postal = caja_codigo_postal.get()
            contacto = caja_contacto.get()

            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            def obtener_o_crear(tabla_db, columna_db, valor):
                cursor.execute(f"SELECT id FROM {tabla_db} WHERE {columna_db} = ?", (valor,))
                res = cursor.fetchone()
                if res: return res[0]
                cursor.execute(f"INSERT INTO {tabla_db} ({columna_db}) VALUES (?)", (valor,))
                return cursor.lastrowid

            # 1. Actualizamos datos principales.

            cursor.execute("UPDATE usuarios SET nombres=?, apellidos=?, dni=? WHERE id=?", (contacto, razon_social, cuit, id_proveedor))
            
            # 2. Actualizamos mapeo de Contactos.

            id_telefono = obtener_o_crear('telefonos', 'telefono', telefono)
            cursor.execute('''
                UPDATE contactoxtelefonos SET id_telefono = ? 
                WHERE id_contacto = (SELECT id FROM usuarioxcontactos WHERE id_usuario = ?)
            ''', (id_telefono, id_proveedor))

            id_mail = obtener_o_crear('mails', 'mail', email)
            cursor.execute('''
                UPDATE contactoxmails SET id_mail = ? 
                WHERE id_contacto = (SELECT id FROM usuarioxcontactos WHERE id_usuario = ?)
            ''', (id_mail, id_proveedor))

            # 3. Actualizamos mapeo de Ubicaciones.

            id_direccion = obtener_o_crear('direcciones', 'direccion', domicilio)
            cursor.execute('''
                UPDATE ubicacionxdireccion SET id_direccion = ? 
                WHERE id_ubicacion = (SELECT id FROM usuarioxubicaciones WHERE id_usuario = ?)
            ''', (id_direccion, id_proveedor))

            id_provincia = obtener_o_crear('provincias', 'provincia', provincia)
            cursor.execute('''
                UPDATE localidadxprovincias SET id_provincia = ? 
                WHERE id_localidad = (
                    SELECT ul.id FROM ubicacionxlocalidades ul 
                    JOIN usuarioxubicaciones uu ON ul.id_ubicacion = uu.id WHERE uu.id_usuario = ?
                )
            ''', (id_provincia, id_proveedor))

            id_ciudad = obtener_o_crear('ciudades', 'ciudad', ciudad)
            id_cp = obtener_o_crear('codigopostales', 'cp', codigo_postal)
            cursor.execute('''
                UPDATE localidadxciudades SET id_ciudad = ?, id_cp = ? 
                WHERE id_localidad = (
                    SELECT ul.id FROM ubicacionxlocalidades ul 
                    JOIN usuarioxubicaciones uu ON ul.id_ubicacion = uu.id WHERE uu.id_usuario = ?
                )
            ''', (id_ciudad, id_cp, id_proveedor))

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



        # =====================================
        #  CAMPOS DEL "FORMULARIO PROVEEDORES"
        # =====================================

        # CAMBIO: Se eliminó el Entry de 'Rubro' para alinearse al esquema unificado. Se reordenaron las filas.

        tk.Label(self, text="Razón Social").grid(row=1, column=0, pady=5, sticky="e", padx=5)
        caja_razon_social = tk.Entry(self)
        caja_razon_social.grid(row=1, column=1)

        tk.Label(self, text="CUIT").grid(row=2, column=0, pady=5, sticky="e", padx=5)
        caja_cuit = tk.Entry(self)
        caja_cuit.grid(row=2, column=1)

        tk.Label(self, text="Teléfono").grid(row=3, column=0, pady=5, sticky="e", padx=5)
        caja_telefono = tk.Entry(self)
        caja_telefono.grid(row=3, column=1)

        tk.Label(self, text="Email").grid(row=4, column=0, pady=5, sticky="e", padx=5)
        caja_email = tk.Entry(self)
        caja_email.grid(row=4, column=1)

        tk.Label(self, text="Domicilio").grid(row=5, column=0, pady=5, sticky="e", padx=5)
        caja_domicilio = tk.Entry(self)
        caja_domicilio.grid(row=5, column=1)

        tk.Label(self, text="Ciudad").grid(row=6, column=0, pady=5, sticky="e", padx=5)
        caja_ciudad = tk.Entry(self)
        caja_ciudad.grid(row=6, column=1)

        tk.Label(self, text="Provincia").grid(row=7, column=0, pady=5, sticky="e", padx=5)
        caja_provincia = tk.Entry(self)
        caja_provincia.grid(row=7, column=1)

        tk.Label(self, text="Código Postal").grid(row=8, column=0, pady=5, sticky="e", padx=5)
        caja_codigo_postal = tk.Entry(self)
        caja_codigo_postal.grid(row=8, column=1)

        tk.Label(self, text="Contacto (Nombre)").grid(row=9, column=0, pady=5, sticky="e", padx=5)
        caja_contacto = tk.Entry(self)
        caja_contacto.grid(row=9, column=1)



        # =========================================================
        #  BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # =========================================================

        boton_guardar = tk.Button(self, text="Guardar Proveedor", command=guardar, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_guardar.grid(row=3, column=3, padx=20)

        boton_modificar = tk.Button(self, text="Modificar Proveedor", command=modificar, bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_modificar.grid(row=5, column=3, padx=20)

        boton_eliminar = tk.Button(self, text="Eliminar Proveedor", command=eliminar, bg="#F44336", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_eliminar.grid(row=7, column=3, padx=20)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy, bg="#9E9E9E", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_cerrar_ventana.grid(row=9, column=3, padx=20)



        # ===============================
        #  TABLA DE DATOS DE PROVEEDORES
        # ===============================

        # CAMBIO: Se mantiene la estructura visual rellenando 'Rubro' con un N/A o valor fijo para no quebrar la UI,
        # aunque los datos internos ya estén normalizados.
        
        columnas = ("Razón Social", "CUIT", "Teléfono", "Email", "Domicilio", "Ciudad", "Provincia", "Código Postal", "Rubro", "Contacto")

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