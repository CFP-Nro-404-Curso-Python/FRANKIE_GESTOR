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


class Empleado(ctk.CTkToplevel):
    """
     Formulario de gestión de Recursos Humanos (RRHH).
     Sincronizado 100% con el Backend 3FN con soporte reactivo de Tema, i18n y WCAG.
    """

    def __init__(self, parent, id_actual, rol_actual):
        super().__init__(parent)

        self.title(gestor_ui.t("emp_win"))
        self.geometry("1240x690")
        self.minsize(1024, 600)
        self.id_actual = id_actual
        self.rol_actual = rol_actual
        self._filas_api = []
        self.after(80, self.lift)

        roles_disponibles = ["Administrador", "Gerente", "Empleado - Ventas", "Empleado - Compras"]

        # ==============================================
        #  2. FUNCIONALIDADES DE "FORMULARIO EMPLEADOS"
        # ==============================================

        def _val_o_sd(valor):
            return valor if valor and valor != "S/D" else gestor_ui.t("sin_dato")

        def renderizar_tabla():
            for item in tabla.get_children():
                tabla.delete(item)

            filtro = caja_busqueda.get().strip().lower()
            visibles = 0

            for p in self._filas_api:
                rol_vis = gestor_ui.rol_a_ui(p.get("rol"))
                valores_fila = (
                    _val_o_sd(p.get("nombres")),
                    _val_o_sd(p.get("apellidos")),
                    _val_o_sd(p.get("dni")),
                    _val_o_sd(p.get("telefono")),
                    _val_o_sd(p.get("email")),
                    _val_o_sd(p.get("direccion")),
                    _val_o_sd(p.get("ciudad")),
                    _val_o_sd(p.get("provincia")),
                    _val_o_sd(p.get("cp")),
                    rol_vis
                )
                texto_busqueda = (" ".join(str(v) for v in valores_fila) + " " + str(p.get("rol", ""))).lower()
                if filtro and filtro not in texto_busqueda:
                    continue

                tag = "par" if visibles % 2 == 0 else "impar"
                tabla.insert("", "end", iid=str(p["id"]), values=valores_fila, tags=(tag,))
                visibles += 1

            lbl_contador.configure(
                text=gestor_ui.t("contador_filas", visibles=visibles, total=len(self._filas_api))
            )

        def cargar_datos_api():
            try:
                perfiles = cliente_http.listar_perfiles()
                self._filas_api = [p for p in perfiles if p.get("rol") not in ("Cliente", "Proveedor")]
                renderizar_tabla()
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_com_tit"), str(e))

        def limpiar_campos():
            cajas = [
                caja_nombres, caja_apellidos, caja_dni, caja_telefono, caja_email,
                caja_domicilio, caja_ciudad, caja_provincia, caja_cp
            ]
            for caja in cajas:
                caja.delete(0, "end")
            caja_rol.set(gestor_ui.t("sel_rol"))
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
            cp = caja_cp.get().strip() or "S/D"
            rol = gestor_ui.rol_a_canonico(caja_rol.get())

            if not nombres or not apellidos or not rol:
                messagebox.showwarning(gestor_ui.t("val_tit"), gestor_ui.t("emp_req"))
                return

            if rol_actual == "Gerente" and rol in ("Administrador", "Gerente"):
                messagebox.showerror(gestor_ui.t("err_acc_tit"), gestor_ui.t("emp_priv_err"))
                limpiar_campos()
                return

            datos_nuevo_empleado = {
                "nombres": nombres,
                "apellidos": apellidos,
                "dni": dni,
                "rol": rol,
                "telefono": telefono,
                "email": email,
                "direccion": domicilio,
                "ciudad": ciudad,
                "provincia": provincia,
                "cp": cp
            }

            try:
                cliente_http.crear_perfil(datos_nuevo_empleado, id_operador=id_actual)
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
                caja_domicilio, caja_ciudad, caja_provincia, caja_cp
            ]
            for i, caja in enumerate(cajas):
                caja.delete(0, "end")
                if not gestor_ui.es_sin_dato(valores[i]):
                    caja.insert(0, valores[i])

            caja_rol.set(valores[9])

        def modificar():
            seleccion = tabla.selection()
            if not seleccion:
                messagebox.showwarning(gestor_ui.t("err_sel_tit"), gestor_ui.t("emp_sel_req"))
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
            rol = gestor_ui.rol_a_canonico(caja_rol.get())

            if not nombres or not apellidos or not rol:
                messagebox.showwarning(gestor_ui.t("val_tit"), gestor_ui.t("emp_req"))
                return

            datos_modificados = {
                "nombres": nombres,
                "apellidos": apellidos,
                "dni": dni,
                "rol": rol,
                "telefono": telefono,
                "email": email,
                "direccion": domicilio,
                "ciudad": ciudad,
                "provincia": provincia,
                "cp": cp
            }

            try:
                cliente_http.modificar_perfil(id_empleado, datos_modificados, id_operador=id_actual)
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_acc_err_tit"), str(e))

        def eliminar():
            seleccion = tabla.selection()
            if not seleccion:
                messagebox.showwarning(gestor_ui.t("err_sel_tit"), gestor_ui.t("emp_sel_req"))
                return

            try:
                for item in seleccion:
                    cliente_http.eliminar_perfil(int(item), id_operador=id_actual)
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

        lbl_header = ctk.CTkLabel(header, text=gestor_ui.t("emp_header"))
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

        # Fila 0: Datos Filiatorios y Contacto.
        caja_nombres = _crear_campo(grid_form, 0, 0, "usu_nombres")
        caja_apellidos = _crear_campo(grid_form, 0, 1, "usu_apellidos")
        caja_dni = _crear_campo(grid_form, 0, 2, "emp_dni")
        caja_telefono = _crear_campo(grid_form, 0, 3, "emp_tel")
        caja_email = _crear_campo(grid_form, 0, 4, "emp_email")

        # Fila 1: Domicilio y Rol.
        caja_domicilio = _crear_campo(grid_form, 1, 0, "emp_dir")
        caja_ciudad = _crear_campo(grid_form, 1, 1, "emp_ciudad")
        caja_provincia = _crear_campo(grid_form, 1, 2, "emp_prov")
        caja_cp = _crear_campo(grid_form, 1, 3, "emp_cp")

        cont_rol = ctk.CTkFrame(grid_form, fg_color="transparent")
        cont_rol.grid(row=1, column=4, padx=6, pady=4, sticky="ew")
        lbl_rol = ctk.CTkLabel(cont_rol, text=gestor_ui.t("emp_rol"), anchor="w")
        lbl_rol.pack(fill="x", pady=(0, 2))
        labels_form.append((lbl_rol, "emp_rol"))

        caja_rol = ctk.CTkComboBox(
            cont_rol,
            values=[gestor_ui.rol_a_ui(r) for r in roles_disponibles],
            state="readonly",
            height=32,
            corner_radius=8
        )
        caja_rol.set(gestor_ui.t("sel_rol"))
        caja_rol.pack(fill="x")

        barra_btns = ctk.CTkFrame(card_form, fg_color="transparent")
        barra_btns.pack(fill="x", padx=22, pady=(4, 10))

        btn_guardar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("emp_btn_guardar"), command=guardar,
            fg_color="#16A34A", hover_color="#15803D", height=34, width=140
        )
        btn_guardar.pack(side="left", padx=(0, 10))

        btn_modificar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("emp_btn_modificar"), command=modificar,
            fg_color="#2563EB", hover_color="#1D4ED8", height=34, width=140
        )
        btn_modificar.pack(side="left", padx=(0, 10))

        btn_eliminar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("emp_btn_eliminar"), command=eliminar,
            fg_color="#DC2626", hover_color="#B91C1C", height=34, width=140
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

        columnas = ("Nombres", "Apellidos", "DNI", "Teléfono", "Email", "Dirección", "Ciudad", "Provincia", "CP", "Rol")
        claves_cols = {
            "Nombres": "col_nombres", "Apellidos": "col_apellidos", "DNI": "col_dni",
            "Teléfono": "col_tel", "Email": "col_email", "Dirección": "col_dir",
            "Ciudad": "col_ciudad", "Provincia": "col_prov", "CP": "col_cp", "Rol": "col_rol"
        }
        tabla = ttk.Treeview(cont_tree, columns=columnas, show="headings", style="Frankie.Treeview")
        anchos = {
            "Nombres": 120, "Apellidos": 120, "DNI": 95, "Teléfono": 110,
            "Email": 160, "Dirección": 145, "Ciudad": 110, "Provincia": 110, "CP": 65, "Rol": 135
        }
        for col in columnas:
            tabla.heading(col, text=gestor_ui.t(claves_cols[col]))
            tabla.column(col, width=anchos[col], minwidth=65)

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
            self.title(gestor_ui.t("emp_win"))
            self.configure(fg_color=p["bg_app"])
            header.configure(fg_color=p["bg_header"])
            lbl_header.configure(text=gestor_ui.t("emp_header"), text_color=p["fg_header"], font=gestor_ui.fuente(15, "bold"))
            btn_cerrar.configure(text=gestor_ui.t("btn_cerrar"), font=gestor_ui.fuente(11, "bold"))
            btn_actualizar.configure(text=gestor_ui.t("btn_actualizar"), font=gestor_ui.fuente(11, "bold"))
            gestor_ui.actualizar_barra_preferencias(botones_pref)

            card_form.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])
            card_tabla.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])

            for lbl, clave in labels_form:
                lbl.configure(text=gestor_ui.t(clave), text_color=p["fg_label"], font=gestor_ui.fuente(11, "bold"))

            for entry in entries_form:
                gestor_ui.estilizar_entry(entry)

            rol_canonico_actual = gestor_ui.rol_a_canonico(caja_rol.get())
            caja_rol.configure(values=[gestor_ui.rol_a_ui(r) for r in roles_disponibles])
            gestor_ui.estilizar_combo(caja_rol)
            caja_rol.set(gestor_ui.rol_a_ui(rol_canonico_actual) if rol_canonico_actual else gestor_ui.t("sel_rol"))

            for btn, clave in (
                (btn_guardar, "emp_btn_guardar"),
                (btn_modificar, "emp_btn_modificar"),
                (btn_eliminar, "emp_btn_eliminar"),
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