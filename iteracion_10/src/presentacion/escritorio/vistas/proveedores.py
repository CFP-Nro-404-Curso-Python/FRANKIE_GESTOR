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
_cache_proveedores_contacto = {}


class Proveedor(tk.Toplevel):
    """
     Formulario de gestión comercial de Proveedores.
     Opera 100% como cliente HTTP: consume los endpoints de /api/perfiles 
     mapeando Razón Social a 'nombres', Contacto a 'apellidos' y CUIT a 'dni'.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.title("FORMULARIO PROVEEDORES")
        self.geometry("925x550")



        # ================================================
        #  2. FUNCIONALIDADES DE "FORMULARIO PROVEEDORES"
        # ================================================

        def cargar_datos_api():
            """
             Consulta la nómina de proveedores activos mediante GET /api/perfiles/rol/Proveedor
             y reconstruye las filas de la tabla visual.
            """
            for item in tabla.get_children():
                tabla.delete(item)
                
            try:
                proveedores = cliente_http.listar_perfiles_por_rol("Proveedor")
                for p in proveedores:
                    id_prov = p["id"]
                    extras = _cache_proveedores_contacto.get(id_prov, {})
                    
                    valores_fila = (
                        p.get("nombres") or "S/D",
                        p.get("dni") or "S/D",
                        extras.get("telefono", "S/D"),
                        extras.get("email", "S/D"),
                        extras.get("direccion", "S/D"),
                        extras.get("ciudad", "S/D"),
                        extras.get("provincia", "S/D"),
                        extras.get("cp", "S/D"),
                        p.get("apellidos") or "S/D"
                    )
                    tabla.insert("", "end", iid=str(id_prov), values=valores_fila)
            except ErrorClienteAPI as e:
                messagebox.showerror("Error de Comunicación", str(e))

        def limpiar_campos():
            cajas = [
                caja_razon_social, caja_cuit, caja_telefono, caja_email, 
                caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal, caja_contacto
            ]
            for caja in cajas:
                caja.delete(0, tk.END)
            
            caja_razon_social.focus_set()

        def guardar():
            """
             Envía los datos del nuevo proveedor a POST /api/perfiles asignando 
             automáticamente el rol 'Proveedor'.
            """
            razon_social = caja_razon_social.get().strip()
            cuit = caja_cuit.get().strip() or "S/D"
            telefono = caja_telefono.get().strip() or "S/D"
            email = caja_email.get().strip() or "S/D"
            domicilio = caja_domicilio.get().strip() or "S/D"
            ciudad = caja_ciudad.get().strip() or "S/D"
            provincia = caja_provincia.get().strip() or "S/D"
            codigo_postal = caja_codigo_postal.get().strip() or "S/D"
            contacto = caja_contacto.get().strip()

            if not razon_social:
                messagebox.showwarning("Validación", "La Razón Social es obligatoria.")
                return

            contacto_seguro = contacto if contacto else "S/D"

            datos_nuevo_proveedor = {
                "nombres": razon_social,
                "apellidos": contacto_seguro,
                "dni": cuit,
                "rol": "Proveedor"
            }

            try:
                respuesta = cliente_http.crear_perfil(datos_nuevo_proveedor)
                id_generado = respuesta.get("id")
                if id_generado is not None:
                    _cache_proveedores_contacto[int(id_generado)] = {
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
                caja_razon_social, caja_cuit, caja_telefono, caja_email, 
                caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal, caja_contacto
            ]
                     
            for i, caja in enumerate(cajas):
                caja.delete(0, tk.END)

                # Convertimos "S/D" a texto vacío para limpiar la edición en la interfaz.
                valor_mostrar = valores[i] if valores[i] != "S/D" else ""
                caja.insert(0, valor_mostrar)
        
        def modificar():
            """
             Actualiza los datos del proveedor seleccionado enviando 
             una petición PUT /api/perfiles/{id} al Backend.
            """
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            id_proveedor = int(seleccion[0])
            
            razon_social = caja_razon_social.get().strip()
            cuit = caja_cuit.get().strip() or "S/D"
            telefono = caja_telefono.get().strip() or "S/D"
            email = caja_email.get().strip() or "S/D"
            domicilio = caja_domicilio.get().strip() or "S/D"
            ciudad = caja_ciudad.get().strip() or "S/D"
            provincia = caja_provincia.get().strip() or "S/D"
            codigo_postal = caja_codigo_postal.get().strip() or "S/D"
            contacto = caja_contacto.get().strip()

            if not razon_social:
                messagebox.showwarning("Validación", "La Razón Social es obligatoria.")
                return

            contacto_seguro = contacto if contacto else "S/D"

            datos_modificados = {
                "nombres": razon_social,
                "apellidos": contacto_seguro,
                "dni": cuit,
                "rol": "Proveedor"
            }

            try:
                cliente_http.modificar_perfil(id_proveedor, datos_modificados)
                _cache_proveedores_contacto[id_proveedor] = {
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
             Ejecuta la baja lógica (Soft Delete) del proveedor mediante DELETE /api/perfiles/{id}.
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



        # ========================================
        #  3. CAMPOS DEL "FORMULARIO PROVEEDORES"
        # ========================================

        tk.Label(self, text="Razón Social").grid(row=1, column=0, pady=5, sticky="e", padx=5)
        caja_razon_social = tk.Entry(self, width=30)
        caja_razon_social.grid(row=1, column=1)

        tk.Label(self, text="CUIT").grid(row=2, column=0, pady=5, sticky="e", padx=5)
        caja_cuit = tk.Entry(self, width=30)
        caja_cuit.grid(row=2, column=1)

        tk.Label(self, text="Teléfono").grid(row=3, column=0, pady=5, sticky="e", padx=5)
        caja_telefono = tk.Entry(self, width=30)
        caja_telefono.grid(row=3, column=1)

        tk.Label(self, text="Email").grid(row=4, column=0, pady=5, sticky="e", padx=5)
        caja_email = tk.Entry(self, width=30)
        caja_email.grid(row=4, column=1)

        tk.Label(self, text="Dirección").grid(row=5, column=0, pady=5, sticky="e", padx=5)
        caja_domicilio = tk.Entry(self, width=30)
        caja_domicilio.grid(row=5, column=1)

        tk.Label(self, text="Ciudad").grid(row=6, column=0, pady=5, sticky="e", padx=5)
        caja_ciudad = tk.Entry(self, width=30)
        caja_ciudad.grid(row=6, column=1)

        tk.Label(self, text="Provincia").grid(row=7, column=0, pady=5, sticky="e", padx=5)
        caja_provincia = tk.Entry(self, width=30)
        caja_provincia.grid(row=7, column=1)

        tk.Label(self, text="Código Postal").grid(row=8, column=0, pady=5, sticky="e", padx=5)
        caja_codigo_postal = tk.Entry(self, width=30)
        caja_codigo_postal.grid(row=8, column=1)

        tk.Label(self, text="Contacto (Rep.)").grid(row=9, column=0, pady=5, sticky="e", padx=5)
        caja_contacto = tk.Entry(self, width=30)
        caja_contacto.grid(row=9, column=1)



        # ============================================================
        #  4. BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # ============================================================

        boton_guardar = tk.Button(self, text="Guardar Proveedor", command=guardar, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=16)
        boton_guardar.grid(row=2, column=3, padx=20)

        boton_modificar = tk.Button(self, text="Modificar Proveedor", command=modificar, bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=16)
        boton_modificar.grid(row=4, column=3, padx=20)

        boton_eliminar = tk.Button(self, text="Eliminar Proveedor", command=eliminar, bg="#F44336", fg="white", font=("Arial", 9, "bold"), width=16)
        boton_eliminar.grid(row=6, column=3, padx=20)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy, bg="#9E9E9E", fg="white", font=("Arial", 9, "bold"), width=16)
        boton_cerrar_ventana.grid(row=8, column=3, padx=20)



        # ==================================
        #  5. TABLA DE DATOS DE PROVEEDORES
        # ==================================

        columnas = ("Razón Social", "CUIT", "Teléfono", "Email", "Dirección", "Ciudad", "Provincia", "Cód. Postal", "Contacto")

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