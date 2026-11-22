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


class Cliente(ctk.CTkToplevel):
    """
     Formulario de gestión comercial de Clientes.
     Sincronizado 100% con el Backend 3FN con soporte reactivo de Tema, i18n y WCAG.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.title(gestor_ui.t("cli_win"))
        self.geometry("1200x670")
        self.minsize(980, 560)
        self._filas_api = []
        self.after(80, self.lift)

        # =============================================
        #  2. FUNCIONALIDADES DE "FORMULARIO CLIENTES"
        # =============================================

        def _val_o_sd(valor):
            return valor if valor and valor != "S/D" else gestor_ui.t("sin_dato")

        def renderizar_tabla():
            for item in tabla.get_children():
                tabla.delete(item)

            filtro = caja_busqueda.get().strip().lower()
            visibles = 0

            for c in self._filas_api:
                valores_fila = (
                    _val_o_sd(c.get("nombres")),
                    _val_o_sd(c.get("apellidos")),
                    _val_o_sd(c.get("dni")),
                    _val_o_sd(c.get("telefono")),
                    _val_o_sd(c.get("email")),
                    _val_o_sd(c.get("direccion")),
                    _val_o_sd(c.get("ciudad")),
                    _val_o_sd(c.get("provincia")),
                    _val_o_sd(c.get("cp"))
                )
                texto_busqueda = " ".join(str(v) for v in valores_fila).lower()
                if filtro and filtro not in texto_busqueda:
                    continue

                tag = "par" if visibles % 2 == 0 else "impar"
                tabla.insert("", "end", iid=str(c["id"]), values=valores_fila, tags=(tag,))
                visibles += 1

            lbl_contador.configure(
                text=gestor_ui.t("contador_filas", visibles=visibles, total=len(self._filas_api))
            )

        def cargar_datos_api():
            try:
                self._filas_api = cliente_http.listar_perfiles_por_rol("Cliente")
                renderizar_tabla()
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_com_tit"), str(e))

        def limpiar_campos():
            cajas = [
                caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email,
                caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal
            ]
            for caja in cajas:
                caja.delete(0, "end")
            for sel in tabla.selection():
                tabla.selection_remove(sel)
            caja_nombres.focus_set()

        def guardar():
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
                messagebox.showwarning(gestor_ui.t("val_tit"), gestor_ui.t("cli_req"))
                return

            datos_nuevo_cliente = {
                "nombres": nombres,
                "apellidos": apellidos,
                "dni": dni,
                "rol": "Cliente",
                "telefono": telefono,
                "email": email,
                "direccion": domicilio,
                "ciudad": ciudad,
                "provincia": provincia,
                "cp": codigo_postal
            }

            try:
                cliente_http.crear_perfil(datos_nuevo_cliente)
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
                caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email,
                caja_domicilio, caja_ciudad, caja_provincia, caja_codigo_postal
            ]
            for i, caja in enumerate(cajas):
                caja.delete(0, "end")
                if not gestor_ui.es_sin_dato(valores[i]):
                    caja.insert(0, valores[i])

        def modificar():
            seleccion = tabla.selection()
            if not seleccion:
                messagebox.showwarning(gestor_ui.t("err_sel_tit"), gestor_ui.t("cli_sel_req"))
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
                messagebox.showwarning(gestor_ui.t("val_tit"), gestor_ui.t("cli_req"))
                return

            datos_modificados = {
                "nombres": nombres,
                "apellidos": apellidos,
                "dni": dni,
                "rol": "Cliente",
                "telefono": telefono,
                "email": email,
                "direccion": domicilio,
                "ciudad": ciudad,
                "provincia": provincia,
                "cp": codigo_postal
            }

            try:
                cliente_http.modificar_perfil(id_cliente, datos_modificados)
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_act_tit"), str(e))

        def eliminar():
            seleccion = tabla.selection()
            if not seleccion:
                messagebox.showwarning(gestor_ui.t("err_sel_tit"), gestor_ui.t("cli_sel_req"))
                return

            try:
                for item in seleccion:
                    cliente_http.eliminar_perfil(int(item))
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

        lbl_header = ctk.CTkLabel(header, text=gestor_ui.t("cli_header"))
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

        def _crear_campo(padre, fila, col, clave_lbl):
            cont = ctk.CTkFrame(padre, fg_color="transparent")
            cont.grid(row=fila, column=col, padx=6, pady=4, sticky="ew")
            lbl = ctk.CTkLabel(cont, text=gestor_ui.t(clave_lbl), anchor="w")
            lbl.pack(fill="x", pady=(0, 2))
            entry = ctk.CTkEntry(cont, height=32, corner_radius=8)
            entry.pack(fill="x")
            labels_form.append((lbl, clave_lbl))
            entries_form.append(entry)
            return entry

        # Orden exacto preservado para compatibilidad E2E.
        caja_nombres = _crear_campo(grid_form, 0, 0, "usu_nombres")
        caja_apellidos = _crear_campo(grid_form, 0, 1, "usu_apellidos")
        caja_dni = _crear_campo(grid_form, 0, 2, "emp_dni")
        caja_telefono = _crear_campo(grid_form, 0, 3, "emp_tel")
        caja_email = _crear_campo(grid_form, 0, 4, "emp_email")

        caja_domicilio = _crear_campo(grid_form, 1, 0, "emp_dir")
        caja_ciudad = _crear_campo(grid_form, 1, 1, "emp_ciudad")
        caja_provincia = _crear_campo(grid_form, 1, 2, "emp_prov")
        caja_codigo_postal = _crear_campo(grid_form, 1, 3, "cli_cp")

        barra_btns = ctk.CTkFrame(card_form, fg_color="transparent")
        barra_btns.pack(fill="x", padx=22, pady=(4, 10))

        btn_guardar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("cli_btn_guardar"), command=guardar,
            fg_color="#16A34A", hover_color="#15803D", height=34, width=145
        )
        btn_guardar.pack(side="left", padx=(0, 10))

        btn_modificar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("cli_btn_modificar"), command=modificar,
            fg_color="#2563EB", hover_color="#1D4ED8", height=34, width=145
        )
        btn_modificar.pack(side="left", padx=(0, 10))

        btn_eliminar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("cli_btn_eliminar"), command=eliminar,
            fg_color="#DC2626", hover_color="#B91C1C", height=34, width=145
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

        lbl_contador = ctk.CTkLabel(barra_tabla, text="", anchor="w")
        lbl_contador.pack(side="left")

        caja_busqueda = ctk.CTkEntry(
            barra_tabla, width=280, height=30, corner_radius=8,
            placeholder_text=gestor_ui.t("buscar_ph")
        )
        caja_busqueda.pack(side="right")
        caja_busqueda.bind("<KeyRelease>", lambda e: renderizar_tabla())

        cont_tree = ctk.CTkFrame(card_tabla, fg_color="transparent")
        cont_tree.pack(fill="both", expand=True, padx=14, pady=(0, 6))
        cont_tree.grid_rowconfigure(0, weight=1)
        cont_tree.grid_columnconfigure(0, weight=1)

        columnas = ("Nombres", "Apellidos", "DNI", "Teléfono", "Email", "Dirección", "Ciudad", "Provincia", "Cód. Postal")
        claves_cols = {
            "Nombres": "col_nombres", "Apellidos": "col_apellidos", "DNI": "col_dni",
            "Teléfono": "col_tel", "Email": "col_email", "Dirección": "col_dir",
            "Ciudad": "col_ciudad", "Provincia": "col_prov", "Cód. Postal": "cli_cp"
        }
        tabla = ttk.Treeview(cont_tree, columns=columnas, show="headings", style="Frankie.Treeview")
        anchos = {
            "Nombres": 125, "Apellidos": 125, "DNI": 95, "Teléfono": 115,
            "Email": 170, "Dirección": 155, "Ciudad": 115, "Provincia": 115, "Cód. Postal": 90
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

        lbl_atajos = ctk.CTkLabel(card_tabla, text=gestor_ui.t("atajos_hint"), anchor="e")
        lbl_atajos.pack(fill="x", padx=14, pady=(0, 8))

        def _aplicar_ui():
            p = gestor_ui.paleta()
            self.title(gestor_ui.t("cli_win"))
            self.configure(fg_color=p["bg_app"])
            header.configure(fg_color=p["bg_header"])
            lbl_header.configure(text=gestor_ui.t("cli_header"), text_color=p["fg_header"], font=gestor_ui.fuente(15, "bold"))
            btn_cerrar.configure(text=gestor_ui.t("btn_cerrar"), font=gestor_ui.fuente(11, "bold"))
            btn_actualizar.configure(text=gestor_ui.t("btn_actualizar"), font=gestor_ui.fuente(11, "bold"))
            gestor_ui.actualizar_barra_preferencias(botones_pref)

            card_form.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])
            card_tabla.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])

            for lbl, clave in labels_form:
                lbl.configure(text=gestor_ui.t(clave), text_color=p["fg_label"], font=gestor_ui.fuente(11, "bold"))

            for entry in entries_form:
                gestor_ui.estilizar_entry(entry)

            for btn, clave in (
                (btn_guardar, "cli_btn_guardar"),
                (btn_modificar, "cli_btn_modificar"),
                (btn_eliminar, "cli_btn_eliminar"),
                (btn_limpiar, "btn_limpiar"),
            ):
                btn.configure(text=gestor_ui.t(clave), font=gestor_ui.fuente(12, "bold"))

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

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<F5>", lambda e: cargar_datos_api())
        self.bind("<Control-f>", lambda e: caja_busqueda.focus_set())
        self.bind("<Control-F>", lambda e: caja_busqueda.focus_set())

        gestor_ui.suscribir(self, _aplicar_ui)
        _aplicar_ui()
        cargar_datos_api()