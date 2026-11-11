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


class Facturacion(tk.Toplevel):
    """
     Formulario de emisión y gestión de comprobantes de Facturación.
     Opera 100% como cliente HTTP: consulta vendedores, clientes y productos 
     desde la API REST y delega las transacciones de venta y stock al Backend.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.title("FORMULARIO FACTURACIÓN")
        self.geometry("590x630")

        # Diccionarios en memoria para traducir rápidamente entre códigos/IDs y datos de productos.
        self.mapa_codigo_a_prod = {}
        self.mapa_id_a_prod = {}



        # ===========================================================
        #  2. FUNCIONES DE EXTRACCIÓN DE DATOS MAESTROS VÍA API REST
        # ===========================================================

        def obtener_vendedores():
            """
             Consulta los usuarios con rol 'Empleado - Ventas' en GET /api/perfiles/rol/Empleado - Ventas
             y los formatea como 'Nombres Apellidos (ID: X)'.
            """
            lista = []
            try:
                vendedores = cliente_http.listar_perfiles_por_rol("Empleado - Ventas")
                for v in vendedores:
                    lista.append(f"{v['nombres']} {v['apellidos']} (ID: {v['id']})")
            except ErrorClienteAPI as e:
                messagebox.showerror("Error de Comunicación", str(e))
            return lista

        def obtener_clientes():
            """
             Consulta los perfiles con rol 'Cliente' en GET /api/perfiles/rol/Cliente
             y los formatea como 'Nombres Apellidos (ID: X)'.
            """
            lista = []
            try:
                clientes = cliente_http.listar_perfiles_por_rol("Cliente")
                for c in clientes:
                    lista.append(f"{c['nombres']} {c['apellidos']} (ID: {c['id']})")
            except ErrorClienteAPI as e:
                messagebox.showerror("Error de Comunicación", str(e))
            return lista

        def obtener_productos():
            """
             Consulta el catálogo activo en GET /api/productos, guarda los detalles en memoria 
             para autocompletar precios y devuelve la lista 'Código - Descripción'.
            """
            self.mapa_codigo_a_prod.clear()
            self.mapa_id_a_prod.clear()
            lista = []
            try:
                productos = cliente_http.listar_productos()
                for p in productos:
                    codigo = p["codigo"]
                    self.mapa_codigo_a_prod[codigo] = p
                    self.mapa_id_a_prod[p["id"]] = p
                    lista.append(f"{codigo} - {p['descripcion']}")
            except ErrorClienteAPI as e:
                messagebox.showerror("Error de Comunicación", str(e))
            return lista

        def autocompletar_precio(event):
            """
             Al elegir un producto del desplegable, coloca automáticamente 
             su precio de venta actual en la caja 'Valor en $'.
            """
            seleccion = caja_producto.get()
            if not seleccion:
                return

            codigo_prod = seleccion.split(" - ")[0]
            prod = self.mapa_codigo_a_prod.get(codigo_prod)
            if prod:
                caja_valor.config(state="normal")
                caja_valor.delete(0, tk.END)
                caja_valor.insert(0, prod["precio_venta"])
                caja_valor.config(state="readonly")



        # ================================================
        #  3. FUNCIONALIDADES DE "FORMULARIO FACTURACIÓN"
        # ================================================

        def cargar_datos_api():
            """
             Recupera las facturas activas desde GET /api/facturas y las muestra 
             en la tabla cruzando el ID del producto con su código y descripción.
            """
            for item in tabla.get_children():
                tabla.delete(item)

            # Actualizamos los catálogos desplegables por si hubo altas recientes.
            caja_datos_vendedor["values"] = obtener_vendedores()
            caja_datos_cliente["values"] = obtener_clientes()
            caja_producto["values"] = obtener_productos()

            try:
                facturas = cliente_http.listar_facturas()
                for f in facturas:
                    prod = self.mapa_id_a_prod.get(f["id_producto"])
                    if prod:
                        etiqueta_prod = f"{prod['codigo']} - {prod['descripcion']}"
                    else:
                        etiqueta_prod = f"ID {f['id_producto']}"

                    # Calculamos el total si por algún motivo viene nulo, o usamos el calculado por SQLite.
                    total_fila = f.get("total")
                    if total_fila is None:
                        total_fila = (float(f["cantidad"]) * float(f["valor"])) * (1.0 - (float(f["descuento"]) / 100.0))

                    tabla.insert(
                        "",
                        "end",
                        iid=str(f["id"]),
                        values=(etiqueta_prod, f["cantidad"], f["valor"], f["descuento"], round(float(total_fila), 2))
                    )
            except ErrorClienteAPI as e:
                messagebox.showerror("Error de Comunicación", str(e))

            actualizar_total_factura()

        def limpiar_campos():
            caja_valor.config(state="normal")
            caja_producto.set("")
            caja_cantidad.delete(0, tk.END)
            caja_valor.delete(0, tk.END)
            caja_descuento.delete(0, tk.END)
            caja_valor.config(state="readonly")
            caja_producto.focus_set()

        def actualizar_total_factura():
            """
             Suma los totales de los renglones en pantalla y aplica 
             el porcentaje de descuento global si fue ingresado.
            """
            gran_total = 0.0
            for item in tabla.get_children():
                valores = tabla.item(item, "values")
                gran_total += float(valores[4])
            
            desc_porcentaje = 0.0
            try:
                desc_str = caja_calc_descuento.get()
                if desc_str.strip():
                    desc_porcentaje = float(desc_str)
                    if not (0 <= desc_porcentaje <= 100):
                        desc_porcentaje = 0.0
            except Exception:
                pass
            
            total_final = gran_total * (1 - (desc_porcentaje / 100))
            
            label_total_factura.config(text=f"TOTAL FACTURA: $ {total_final:.2f}")
            
            try:
                label_resultado_desc.config(text=f"Total con descuento ({desc_porcentaje}%): $ {total_final:.2f}")
            except Exception:
                pass

        def guardar():
            """
             Envía los datos de la venta a POST /api/facturas.
             El Backend verifica el stock, registra la factura y descuenta 
             el inventario en una sola transacción atómica (Unit of Work).
            """
            producto_seleccionado = caja_producto.get().strip()
            vendedor_seleccionado = caja_datos_vendedor.get().strip()
            cliente_seleccionado = caja_datos_cliente.get().strip()
            
            if not producto_seleccionado or not vendedor_seleccionado or not cliente_seleccionado:
                messagebox.showwarning("Validación", "Vendedor, Cliente y Producto son obligatorios.")
                return

            try:
                cantidad = float(caja_cantidad.get())
                descuento_str = caja_descuento.get().strip()
                descuento = float(descuento_str) if descuento_str else 0.0

                if descuento < 0 or descuento > 100:
                    messagebox.showerror("Validación", "El descuento por producto debe estar entre 0 y 100%.")
                    return

                id_vendedor = int(vendedor_seleccionado.split("ID: ")[1].replace(")", ""))
                id_cliente = int(cliente_seleccionado.split("ID: ")[1].replace(")", ""))
                codigo_prod = producto_seleccionado.split(" - ")[0]

                prod = self.mapa_codigo_a_prod.get(codigo_prod)
                if not prod:
                    messagebox.showerror("Error", "El producto seleccionado no se encuentra activo en el catálogo.")
                    return

                id_producto = prod["id"]

                # Emitimos la factura a través de la API REST (descuenta stock automáticamente).
                cliente_http.emitir_factura({
                    "id_vendedor": id_vendedor,
                    "id_cliente": id_cliente,
                    "id_producto": id_producto,
                    "cantidad": cantidad,
                    "descuento": descuento
                })

                # Verificamos si el stock resultante llegó al mínimo para mostrar la alerta preventiva.
                nuevo_stock = float(prod["stock_actual"]) - cantidad
                stock_minimo = float(prod["stock_minimo"])

                limpiar_campos()
                cargar_datos_api()

                if nuevo_stock <= stock_minimo:
                    messagebox.showwarning(
                        "Alerta de Reposición",
                        f"El producto llegó a su stock mínimo. Quedan {int(nuevo_stock)} unidades."
                    )

            except ValueError:
                messagebox.showerror("Error de Formato", "Ingrese valores numéricos válidos en Cantidad y Descuento.")
            except IndexError:
                messagebox.showerror("Error de Asociación", "Seleccione un vendedor y cliente válidos del menú.")
            except ErrorClienteAPI as e:
                messagebox.showerror("Transacción Rechazada", str(e))

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            valores = tabla.item(seleccion[0], "values")

            caja_valor.config(state="normal")
            caja_producto.set(valores[0])
            caja_cantidad.delete(0, tk.END)
            caja_cantidad.insert(0, valores[1])
            caja_valor.delete(0, tk.END)
            caja_valor.insert(0, valores[2])
            caja_descuento.delete(0, tk.END)
            caja_descuento.insert(0, valores[3])
            caja_valor.config(state="readonly")
            
        def modificar():
            """
             Como las facturas son documentos contables inmutables en el Backend, 
             la modificación restituye el stock anterior, emite el nuevo 
             comprobante y anula (baja lógica) el comprobante previo.
            """
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            producto_nuevo = caja_producto.get().strip()
            vendedor_seleccionado = caja_datos_vendedor.get().strip()
            cliente_seleccionado = caja_datos_cliente.get().strip()
            
            if not producto_nuevo or not vendedor_seleccionado or not cliente_seleccionado:
                messagebox.showerror("Error de Carga", "Vendedor, Cliente y Producto son obligatorios.")
                return
            
            try:
                id_factura_vieja = int(seleccion[0])
                cantidad_nueva = float(caja_cantidad.get())
                descuento_str = caja_descuento.get().strip()
                descuento = float(descuento_str) if descuento_str else 0.0

                if descuento < 0 or descuento > 100:
                    messagebox.showerror("Validación", "El descuento por producto debe estar entre 0 y 100%.")
                    return

                id_vendedor = int(vendedor_seleccionado.split("ID: ")[1].replace(")", ""))
                id_cliente = int(cliente_seleccionado.split("ID: ")[1].replace(")", ""))

                valores_viejos = tabla.item(seleccion[0], "values")
                codigo_viejo = valores_viejos[0].split(" - ")[0]
                cantidad_vieja = float(valores_viejos[1])
                codigo_nuevo = producto_nuevo.split(" - ")[0]

                prod_viejo = self.mapa_codigo_a_prod.get(codigo_viejo)
                prod_nuevo = self.mapa_codigo_a_prod.get(codigo_nuevo)

                if not prod_viejo or not prod_nuevo:
                    messagebox.showerror("Error", "No se pudo identificar el producto en el catálogo.")
                    return

                # 1. Restituimos el stock del comprobante original.
                cliente_http.ingresar_stock(prod_viejo["id"], cantidad_vieja)

                try:
                    # 2. Intentamos emitir el nuevo comprobante con la nueva cantidad.
                    cliente_http.emitir_factura({
                        "id_vendedor": id_vendedor,
                        "id_cliente": id_cliente,
                        "id_producto": prod_nuevo["id"],
                        "cantidad": cantidad_nueva,
                        "descuento": descuento
                    })
                except ErrorClienteAPI as error_emision:

                    # Si falla por falta de stock, revertimos la restitución para dejar todo intacto.
                    cliente_http.ingresar_stock(prod_viejo["id"], -cantidad_vieja)
                    messagebox.showerror(
                        "Transacción Rechazada",
                        f"No se pudo modificar la facturación ({error_emision}). Se ha deshecho el cambio."
                    )
                    return

                # 3. Anulamos (baja lógica) el comprobante anterior reemplazado.
                cliente_http.anular_factura(id_factura_vieja)

                limpiar_campos()
                cargar_datos_api()

                prod_actualizado = self.mapa_codigo_a_prod.get(codigo_nuevo)
                if prod_actualizado and float(prod_actualizado["stock_actual"]) <= float(prod_actualizado["stock_minimo"]):
                    messagebox.showwarning(
                        "Alerta de Reposición",
                        f"El producto llegó a su stock mínimo. Quedan {int(float(prod_actualizado['stock_actual']))} unidades."
                    )

            except ValueError:
                messagebox.showerror("Error de Formato", "Ingrese valores numéricos válidos en Cantidad y Descuento.")
            except IndexError:
                messagebox.showerror("Error de Asociación", "Seleccione un vendedor y cliente válidos del menú.")
            except ErrorClienteAPI as e:
                messagebox.showerror("Error Transaccional", str(e))

        def eliminar():
            """
             Anula el comprobante seleccionado mediante DELETE /api/facturas/{id} 
             y restituye las unidades al inventario con POST /api/productos/{id}/stock.
            """
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            try:
                for item in seleccion:
                    valores = tabla.item(item, "values")
                    codigo_prod = valores[0].split(" - ")[0]
                    cantidad_a_devolver = float(valores[1])

                    prod = self.mapa_codigo_a_prod.get(codigo_prod)
                    if prod:
                        cliente_http.ingresar_stock(prod["id"], cantidad_a_devolver)

                    cliente_http.anular_factura(int(item))
                
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror("Operación Bloqueada", str(e))

        def calcular_descuento_final():
            try:
                desc_str = caja_calc_descuento.get()
                if desc_str.strip():
                    desc_porcentaje = float(desc_str)
                    if desc_porcentaje < 0 or desc_porcentaje > 100:
                        messagebox.showerror("Validación", "El descuento global debe estar entre 0 y 100%.")
                        return
                
                actualizar_total_factura()
                caja_calc_descuento.delete(0, tk.END)
            except ValueError:
                messagebox.showerror("Error", "Ingrese un porcentaje global válido.")



        # ========================================
        #  4. CAMPOS DEL "FORMULARIO FACTURACIÓN"
        # ========================================

        tk.Label(self, text="Datos del Vendedor").grid(row=1, column=0, pady=5, sticky="e", padx=5)
        caja_datos_vendedor = ttk.Combobox(self, values=obtener_vendedores(), state="readonly", width=35)
        caja_datos_vendedor.grid(row=1, column=1)

        tk.Label(self, text="Datos del Cliente").grid(row=2, column=0, pady=5, sticky="e", padx=5)
        caja_datos_cliente = ttk.Combobox(self, values=obtener_clientes(), state="readonly", width=35)
        caja_datos_cliente.grid(row=2, column=1)

        tk.Label(self, text="").grid(row=3, column=0)  # Espaciador.
        
        tk.Label(self, text="Producto").grid(row=4, column=0, pady=5, sticky="e", padx=5)
        caja_producto = ttk.Combobox(self, values=obtener_productos(), state="readonly", width=35)
        caja_producto.grid(row=4, column=1)
        caja_producto.bind("<<ComboboxSelected>>", autocompletar_precio)

        tk.Label(self, text="Cantidad").grid(row=5, column=0, pady=5, sticky="e", padx=5)
        caja_cantidad = tk.Entry(self)
        caja_cantidad.grid(row=5, column=1)
        
        tk.Label(self, text="Valor en $").grid(row=6, column=0, pady=5, sticky="e", padx=5)
        caja_valor = tk.Entry(self)
        caja_valor.grid(row=6, column=1)
        caja_valor.config(state="readonly")

        tk.Label(self, text="Descuento en %").grid(row=7, column=0, pady=5, sticky="e", padx=5)
        caja_descuento = tk.Entry(self)
        caja_descuento.grid(row=7, column=1)



        # ============================================================
        #  5. BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # ============================================================

        boton_guardar = tk.Button(self, text="Guardar Facturación", command=guardar, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=18)
        boton_guardar.grid(row=4, column=3, padx=20)

        boton_modificar = tk.Button(self, text="Modificar Facturación", command=modificar, bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=18)
        boton_modificar.grid(row=5, column=3, padx=20)

        boton_eliminar = tk.Button(self, text="Eliminar Facturación", command=eliminar, bg="#F44336", fg="white", font=("Arial", 9, "bold"), width=18)
        boton_eliminar.grid(row=6, column=3, padx=20)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy, bg="#9E9E9E", fg="white", font=("Arial", 9, "bold"), width=18)
        boton_cerrar_ventana.grid(row=7, column=3, padx=20)



        # ==================================
        #  6. TABLA DE DATOS DE FACTURACIÓN
        # ==================================

        columnas = ("Producto", "Cantidad", "Valor en $", "Descuento en %", "Total en $")

        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=110)

        tabla.grid(row=8, column=0, columnspan=5, pady=20, padx=10)
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)



        # ======================================
        #  7. ETIQUETA GLOBAL: TOTAL DE FACTURA
        # ======================================

        label_total_factura = tk.Label(self, text="TOTAL FACTURA: $ 0.00", font=("Arial", 10, "bold"))
        label_total_factura.grid(row=9, column=0, columnspan=2, sticky="w", padx=10)



        # =========================================
        #  8. SECCIÓN: DESCUENTO GLOBAL DE FACTURA
        # =========================================

        tk.Label(self, text="APLICAR DESCUENTO GLOBAL", font=("Arial", 9, "bold")).grid(row=10, column=0, pady=10, columnspan=2)

        tk.Label(self, text="Descuento Global en %").grid(row=11, column=0, pady=5, sticky="e", padx=5)
        caja_calc_descuento = tk.Entry(self)
        caja_calc_descuento.grid(row=11, column=1)

        boton_calcular_desc = tk.Button(self, text="Calcular Descuento Final", command=calcular_descuento_final, bg="#FF9800", fg="white", font=("Arial", 9, "bold"))
        boton_calcular_desc.grid(row=11, column=3)



        # =================================================
        #  9. ETIQUETA QUE MUESTRA RESULTANTE DE DESCUENTO
        # =================================================

        label_resultado_desc = tk.Label(self, text="TOTAL CON DESCUENTO: $ 0.00", font=("Arial", 9, "bold"))
        label_resultado_desc.grid(row=12, column=0, columnspan=4, pady=15)



        # ============================
        #  10. CARGA INICIAL DE DATOS
        # ============================
        
        cargar_datos_api()