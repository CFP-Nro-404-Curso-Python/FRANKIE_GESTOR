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

# Memoria auxiliar de sesión para conservar los datos de contacto y ubicación en la grilla.
_cache_legajo_rrhh = {}


class Empleado(tk.Toplevel):
    """
     Formulario de gestión de Recursos Humanos (RRHH).
     Opera 100% desacoplado de SQLite: delega altas, bajas, modificaciones y 
     validaciones jerárquicas (RBAC) a la API REST mediante cliente_http.
    """

    def __init__(self, parent, id_actual, rol_actual):
        super().__init__(parent)

        self.title("FORMULARIO EMPLEADOS (RRHH)")
        self.geometry("1020x600")
        self.id_actual = id_actual
        self.rol_actual = rol_actual



        # ==============================================
        #  2. FUNCIONALIDADES DE "FORMULARIO EMPLEADOS"
        # ==============================================

        def cargar_datos_api():
            """
             Consulta los perfiles activos mediante GET /api/perfiles y filtra
             el personal interno de la empresa (excluyendo Clientes y Proveedores).
            """
            for item in tabla.get_children():
                tabla.delete(item)
                
            try:
                perfiles = cliente_http.listar_perfiles()
                for p in perfiles:
                    if p.get("rol") not in ("Cliente", "Proveedor"):
                        id_emp = p["id"]
                        extras = _cache_legajo_rrhh.get(id_emp, {})
                        
                        valores_fila = (
                            p.get("nombres") or "S/D",
                            p.get("apellidos") or "S/D",
                            p.get("dni") or "S/D",
                            extras.get("telefono", "S/D"),
                            extras.get("email", "S/D"),
                            extras.get("direccion", "S/D"),
                            extras.get("ciudad", "S/D"),
                            extras.get("provincia", "S/D"),
                            extras.get("cp", "S/D"),
                            p.get("rol") or "S/D"
                        )
                        tabla.insert("", "end", iid=str(id_emp), values=valores_fila)
            except ErrorClienteAPI as e:
                messagebox.showerror("Error de Comunicación", str(e))

        def limpiar_campos():
            cajas = [
                caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email,
                caja_domicilio, caja_ciudad, caja_provincia, caja_cp
            ]
            for caja in cajas:
                caja.delete(0, tk.END)
            caja_rol.set("")
            caja_nombres.focus_set()

        def guardar():
            """
             Envía el alta del empleado a POST /api/perfiles.
             El Backend valida la jerarquía RBAC del operador antes de persistir.
            """
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            dni = caja_dni.get().strip() or "S/D"
            telefono = caja_telefono.get().strip() or "S/D"
            email = caja_email.get().strip() or "S/D"
            domicilio = caja_domicilio.get().strip() or "S/D"
            ciudad = caja_ciudad.get().strip() or "S/D"
            provincia = caja_provincia.get().strip() or "S/D"
            cp = caja_cp.get().strip() or "S/D"
            rol = caja_rol.get()

            if not nombres or not apellidos or not rol:
                messagebox.showwarning("Validación", "Nombres, Apellidos y Rol Organizacional son obligatorios.")
                return

            # Barrera preventiva en UI (respaldada por la validación RBAC del servidor).
            if rol_actual == "Gerente" and rol in ["Administrador", "Gerente"]:
                messagebox.showerror(
                    "Acceso Denegado",
                    "Privilegios insuficientes para crear perfiles de esta jerarquía organizativa."
                )
                limpiar_campos()
                return

            datos_nuevo_empleado = {
                "nombres": nombres,
                "apellidos": apellidos,
                "dni": dni,
                "rol": rol
            }

            try:
                respuesta = cliente_http.crear_perfil(datos_nuevo_empleado, id_operador=id_actual)
                id_generado = respuesta.get("id")
                if id_generado is not None:
                    _cache_legajo_rrhh[int(id_generado)] = {
                        "telefono": telefono,
                        "email": email,
                        "direccion": domicilio,
                        "ciudad": ciudad,
                        "provincia": provincia,
                        "cp": cp
                    }
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror("Error de Transacción", str(e))

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            valores = tabla.item(seleccion[0], "values")
            
            cajas = [
                caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email,
                caja_domicilio, caja_ciudad, caja_provincia, caja_cp
            ]
                     
            for i, caja in enumerate(cajas):
                caja.delete(0, tk.END)

                # Convertimos "S/D" en vacío para facilitar la edición en las cajas de texto.
                valor_mostrar = valores[i] if valores[i] != "S/D" else ""
                caja.insert(0, valor_mostrar)
                
            caja_rol.set(valores[9])

        def modificar():
            """
             Actualiza los datos del empleado en PUT /api/perfiles/{id} sin alterar 
             sus credenciales de acceso (usuario/contraseña) en el Backend.
            """
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            id_empleado = int(seleccion[0])
            
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            dni = caja_dni.get().strip() or "S/D"
            telefono = caja_telefono.get().strip() or "S/D"
            email = caja_email.get().strip() or "S/D"
            domicilio = caja_domicilio.get().strip() or "S/D"
            ciudad = caja_ciudad.get().strip() or "S/D"
            provincia = caja_provincia.get().strip() or "S/D"
            cp = caja_cp.get().strip() or "S/D"
            rol = caja_rol.get()

            if not nombres or not apellidos or not rol:
                messagebox.showwarning("Validación", "Nombres, Apellidos y Rol Organizacional son obligatorios.")
                return

            # Solo enviamos los campos maestros; al omitir 'usuario' y 'password_plana', 
            # el Backend preserva intactas las credenciales de login existentes.
            datos_modificados = {
                "nombres": nombres,
                "apellidos": apellidos,
                "dni": dni,
                "rol": rol
            }

            try:
                cliente_http.modificar_perfil(id_empleado, datos_modificados, id_operador=id_actual)
                _cache_legajo_rrhh[id_empleado] = {
                    "telefono": telefono,
                    "email": email,
                    "direccion": domicilio,
                    "ciudad": ciudad,
                    "provincia": provincia,
                    "cp": cp
                }
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror("Acceso Denegado / Error", str(e))

        def eliminar():
            """
             Solicita la baja lógica (Soft Delete) del empleado a DELETE /api/perfiles/{id}.
             Respeta la jerarquía RBAC y el bloqueo de eliminación del último Administrador.
            """
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            try:
                for item in seleccion:
                    cliente_http.eliminar_perfil(int(item), id_operador=id_actual)
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror("Operación Bloqueada", str(e))



        # ======================================
        #  3. CAMPOS DEL "FORMULARIO EMPLEADOS"
        # ======================================

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



        # ============================================================
        #  4. BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # ============================================================

        boton_guardar = tk.Button(self, text="Guardar Perfil", command=guardar, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_guardar.grid(row=3, column=3, padx=20)

        boton_modificar = tk.Button(self, text="Modificar Perfil", command=modificar, bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_modificar.grid(row=5, column=3, padx=20)

        boton_eliminar = tk.Button(self, text="Eliminar Perfil", command=eliminar, bg="#F44336", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_eliminar.grid(row=7, column=3, padx=20)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy, bg="#9E9E9E", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_cerrar_ventana.grid(row=9, column=3, padx=20)



        # ================================
        #  5. TABLA DE DATOS DE EMPLEADOS
        # ================================

        columnas = ("Nombres", "Apellidos", "DNI", "Teléfono", "Email", "Dirección", "Ciudad", "Provincia", "CP", "Rol")

        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=100)

        tabla.grid(row=11, column=0, columnspan=5, pady=20, padx=10, sticky="nsew")
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)



        # ===========================
        #  6. CARGA INICIAL DE DATOS
        # ===========================
        
        cargar_datos_api()