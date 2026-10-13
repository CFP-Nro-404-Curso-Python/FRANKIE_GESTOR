import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import bcrypt



class Usuario(tk.Toplevel):
    # CAMBIO: Recibimos id_actual desde panel_control.py para auditoría de auto-modificación.
    def __init__(self, parent, id_actual, rol_actual):
        super().__init__(parent)
        
        self.title("GESTIÓN DE USUARIOS")
        self.geometry("750x550")
        


        # ======================================================
        #  ANCLAJE DE DIRECTORIOS (ADAPTADO A NUEVA ESTRUCTURA)
        # ======================================================

        # CAMBIO: usuarios.py ahora reside en /vistas. Subimos un nivel para anclar en /db.
        DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
        DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_VISTAS)
        DB_PATH = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")



        # ==================================
        #  FUNCIONALIDADES DE BASE DE DATOS
        # ==================================

        def cargar_datos_db():
            for item in tabla.get_children():
                tabla.delete(item)
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # CAMBIO: Para mostrar los usuarios en la grilla sin perder información vital (como el nombre de usuario de login),
            # y dado que un empleado puede ser creado en 'empleados.py' sin usuario/password, usamos un LEFT JOIN
            # para traer a TODOS los empleados/gerentes/admins, tengan o no credenciales, y reemplazamos los NULL por un aviso visual.
            cursor.execute('''
                SELECT u.id, 
                       IFNULL(u.usuario, '[Sin Credenciales]') as usuario, 
                       r.rol, u.nombres, u.apellidos 
                FROM usuarios u
                JOIN usuxroles ur ON u.id = ur.id_usuario
                JOIN roles r ON ur.id_rol = r.id
                WHERE u.habilitado = 1 AND ur.habilitado = 1 AND r.rol NOT IN ('Cliente', 'Proveedor')
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

            # CAMBIO: La validación ahora asume que si alguien crea un usuario desde acá,
            # DEBE tener credenciales. Si lo crea desde empleados.py, no las tendrá.
            if not nombres or not apellidos or not usuario or not password or not rol:
                messagebox.showwarning("Validación", "Todos los campos son obligatorios en este módulo.")
                return
    
            # BARRERA RBAC FRONT-TO-BACK: Bloquea la creación de roles superiores.
            # Un Gerente NUNCA puede crear otro Gerente ni a un Administrador.
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
                
                # CAMBIO: Transacción escalonada (Normalización)
                # 1. Recuperamos el ID numérico del rol seleccionado desde el catálogo.
                cursor.execute("SELECT id FROM roles WHERE rol=?", (rol,))
                id_rol = cursor.fetchone()[0]

                # 2. Insertamos al usuario en la tabla central y rescatamos su nuevo ID.
                cursor.execute('''
                    INSERT INTO usuarios (usuario, password, nombres, apellidos)
                    VALUES (?, ?, ?, ?)
                ''', (usuario, password_hash, nombres, apellidos))
                id_nuevo_usuario = cursor.lastrowid
                
                # 3. Vinculamos al usuario con su rol en la tabla asociativa (N:M).
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

            # CAMBIO: Extracción de rol objetivo mediante JOIN para validar permisos RBAC.
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
            
            # CAMBIO: Barrera RBAC corregida. 
            # Si es Gerente, no puede modificar a un Admin ni a otro Gerente, 
            # EXCEPTO si el ID seleccionado coincide con su propio ID (Auto-modificación).
            if rol_actual == "Gerente":
                if rol_target == "Administrador" or (rol_target == "Gerente" and int(id_usuario) != id_actual):
                    messagebox.showerror("Acceso Denegado", "Privilegios insuficientes para modificar a este usuario.")
                    conexion.close()
                    return
            
            try:
                # 1. Modificación de datos personales y credenciales (Tabla Central).
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
                
                # 2. Modificación del Rol (Tabla Intermedia).
                cursor.execute("SELECT id FROM roles WHERE rol=?", (rol,))
                id_rol_nuevo = cursor.fetchone()[0]
                
                cursor.execute('''UPDATE usuxroles SET id_rol=? WHERE id_usuario=? AND habilitado=1''', (id_rol_nuevo, id_usuario))
                
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
            
            # Extraemos el rol del usuario a eliminar mediante JOIN.
            cursor.execute('''
                SELECT r.rol FROM usuarios u
                JOIN usuxroles ur ON u.id = ur.id_usuario
                JOIN roles r ON ur.id_rol = r.id
                WHERE u.id=? AND ur.habilitado=1
            ''', (id_usuario,))
            rol_a_borrar = cursor.fetchone()[0]

            # CAMBIO: Barrera RBAC corregida.
            # Un Gerente no puede borrar a un Administrador, a otro Gerente, NI A SÍ MISMO.
            # El borrado propio solo lo puede ejecutar un Administrador (despido/baja corporativa).
            if rol_actual == "Gerente" and rol_a_borrar in ["Administrador", "Gerente"]:
                if int(id_usuario) == id_actual:
                     messagebox.showerror("Acceso Denegado", "Por políticas de seguridad, no podés darte de baja a vos mismo. Contactá a un Administrador.")
                else:
                     messagebox.showerror("Acceso Denegado", "Privilegios insuficientes para eliminar a este usuario.")
                conexion.close()
                return
            
            try:
                # CAMBIO: Cumplimiento de requerimiento de Cátedra (Borrado Lógico).
                # En lugar de DELETE, aplicamos un UPDATE en ambas tablas para ocultar el registro.
                # Si se intenta deshabilitar al último Admin, el trigger de SQLite lanzará una 
                # excepción que será capturada por el bloque except.
                cursor.execute("UPDATE usuarios SET habilitado=0 WHERE id=?", (id_usuario,))
                cursor.execute("UPDATE usuxroles SET habilitado=0 WHERE id_usuario=?", (id_usuario,))
                conexion.commit()
            except sqlite3.Error as error_db:
                
                # Capturamos el RAISE(ABORT) emitido por el trigger de la base de datos (trg_proteger_ultimo_admin).
                messagebox.showerror("Operación Bloqueada por Motor DB", str(error_db))
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
        
        # Filtro de seguridad visual basado en rol.
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

        # Grilla de Usuarios.
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