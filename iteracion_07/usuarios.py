import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
# Se importa bcrypt para la generación y validación de hashes seguros.
import bcrypt



class Usuario(tk.Toplevel):
    def __init__(self, parent, rol_actual):
        super().__init__(parent)
        
        self.title("GESTIÓN DE USUARIOS")
        # Ampliamos un poco la ventana para acomodar los nuevos campos y columnas.
        self.geometry("850x550")
        


        # =======================================
        #  ANCLAJE DE DIRECTORIO Y BASE DE DATOS
        # =======================================

        DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
        DB_PATH = os.path.join(DIRECTORIO_ACTUAL, "db", "frankie_gestor.db")



        # ==================================
        #  FUNCIONALIDADES DE BASE DE DATOS
        # ==================================

        def cargar_datos_db():
            for item in tabla.get_children():
                tabla.delete(item)
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            # Extraemos también nombres y apellidos para poblar la grilla de la UI.
            cursor.execute("SELECT id, usuario, rol, nombres, apellidos FROM usuarios")
            filas = cursor.fetchall()
            
            for fila in filas:
                # fila[0] es el ID oculto.
                tabla.insert("", "end", iid=fila[0], values=(fila[1], fila[2], fila[3], fila[4]))
            conexion.close()

        def limpiar_campos():
            # Limpieza de las nuevas cajas de texto.
            caja_nombres.delete(0, tk.END)
            caja_apellidos.delete(0, tk.END)
            caja_usuario.delete(0, tk.END)
            caja_password.delete(0, tk.END)
            caja_rol.set("")
            # El foco ahora va al primer campo del formulario.
            caja_nombres.focus_set()

        def guardar():
            # Capturamos nombres y apellidos.
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            usuario = caja_usuario.get().strip()
            password = caja_password.get().strip()
            rol = caja_rol.get()

            # Actualizamos la barrera de validación de campos vacíos.
            if not nombres or not apellidos or not usuario or not password or not rol:
                messagebox.showwarning("Validación", "Todos los campos son obligatorios.")
                return

            # BARRERA RBAC FRONT-TO-BACK: Bloquea la creación de roles superiores heredados de la grilla.
            if rol_actual == "Gerente" and rol in ["Administrador", "Gerente"]:
                messagebox.showerror("Acceso Denegado", "Privilegios insuficientes para crear perfiles de esta jerarquía.")
                limpiar_campos()
                return

            # Encriptación de la contraseña utilizando Bcrypt antes de guardarla.
            password_bytes = password.encode('utf-8')
            sal = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, sal).decode('utf-8')

            try:
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                # Sentencia DML actualizada para insertar nombres, apellidos y el HASH de la contraseña.
                cursor.execute('''
                    INSERT INTO usuarios (usuario, password, rol, nombres, apellidos)
                    VALUES (?, ?, ?, ?, ?)
                ''', (usuario, password_hash, rol, nombres, apellidos))
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
            
            # Poblamos los nuevos campos con la información de la grilla.
            caja_nombres.delete(0, tk.END)
            caja_nombres.insert(0, valores[2])
            caja_apellidos.delete(0, tk.END)
            caja_apellidos.insert(0, valores[3])
            
            # La contraseña se deja en blanco por seguridad. Si quieren modificarla, deben tipearla.
            caja_password.delete(0, tk.END)

        def modificar():
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            id_usuario = seleccion[0]
            # Captura de los nuevos campos.
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            usuario = caja_usuario.get().strip()
            password = caja_password.get().strip()
            rol = caja_rol.get()

            # Validamos que los campos obligatorios (excluyendo password que puede quedar igual) no estén vacíos.
            if not nombres or not apellidos or not usuario or not rol:
                messagebox.showwarning("Validación", "Nombres, Apellidos, Usuario y Rol son obligatorios.")
                return

            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()

            # BARRERA RBAC: Evita que un Gerente modifique cuentas de igual o mayor jerarquía.
            cursor.execute("SELECT rol FROM usuarios WHERE id=?", (id_usuario,))
            rol_target = cursor.fetchone()[0]
            
            if rol_actual == "Gerente" and rol_target in ["Administrador", "Gerente"]:
                messagebox.showerror("Acceso Denegado", "Privilegios insuficientes para modificar a este usuario.")
                conexion.close()
                return
            
            try:
                # Lógica bifurcada: Si tipeó contraseña nueva, se encripta y actualiza. Si la dejó en blanco, se mantiene el hash viejo.
                if password:
                    # Encriptación del nuevo password introducido.
                    password_bytes = password.encode('utf-8')
                    sal = bcrypt.gensalt()
                    password_hash = bcrypt.hashpw(password_bytes, sal).decode('utf-8')
                    
                    cursor.execute('''UPDATE usuarios SET 
                                      usuario=?, password=?, rol=?, nombres=?, apellidos=? 
                                      WHERE id=?''', 
                                   (usuario, password_hash, rol, nombres, apellidos, id_usuario))
                else:
                    # Actualizamos el resto de los datos (incluyendo nombres/apellidos) sin tocar la password.
                    cursor.execute('''UPDATE usuarios SET 
                                      usuario=?, rol=?, nombres=?, apellidos=? 
                                      WHERE id=?''', 
                                   (usuario, rol, nombres, apellidos, id_usuario))
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
            
            # Obtenemos el rol del usuario que se intentó seleccionar.
            cursor.execute("SELECT rol FROM usuarios WHERE id=?", (id_usuario,))
            rol_a_borrar = cursor.fetchone()[0]

            # BARRERA RBAC: Evita que un Gerente elimine cuentas de igual o mayor jerarquía.
            if rol_actual == "Gerente" and rol_a_borrar in ["Administrador", "Gerente"]:
                messagebox.showerror("Acceso Denegado", "Privilegios insuficientes para eliminar a este usuario.")
                conexion.close()
                return

            if rol_a_borrar == "Administrador":
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol='Administrador'")
                total_admins = cursor.fetchone()[0]
                if total_admins <= 1:
                    messagebox.showerror("Operación Bloqueada", "No podés eliminar al único Administrador del sistema.")
                    conexion.close()
                    return

            cursor.execute("DELETE FROM usuarios WHERE id=?", (id_usuario,))
            conexion.commit()
            conexion.close()
            
            limpiar_campos()
            cargar_datos_db()



        # =====================
        #  INTERFAZ DE USUARIO
        # =====================

        frame_form = tk.Frame(self)
        frame_form.pack(pady=20)

        # Inserción de campos Nombre y Apellido al principio del formulario.
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

        # Botonera.
        frame_botones = tk.Frame(self)
        frame_botones.pack(pady=10)

        tk.Button(frame_botones, text="Guardar", command=guardar, bg="#4CAF50", fg="white", width=12).grid(row=0, column=0, padx=5)
        tk.Button(frame_botones, text="Modificar", command=modificar, bg="#2196F3", fg="white", width=12).grid(row=0, column=1, padx=5)
        tk.Button(frame_botones, text="Eliminar", command=eliminar, bg="#F44336", fg="white", width=12).grid(row=0, column=2, padx=5)

        # Grilla de Usuarios.
        # Expandimos las columnas del Treeview para reflejar nombres y apellidos.
        columnas = ("Usuario", "Rol", "Nombres", "Apellidos")
        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=8)
        tabla.heading("Usuario", text="Usuario")
        tabla.heading("Rol", text="Rol del Sistema")
        tabla.heading("Nombres", text="Nombres")
        tabla.heading("Apellidos", text="Apellidos")
        
        # Ajustamos el ancho para que entre bien en la ventana ampliada.
        tabla.column("Usuario", width=150)
        tabla.column("Rol", width=150)
        tabla.column("Nombres", width=200)
        tabla.column("Apellidos", width=200)
        
        tabla.pack(pady=10, padx=20, fill="x")
        
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)

        cargar_datos_db()