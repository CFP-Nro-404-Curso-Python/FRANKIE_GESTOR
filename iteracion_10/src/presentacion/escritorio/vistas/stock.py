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

# Memoria auxiliar de sesión para conservar la ubicación física de cada producto en la grilla.
_cache_ubicaciones_stock = {}


class Stock(tk.Toplevel):
    """
     Formulario de gestión de Stock e Inventario.
     Opera 100% como cliente HTTP: consume los endpoints de /api/productos y 
     /api/perfiles/rol/Proveedor sin tocar SQLite desde la interfaz.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.title("FORMULARIO STOCK E INVENTARIO")
        self.geometry("1020x550")

        # Diccionarios internos para traducir entre el nombre del Proveedor (UI) y su ID (API).
        self.mapa_nombre_a_id_prov = {}
        self.mapa_id_a_nombre_prov = {}



        # ==========================================
        #  2. FUNCIONALIDADES DE "FORMULARIO STOCK"
        # ==========================================

        def obtener_proveedores():
            """
             Consulta los proveedores activos en GET /api/perfiles/rol/Proveedor 
             y actualiza los diccionarios de traducción Nombre <-> ID.
            """
            self.mapa_nombre_a_id_prov.clear()
            self.mapa_id_a_nombre_prov.clear()
            lista_provs = []

            try:
                proveedores = cliente_http.listar_perfiles_por_rol("Proveedor")
                for p in proveedores:
                    nombre_prov = p.get("nombres", "").strip()
                    id_prov = p["id"]
                    if nombre_prov:
                        self.mapa_nombre_a_id_prov[nombre_prov] = id_prov
                        self.mapa_id_a_nombre_prov[id_prov] = nombre_prov
                        lista_provs.append(nombre_prov)
            except ErrorClienteAPI as e:
                messagebox.showerror("Error de Comunicación", str(e))

            return lista_provs

        def cargar_datos_api():
            """
             Recupera el catálogo activo mediante GET /api/productos y 
             arma las filas reemplazando el ID del proveedor por su Razón Social.
            """
            for item in tabla.get_children():
                tabla.delete(item)

            # Refrescamos el listado de proveedores para asegurar que el Combobox y los nombres estén al día.
            caja_proveedor["values"] = obtener_proveedores()

            try:
                productos = cliente_http.listar_productos()
                for prod in productos:
                    id_prod = prod["id"]
                    nombre_prov = self.mapa_id_a_nombre_prov.get(prod["id_proveedor"], f"ID {prod['id_proveedor']}")
                    ubicacion_mostrar = _cache_ubicaciones_stock.get(id_prod, "S/D")
                    vencimiento_mostrar = prod.get("vencimiento") if prod.get("vencimiento") else "S/D"

                    valores_fila = (
                        prod.get("codigo") or "S/D",
                        prod.get("descripcion") or "S/D",
                        prod.get("categoria") or "S/D",
                        nombre_prov,
                        prod.get("stock_actual", 0.0),
                        prod.get("stock_minimo", 0.0),
                        prod.get("precio_costo", 0.0),
                        prod.get("precio_venta", 0.0),
                        ubicacion_mostrar,
                        vencimiento_mostrar
                    )
                    tabla.insert("", "end", iid=str(id_prod), values=valores_fila)
            except ErrorClienteAPI as e:
                messagebox.showerror("Error de Comunicación", str(e))

        def limpiar_campos():
            cajas = [
                caja_codigo, caja_descripcion, caja_categoria, caja_stock_actual,
                caja_stock_minimo, caja_precio_costo, caja_precio_venta,
                caja_ubicacion, caja_vencimiento
            ]
            for caja in cajas:
                caja.delete(0, tk.END)
            
            caja_proveedor.set("")
            caja_codigo.focus_set()
        
        def guardar():
            """
             Valida los campos numéricos y registra un nuevo artículo en el catálogo 
             enviando una petición POST /api/productos al Backend.
            """
            codigo = caja_codigo.get().strip()
            descripcion = caja_descripcion.get().strip()
            categoria = caja_categoria.get().strip() or "S/D"
            proveedor = caja_proveedor.get().strip()
            stock_actual = caja_stock_actual.get().strip()
            stock_minimo = caja_stock_minimo.get().strip()
            precio_costo = caja_precio_costo.get().strip()
            precio_venta = caja_precio_venta.get().strip()
            ubicacion = caja_ubicacion.get().strip() or "S/D"
            vencimiento = caja_vencimiento.get().strip() or "S/D"

            if not codigo or not descripcion or not proveedor:
                messagebox.showwarning("Validación", "Código, Descripción y Proveedor son campos obligatorios.")
                return

            id_proveedor = self.mapa_nombre_a_id_prov.get(proveedor)
            if not id_proveedor:
                messagebox.showerror("Error", "El proveedor seleccionado no es válido o fue dado de baja.")
                return

            try:
                st_act = float(stock_actual) if stock_actual else 0.0
                st_min = float(stock_minimo) if stock_minimo else 0.0
                p_cost = float(precio_costo) if precio_costo else 0.0
                p_vent = float(precio_venta) if precio_venta else 0.0
            except ValueError:
                messagebox.showerror("Error de Formato", "Asegúrese de ingresar valores numéricos válidos en precios y stock.")
                return

            datos_nuevo_producto = {
                "codigo": codigo,
                "descripcion": descripcion,
                "categoria": categoria,
                "id_proveedor": id_proveedor,
                "precio_costo": p_cost,
                "precio_venta": p_vent,
                "stock_actual": st_act,
                "stock_minimo": st_min,
                "vencimiento": vencimiento
            }

            try:
                respuesta = cliente_http.crear_producto(datos_nuevo_producto)
                id_generado = respuesta.get("id")
                if id_generado is not None:
                    _cache_ubicaciones_stock[int(id_generado)] = ubicacion
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror("Error Transaccional", str(e))

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            valores = tabla.item(seleccion[0], "values")

            cajas = [
                caja_codigo, caja_descripcion, caja_categoria, caja_stock_actual,
                caja_stock_minimo, caja_precio_costo, caja_precio_venta,
                caja_ubicacion, caja_vencimiento
            ]
            indices = [0, 1, 2, 4, 5, 6, 7, 8, 9]
                     
            for caja, idx in zip(cajas, indices):
                caja.delete(0, tk.END)
                valor_mostrar = valores[idx] if valores[idx] != "S/D" else ""
                caja.insert(0, valor_mostrar)

            # El proveedor está en el índice 3 visual de la grilla.
            caja_proveedor.set(valores[3])

        def modificar():
            """
             Actualiza los datos comerciales del producto mediante PUT /api/productos/{id}.
             Si el usuario también ajustó el stock en el formulario, envía la diferencia 
             de forma atómica a POST /api/productos/{id}/stock.
            """
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            id_producto = int(seleccion[0])
            valores_actuales = tabla.item(seleccion[0], "values")
            stock_anterior = float(valores_actuales[4]) if valores_actuales else 0.0
            
            codigo = caja_codigo.get().strip()
            descripcion = caja_descripcion.get().strip()
            categoria = caja_categoria.get().strip() or "S/D"
            proveedor = caja_proveedor.get().strip()
            stock_actual = caja_stock_actual.get().strip()
            stock_minimo = caja_stock_minimo.get().strip()
            precio_costo = caja_precio_costo.get().strip()
            precio_venta = caja_precio_venta.get().strip()
            ubicacion = caja_ubicacion.get().strip() or "S/D"
            vencimiento = caja_vencimiento.get().strip() or "S/D"

            if not codigo or not descripcion or not proveedor:
                messagebox.showwarning("Validación", "Código, Descripción y Proveedor son campos obligatorios.")
                return

            id_proveedor = self.mapa_nombre_a_id_prov.get(proveedor)
            if not id_proveedor:
                messagebox.showerror("Error", "El proveedor seleccionado no es válido o fue dado de baja.")
                return

            try:
                st_act = float(stock_actual) if stock_actual else 0.0
                st_min = float(stock_minimo) if stock_minimo else 0.0
                p_cost = float(precio_costo) if precio_costo else 0.0
                p_vent = float(precio_venta) if precio_venta else 0.0
            except ValueError:
                messagebox.showerror("Error de Formato", "Asegúrese de ingresar valores numéricos válidos en precios y stock.")
                return

            datos_modificados = {
                "codigo": codigo,
                "descripcion": descripcion,
                "categoria": categoria,
                "id_proveedor": id_proveedor,
                "precio_costo": p_cost,
                "precio_venta": p_vent,
                "stock_minimo": st_min,
                "vencimiento": vencimiento
            }

            try:
                # 1. Actualizamos los datos comerciales del producto.
                cliente_http.modificar_producto(id_producto, datos_modificados)
                
                # 2. Si hubo variación en la cantidad de stock, ejecutamos el ajuste atómico.
                diferencia_stock = st_act - stock_anterior
                if abs(diferencia_stock) > 1e-6:
                    cliente_http.ingresar_stock(id_producto, diferencia_stock)

                _cache_ubicaciones_stock[id_producto] = ubicacion
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror("Error Transaccional", str(e))
        
        def eliminar():
            """
             Ejecuta la baja lógica del producto en el catálogo mediante DELETE /api/productos/{id}.
            """
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            try:
                for item in seleccion:
                    cliente_http.eliminar_producto(int(item))
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror("Operación Bloqueada", str(e))



        # ==================================
        #  3. CAMPOS DEL "FORMULARIO STOCK"
        # ==================================

        tk.Label(self, text="Código").grid(row=1, column=0, pady=5, sticky="e", padx=5)
        caja_codigo = tk.Entry(self, width=30)
        caja_codigo.grid(row=1, column=1)

        tk.Label(self, text="Descripción").grid(row=2, column=0, pady=5, sticky="e", padx=5)
        caja_descripcion = tk.Entry(self, width=30)
        caja_descripcion.grid(row=2, column=1)

        tk.Label(self, text="Categoría").grid(row=3, column=0, pady=5, sticky="e", padx=5)
        caja_categoria = tk.Entry(self, width=30)
        caja_categoria.grid(row=3, column=1)

        tk.Label(self, text="Proveedor").grid(row=4, column=0, pady=5, sticky="e", padx=5)
        lista_proveedores = obtener_proveedores()
        caja_proveedor = ttk.Combobox(self, values=lista_proveedores, state="readonly", width=27)
        caja_proveedor.grid(row=4, column=1)

        tk.Label(self, text="Stock Actual").grid(row=5, column=0, pady=5, sticky="e", padx=5)
        caja_stock_actual = tk.Entry(self, width=30)
        caja_stock_actual.grid(row=5, column=1)

        tk.Label(self, text="Stock Mínimo").grid(row=6, column=0, pady=5, sticky="e", padx=5)
        caja_stock_minimo = tk.Entry(self, width=30)
        caja_stock_minimo.grid(row=6, column=1)

        tk.Label(self, text="Precio Costo").grid(row=7, column=0, pady=5, sticky="e", padx=5)
        caja_precio_costo = tk.Entry(self, width=30)
        caja_precio_costo.grid(row=7, column=1)

        tk.Label(self, text="Precio Venta").grid(row=8, column=0, pady=5, sticky="e", padx=5)
        caja_precio_venta = tk.Entry(self, width=30)
        caja_precio_venta.grid(row=8, column=1)

        tk.Label(self, text="Ubicación").grid(row=9, column=0, pady=5, sticky="e", padx=5)
        caja_ubicacion = tk.Entry(self, width=30)
        caja_ubicacion.grid(row=9, column=1)

        tk.Label(self, text="Vencimiento").grid(row=10, column=0, pady=5, sticky="e", padx=5)
        caja_vencimiento = tk.Entry(self, width=30)
        caja_vencimiento.grid(row=10, column=1)



        # ============================================================
        #  4. BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # ============================================================

        boton_guardar = tk.Button(self, text="Guardar Producto", command=guardar, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=16)
        boton_guardar.grid(row=3, column=3, padx=20)

        boton_modificar = tk.Button(self, text="Modificar Producto", command=modificar, bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=16)
        boton_modificar.grid(row=5, column=3, padx=20)

        boton_eliminar = tk.Button(self, text="Eliminar Producto", command=eliminar, bg="#F44336", fg="white", font=("Arial", 9, "bold"), width=16)
        boton_eliminar.grid(row=7, column=3, padx=20)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy, bg="#9E9E9E", fg="white", font=("Arial", 9, "bold"), width=16)
        boton_cerrar_ventana.grid(row=9, column=3, padx=20)



        # ============================
        #  5. TABLA DE DATOS DE STOCK
        # ============================

        columnas = ("Código", "Descripción", "Categoría", "Proveedor", "Stock Actual", "Stock Mínimo", "Precio Costo", "Precio Venta", "Ubicación", "Vencimiento")

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