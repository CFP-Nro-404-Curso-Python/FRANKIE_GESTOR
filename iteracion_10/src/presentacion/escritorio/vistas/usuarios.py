import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys



# ==========================================================
#  1. ANCLAJE DE DIRECTORIOS E INTEGRACIÓN CON CLIENTE HTTP
# ==========================================================

# Subimos 4 niveles desde src/presentacion/escritorio/vistas/ hasta la raíz del proyecto.
DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_ESCRITORIO = os.path.dirname(DIRECTORIO_VISTAS)
DIRECTORIO_PRESENTACION = os.path.dirname(DIRECTORIO_ESCRITORIO)
DIRECTORIO_SRC = os.path.dirname(DIRECTORIO_PRESENTACION)
DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_SRC)

for ruta in (DIRECTORIO_RAIZ, DIRECTORIO_ESCRITORIO, DIRECTORIO_VISTAS):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

from src.presentacion.escritorio.cliente_api import cliente_http, ErrorClienteAPI


class Usuario(tk.Toplevel):
    """
     Ventana de administración de credenciales y roles de acceso al sistema.
     Opera 100% como cliente HTTP: delega el hashing Bcrypt y las reglas RBAC al Backend.
    """

    def __init__(self, parent, id_actual, rol_actual):
        super().__init__(parent)
        
        self.title("GESTIÓN DE USUARIOS")
        self.geometry("750x550")
        self.id_actual = id_actual
        self.rol_actual = rol_actual



        # ===================================================
        #  2. FUNCIONALIDADES CONSUMIENDO LA API REST (HTTP)
        # ===================================================

        def cargar_datos_api():
            """
             Consulta todos los perfiles activos en GET /api/perfiles y filtra
             los actores internos del sistema (excluyendo Clientes y Proveedores).
            """
            for item in tabla.get_children():
                tabla.delete(item)
                
            try:
                perfiles = cliente_http.listar_perfiles()
                for p in perfiles:
                    if p.get("rol") not in ("Cliente", "Proveedor"):
                        usuario_mostrar = p.get("usuario") if p.get("usuario") else "[Sin Credenciales]"
                        tabla.insert(
                            "",
                            "end",
                            iid=str(p["id"]),
                            values=(usuario_mostrar, p["rol"], p["nombres"], p["apellidos"])
                        )
            except ErrorClienteAPI as e:
                messagebox.showerror("Error de Comunicación", str(e))

        def limpiar_campos():
            caja_nombres.delete(0, tk.END)
            caja_apellidos.delete(0, tk.END)
            caja_usuario.delete(0, tk.END)
            caja_password.delete(0, tk.END)
            caja_rol.set("")
            caja_nombres.focus_set()

        def guardar():
            """
             Envía los datos a POST /api/perfiles para dar de alta un nuevo usuario.
             El Backend se encarga de validar el permiso RBAC y encriptar la clave con Bcrypt.
            """
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            usuario = caja_usuario.get().strip()
            password = caja_password.get().strip()
            rol = caja_rol.get()

            if not nombres or not apellidos or not usuario or not password or not rol:
                messagebox.showwarning("Validación", "Todos los campos son obligatorios en este módulo.")
                return

            # Validación preventiva en interfaz (respaldada por la validación RBAC del servidor).
            if rol_actual == "Gerente" and rol in ["Administrador", "Gerente"]:
                messagebox.showerror("Acceso Denegado", "Privilegios insuficientes para crear perfiles de esta jerarquía.")
                limpiar_campos()
                return

            datos_nuevo_perfil = {
                "nombres": nombres,
                "apellidos": apellidos,
                "dni": "00000000",  # Valor base para altas rápidas desde el módulo de credenciales.
                "rol": rol,
                "usuario": usuario,
                "password_plana": password
            }

            try:
                cliente_http.crear_perfil(datos_nuevo_perfil, id_operador=id_actual)
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror("Error al Guardar", str(e))

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
            """
             Envía los cambios a PUT /api/perfiles/{id}. Si el campo contraseña está vacío,
             no se envía 'password_plana' para que el Backend conserve el hash actual.
            """
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            id_usuario_destino = int(seleccion[0])
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            usuario = caja_usuario.get().strip()
            password = caja_password.get().strip()
            rol = caja_rol.get()

            if not nombres or not apellidos or not usuario or not rol:
                messagebox.showwarning("Validación", "Nombres, Apellidos, Usuario y Rol son obligatorios.")
                return

            datos_modificados = {
                "nombres": nombres,
                "apellidos": apellidos,
                "rol": rol,
                "usuario": usuario
            }

            # Solo enviamos la contraseña nueva si el operador escribió algo en el campo.
            if password:
                datos_modificados["password_plana"] = password

            try:
                cliente_http.modificar_perfil(id_usuario_destino, datos_modificados, id_operador=id_actual)
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror("Acceso Denegado / Error", str(e))

        def eliminar():
            """
             Solicita la baja lógica (habilitado = 0) enviando DELETE /api/perfiles/{id}.
             Respeta tanto las políticas RBAC como el trigger que protege al último Administrador.
            """
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            id_usuario_destino = int(seleccion[0])

            try:
                cliente_http.eliminar_perfil(id_usuario_destino, id_operador=id_actual)
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror("Operación Bloqueada", str(e))



        # ========================
        #  3. INTERFAZ DE USUARIO
        # ========================

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

        cargar_datos_api()