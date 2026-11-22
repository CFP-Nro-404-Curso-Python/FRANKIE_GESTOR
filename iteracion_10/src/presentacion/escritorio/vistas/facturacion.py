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


class Facturacion(ctk.CTkToplevel):
    """
     Formulario de Facturación y Operaciones Comerciales.
     Opera 100% contra la API REST con soporte reactivo de Tema, i18n y WCAG.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.title(gestor_ui.t("fac_win"))
        self.geometry("1240x690")
        self.minsize(1024, 600)
        self.after(80, self.lift)

        self.mapa_productos_codigo = {}
        self.mapa_productos_id = {}
        self.factura_seleccionada = None
        self.total_acumulado_tabla = 0.0
        self._porcentaje_global_activo = 0.0
        self._facturas_api = []

        # ================================================
        #  2. FUNCIONALIDADES DE "FORMULARIO FACTURACIÓN"
        # ================================================

        def _es_placeholder_combo(texto: str) -> bool:
            limpio = (texto or "").strip()
            return (
                not limpio
                or limpio.startswith(("Seleccione", "Select ", "Sin ", "No ", "Cargando", "Loading"))
            )

        def _setear_valor_unitario(texto: str):
            caja_valor.configure(state="normal")
            caja_valor.delete(0, "end")
            if texto:
                caja_valor.insert(0, texto)
            caja_valor.configure(state="readonly")

        def autocompletar_precio(seleccion=None):
            valor_sel = seleccion if seleccion is not None else caja_producto.get()
            if _es_placeholder_combo(valor_sel):
                _setear_valor_unitario("")
                return
            codigo = valor_sel.split(" - ")[0]
            prod = self.mapa_productos_codigo.get(codigo)
            if prod:
                _setear_valor_unitario(str(prod["precio_venta"]))

        def _extraer_id_de_etiqueta(etiqueta: str):
            if "ID: " not in etiqueta:
                return None
            try:
                return int(etiqueta.split("ID: ")[1].replace(")", "").strip())
            except ValueError:
                return None

        def actualizar_etiquetas_totales(gran_total: float, porcentaje_global: float = 0.0):
            self._porcentaje_global_activo = porcentaje_global
            total_final = gran_total * (1.0 - (porcentaje_global / 100.0))
            monto_fmt = f"{total_final:,.2f}"
            lbl_total_general.configure(text=gestor_ui.t("fac_total", monto=monto_fmt))
            lbl_total_descuento.configure(
                text=gestor_ui.t("fac_total_desc", pct=f"{porcentaje_global:g}", monto=monto_fmt)
            )

        def renderizar_tabla():
            for item in tabla.get_children():
                tabla.delete(item)

            filtro = caja_busqueda.get().strip().lower()
            visibles = 0

            for f in self._facturas_api:
                prod = self.mapa_productos_id.get(f["id_producto"])
                etiqueta_prod = f"{prod['codigo']} - {prod['descripcion']}" if prod else f"ID {f['id_producto']}"
                cantidad = float(f["cantidad"])
                valor = float(f["valor"])
                descuento = float(f.get("descuento") or 0.0)
                total_fila = (
                    float(f["total"])
                    if f.get("total") is not None
                    else (cantidad * valor) * (1.0 - (descuento / 100.0))
                )

                valores_fila = (
                    etiqueta_prod,
                    f"{cantidad:g}",
                    f"$ {valor:,.2f}",
                    f"{descuento:g}%",
                    f"$ {total_fila:,.2f}"
                )
                texto_busqueda = " ".join(str(v) for v in valores_fila).lower()
                if filtro and filtro not in texto_busqueda:
                    continue

                tag = "par" if visibles % 2 == 0 else "impar"
                tabla.insert("", "end", iid=str(f["id"]), values=valores_fila, tags=(tag,))
                visibles += 1

            lbl_contador.configure(
                text=gestor_ui.t("contador_filas", visibles=visibles, total=len(self._facturas_api))
            )

        def cargar_datos_api():
            vendedor_previo = caja_vendedor.get()
            cliente_previo = caja_cliente.get()

            self.mapa_productos_codigo.clear()
            self.mapa_productos_id.clear()
            self.total_acumulado_tabla = 0.0

            try:
                vendedores = cliente_http.listar_perfiles_por_rol("Empleado - Ventas")
                clientes = cliente_http.listar_perfiles_por_rol("Cliente")
                productos = cliente_http.listar_productos()
                facturas = cliente_http.listar_facturas()

                lista_vendedores = [f"{v['nombres']} {v['apellidos']} (ID: {v['id']})" for v in vendedores]
                lista_clientes = [f"{c['nombres']} {c['apellidos']} (ID: {c['id']})" for c in clientes]
                lista_productos = []

                for p in productos:
                    self.mapa_productos_codigo[p["codigo"]] = p
                    self.mapa_productos_id[p["id"]] = p
                    lista_productos.append(f"{p['codigo']} - {p['descripcion']}")

                caja_vendedor.configure(values=lista_vendedores if lista_vendedores else [gestor_ui.t("fac_sin_vend")])
                caja_cliente.configure(values=lista_clientes if lista_clientes else [gestor_ui.t("fac_sin_cli")])
                caja_producto.configure(values=lista_productos if lista_productos else [gestor_ui.t("fac_sin_prod")])

                if vendedor_previo in lista_vendedores:
                    caja_vendedor.set(vendedor_previo)
                else:
                    caja_vendedor.set(gestor_ui.t("fac_sel_vend"))

                if cliente_previo in lista_clientes:
                    caja_cliente.set(cliente_previo)
                else:
                    caja_cliente.set(gestor_ui.t("fac_sel_cli"))

                if _es_placeholder_combo(caja_producto.get()):
                    caja_producto.set(gestor_ui.t("fac_sel_prod"))

                gran_total = 0.0
                for f in facturas:
                    cantidad = float(f["cantidad"])
                    valor = float(f["valor"])
                    descuento = float(f.get("descuento") or 0.0)
                    total_fila = (
                        float(f["total"])
                        if f.get("total") is not None
                        else (cantidad * valor) * (1.0 - (descuento / 100.0))
                    )
                    gran_total += total_fila

                self._facturas_api = facturas
                self.total_acumulado_tabla = gran_total
                renderizar_tabla()
                actualizar_etiquetas_totales(gran_total, 0.0)
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_com_tit"), str(e))

        def limpiar_campos():
            caja_producto.set(gestor_ui.t("fac_sel_prod"))
            caja_cantidad.delete(0, "end")
            _setear_valor_unitario("")
            caja_descuento.delete(0, "end")
            caja_descuento.insert(0, "0")
            self.factura_seleccionada = None
            for sel in tabla.selection():
                tabla.selection_remove(sel)

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            if not seleccion:
                return

            id_fac = int(seleccion[0])
            valores = tabla.item(seleccion[0], "values")
            etiqueta_prod = valores[0]
            cantidad_str = str(valores[1])
            valor_str = str(valores[2]).replace("$", "").replace(",", "").strip()
            descuento_str = str(valores[3]).replace("%", "").strip()

            caja_producto.set(etiqueta_prod)
            caja_cantidad.delete(0, "end")
            caja_cantidad.insert(0, cantidad_str)
            _setear_valor_unitario(valor_str)
            caja_descuento.delete(0, "end")
            caja_descuento.insert(0, descuento_str)

            self.factura_seleccionada = {
                "id": id_fac,
                "etiqueta_prod": etiqueta_prod,
                "cantidad": float(cantidad_str),
                "descuento": float(descuento_str)
            }

        def guardar():
            vendedor_sel = caja_vendedor.get().strip()
            cliente_sel = caja_cliente.get().strip()
            producto_sel = caja_producto.get().strip()
            cantidad_str = caja_cantidad.get().strip()
            descuento_str = caja_descuento.get().strip()

            if (
                _es_placeholder_combo(vendedor_sel)
                or _es_placeholder_combo(cliente_sel)
                or _es_placeholder_combo(producto_sel)
            ):
                messagebox.showwarning(gestor_ui.t("val_tit"), gestor_ui.t("fac_req"))
                return

            try:
                cantidad = float(cantidad_str)
                descuento = float(descuento_str) if descuento_str else 0.0
            except ValueError:
                messagebox.showerror(gestor_ui.t("err_fmt_tit"), gestor_ui.t("fac_nums_err"))
                return

            if cantidad <= 0 or descuento < 0 or descuento > 100:
                messagebox.showerror(gestor_ui.t("val_tit"), gestor_ui.t("fac_rango_err"))
                return

            id_vendedor = _extraer_id_de_etiqueta(vendedor_sel)
            id_cliente = _extraer_id_de_etiqueta(cliente_sel)
            codigo_prod = producto_sel.split(" - ")[0]
            prod = self.mapa_productos_codigo.get(codigo_prod)

            if not id_vendedor or not id_cliente or not prod:
                messagebox.showerror(gestor_ui.t("err_tx_tit"), gestor_ui.t("fac_asoc_err"))
                return

            try:
                cliente_http.emitir_factura({
                    "id_vendedor": id_vendedor,
                    "id_cliente": id_cliente,
                    "id_producto": prod["id"],
                    "cantidad": cantidad,
                    "descuento": descuento
                })

                nuevo_stock = float(prod["stock_actual"]) - cantidad
                stock_minimo = float(prod["stock_minimo"])

                limpiar_campos()
                cargar_datos_api()

                if nuevo_stock <= stock_minimo:
                    messagebox.showwarning(
                        gestor_ui.t("fac_rep_tit"),
                        gestor_ui.t("fac_rep_msg", u=int(nuevo_stock))
                    )
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_tx_tit"), str(e))

        def modificar():
            """
             Reemplaza el comprobante seleccionado apoyándose en la atomicidad
             de DELETE /api/facturas/{id} (restitución de stock en Backend).
            """
            if not self.factura_seleccionada:
                messagebox.showwarning(gestor_ui.t("err_sel_tit"), gestor_ui.t("fac_sel_req"))
                return

            vendedor_sel = caja_vendedor.get().strip()
            cliente_sel = caja_cliente.get().strip()
            producto_sel = caja_producto.get().strip()
            cantidad_str = caja_cantidad.get().strip()
            descuento_str = caja_descuento.get().strip()

            if (
                _es_placeholder_combo(vendedor_sel)
                or _es_placeholder_combo(cliente_sel)
                or _es_placeholder_combo(producto_sel)
            ):
                messagebox.showwarning(gestor_ui.t("val_tit"), gestor_ui.t("fac_req"))
                return

            try:
                cantidad_nueva = float(cantidad_str)
                descuento_nuevo = float(descuento_str) if descuento_str else 0.0
            except ValueError:
                messagebox.showerror(gestor_ui.t("err_fmt_tit"), gestor_ui.t("fac_nums_err"))
                return

            if cantidad_nueva <= 0 or descuento_nuevo < 0 or descuento_nuevo > 100:
                messagebox.showerror(gestor_ui.t("val_tit"), gestor_ui.t("fac_rango_err"))
                return

            id_vendedor = _extraer_id_de_etiqueta(vendedor_sel)
            id_cliente = _extraer_id_de_etiqueta(cliente_sel)
            codigo_viejo = self.factura_seleccionada["etiqueta_prod"].split(" - ")[0]
            codigo_nuevo = producto_sel.split(" - ")[0]
            prod_viejo = self.mapa_productos_codigo.get(codigo_viejo)
            prod_nuevo = self.mapa_productos_codigo.get(codigo_nuevo)

            if not id_vendedor or not id_cliente or not prod_nuevo:
                messagebox.showerror(gestor_ui.t("err_tx_tit"), gestor_ui.t("fac_asoc_err"))
                return

            try:
                cliente_http.anular_factura(self.factura_seleccionada["id"])

                try:
                    cliente_http.emitir_factura({
                        "id_vendedor": id_vendedor,
                        "id_cliente": id_cliente,
                        "id_producto": prod_nuevo["id"],
                        "cantidad": cantidad_nueva,
                        "descuento": descuento_nuevo
                    })
                except ErrorClienteAPI as error_emision:
                    if prod_viejo:
                        cliente_http.emitir_factura({
                            "id_vendedor": id_vendedor,
                            "id_cliente": id_cliente,
                            "id_producto": prod_viejo["id"],
                            "cantidad": self.factura_seleccionada["cantidad"],
                            "descuento": self.factura_seleccionada["descuento"]
                        })
                    messagebox.showerror(gestor_ui.t("err_tx_tit"), str(error_emision))
                    cargar_datos_api()
                    return

                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_tx_tit"), str(e))

        def eliminar():
            """Anula el comprobante delegando al Backend la baja lógica y restitución atómica."""
            if not self.factura_seleccionada:
                messagebox.showwarning(gestor_ui.t("err_sel_tit"), gestor_ui.t("fac_sel_req"))
                return

            try:
                cliente_http.anular_factura(self.factura_seleccionada["id"])
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_bloq_tit"), str(e))

        def calcular_descuento_global():
            valor_str = caja_descuento_global.get().strip()
            try:
                porcentaje = float(valor_str) if valor_str else 0.0
            except ValueError:
                messagebox.showerror(gestor_ui.t("err_fmt_tit"), gestor_ui.t("fac_desc_num"))
                return

            if porcentaje < 0 or porcentaje > 100:
                messagebox.showerror(gestor_ui.t("val_tit"), gestor_ui.t("fac_desc_rango"))
                return

            actualizar_etiquetas_totales(self.total_acumulado_tabla, porcentaje)
            caja_descuento_global.delete(0, "end")

        # ========================
        #  3. INTERFAZ DE USUARIO
        # ========================

        header = ctk.CTkFrame(self, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        lbl_header = ctk.CTkLabel(header, text=gestor_ui.t("fac_header"))
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
        cuerpo.pack(fill="both", expand=True, padx=18, pady=10)

        # Tarjeta de Formulario (combos[0..2] y cajas[0..2] preservados para E2E).
        card_form = ctk.CTkFrame(cuerpo, corner_radius=12)
        card_form.pack(fill="x", pady=(0, 8))

        grid_form = ctk.CTkFrame(card_form, fg_color="transparent")
        grid_form.pack(fill="x", padx=16, pady=(10, 4))
        for col_idx in range(3):
            grid_form.grid_columnconfigure(col_idx, weight=1)

        labels_form = []
        entries_form = []

        def _crear_combo(padre, fila, col, clave_lbl, comando=None):
            cont = ctk.CTkFrame(padre, fg_color="transparent")
            cont.grid(row=fila, column=col, padx=6, pady=3, sticky="ew")
            lbl = ctk.CTkLabel(cont, text=gestor_ui.t(clave_lbl), anchor="w")
            lbl.pack(fill="x", pady=(0, 2))
            combo = ctk.CTkComboBox(
                cont, values=["..."], state="readonly",
                command=comando, height=32, corner_radius=8
            )
            combo.pack(fill="x")
            labels_form.append((lbl, clave_lbl))
            return combo

        def _crear_entry(padre, fila, col, clave_lbl, placeholder="", readonly=False):
            cont = ctk.CTkFrame(padre, fg_color="transparent")
            cont.grid(row=fila, column=col, padx=6, pady=3, sticky="ew")
            lbl = ctk.CTkLabel(cont, text=gestor_ui.t(clave_lbl), anchor="w")
            lbl.pack(fill="x", pady=(0, 2))
            entry = ctk.CTkEntry(cont, height=32, corner_radius=8, placeholder_text=placeholder)
            if readonly:
                entry.configure(state="readonly")
            entry.pack(fill="x")
            labels_form.append((lbl, clave_lbl))
            entries_form.append((entry, readonly))
            return entry

        caja_vendedor = _crear_combo(grid_form, 0, 0, "fac_vendedor")
        caja_cliente = _crear_combo(grid_form, 0, 1, "fac_cliente")
        caja_producto = _crear_combo(grid_form, 0, 2, "fac_producto", comando=autocompletar_precio)

        caja_cantidad = _crear_entry(grid_form, 1, 0, "fac_cantidad", "1")
        caja_valor = _crear_entry(grid_form, 1, 1, "fac_valor", "0.00", readonly=True)
        caja_descuento = _crear_entry(grid_form, 1, 2, "fac_desc_item", "0")
        caja_descuento.insert(0, "0")

        barra_btns = ctk.CTkFrame(card_form, fg_color="transparent")
        barra_btns.pack(fill="x", padx=22, pady=(6, 10))

        btn_guardar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("fac_btn_guardar"), command=guardar,
            fg_color="#16A34A", hover_color="#15803D", height=34, width=165
        )
        btn_guardar.pack(side="left", padx=(0, 10))

        btn_modificar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("fac_btn_modificar"), command=modificar,
            fg_color="#2563EB", hover_color="#1D4ED8", height=34, width=165
        )
        btn_modificar.pack(side="left", padx=(0, 10))

        btn_eliminar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("fac_btn_eliminar"), command=eliminar,
            fg_color="#DC2626", hover_color="#B91C1C", height=34, width=165
        )
        btn_eliminar.pack(side="left", padx=(0, 10))

        btn_limpiar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("btn_limpiar"), command=limpiar_campos,
            fg_color="#64748B", hover_color="#475569", height=34, width=105
        )
        btn_limpiar.pack(side="left")

        # Tarjeta de Tabla.
        card_tabla = ctk.CTkFrame(cuerpo, corner_radius=12)
        card_tabla.pack(fill="both", expand=True, pady=(0, 8))

        barra_tabla = ctk.CTkFrame(card_tabla, fg_color="transparent")
        barra_tabla.pack(fill="x", padx=14, pady=(8, 4))

        lbl_contador = ctk.CTkLabel(barra_tabla, text="", anchor="w")
        lbl_contador.pack(side="left")

        caja_busqueda = ctk.CTkEntry(
            barra_tabla, width=280, height=28, corner_radius=8,
            placeholder_text=gestor_ui.t("buscar_ph")
        )
        caja_busqueda.pack(side="right")
        caja_busqueda.bind("<KeyRelease>", lambda e: renderizar_tabla())

        cont_tree = ctk.CTkFrame(card_tabla, fg_color="transparent")
        cont_tree.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        cont_tree.grid_rowconfigure(0, weight=1)
        cont_tree.grid_columnconfigure(0, weight=1)

        columnas = ("Producto", "Cantidad", "Valor en $", "Descuento en %", "Total en $")
        claves_cols = {
            "Producto": "col_prod",
            "Cantidad": "col_cant",
            "Valor en $": "col_valor",
            "Descuento en %": "col_desc_pct",
            "Total en $": "col_total"
        }
        tabla = ttk.Treeview(cont_tree, columns=columnas, show="headings", style="Frankie.Treeview")
        anchos = {"Producto": 420, "Cantidad": 110, "Valor en $": 160, "Descuento en %": 130, "Total en $": 180}

        for col in columnas:
            tabla.heading(col, text=gestor_ui.t(claves_cols[col]))
            tabla.column(col, width=anchos[col], minwidth=90)

        scroll_y = ctk.CTkScrollbar(cont_tree, orientation="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=scroll_y.set)

        tabla.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)

        # Tarjeta inferior de Totales y Descuento Global.
        card_totales = ctk.CTkFrame(cuerpo, corner_radius=12)
        card_totales.pack(fill="x")

        fila_totales = ctk.CTkFrame(card_totales, fg_color="transparent")
        fila_totales.pack(fill="x", padx=18, pady=10)

        bloque_izq = ctk.CTkFrame(fila_totales, fg_color="transparent")
        bloque_izq.pack(side="left")

        lbl_total_general = ctk.CTkLabel(bloque_izq, text="", anchor="w")
        lbl_total_general.pack(anchor="w")

        lbl_total_descuento = ctk.CTkLabel(bloque_izq, text="", anchor="w")
        lbl_total_descuento.pack(anchor="w")

        bloque_der = ctk.CTkFrame(fila_totales, fg_color="transparent")
        bloque_der.pack(side="right")

        lbl_desc_global = ctk.CTkLabel(bloque_der, text=gestor_ui.t("fac_desc_global"))
        lbl_desc_global.pack(side="left", padx=(0, 8))

        caja_descuento_global = ctk.CTkEntry(
            bloque_der, width=90, height=34, corner_radius=8, placeholder_text="0"
        )
        caja_descuento_global.pack(side="left", padx=(0, 10))

        btn_calc_global = ctk.CTkButton(
            bloque_der,
            text=gestor_ui.t("fac_btn_calc"),
            command=calcular_descuento_global,
            fg_color="#D97706",
            hover_color="#B45309",
            height=34
        )
        btn_calc_global.pack(side="left")

        def _aplicar_ui():
            p = gestor_ui.paleta()
            self.title(gestor_ui.t("fac_win"))
            self.configure(fg_color=p["bg_app"])
            header.configure(fg_color=p["bg_header"])
            lbl_header.configure(text=gestor_ui.t("fac_header"), text_color=p["fg_header"], font=gestor_ui.fuente(15, "bold"))
            btn_cerrar.configure(text=gestor_ui.t("btn_cerrar"), font=gestor_ui.fuente(11, "bold"))
            btn_actualizar.configure(text=gestor_ui.t("btn_actualizar"), font=gestor_ui.fuente(11, "bold"))
            gestor_ui.actualizar_barra_preferencias(botones_pref)

            for card in (card_form, card_tabla, card_totales):
                card.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])

            for lbl, clave in labels_form:
                lbl.configure(text=gestor_ui.t(clave), text_color=p["fg_label"], font=gestor_ui.fuente(11, "bold"))

            for entry, ro in entries_form:
                gestor_ui.estilizar_entry(entry, readonly=ro)

            for combo, clave_sel in (
                (caja_vendedor, "fac_sel_vend"),
                (caja_cliente, "fac_sel_cli"),
                (caja_producto, "fac_sel_prod"),
            ):
                gestor_ui.estilizar_combo(combo)
                if _es_placeholder_combo(combo.get()):
                    combo.set(gestor_ui.t(clave_sel))

            for btn, clave in (
                (btn_guardar, "fac_btn_guardar"),
                (btn_modificar, "fac_btn_modificar"),
                (btn_eliminar, "fac_btn_eliminar"),
                (btn_limpiar, "btn_limpiar"),
            ):
                btn.configure(text=gestor_ui.t(clave), font=gestor_ui.fuente(12, "bold"))

            gestor_ui.estilizar_entry(caja_busqueda)
            if not caja_busqueda.get():
                caja_busqueda.configure(placeholder_text=gestor_ui.t("buscar_ph"))

            gestor_ui.estilizar_entry(caja_descuento_global)

            gestor_ui.aplicar_estilo_treeview(self)
            gestor_ui.aplicar_tags_tabla(tabla)
            for col in columnas:
                tabla.heading(col, text=gestor_ui.t(claves_cols[col]))

            lbl_contador.configure(text_color=p["fg_muted"], font=gestor_ui.fuente(10))
            lbl_total_general.configure(text_color=p["fg_text"], font=gestor_ui.fuente(14, "bold"))
            lbl_total_descuento.configure(text_color="#16A34A", font=gestor_ui.fuente(12, "bold"))
            lbl_desc_global.configure(text=gestor_ui.t("fac_desc_global"), text_color=p["fg_label"], font=gestor_ui.fuente(11, "bold"))
            btn_calc_global.configure(text=gestor_ui.t("fac_btn_calc"), font=gestor_ui.fuente(12, "bold"))

            actualizar_etiquetas_totales(self.total_acumulado_tabla, self._porcentaje_global_activo)
            renderizar_tabla()

        # Exponemos helpers útiles para pruebas automatizadas.
        self.autocompletar_precio = autocompletar_precio

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<F5>", lambda e: cargar_datos_api())
        self.bind("<Control-f>", lambda e: caja_busqueda.focus_set())
        self.bind("<Control-F>", lambda e: caja_busqueda.focus_set())

        gestor_ui.suscribir(self, _aplicar_ui)
        _aplicar_ui()
        cargar_datos_api()