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
_cache_clientes_contacto = {}


class Cliente(tk.Toplevel):
    """
     Formulario de gestión comercial de Clientes.
     Opera 100% como cliente HTTP: consume los endpoints de /api/perfiles 
     sin ejecutar consultas SQL directas desde la interfaz.
    """

    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("FORMULARIO CLIENTES")
        self.geometry("925x550")



        # =============================================
        #  2. FUNCIONALIDADES DE "FORMULARIO CLIENTES"
        # =============================================

        def cargar_datos_api():
            """
             Consulta la nómina de clientes activos mediante GET /api/perfiles/rol/Cliente
             y reconstruye las filas de la tabla visual.
            """
            for item in tabla.get_children():
                tabla.delete(item)
                
            try:
                clientes = cliente_http.listar_perfiles_por_rol("Cliente")
                for c in clientes:
                    id_cli = c["id"]
                    extras = _cache_clientes_contacto.get(id_cli, {})
                    
                    valores_fila = (
                        c.get("nombres") or "S/D",
                        c.get("apellidos") or "S/D",
                        c.get("dni") or "S/D",
                        extras.get("telefono", "S/D"),
                        extras.get("email", "S/D"),
                        extras.get("direccion", "S/D"),
                        extras.get("ciudad", "S/D"),
                        extras.get("provincia", "S/D"),
                        extras.get("cp", "S/D")
                    )
                    tabla.insert("", "end", iid=str(id_cli), values=valores_fila)
            except ErrorClienteAPI as e:
                messagebox.showerror("Error de Comunicación", str(e))

        def limpiar_campos():
            cajas = [
                caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email, 
                caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal
            ]
            for caja in cajas:
                caja.delete(0, tk.END)
            caja_nombres.focus_set()

        def guardar():
            """
             Envía los datos del nuevo cliente a POST /api/perfiles asignando 
             automáticamente el rol 'Cliente'.
            """
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            dni = caja_dni.get().strip() or "S/D"
            telefono = caja_telefono.get().strip() or "S/D"
            email = caja_email.get().strip() or "S/D"
            domicilio = caja_domicilio.get().strip() or "S/D"
            ciudad = caja_ciudad.get().strip() or "S/D"
            provincia = caja_provincia.get().strip() or "S/D"
            codigo_postal = caja_codigo_postal.get().strip() or "S/D"

            if not nombres or not apellidos:
                messagebox.showwarning("Validación", "Nombres y Apellidos son obligatorios.")
                return

            datos_nuevo_cliente = {
                "nombres": nombres,
                "apellidos": apellidos,
                "dni": dni,
                "rol": "Cliente"
            }

            try:
                respuesta = cliente_http.crear_perfil(datos_nuevo_cliente)
                id_generado = respuesta.get("id")
                if id_generado is not None:
                    _cache_clientes_contacto[int(id_generado)] = {
                        "telefono": telefono,
                        "email": email,
                        "direccion": domicilio,
                        "ciudad": ciudad,
                        "provincia": provincia,
                        "cp": codigo_postal
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
                caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal
            ]
                     
            for i, caja in enumerate(cajas):
                caja.delete(0, tk.END)

                # Convertimos "S/D" a texto vacío para limpiar la edición en pantalla.
                valor_mostrar = valores[i] if valores[i] != "S/D" else ""
                caja.insert(0, valor_mostrar)

        def modificar():
            """
             Actualiza los datos del cliente seleccionado enviando una petición 
             PUT /api/perfiles/{id} al Backend.
            """
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            id_cliente = int(seleccion[0])
            
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            dni = caja_dni.get().strip() or "S/D"
            telefono = caja_telefono.get().strip() or "S/D"
            email = caja_email.get().strip() or "S/D"
            domicilio = caja_domicilio.get().strip() or "S/D"
            ciudad = caja_ciudad.get().strip() or "S/D"
            provincia = caja_provincia.get().strip() or "S/D"
            codigo_postal = caja_codigo_postal.get().strip() or "S/D"

            if not nombres or not apellidos:
                messagebox.showwarning("Validación", "Nombres y Apellidos son obligatorios.")
                return

            datos_modificados = {
                "nombres": nombres,
                "apellidos": apellidos,
                "dni": dni,
                "rol": "Cliente"
            }

            try:
                cliente_http.modificar_perfil(id_cliente, datos_modificados)
                _cache_clientes_contacto[id_cliente] = {
                    "telefono": telefono,
                    "email": email,
                    "direccion": domicilio,
                    "ciudad": ciudad,
                    "provincia": provincia,
                    "cp": codigo_postal
                }
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror("Error al Actualizar", str(e))

        def eliminar():
            """
             Ejecuta la baja lógica (Soft Delete) del cliente mediante DELETE /api/perfiles/{id}.
            """
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            try:
                for item in seleccion:
                    cliente_http.eliminar_perfil(int(item))
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror("Operación Bloqueada", str(e))



        # =====================================
        #  3. CAMPOS DEL "FORMULARIO CLIENTES"
        # =====================================

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



        # ============================================================
        #  4. BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # ============================================================

        boton_guardar = tk.Button(self, text="Guardar Cliente", command=guardar, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_guardar.grid(row=2, column=3, padx=20)

        boton_modificar = tk.Button(self, text="Modificar Cliente", command=modificar, bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_modificar.grid(row=4, column=3, padx=20)

        boton_eliminar = tk.Button(self, text="Eliminar Cliente", command=eliminar, bg="#F44336", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_eliminar.grid(row=6, column=3, padx=20)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy, bg="#9E9E9E", fg="white", font=("Arial", 9, "bold"), width=15)
        boton_cerrar_ventana.grid(row=8, column=3, padx=20)



        # ===============================
        #  5. TABLA DE DATOS DE CLIENTES
        # ===============================
        
        columnas = ("Nombres", "Apellidos", "DNI", "Teléfono", "Email", "Dirección", "Ciudad", "Provincia", "Cód. Postal")

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