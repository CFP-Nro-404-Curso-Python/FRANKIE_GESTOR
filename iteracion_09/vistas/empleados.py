import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os


class Empleado(tk.Toplevel):
    # CAMBIO: Recibimos id_actual y rol_actual desde panel_control.py para replicar el blindaje RBAC.
    def __init__(self, parent, id_actual, rol_actual):
        super().__init__(parent)

        self.title("FORMULARIO EMPLEADOS (RRHH)")
        self.geometry("1020x600")

        # ======================================================
        #  ANCLAJE DE DIRECTORIOS (ADAPTADO A NUEVA ESTRUCTURA)
        # ======================================================
        
        DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
        DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_VISTAS)
        DB_PATH = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")



        # =====================================================
        #  MÓDULO DE NORMALIZACIÓN EXTREMA (HELPERS DE FASE 1)
        # =====================================================
        
        # Esta función busca si el texto (ej. "Mar del Plata") ya existe en el catálogo.
        # Si existe, retorna su ID para evitar redundancia. Si no, lo inserta y retorna el nuevo ID.
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



        # ===========================================
        #  FUNCIONALIDADES DE "FORMULARIO EMPLEADOS"
        # ===========================================

        def cargar_datos_db():
            for item in tabla.get_children():
                tabla.delete(item)
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # CAMBIO: Se utiliza la Vista SQL definida en esquema.sql que pre-calcula los JOINs.
            cursor.execute('''
                SELECT id, nombres, apellidos, dni, telefono, mail, direccion, ciudad, provincia, cp, rol
                FROM vista_empleados_activos
            ''')
            filas = cursor.fetchall()
            
            for fila in filas:

                # El ID viaja oculto en el parámetro iid. Transformamos los None en "S/D" por si acaso.
                valores_limpios = ["S/D" if v is None else v for v in fila[1:]]
                tabla.insert("", "end", iid=fila[0], values=valores_limpios)
                
            conexion.close()

        def limpiar_campos():
            cajas = [caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email, 
                     caja_domicilio, caja_ciudad, caja_provincia, caja_cp]
            for caja in cajas:
                caja.delete(0, tk.END)
            caja_rol.set("")
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
            cp = caja_cp.get().strip()
            rol = caja_rol.get()

            
            if not nombres or not apellidos or not rol:
                messagebox.showwarning("Validación", "Nombres, Apellidos y Rol Organizacional son obligatorios.")
                return

            # CAMBIO: Barrera RBAC FRONT-TO-BACK. Bloquea la creación de perfiles superiores.
            # Evita que un Gerente desde RRHH cree un Administrador Maestro.
            if rol_actual == "Gerente" and rol in ["Administrador", "Gerente"]:
                messagebox.showerror("Acceso Denegado", "Privilegios insuficientes para crear perfiles de esta jerarquía organizativa.")
                limpiar_campos()
                return

            try:
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                


                # ============================================
                #  TRANSACCIÓN ESCALONADA DE INSERCIÓN MASIVA
                # ============================================

                # 1. Tabla Central.
                cursor.execute("INSERT INTO usuarios (nombres, apellidos, dni) VALUES (?, ?, ?)", (nombres, apellidos, dni))
                id_usuario = cursor.lastrowid
                
                # 2. Roles (Tabla Intermedia).
                id_rol = obtener_o_crear(cursor, "roles", "rol", rol)
                cursor.execute("INSERT INTO usuxroles (id_usuario, id_rol) VALUES (?, ?)", (id_usuario, id_rol))
                
                # 3. Contactos (Árbol Jerárquico).
                cursor.execute("INSERT INTO usuarioxcontactos (id_usuario) VALUES (?)", (id_usuario,))
                id_contacto = cursor.lastrowid
                
                id_telefono = obtener_o_crear(cursor, "telefonos", "telefono", telefono)
                cursor.execute("INSERT INTO contactoxtelefonos (id_contacto, id_telefono) VALUES (?, ?)", (id_contacto, id_telefono))
                
                id_mail = obtener_o_crear(cursor, "mails", "mail", email)
                cursor.execute("INSERT INTO contactoxmails (id_contacto, id_mail) VALUES (?, ?)", (id_contacto, id_mail))
                
                # 4. Ubicaciones (Árbol Geográfico).
                cursor.execute("INSERT INTO usuarioxubicaciones (id_usuario) VALUES (?)", (id_usuario,))
                id_ubicacion = cursor.lastrowid
                
                id_direccion = obtener_o_crear(cursor, "direcciones", "direccion", domicilio)
                cursor.execute("INSERT INTO ubicacionxdireccion (id_ubicacion, id_direccion) VALUES (?, ?)", (id_ubicacion, id_direccion))
                
                cursor.execute("INSERT INTO ubicacionxlocalidades (id_ubicacion) VALUES (?)", (id_ubicacion,))
                id_localidad = cursor.lastrowid
                
                id_ciudad = obtener_o_crear(cursor, "ciudades", "ciudad", ciudad)
                id_cp = obtener_o_crear(cursor, "codigopostales", "cp", cp)
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
                     caja_domicilio, caja_ciudad, caja_provincia, caja_cp]
                     
            for i, caja in enumerate(cajas):
                caja.delete(0, tk.END)

                # Parseamos los "S/D" de vuelta a strings vacíos para que la UI no quede sucia.
                valor_mostrar = valores[i] if valores[i] != "S/D" else ""
                caja.insert(0, valor_mostrar)
                
            caja_rol.set(valores[9])

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
            cp = caja_cp.get().strip()
            rol = caja_rol.get()

            if not nombres or not apellidos or not rol:
                messagebox.showwarning("Validación", "Nombres, Apellidos y Rol Organizacional son obligatorios.")
                return

            try:
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()

                # CAMBIO: Extracción del rol objetivo y validación RBAC idéntica a usuarios.py.
                cursor.execute('''
                    SELECT r.rol FROM usuarios u
                    JOIN usuxroles ur ON u.id = ur.id_usuario
                    JOIN roles r ON ur.id_rol = r.id
                    WHERE u.id=? AND ur.habilitado=1
                ''', (id_usuario,))
                resultado_rol_target = cursor.fetchone()
                
                if not resultado_rol_target:
                    conexion.close()
                    return
                    
                rol_target = resultado_rol_target[0]
                
                # Barrera: Un Gerente no puede modificar a un Admin ni a otro Gerente en RRHH, 
                # salvo que esté editando sus propios datos de contacto.
                if rol_actual == "Gerente":
                    if rol_target == "Administrador" or (rol_target == "Gerente" and int(id_usuario) != id_actual):
                        messagebox.showerror("Acceso Denegado", "Privilegios insuficientes para modificar a este empleado.")
                        conexion.close()
                        return
                                
                # 1. Actualizamos la tabla central (solo pisa los datos base, no destruye las credenciales de Login).
                cursor.execute("UPDATE usuarios SET nombres=?, apellidos=?, dni=? WHERE id=?", (nombres, apellidos, dni, id_usuario))
                
                # 2. Desactivamos las relaciones viejas para mantener el historial (Borrado Lógico).
                cursor.execute("UPDATE usuxroles SET habilitado=0 WHERE id_usuario=?", (id_usuario,))
                cursor.execute("UPDATE usuarioxcontactos SET habilitado=0 WHERE id_usuario=?", (id_usuario,))
                cursor.execute("UPDATE usuarioxubicaciones SET habilitado=0 WHERE id_usuario=?", (id_usuario,))
                
                # 3. Insertamos el nuevo esquema de relaciones.
                id_rol = obtener_o_crear(cursor, "roles", "rol", rol)
                cursor.execute("INSERT INTO usuxroles (id_usuario, id_rol) VALUES (?, ?)", (id_usuario, id_rol))
                
                cursor.execute("INSERT INTO usuarioxcontactos (id_usuario) VALUES (?)", (id_usuario,))
                id_contacto = cursor.lastrowid
                
                id_telefono = obtener_o_crear(cursor, "telefonos", "telefono", telefono)
                cursor.execute("INSERT INTO contactoxtelefonos (id_contacto, id_telefono) VALUES (?, ?)", (id_contacto, id_telefono))
                
                id_mail = obtener_o_crear(cursor, "mails", "mail", email)
                cursor.execute("INSERT INTO contactoxmails (id_contacto, id_mail) VALUES (?, ?)", (id_contacto, id_mail))
                
                cursor.execute("INSERT INTO usuarioxubicaciones (id_usuario) VALUES (?)", (id_usuario,))
                id_ubicacion = cursor.lastrowid
                
                id_direccion = obtener_o_crear(cursor, "direcciones", "direccion", domicilio)
                cursor.execute("INSERT INTO ubicacionxdireccion (id_ubicacion, id_direccion) VALUES (?, ?)", (id_ubicacion, id_direccion))
                
                cursor.execute("INSERT INTO ubicacionxlocalidades (id_ubicacion) VALUES (?)", (id_ubicacion,))
                id_localidad = cursor.lastrowid
                
                id_ciudad = obtener_o_crear(cursor, "ciudades", "ciudad", ciudad)
                id_cp = obtener_o_crear(cursor, "codigopostales", "cp", cp)
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
            
            id_usuario_borrar = seleccion[0]
                
            try:
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()

                # CAMBIO: Validación RBAC antes de ejecutar el borrado lógico.
                cursor.execute('''
                    SELECT r.rol FROM usuarios u
                    JOIN usuxroles ur ON u.id = ur.id_usuario
                    JOIN roles r ON ur.id_rol = r.id
                    WHERE u.id=? AND ur.habilitado=1
                ''', (id_usuario_borrar,))
                rol_a_borrar = cursor.fetchone()[0]

                if rol_actual == "Gerente" and rol_a_borrar in ["Administrador", "Gerente"]:
                    if int(id_usuario_borrar) == id_actual:
                         messagebox.showerror("Acceso Denegado", "Por políticas corporativas, no podés darte de baja a vos mismo. Contactá a RRHH/Administración.")
                    else:
                         messagebox.showerror("Acceso Denegado", "Privilegios insuficientes para despedir o dar de baja a este empleado.")
                    conexion.close()
                    return
                
                # Aplicamos el Borrado Lógico en cascada manual.
                for item in seleccion:
                    cursor.execute("UPDATE usuarios SET habilitado=0 WHERE id=?", (item,))
                    cursor.execute("UPDATE usuxroles SET habilitado=0 WHERE id_usuario=?", (item,))
                    
                conexion.commit()
                
            except sqlite3.Error as e:

                # Captura el trigger de seguridad si intentan borrar al último admin.
                messagebox.showerror("Operación Bloqueada", str(e))
            finally:
                conexion.close()
            
            limpiar_campos()
            cargar_datos_db()



        # ===================================
        #  CAMPOS DEL "FORMULARIO EMPLEADOS"
        # ===================================

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

        tk.Label(self, text="Cód. Postal").grid(row=9, column=0, pady=5, sticky="e", padx=5)
        caja_cp = tk.Entry(self, width=30)
        caja_cp.grid(row=9, column=1)

        tk.Label(self, text="Rol Organizacional").grid(row=10, column=0, pady=5, sticky="e", padx=5)
        roles_disponibles = ['Administrador', 'Gerente', 'Empleado - Ventas', 'Empleado - Compras']
        caja_rol = ttk.Combobox(self, values=roles_disponibles, state="readonly", width=27)
        caja_rol.grid(row=10, column=1)



        # =========================================================
        #  BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # =========================================================

        boton_guardar = tk.Button(self, text="Guardar Perfil", command=guardar, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_guardar.grid(row=3, column=3, padx=20)

        boton_modificar = tk.Button(self, text="Modificar Perfil", command=modificar, bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_modificar.grid(row=5, column=3, padx=20)

        boton_eliminar = tk.Button(self, text="Eliminar Perfil", command=eliminar, bg="#F44336", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_eliminar.grid(row=7, column=3, padx=20)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy, bg="#9E9E9E", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_cerrar_ventana.grid(row=9, column=3, padx=20)



        # =============================
        #  TABLA DE DATOS DE EMPLEADOS
        # =============================

        columnas = ("Nombres", "Apellidos", "DNI", "Teléfono", "Email", "Dirección", "Ciudad", "Provincia", "CP", "Rol")

        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)

        for col in columnas:
            tabla.heading(col, text=col)

            # Ajustamos un ancho base, pero la ventana es resizable.
            tabla.column(col, width=100)

        tabla.grid(row=11, column=0, columnspan=5, pady=20, padx=10, sticky="nsew")
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)



        # ========================
        #  CARGA INICIAL DE DATOS
        # ========================
        
        cargar_datos_db()