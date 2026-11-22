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


class Usuario(ctk.CTkToplevel):
    """
     Ventana de administración de credenciales y roles de acceso al sistema (IAM).
     Soporta Modo Claro/Oscuro, Alto Contraste, Zoom, i18n ES/EN y búsqueda en vivo.
    """

    def __init__(self, parent, id_actual, rol_actual):
        super().__init__(parent)

        self.title(gestor_ui.t("usu_win"))
        self.geometry("1060x640")
        self.minsize(880, 540)
        self.id_actual = id_actual
        self.rol_actual = rol_actual
        self._filas_api = []
        self.after(80, self.lift)

        roles_base = ["Empleado - Ventas", "Empleado - Compras"]
        if rol_actual == "Administrador":
            roles_base = ["Administrador", "Gerente"] + roles_base

        # ===================================================
        #  2. FUNCIONALIDADES CONSUMIENDO LA API REST (HTTP)
        # ===================================================

        def renderizar_tabla():
            for item in tabla.get_children():
                tabla.delete(item)

            filtro = caja_busqueda.get().strip().lower()
            visibles = 0

            for p in self._filas_api:
                usuario_mostrar = p.get("usuario") if p.get("usuario") else gestor_ui.t("sin_cred")
                rol_vis = gestor_ui.rol_a_ui(p.get("rol"))
                nombres = p.get("nombres") or gestor_ui.t("sin_dato")
                apellidos = p.get("apellidos") or gestor_ui.t("sin_dato")

                texto_busqueda = f"{usuario_mostrar} {rol_vis} {p.get('rol', '')} {nombres} {apellidos}".lower()
                if filtro and filtro not in texto_busqueda:
                    continue

                tag = "par" if visibles % 2 == 0 else "impar"
                tabla.insert(
                    "",
                    "end",
                    iid=str(p["id"]),
                    values=(usuario_mostrar, rol_vis, nombres, apellidos),
                    tags=(tag,)
                )
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
            for caja in (caja_nombres, caja_apellidos, caja_usuario, caja_password):
                caja.delete(0, "end")
            caja_rol.set(gestor_ui.t("sel_rol"))
            for sel in tabla.selection():
                tabla.selection_remove(sel)
            caja_nombres.focus_set()

        def guardar():
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            usuario = caja_usuario.get().strip()
            password = caja_password.get().strip()
            rol = gestor_ui.rol_a_canonico(caja_rol.get())

            if not nombres or not apellidos or not usuario or not password or not rol:
                messagebox.showwarning(gestor_ui.t("val_tit"), gestor_ui.t("usu_todos_req"))
                return

            if rol_actual == "Gerente" and rol in ("Administrador", "Gerente"):
                messagebox.showerror(gestor_ui.t("err_acc_tit"), gestor_ui.t("usu_priv_err"))
                limpiar_campos()
                return

            datos_nuevo_perfil = {
                "nombres": nombres,
                "apellidos": apellidos,
                "dni": "00000000",
                "rol": rol,
                "usuario": usuario,
                "password_plana": password
            }

            try:
                cliente_http.crear_perfil(datos_nuevo_perfil, id_operador=id_actual)
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_gua_tit"), str(e))

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            if not seleccion:
                return

            valores = tabla.item(seleccion[0], "values")
            caja_usuario.delete(0, "end")
            if valores[0] not in ("[Sin Credenciales]", "[No Credentials]"):
                caja_usuario.insert(0, valores[0])

            caja_rol.set(valores[1])

            caja_nombres.delete(0, "end")
            caja_nombres.insert(0, valores[2])
            caja_apellidos.delete(0, "end")
            caja_apellidos.insert(0, valores[3])
            caja_password.delete(0, "end")

        def modificar():
            seleccion = tabla.selection()
            if not seleccion:
                messagebox.showwarning(gestor_ui.t("err_sel_tit"), gestor_ui.t("usu_sel_req"))
                return

            id_usuario_destino = int(seleccion[0])
            nombres = caja_nombres.get().strip()
            apellidos = caja_apellidos.get().strip()
            usuario = caja_usuario.get().strip()
            password = caja_password.get().strip()
            rol = gestor_ui.rol_a_canonico(caja_rol.get())

            if not nombres or not apellidos or not usuario or not rol:
                messagebox.showwarning(gestor_ui.t("val_tit"), gestor_ui.t("usu_mod_req"))
                return

            datos_modificados = {
                "nombres": nombres,
                "apellidos": apellidos,
                "rol": rol,
                "usuario": usuario
            }
            if password:
                datos_modificados["password_plana"] = password

            try:
                cliente_http.modificar_perfil(id_usuario_destino, datos_modificados, id_operador=id_actual)
                limpiar_campos()
                cargar_datos_api()
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_acc_err_tit"), str(e))

        def eliminar():
            seleccion = tabla.selection()
            if not seleccion:
                messagebox.showwarning(gestor_ui.t("err_sel_tit"), gestor_ui.t("usu_sel_req"))
                return

            id_usuario_destino = int(seleccion[0])
            try:
                cliente_http.eliminar_perfil(id_usuario_destino, id_operador=id_actual)
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

        lbl_header = ctk.CTkLabel(header, text=gestor_ui.t("usu_header"))
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

        # Tarjeta de Formulario.
        card_form = ctk.CTkFrame(cuerpo, corner_radius=12)
        card_form.pack(fill="x", pady=(0, 12))

        grid_form = ctk.CTkFrame(card_form, fg_color="transparent")
        grid_form.pack(fill="x", padx=18, pady=(12, 8))
        for col_idx in range(3):
            grid_form.grid_columnconfigure(col_idx, weight=1)

        labels_form = []
        entries_form = []

        def _crear_campo(padre, fila, col, clave_lbl, clave_ph="", oculto=False):
            cont = ctk.CTkFrame(padre, fg_color="transparent")
            cont.grid(row=fila, column=col, padx=8, pady=5, sticky="ew")
            lbl = ctk.CTkLabel(cont, text=gestor_ui.t(clave_lbl), anchor="w")
            lbl.pack(fill="x", pady=(0, 3))
            entry = ctk.CTkEntry(
                cont, height=34, corner_radius=8,
                placeholder_text=gestor_ui.t(clave_ph) if clave_ph else "",
                show="*" if oculto else ""
            )
            entry.pack(fill="x")
            labels_form.append((lbl, clave_lbl))
            entries_form.append((entry, clave_ph))
            return entry

        caja_nombres = _crear_campo(grid_form, 0, 0, "usu_nombres", "usu_nombres_ph")
        caja_apellidos = _crear_campo(grid_form, 0, 1, "usu_apellidos", "usu_apellidos_ph")
        caja_usuario = _crear_campo(grid_form, 0, 2, "usu_login", "usu_login_ph")
        caja_password = _crear_campo(grid_form, 1, 0, "usu_pass", "usu_pass_ph", oculto=True)

        cont_rol = ctk.CTkFrame(grid_form, fg_color="transparent")
        cont_rol.grid(row=1, column=1, padx=8, pady=5, sticky="ew")
        lbl_rol = ctk.CTkLabel(cont_rol, text=gestor_ui.t("usu_rol"), anchor="w")
        lbl_rol.pack(fill="x", pady=(0, 3))
        labels_form.append((lbl_rol, "usu_rol"))

        caja_rol = ctk.CTkComboBox(
            cont_rol,
            values=[gestor_ui.rol_a_ui(r) for r in roles_base],
            state="readonly",
            height=34,
            corner_radius=8
        )
        caja_rol.set(gestor_ui.t("sel_rol"))
        caja_rol.pack(fill="x")

        barra_btns = ctk.CTkFrame(card_form, fg_color="transparent")
        barra_btns.pack(fill="x", padx=26, pady=(6, 12))

        btn_guardar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("btn_guardar"), command=guardar,
            fg_color="#16A34A", hover_color="#15803D", height=35, width=130
        )
        btn_guardar.pack(side="left", padx=(0, 10))

        btn_modificar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("btn_modificar"), command=modificar,
            fg_color="#2563EB", hover_color="#1D4ED8", height=35, width=130
        )
        btn_modificar.pack(side="left", padx=(0, 10))

        btn_eliminar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("btn_eliminar"), command=eliminar,
            fg_color="#DC2626", hover_color="#B91C1C", height=35, width=130
        )
        btn_eliminar.pack(side="left", padx=(0, 10))

        btn_limpiar = ctk.CTkButton(
            barra_btns, text=gestor_ui.t("btn_limpiar"), command=limpiar_campos,
            fg_color="#64748B", hover_color="#475569", height=35, width=110
        )
        btn_limpiar.pack(side="left")

        # Tarjeta de Tabla (el buscador vive acá para mantener intactos los índices del formulario).
        card_tabla = ctk.CTkFrame(cuerpo, corner_radius=12)
        card_tabla.pack(fill="both", expand=True)

        barra_tabla = ctk.CTkFrame(card_tabla, fg_color="transparent")
        barra_tabla.pack(fill="x", padx=14, pady=(10, 6))

        lbl_ayuda = ctk.CTkLabel(barra_tabla, text=gestor_ui.t("usu_ayuda"), anchor="w")
        lbl_ayuda.pack(side="left", fill="x", expand=True)

        caja_busqueda = ctk.CTkEntry(
            barra_tabla, width=260, height=30, corner_radius=8,
            placeholder_text=gestor_ui.t("buscar_ph")
        )
        caja_busqueda.pack(side="right")
        caja_busqueda.bind("<KeyRelease>", lambda e: renderizar_tabla())

        cont_tree = ctk.CTkFrame(card_tabla, fg_color="transparent")
        cont_tree.pack(fill="both", expand=True, padx=14, pady=(0, 6))
        cont_tree.grid_rowconfigure(0, weight=1)
        cont_tree.grid_columnconfigure(0, weight=1)

        columnas = ("Usuario", "Rol", "Nombres", "Apellidos")
        claves_cols = {
            "Usuario": "col_usuario",
            "Rol": "col_rol_sis",
            "Nombres": "col_nombres",
            "Apellidos": "col_apellidos",
        }
        tabla = ttk.Treeview(cont_tree, columns=columnas, show="headings", style="Frankie.Treeview")
        anchos = {"Usuario": 190, "Rol": 190, "Nombres": 250, "Apellidos": 250}

        for col in columnas:
            tabla.heading(col, text=gestor_ui.t(claves_cols[col]))
            tabla.column(col, width=anchos[col], minwidth=120)

        scroll_y = ctk.CTkScrollbar(cont_tree, orientation="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=scroll_y.set)

        tabla.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)

        pie_tabla = ctk.CTkFrame(card_tabla, fg_color="transparent")
        pie_tabla.pack(fill="x", padx=14, pady=(0, 8))

        lbl_contador = ctk.CTkLabel(pie_tabla, text="", anchor="w")
        lbl_contador.pack(side="left")

        lbl_atajos = ctk.CTkLabel(pie_tabla, text=gestor_ui.t("atajos_hint"), anchor="e")
        lbl_atajos.pack(side="right")

        def _aplicar_ui():
            p = gestor_ui.paleta()
            self.title(gestor_ui.t("usu_win"))
            self.configure(fg_color=p["bg_app"])
            header.configure(fg_color=p["bg_header"])
            lbl_header.configure(text=gestor_ui.t("usu_header"), text_color=p["fg_header"], font=gestor_ui.fuente(15, "bold"))
            btn_cerrar.configure(text=gestor_ui.t("btn_cerrar"), font=gestor_ui.fuente(11, "bold"))
            btn_actualizar.configure(text=gestor_ui.t("btn_actualizar"), font=gestor_ui.fuente(11, "bold"))
            gestor_ui.actualizar_barra_preferencias(botones_pref)

            card_form.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])
            card_tabla.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])

            for lbl, clave in labels_form:
                lbl.configure(text=gestor_ui.t(clave), text_color=p["fg_label"], font=gestor_ui.fuente(11, "bold"))

            for entry, clave_ph in entries_form:
                gestor_ui.estilizar_entry(entry)
                if clave_ph and not entry.get():
                    entry.configure(placeholder_text=gestor_ui.t(clave_ph))

            rol_canonico_actual = gestor_ui.rol_a_canonico(caja_rol.get())
            caja_rol.configure(values=[gestor_ui.rol_a_ui(r) for r in roles_base])
            gestor_ui.estilizar_combo(caja_rol)
            caja_rol.set(gestor_ui.rol_a_ui(rol_canonico_actual) if rol_canonico_actual else gestor_ui.t("sel_rol"))

            for btn, clave in (
                (btn_guardar, "btn_guardar"),
                (btn_modificar, "btn_modificar"),
                (btn_eliminar, "btn_eliminar"),
                (btn_limpiar, "btn_limpiar"),
            ):
                btn.configure(text=gestor_ui.t(clave), font=gestor_ui.fuente(12, "bold"))

            lbl_ayuda.configure(text=gestor_ui.t("usu_ayuda"), text_color=p["fg_muted"], font=gestor_ui.fuente(11))
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

        # Atajos de accesibilidad por teclado.
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<F5>", lambda e: cargar_datos_api())
        self.bind("<Control-f>", lambda e: caja_busqueda.focus_set())
        self.bind("<Control-F>", lambda e: caja_busqueda.focus_set())

        gestor_ui.suscribir(self, _aplicar_ui)
        _aplicar_ui()
        cargar_datos_api()