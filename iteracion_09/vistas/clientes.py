import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os



class Cliente(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("FORMULARIO CLIENTES")
        self.geometry("925x550")
        


        # ======================================================
        #  ANCLAJE DE DIRECTORIOS (ADAPTADO A NUEVA ESTRUCTURA)
        # ======================================================
        
        DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
        DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_VISTAS)
        DB_PATH = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")



        # =====================================================
        #  MÓDULO DE NORMALIZACIÓN EXTREMA (HELPERS DE FASE 1)
        # =====================================================
        
        # Esta función busca si el texto ya existe en el catálogo para evitar redundancia.
        # Si existe, retorna su ID. Si no, lo inserta y retorna el nuevo ID.
        def obtener_o_crear(cursor, tabla, columna, valor):
            valor_limpio = str(valor).strip() if valor else "S/D"
            if not valor_limpio:
                valor_limpio = "S/D"
                
            cursor.execute(f"SELECT id FROM {tabla} WHERE {columna}=?", (valor_limpio,))
            resultado = cursor.fetchone()
            
            if resultado:
                return resultado[0]
            
            cursor.execute(f"INSERT INTO {tabla} ({columna}) VALUES (?)", (valor_limpio,))
            return cursor.lastrowid



        # ==========================================
        #  FUNCIONALIDADES DE "FORMULARIO CLIENTES"
        # ==========================================

        def cargar_datos_db():
            for item in tabla.get_children():
                tabla.delete(item)
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # CAMBIO: Extracción masiva con JOINs para reconstruir el perfil del Cliente.
            # Filtramos estrictamente por el rol 'Cliente' y verificamos que no estén dados de baja.
            cursor.execute('''
                SELECT u.id, u.nombres, u.apellidos, u.dni, t.telefono, m.mail, d.direccion, c.ciudad, p.provincia, cp.cp
                FROM usuarios u
                JOIN usuxroles ur ON u.id = ur.id_usuario
                JOIN roles r ON ur.id_rol = r.id
                LEFT JOIN usuarioxcontactos uc ON u.id = uc.id_usuario AND uc.habilitado = 1
                LEFT JOIN contactoxtelefonos ct ON uc.id = ct.id_contacto AND ct.habilitado = 1
                LEFT JOIN telefonos t ON ct.id_telefono = t.id
                LEFT JOIN contactoxmails cm ON uc.id = cm.id_contacto AND cm.habilitado = 1
                LEFT JOIN mails m ON cm.id_mail = m.id
                LEFT JOIN usuarioxubicaciones uu ON u.id = uu.id_usuario AND uu.habilitado = 1
                LEFT JOIN ubicacionxdireccion ud ON uu.id = ud.id_ubicacion AND ud.habilitado = 1
                LEFT JOIN direcciones d ON ud.id_direccion = d.id
                LEFT JOIN ubicacionxlocalidades ul ON uu.id = ul.id_ubicacion AND ul.habilitado = 1
                LEFT JOIN localidadxciudades lc ON ul.id = lc.id_localidad AND lc.habilitado = 1
                LEFT JOIN ciudades c ON lc.id_ciudad = c.id
                LEFT JOIN codigopostales cp ON lc.id_cp = cp.id
                LEFT JOIN localidadxprovincias lp ON ul.id = lp.id_localidad AND lp.habilitado = 1
                LEFT JOIN provincias p ON lp.id_provincia = p.id
                WHERE r.rol = 'Cliente' AND u.habilitado = 1 AND ur.habilitado = 1
            ''')
            filas = cursor.fetchall()
            
            for fila in filas:

                # El ID viaja oculto en iid. Limpiamos los None a "S/D".
                valores_limpios = ["S/D" if v is None else v for v in fila[1:]]
                tabla.insert("", "end", iid=fila[0], values=valores_limpios)
                
            conexion.close()

        def limpiar_campos():
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

            try:
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                
                # TRANSACCIÓN ESCALONADA DE INSERCIÓN MASIVA
                
                # 1. Tabla Central (Los clientes no tienen login, usuario y password quedan NULL).
                cursor.execute("INSERT INTO usuarios (nombres, apellidos, dni) VALUES (?, ?, ?)", (nombres, apellidos, dni))
                id_usuario = cursor.lastrowid
                
                # 2. Asignación Estricta del Rol 'Cliente'.
                id_rol = obtener_o_crear(cursor, "roles", "rol", "Cliente")
                cursor.execute("INSERT INTO usuxroles (id_usuario, id_rol) VALUES (?, ?)", (id_usuario, id_rol))
                
                # 3. Contactos.
                cursor.execute("INSERT INTO usuarioxcontactos (id_usuario) VALUES (?)", (id_usuario,))
                id_contacto = cursor.lastrowid
                
                id_telefono = obtener_o_crear(cursor, "telefonos", "telefono", telefono)
                cursor.execute("INSERT INTO contactoxtelefonos (id_contacto, id_telefono) VALUES (?, ?)", (id_contacto, id_telefono))
                
                id_mail = obtener_o_crear(cursor, "mails", "mail", email)
                cursor.execute("INSERT INTO contactoxmails (id_contacto, id_mail) VALUES (?, ?)", (id_contacto, id_mail))
                
                # 4. Ubicaciones.
                cursor.execute("INSERT INTO usuarioxubicaciones (id_usuario) VALUES (?)", (id_usuario,))
                id_ubicacion = cursor.lastrowid
                
                id_direccion = obtener_o_crear(cursor, "direcciones", "direccion", domicilio)
                cursor.execute("INSERT INTO ubicacionxdireccion (id_ubicacion, id_direccion) VALUES (?, ?)", (id_ubicacion, id_direccion))
                
                cursor.execute("INSERT INTO ubicacionxlocalidades (id_ubicacion) VALUES (?)", (id_ubicacion,))
                id_localidad = cursor.lastrowid
                
                id_ciudad = obtener_o_crear(cursor, "ciudades", "ciudad", ciudad)
                id_cp = obtener_o_crear(cursor, "codigopostales", "cp", codigo_postal)
                cursor.execute("INSERT INTO localidadxciudades (id_localidad, id_ciudad, id_cp) VALUES (?, ?, ?)", (id_localidad, id_ciudad, id_cp))
                
                id_provincia = obtener_o_crear(cursor, "provincias", "provincia", provincia)
                cursor.execute("INSERT INTO localidadxprovincias (id_localidad, id_provincia) VALUES (?, ?)", (id_localidad, id_provincia))
                
                id_pais = obtener_o_crear(cursor, "paises", "pais", "Argentina")
                cursor.execute("INSERT INTO localidadxpaises (id_localidad, id_pais) VALUES (?, ?)", (id_localidad, id_pais))

                conexion.commit()
            except Exception as e:
                messagebox.showerror("Error de Transacción", f"No se pudo guardar el registro: {e}")
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

                # Parseamos "S/D" a string vacío para la UI.
                valor_mostrar = valores[i] if valores[i] != "S/D" else ""
                caja.insert(0, valor_mostrar)

        def modificar():
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            id_cliente = seleccion[0]
            
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

            try:
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                
                # 1. Actualizamos la tabla central.
                cursor.execute("UPDATE usuarios SET nombres=?, apellidos=?, dni=? WHERE id=?", (nombres, apellidos, dni, id_cliente))
                
                # 2. Desactivamos las relaciones viejas de contacto y ubicación (Borrado Lógico).
                cursor.execute("UPDATE usuarioxcontactos SET habilitado=0 WHERE id_usuario=?", (id_cliente,))
                cursor.execute("UPDATE usuarioxubicaciones SET habilitado=0 WHERE id_usuario=?", (id_cliente,))
                
                # 3. Insertamos el nuevo esquema de relaciones.
                cursor.execute("INSERT INTO usuarioxcontactos (id_usuario) VALUES (?)", (id_cliente,))
                id_contacto = cursor.lastrowid
                
                id_telefono = obtener_o_crear(cursor, "telefonos", "telefono", telefono)
                cursor.execute("INSERT INTO contactoxtelefonos (id_contacto, id_telefono) VALUES (?, ?)", (id_contacto, id_telefono))
                
                id_mail = obtener_o_crear(cursor, "mails", "mail", email)
                cursor.execute("INSERT INTO contactoxmails (id_contacto, id_mail) VALUES (?, ?)", (id_contacto, id_mail))
                
                cursor.execute("INSERT INTO usuarioxubicaciones (id_usuario) VALUES (?)", (id_cliente,))
                id_ubicacion = cursor.lastrowid
                
                id_direccion = obtener_o_crear(cursor, "direcciones", "direccion", domicilio)
                cursor.execute("INSERT INTO ubicacionxdireccion (id_ubicacion, id_direccion) VALUES (?, ?)", (id_ubicacion, id_direccion))
                
                cursor.execute("INSERT INTO ubicacionxlocalidades (id_ubicacion) VALUES (?)", (id_ubicacion,))
                id_localidad = cursor.lastrowid
                
                id_ciudad = obtener_o_crear(cursor, "ciudades", "ciudad", ciudad)
                id_cp = obtener_o_crear(cursor, "codigopostales", "cp", codigo_postal)
                cursor.execute("INSERT INTO localidadxciudades (id_localidad, id_ciudad, id_cp) VALUES (?, ?, ?)", (id_localidad, id_ciudad, id_cp))
                
                id_provincia = obtener_o_crear(cursor, "provincias", "provincia", provincia)
                cursor.execute("INSERT INTO localidadxprovincias (id_localidad, id_provincia) VALUES (?, ?)", (id_localidad, id_provincia))
                
                id_pais = obtener_o_crear(cursor, "paises", "pais", "Argentina")
                cursor.execute("INSERT INTO localidadxpaises (id_localidad, id_pais) VALUES (?, ?)", (id_localidad, id_pais))

                conexion.commit()
            except Exception as e:
                messagebox.showerror("Error", f"Fallo al actualizar: {e}")
            finally:
                conexion.close()

            limpiar_campos()
            cargar_datos_db()

        def eliminar():
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            try:
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                
                for item in seleccion:

                    # Aplicamos el Borrado Lógico.
                    cursor.execute("UPDATE usuarios SET habilitado=0 WHERE id=?", (item,))
                    cursor.execute("UPDATE usuxroles SET habilitado=0 WHERE id_usuario=?", (item,))
                    
                conexion.commit()
            except sqlite3.Error as e:
                messagebox.showerror("Operación Bloqueada", str(e))
            finally:
                conexion.close()
            
            limpiar_campos()
            cargar_datos_db()



        # ==================================
        #  CAMPOS DEL "FORMULARIO CLIENTES"
        # ==================================

        # CAMBIO: Se eliminó el campo 'Edad' para alinear la interfaz con la tabla central 'usuarios' normalizada.
        tk.Label(self, text="Nombres").grid(row=1, column=0, pady=5, sticky="e", padx=5)
        caja_nombres = tk.Entry(self, width=30)
        caja_nombres.grid(row=1, column=1)

        tk.Label(self, text="Apellidos").grid(row=2, column=0, pady=5, sticky="e", padx=5)
        caja_apellidos = tk.Entry(self, width=30)
        caja_apellidos.grid(row=2, column=1)

        tk.Label(self, text="DNI").grid(row=3, column=0, pady=5, sticky="e", padx=5)
        caja_dni = tk.Entry(self, width=30)
        caja_dni.grid(row=3, column=1)

        tk.Label(self, text="Teléfono").grid(row=4, column=0, pady=5, sticky="e", padx=5)
        caja_telefono = tk.Entry(self, width=30)
        caja_telefono.grid(row=4, column=1)

        tk.Label(self, text="Email").grid(row=5, column=0, pady=5, sticky="e", padx=5)
        caja_email = tk.Entry(self, width=30)
        caja_email.grid(row=5, column=1)

        tk.Label(self, text="Dirección").grid(row=6, column=0, pady=5, sticky="e", padx=5)
        caja_domicilio = tk.Entry(self, width=30)
        caja_domicilio.grid(row=6, column=1)

        tk.Label(self, text="Ciudad").grid(row=7, column=0, pady=5, sticky="e", padx=5)
        caja_ciudad = tk.Entry(self, width=30)
        caja_ciudad.grid(row=7, column=1)

        tk.Label(self, text="Provincia").grid(row=8, column=0, pady=5, sticky="e", padx=5)
        caja_provincia = tk.Entry(self, width=30)
        caja_provincia.grid(row=8, column=1)

        tk.Label(self, text="Código Postal").grid(row=9, column=0, pady=5, sticky="e", padx=5)
        caja_codigo_postal = tk.Entry(self, width=30)
        caja_codigo_postal.grid(row=9, column=1)



        # =========================================================
        #  BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # =========================================================

        boton_guardar = tk.Button(self, text="Guardar Cliente", command=guardar, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_guardar.grid(row=2, column=3, padx=20)

        boton_modificar = tk.Button(self, text="Modificar Cliente", command=modificar, bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_modificar.grid(row=4, column=3, padx=20)

        boton_eliminar = tk.Button(self, text="Eliminar Cliente", command=eliminar, bg="#F44336", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_eliminar.grid(row=6, column=3, padx=20)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy, bg="#9E9E9E", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_cerrar_ventana.grid(row=8, column=3, padx=20)



        # ============================
        #  TABLA DE DATOS DE CLIENTES
        # ============================
        
        columnas = ("Nombres", "Apellidos", "DNI", "Teléfono", "Email", "Dirección", "Ciudad", "Provincia", "Cód. Postal")

        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=100)

        tabla.grid(row=11, column=0, columnspan=5, pady=20, padx=10, sticky="nsew")
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)



        # ========================
        #  CARGA INICIAL DE DATOS
        # ========================
        
        cargar_datos_db()