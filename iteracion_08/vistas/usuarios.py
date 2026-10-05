import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import bcrypt



class Usuario(tk.Toplevel):
    def __init__(self, parent, rol_actual):
        super().__init__(parent)
        
        self.title("GESTIÓN DE USUARIOS")
        self.geometry("750x550")
        


        # =======================================================================
        #  ANCLAJE DE DIRECTORIO Y BASE DE DATOS (REFACTORIZACIÓN DE ESTRUCTURA)
        # =======================================================================

        # CAMBIO: Adaptación a la nueva estructura de carpetas (vistas -> raíz -> db).
        DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
        DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_VISTAS)
        DB_PATH = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")



        # ==================================
        #  FUNCIONALIDADES DE BASE DE DATOS
        # ==================================

        # CAMBIO: Función Helper. Como el modelo de datos ahora está normalizado, necesitamos convertir el texto 
        # del rol que elige el usuario en el ComboBox al ID numérico que corresponde en la tabla 'roles'.
        def obtener_id_rol(cursor, nombre_rol):
            cursor.execute("SELECT id FROM roles WHERE rol = ?", (nombre_rol,))
            resultado = cursor.fetchone()
            if resultado:
                return resultado[0]
            else:
                # Si el rol no existe en el catálogo, lo insertamos dinámicamente y retornamos el nuevo ID.
                cursor.execute("INSERT INTO roles (rol) VALUES (?)", (nombre_rol,))
                return cursor.lastrowid

        def cargar_datos_db():
            for item in tabla.get_children():
                tabla.delete(item)
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # CAMBIO: La columna 'rol' ya no existe en la tabla usuarios.
            # Se requiere un JOIN con la tabla puente 'usuxroles' y el catálogo 'roles'.
            # Además, filtramos por 'habilitado = 1' para ocultar los usuarios dados de baja lógica.
            cursor.execute('''
                SELECT u.id, u.usuario, r.rol, u.nombres, u.apellidos 
                FROM usuarios u
                JOIN usuxroles ur ON u.id = ur.id_usuario
                JOIN roles r ON ur.id_rol = r.id
                WHERE u.habilitado = 1 AND ur.habilitado = 1
            ''')
            filas = cursor.fetchall()
            
            for fila in filas:
                tabla.insert("", "end", iid=fila[0], values=(fila[1], fila[2], fila[3], fila[4]))
            conexion.close()

        def limpiar_campos():
            caja_nombres.delete(0, tk.END)
            caja_apellidos.delete(0, tk.END)
            caja_usuario.delete(0, tk.END)
            caja_password.delete(0, tk.END)
            caja_rol.set("")
            caja_nombres.focus_set()

        def guardar():
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            usuario = caja_usuario.get().strip()
            password = caja_password.get().strip()
            rol = caja_rol.get()

            if not nombres or not apellidos or not usuario or not password or not rol:
                messagebox.showwarning("Validación", "Todos los campos son obligatorios.")
                return

            if rol_actual == "Gerente" and rol in ["Administrador", "Gerente"]:
                messagebox.showerror("Acceso Denegado", "Privilegios insuficientes para crear perfiles de esta jerarquía.")
                limpiar_campos()
                return

            password_bytes = password.encode('utf-8')
            sal = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, sal).decode('utf-8')

            try:
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                
                # CAMBIO: Transacción en 2 pasos para respetar la Normalización Extrema.
                # 1. Insertamos al usuario en la tabla central (sin rol).
                cursor.execute('''
                    INSERT INTO usuarios (usuario, password, nombres, apellidos)
                    VALUES (?, ?, ?, ?)
                ''', (usuario, password_hash, nombres, apellidos))
                
                id_nuevo_usuario = cursor.lastrowid
                
                # 2. Obtenemos el ID del rol y lo vinculamos en la tabla puente (usuxroles).
                id_rol = obtener_id_rol(cursor, rol)
                cursor.execute('''
                    INSERT INTO usuxroles (id_usuario, id_rol)
                    VALUES (?, ?)
                ''', (id_nuevo_usuario, id_rol))
                
                conexion.commit()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "El nombre de usuario ya existe. Elegí otro.")
            finally:
                conexion.close()
                
            limpiar_campos()
            cargar_datos_db()

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            valores = tabla.item(seleccion[0], "values")
            caja_usuario.delete(0, tk.END)
            caja_usuario.insert(0, valores[0])
            caja_rol.set(valores[1])
            
            caja_nombres.delete(0, tk.END)
            caja_nombres.insert(0, valores[2])
            caja_apellidos.delete(0, tk.END)
            caja_apellidos.insert(0, valores[3])
            
            caja_password.delete(0, tk.END)

        def modificar():
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            id_usuario = seleccion[0]
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            usuario = caja_usuario.get().strip()
            password = caja_password.get().strip()
            rol = caja_rol.get()

            if not nombres or not apellidos or not usuario or not rol:
                messagebox.showwarning("Validación", "Nombres, Apellidos, Usuario y Rol son obligatorios.")
                return

            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()

            # CAMBIO: Barrera RBAC actualizada al nuevo modelo con JOINs.
            cursor.execute('''
                SELECT r.rol 
                FROM usuarios u
                JOIN usuxroles ur ON u.id = ur.id_usuario
                JOIN roles r ON ur.id_rol = r.id
                WHERE u.id = ? AND u.habilitado = 1
            ''', (id_usuario,))
            rol_target = cursor.fetchone()[0]
            
            if rol_actual == "Gerente" and rol_target in ["Administrador", "Gerente"]:
                messagebox.showerror("Acceso Denegado", "Privilegios insuficientes para modificar a este usuario.")
                conexion.close()
                return
            
            try:
                # CAMBIO: Actualizamos la tabla central (usuarios).
                if password:
                    password_bytes = password.encode('utf-8')
                    sal = bcrypt.gensalt()
                    password_hash = bcrypt.hashpw(password_bytes, sal).decode('utf-8')
                    
                    cursor.execute('''UPDATE usuarios SET 
                                      usuario=?, password=?, nombres=?, apellidos=? 
                                      WHERE id=?''', 
                                   (usuario, password_hash, nombres, apellidos, id_usuario))
                else:
                    cursor.execute('''UPDATE usuarios SET 
                                      usuario=?, nombres=?, apellidos=? 
                                      WHERE id=?''', 
                                   (usuario, nombres, apellidos, id_usuario))
                
                # CAMBIO: Actualizamos la tabla puente (usuxroles).
                id_rol = obtener_id_rol(cursor, rol)
                cursor.execute('''
                    UPDATE usuxroles SET id_rol = ? WHERE id_usuario = ?
                ''', (id_rol, id_usuario))
                
                conexion.commit()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "El nombre de usuario ya está en uso.")
            finally:
                conexion.close()

            limpiar_campos()
            cargar_datos_db()

        def eliminar():
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            id_usuario = seleccion[0]
            
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # CAMBIO: Obtenemos el rol mediante JOIN para la validación de seguridad.
            cursor.execute('''
                SELECT r.rol FROM usuarios u
                JOIN usuxroles ur ON u.id = ur.id_usuario
                JOIN roles r ON ur.id_rol = r.id
                WHERE u.id = ?
            ''', (id_usuario,))
            rol_a_borrar = cursor.fetchone()[0]

            if rol_actual == "Gerente" and rol_a_borrar in ["Administrador", "Gerente"]:
                messagebox.showerror("Acceso Denegado", "Privilegios insuficientes para eliminar a este usuario.")
                conexion.close()
                return

            if rol_a_borrar == "Administrador":
                cursor.execute('''
                    SELECT COUNT(*) FROM usuarios u 
                    JOIN usuxroles ur ON u.id = ur.id_usuario 
                    JOIN roles r ON ur.id_rol = r.id 
                    WHERE r.rol = 'Administrador' AND u.habilitado = 1
                ''')
                total_admins = cursor.fetchone()[0]
                if total_admins <= 1:
                    messagebox.showerror("Operación Bloqueada", "No podés dar de baja al único Administrador del sistema.")
                    conexion.close()
                    return

            # ===============================================
            #  CAMBIO CRÍTICO: IMPLEMENTACIÓN DE BAJA LÓGICA
            # ===============================================

            # Se eliminaron los comandos DELETE FROM para respetar la política de no destrucción de datos de la cátedra. 
            # Ahora se setea habilitado = 0 tanto en el registro matriz como en sus relaciones directas.
            
            try:
                # Si esto falla, el Trigger 'trg_proteger_ultimo_admin' en DB abortará.
                cursor.execute("UPDATE usuarios SET habilitado = 0 WHERE id = ?", (id_usuario,))
                cursor.execute("UPDATE usuxroles SET habilitado = 0 WHERE id_usuario = ?", (id_usuario,))
                conexion.commit()
            except sqlite3.Error as e:
                messagebox.showerror("Error de Base de Datos", f"Transacción abortada: {e}")
            finally:
                conexion.close()
            
            limpiar_campos()
            cargar_datos_db()



        # =====================
        #  INTERFAZ DE USUARIO
        # =====================

        frame_form = tk.Frame(self)
        frame_form.pack(pady=20)

        tk.Label(frame_form, text="Nombres:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        caja_nombres = tk.Entry(frame_form, width=30)
        caja_nombres.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(frame_form, text="Apellidos:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        caja_apellidos = tk.Entry(frame_form, width=30)
        caja_apellidos.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(frame_form, text="Usuario:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        caja_usuario = tk.Entry(frame_form, width=30)
        caja_usuario.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(frame_form, text="Contraseña:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        caja_password = tk.Entry(frame_form, width=30, show="*")
        caja_password.grid(row=3, column=1, padx=10, pady=5)

        tk.Label(frame_form, text="Rol Asignado:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        
        roles_permitidos = ["Empleado - Ventas", "Empleado - Compras"]
        if rol_actual == "Administrador":
            roles_permitidos = ["Administrador", "Gerente"] + roles_permitidos
            
        caja_rol = ttk.Combobox(frame_form, values=roles_permitidos, state="readonly", width=27)
        caja_rol.grid(row=4, column=1, padx=10, pady=5)

        frame_botones = tk.Frame(self)
        frame_botones.pack(pady=10)

        tk.Button(frame_botones, text="Guardar", command=guardar, bg="#4CAF50", fg="white", width=12).grid(row=0, column=0, padx=5)
        tk.Button(frame_botones, text="Modificar", command=modificar, bg="#2196F3", fg="white", width=12).grid(row=0, column=1, padx=5)
        tk.Button(frame_botones, text="Eliminar", command=eliminar, bg="#F44336", fg="white", width=12).grid(row=0, column=2, padx=5)

        columnas = ("Usuario", "Rol", "Nombres", "Apellidos")
        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=8)
        tabla.heading("Usuario", text="Usuario")
        tabla.heading("Rol", text="Rol del Sistema")
        tabla.heading("Nombres", text="Nombres")
        tabla.heading("Apellidos", text="Apellidos")
        
        tabla.column("Usuario", width=150)
        tabla.column("Rol", width=150)
        tabla.column("Nombres", width=200)
        tabla.column("Apellidos", width=200)
        
        tabla.pack(pady=10, padx=20, fill="x")
        
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)

        cargar_datos_db()