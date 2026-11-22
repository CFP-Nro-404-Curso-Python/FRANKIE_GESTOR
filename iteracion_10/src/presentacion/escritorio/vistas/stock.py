import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk


# ==========================================================
#  1. ANCLAJE DE DIRECTORIOS E INTEGRACIÓN CON CLIENTE HTTP
# ==========================================================

DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_ESCRITORIO = os.path.dirname(DIRECTORIO_VISTAS)
DIRECTORIO_PRESENTACION = os.path.dirname(DIRECTORIO_ESCRITORIO)
DIRECTORIO_SRC = os.path.dirname(DIRECTORIO_PRESENTACION)
DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_SRC)

for ruta in (DIRECTORIO_RAIZ, DIRECTORIO_ESCRITORIO, DIRECTORIO_VISTAS):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

from src.presentacion.escritorio.cliente_api import cliente_http, ErrorClienteAPI, gestor_ui


class Stock(ctk.CTkToplevel):
    """
     Formulario de gestión de Stock e Inventario.
     Sincronizado 100% con el Backend 3FN, con semáforo de stock, búsqueda en vivo,
     Modo Claro/Oscuro, Alto Contraste WCAG e i18n ES/EN.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.title(gestor_ui.t("stk_win"))
        self.geometry("1240x690")
        self.minsize(1024, 600)
        self.after(80, self.lift)

        self.mapa_nombre_a_id_prov = {}
        self.mapa_id_a_nombre_prov = {}
        self._productos_api = []

        # ==========================================
        #  2. FUNCIONALIDADES DE "FORMULARIO STOCK"
        # ==========================================

        def _val_o_sd(valor):
            return valor if valor and valor != "S/D" else gestor_ui.t("sin_dato")

        def _es_placeholder_prov(texto: str) -> bool:
            return texto in (
                "",
                "Seleccione proveedor...", "Select supplier...",
                "Sin proveedores", "No suppliers"
            )

        def obtener_proveedores():
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
                messagebox.showerror(gestor_ui.t("err_com_tit"), str(e))

            return lista_provs

        def renderizar_tabla():
            for item in tabla.get_children():
                tabla.delete(item)

            filtro = caja_busqueda.get().strip().lower()
            visibles = 0

            for prod in self._productos_api:
                id_prod = prod["id"]
                nombre_prov = self.mapa_id_a_nombre_prov.get(prod["id_proveedor"], f"ID {prod['id_proveedor']}")
                st_act = float(prod.get("stock_actual", 0.0))
                st_min = float(prod.get("stock_minimo", 0.0))

                valores_fila = (
                    _val_o_sd(prod.get("codigo")),
                    _val_o_sd(prod.get("descripcion")),
                    _val_o_sd(prod.get("categoria")),
                    nombre_prov,
                    st_act,
                    st_min,
                    prod.get("precio_costo", 0.0),
                    prod.get("precio_venta", 0.0),
                    _val_o_sd(prod.get("ubicacion")),
                    _val_o_sd(prod.get("vencimiento"))
                )
                texto_busqueda = " ".join(str(v) for v in valores_fila).lower()
                if filtro and filtro not in texto_busqueda:
                    continue

                if st_act <= 0:
                    tag = "stock_agotado"
                elif st_act <= st_min:
                    tag = "stock_bajo"
                else:
                    tag = "par" if visibles % 2 == 0 else "impar"

                tabla.insert("", "end", iid=str(id_prod), values=valores_fila, tags=(tag,))
                visibles += 1

            lbl_contador.configure(
                text=gestor_ui.t("contador_filas", visibles=visibles, total=len(self._productos_api))
            )

        def cargar_datos_api():
            prov_actual = caja_proveedor.get()
            lista_provs = obtener_proveedores()
            caja_proveedor.configure(values=lista_provs if lista_provs else [gestor_ui.t("stk_sin_prov")])
            if prov_actual in lista_provs:
                caja_proveedor.set(prov_actual)
            elif _es_placeholder_prov(prov_actual):
                caja_proveedor.set(gestor_ui.t("stk_sel_prov"))

            try:
                self._productos_api = cliente_http.listar_productos()
                renderizar_tabla()
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_com_tit"), str(e))

        def limpiar_campos():
            cajas = [
                caja_codigo, caja_descripcion, caja_categoria, caja_stock_actual,
                caja_stock_minimo, caja_precio_costo, caja_precio_venta,
                caja_ubicacion, caja_vencimiento
            ]
            for caja in cajas:
                caja.delete(0, "end")
            caja_proveedor.set(gestor_ui.t("stk_sel_prov"))
            for sel in tabla.selection():
                tabla.selection_remove(sel)
            caja_codigo.focus_set()

        def guardar():
            codigo = caja_codigo.get().strip()
            descripcion = caja_descripcion.get().strip()
            categoria = caja_categoria.get().strip() or "S/D"
            proveedor = caja_proveedor.get().strip()
            if _es_placeholder_prov(proveedor):
                proveedor = ""
            stock_actual = caja_stock_actual.get().strip()
            stock_minimo = caja_stock_minimo.get().strip()
            precio_costo = caja_precio_costo.get().strip()
            precio_venta = caja_precio_venta.get().strip()
            ubicacion = caja_ubicacion.get().strip() or "S/D"
            vencimiento = caja_vencimiento.get().strip() or "S/D"

            if not codigo or not descripcion or not proveedor:
                messagebox.showwarning(gestor_ui.t("val_tit"), gestor_ui.t("stk_req"))
                return

            id_proveedor = self.mapa_nombre_a_id_prov.get(proveedor)
            if not id_proveedor:
                messagebox.showerror(gestor_ui.t("err_tx_tit"), gestor_ui.t("stk_prov_inv"))
                return

            try:
                st_act = float(stock_actual) if stock_actual else 0.0
                st_min = float(stock_minimo) if stock_minimo else 0.0
                p_cost = float(precio_costo) if precio_costo else 0.0
                p_vent = float(precio_venta) if precio_venta else 0.0
            except ValueError:
                messagebox.showerror(gestor_ui.t("err_fmt_tit"), gestor_ui.t("stk_nums_err"))
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
                "ubicacion": ubicacion,
                "vencimiento": vencimiento
            }

            try:
                cliente_http.crear_producto(datos_nuevo_producto)
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_tx_tit"), str(e))

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
                caja.delete(0, "end")
                if not gestor_ui.es_sin_dato(str(valores[idx])):
                    caja.insert(0, valores[idx])

            caja_proveedor.set(valores[3])

        def modificar():
            seleccion = tabla.selection()
            if not seleccion:
                messagebox.showwarning(gestor_ui.t("err_sel_tit"), gestor_ui.t("stk_sel_req"))
                return

            id_producto = int(seleccion[0])
            valores_actuales = tabla.item(seleccion[0], "values")
            stock_anterior = float(valores_actuales[4]) if valores_actuales else 0.0

            codigo = caja_codigo.get().strip()
            descripcion = caja_descripcion.get().strip()
            categoria = caja_categoria.get().strip() or "S/D"
            proveedor = caja_proveedor.get().strip()
            if _es_placeholder_prov(proveedor):
                proveedor = ""
            stock_actual = caja_stock_actual.get().strip()
            stock_minimo = caja_stock_minimo.get().strip()
            precio_costo = caja_precio_costo.get().strip()
            precio_venta = caja_precio_venta.get().strip()
            ubicacion = caja_ubicacion.get().strip() or "S/D"
            vencimiento = caja_vencimiento.get().strip() or "S/D"

            if not codigo or not descripcion or not proveedor:
                messagebox.showwarning(gestor_ui.t("val_tit"), gestor_ui.t("stk_req"))
                return

            id_proveedor = self.mapa_nombre_a_id_prov.get(proveedor)
            if not id_proveedor:
                messagebox.showerror(gestor_ui.t("err_tx_tit"), gestor_ui.t("stk_prov_inv"))
                return

            try:
                st_act = float(stock_actual) if stock_actual else 0.0
                st_min = float(stock_minimo) if stock_minimo else 0.0
                p_cost = float(precio_costo) if precio_costo else 0.0
                p_vent = float(precio_venta) if precio_venta else 0.0
            except ValueError:
                messagebox.showerror(gestor_ui.t("err_fmt_tit"), gestor_ui.t("stk_nums_err"))
                return

            datos_modificados = {
                "codigo": codigo,
                "descripcion": descripcion,
                "categoria": categoria,
                "id_proveedor": id_proveedor,
                "precio_costo": p_cost,
                "precio_venta": p_vent,
                "stock_minimo": st_min,
                "ubicacion": ubicacion,
                "vencimiento": vencimiento
            }

            try:
                cliente_http.modificar_producto(id_producto, datos_modificados)
                diferencia_stock = st_act - stock_anterior
                if abs(diferencia_stock) > 1e-6:
                    cliente_http.ingresar_stock(id_producto, diferencia_stock)

                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_tx_tit"), str(e))

        def eliminar():
            seleccion = tabla.selection()
            if not seleccion:
                messagebox.showwarning(gestor_ui.t("err_sel_tit"), gestor_ui.t("stk_sel_req"))
                return

            try:
                for item in seleccion:
                    cliente_http.eliminar_producto(int(item))
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_bloq_tit"), str(e))

        # ========================
        #  3. INTERFAZ DE USUARIO
        # ========================

        header = ctk.CTkFrame(self, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        lbl_header = ctk.CTkLabel(header, text=gestor_ui.t("stk_header"))
        lbl_header.pack(side="left", padx=20)

        btn_cerrar = ctk.CTkButton(
            header, text=gestor_ui.t("btn_cerrar"), command=self.destroy,
            width=86, height=30, fg_color="#475569", hover_color="#334155"
        )
        btn_cerrar.pack(side="right", padx=(4, 16))

        btn_actualizar = ctk.CTkButton(
            header, text=gestor_ui.t("btn_actualizar"), command=cargar_datos_api,
            width=96, height=30, fg_color="#0284C7", hover_color="#0369A1"
        )
        btn_actualizar.pack(side="right", padx=4)

        botones_pref = gestor_ui.crear_barra_preferencias(header)

        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=18, pady=12)

        card_form = ctk.CTkFrame(cuerpo, corner_radius=12)
        card_form.pack(fill="x", pady=(0, 10))

        grid_form = ctk.CTkFrame(card_form, fg_color="transparent")
        grid_form.pack(fill="x", padx=16, pady=(10, 6))
        for col_idx in range(5):
            grid_form.grid_columnconfigure(col_idx, weight=1)

        labels_form = []
        entries_form = []

        def _crear_campo(padre, fila, col, clave_lbl, placeholder=""):
            cont = ctk.CTkFrame(padre, fg_color="transparent")
            cont.grid(row=fila, column=col, padx=6, pady=4, sticky="ew")
            lbl = ctk.CTkLabel(cont, text=gestor_ui.t(clave_lbl), anchor="w")
            lbl.pack(fill="x", pady=(0, 2))
            entry = ctk.CTkEntry(cont, height=32, corner_radius=8, placeholder_text=placeholder)
            entry.pack(fill="x")
            labels_form.append((lbl, clave_lbl))
            entries_form.append(entry)
            return entry

        # Fila 0: Identificación, Proveedor y Ubicación (orden preservado para E2E).
        caja_codigo = _crear_campo(grid_form, 0, 0, "stk_codigo", "Ej: PROD-001")
        caja_descripcion = _crear_campo(grid_form, 0, 1, "stk_desc")
        caja_categoria = _crear_campo(grid_form, 0, 2, "stk_cat")

        cont_prov = ctk.CTkFrame(grid_form, fg_color="transparent")
        cont_prov.grid(row=0, column=3, padx=6, pady=4, sticky="ew")
        lbl_prov = ctk.CTkLabel(cont_prov, text=gestor_ui.t("stk_prov"), anchor="w")
        lbl_prov.pack(fill="x", pady=(0, 2))
        labels_form.append((lbl_prov, "stk_prov"))

        caja_proveedor = ctk.CTkComboBox(
            cont_prov, values=[gestor_ui.t("stk_sel_prov")], state="readonly",
            height=32, corner_radius=8
        )
        caja_proveedor.set(gestor_ui.t("stk_sel_prov"))
        caja_proveedor.pack(fill="x")

        caja_ubicacion = _crear_campo(grid_form, 0, 4, "stk_ubic", "Ej: Depósito A")

        # Fila 1: Cantidades, Precios y Vencimiento.
        caja_stock_actual = _crear_campo(grid_form, 1, 0, "stk_act", "0")
        caja_stock_minimo = _crear_campo(grid_form, 1, 1, "stk_min", "0")
        caja_precio_costo = _crear_campo(grid_form, 1, 2, "stk_costo", "0.00")
        caja_precio_venta = _crear_campo(grid_form, 1, 3, "stk_venta", "0.00")
        caja_vencimiento = _crear_campo(grid_form, 1, 4, "stk_venc", "S/D")

        barra_btns = ctk.CTkFrame(card_form, fg_color="transparent")
        barra_btns.pack(fill="x", padx=22, pady=(4, 10))

        btn_guardar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("stk_btn_guardar"), command=guardar,
            fg_color="#16A34A", hover_color="#15803D", height=34, width=150
        )
        btn_guardar.pack(side="left", padx=(0, 10))

        btn_modificar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("stk_btn_modificar"), command=modificar,
            fg_color="#2563EB", hover_color="#1D4ED8", height=34, width=150
        )
        btn_modificar.pack(side="left", padx=(0, 10))

        btn_eliminar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("stk_btn_eliminar"), command=eliminar,
            fg_color="#DC2626", hover_color="#B91C1C", height=34, width=150
        )
        btn_eliminar.pack(side="left", padx=(0, 10))

        btn_limpiar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("btn_limpiar"), command=limpiar_campos,
            fg_color="#64748B", hover_color="#475569", height=34, width=105
        )
        btn_limpiar.pack(side="left")

        # Tarjeta de Tabla.
        card_tabla = ctk.CTkFrame(cuerpo, corner_radius=12)
        card_tabla.pack(fill="both", expand=True)

        barra_tabla = ctk.CTkFrame(card_tabla, fg_color="transparent")
        barra_tabla.pack(fill="x", padx=14, pady=(10, 6))

        lbl_semaforo = ctk.CTkLabel(barra_tabla, text=gestor_ui.t("stk_semaforo"), anchor="w")
        lbl_semaforo.pack(side="left", fill="x", expand=True)

        caja_busqueda = ctk.CTkEntry(
            barra_tabla, width=280, height=30, corner_radius=8,
            placeholder_text=gestor_ui.t("buscar_ph")
        )
        caja_busqueda.pack(side="right")
        caja_busqueda.bind("<KeyRelease>", lambda e: renderizar_tabla())
        caja_busqueda.bind("<<Paste>>", lambda e: self.after(10, renderizar_tabla))
        caja_busqueda.bind("<<Cut>>", lambda e: self.after(10, renderizar_tabla))

        cont_tree = ctk.CTkFrame(card_tabla, fg_color="transparent")
        cont_tree.pack(fill="both", expand=True, padx=14, pady=(0, 6))
        cont_tree.grid_rowconfigure(0, weight=1)
        cont_tree.grid_columnconfigure(0, weight=1)

        columnas = (
            "Código", "Descripción", "Categoría", "Proveedor",
            "Stock Actual", "Stock Mínimo", "Precio Costo", "Precio Venta",
            "Ubicación", "Vencimiento"
        )
        claves_cols = {
            "Código": "col_codigo", "Descripción": "col_desc", "Categoría": "col_cat",
            "Proveedor": "col_prov_col", "Stock Actual": "col_stk_act", "Stock Mínimo": "col_stk_min",
            "Precio Costo": "col_costo", "Precio Venta": "col_venta",
            "Ubicación": "col_ubic", "Vencimiento": "col_venc"
        }
        tabla = ttk.Treeview(cont_tree, columns=columnas, show="headings", style="Frankie.Treeview")
        anchos = {
            "Código": 100, "Descripción": 180, "Categoría": 110, "Proveedor": 135,
            "Stock Actual": 90, "Stock Mínimo": 90, "Precio Costo": 95, "Precio Venta": 95,
            "Ubicación": 115, "Vencimiento": 95
        }
        for col in columnas:
            tabla.heading(col, text=gestor_ui.t(claves_cols[col]))
            tabla.column(col, width=anchos[col], minwidth=75)

        scroll_y = ctk.CTkScrollbar(cont_tree, orientation="vertical", command=tabla.yview)
        scroll_x = ctk.CTkScrollbar(cont_tree, orientation="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        tabla.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)

        pie_tabla = ctk.CTkFrame(card_tabla, fg_color="transparent")
        pie_tabla.pack(fill="x", padx=14, pady=(0, 8))

        lbl_contador = ctk.CTkLabel(pie_tabla, text="", anchor="w")
        lbl_contador.pack(side="left")

        lbl_atajos = ctk.CTkLabel(pie_tabla, text=gestor_ui.t("atajos_hint"), anchor="e")
        lbl_atajos.pack(side="right")

        def _aplicar_ui():
            p = gestor_ui.paleta()
            self.title(gestor_ui.t("stk_win"))
            self.configure(fg_color=p["bg_app"])
            header.configure(fg_color=p["bg_header"])
            lbl_header.configure(text=gestor_ui.t("stk_header"), text_color=p["fg_header"], font=gestor_ui.fuente(15, "bold"))
            btn_cerrar.configure(text=gestor_ui.t("btn_cerrar"), font=gestor_ui.fuente(11, "bold"))
            btn_actualizar.configure(text=gestor_ui.t("btn_actualizar"), font=gestor_ui.fuente(11, "bold"))
            gestor_ui.actualizar_barra_preferencias(botones_pref)

            card_form.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])
            card_tabla.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])

            for lbl, clave in labels_form:
                lbl.configure(text=gestor_ui.t(clave), text_color=p["fg_label"], font=gestor_ui.fuente(11, "bold"))

            for entry in entries_form:
                gestor_ui.estilizar_entry(entry)

            gestor_ui.estilizar_combo(caja_proveedor)
            if _es_placeholder_prov(caja_proveedor.get()):
                caja_proveedor.set(gestor_ui.t("stk_sel_prov"))

            for btn, clave in (
                (btn_guardar, "stk_btn_guardar"),
                (btn_modificar, "stk_btn_modificar"),
                (btn_eliminar, "stk_btn_eliminar"),
                (btn_limpiar, "btn_limpiar"),
            ):
                btn.configure(text=gestor_ui.t(clave), font=gestor_ui.fuente(12, "bold"))

            lbl_semaforo.configure(text=gestor_ui.t("stk_semaforo"), text_color=p["fg_muted"], font=gestor_ui.fuente(10, "bold"))
            gestor_ui.estilizar_entry(caja_busqueda)
            if not caja_busqueda.get():
                caja_busqueda.configure(placeholder_text=gestor_ui.t("buscar_ph"))

            gestor_ui.aplicar_estilo_treeview(self)
            gestor_ui.aplicar_tags_tabla(tabla)
            for col in columnas:
                tabla.heading(col, text=gestor_ui.t(claves_cols[col]))

            lbl_contador.configure(text_color=p["fg_muted"], font=gestor_ui.fuente(10))
            lbl_atajos.configure(text=gestor_ui.t("atajos_hint"), text_color=p["fg_muted"], font=gestor_ui.fuente(10))
            renderizar_tabla()

        # Exponemos el helper de filtrado para pruebas headless deterministas.
        self.filtrar_tabla = renderizar_tabla

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<F5>", lambda e: cargar_datos_api())
        self.bind("<Control-f>", lambda e: caja_busqueda.focus_set())
        self.bind("<Control-F>", lambda e: caja_busqueda.focus_set())

        gestor_ui.suscribir(self, _aplicar_ui)
        _aplicar_ui()
        cargar_datos_api()