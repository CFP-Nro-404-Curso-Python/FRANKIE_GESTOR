import os
import re
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


class ConsolaSQL(ctk.CTkToplevel):
    """
     Consola SQL de Auditoría (Solo Lectura / Sandboxing).
     Valida el rol Administrador contra la API REST y proyecta sentencias SELECT
     sin acoplar la vista a sqlite3, con soporte reactivo de Tema, i18n y WCAG.
    """

    PATRON_PROHIBIDO = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|GRANT|REVOKE|ATTACH|DETACH|PRAGMA)\b",
        re.IGNORECASE
    )

    def __init__(self, parent, id_actual=None):
        super().__init__(parent)

        self.id_actual = id_actual if id_actual is not None else cliente_http.id_operador
        self.title(gestor_ui.t("sql_win"))
        self.geometry("1140x670")
        self.minsize(920, 560)
        self.after(80, self.lift)

        # Estado persistido en memoria para traducirlo en vivo al cambiar ES/EN.
        self._estado_meta = {"clave": "sql_est_esp", "kwargs": {}, "texto_libre": None, "tipo": "muted"}

        # ==================================================
        #  2. MOTOR DE SANDBOXING Y PROYECCIÓN DE CONSULTAS
        # ==================================================

        def _actualizar_label_estado():
            p = gestor_ui.paleta()
            color_map = {
                "muted": p["fg_muted"],
                "ok": "#16A34A",
                "error": "#DC2626",
            }
            if self._estado_meta["texto_libre"] is not None:
                texto = self._estado_meta["texto_libre"]
            else:
                texto = gestor_ui.t(self._estado_meta["clave"], **self._estado_meta["kwargs"])
            lbl_estado.configure(
                text=texto,
                text_color=color_map.get(self._estado_meta["tipo"], p["fg_muted"]),
                font=gestor_ui.fuente(11, slant="italic")
            )

        def _set_estado(clave=None, tipo="muted", texto_libre=None, **kwargs):
            self._estado_meta = {
                "clave": clave or "sql_est_esp",
                "kwargs": kwargs,
                "texto_libre": texto_libre,
                "tipo": tipo
            }
            _actualizar_label_estado()

        def cargar_ejemplo(sentencia: str):
            editor_sql.delete("1.0", "end")
            editor_sql.insert("1.0", sentencia)

        def limpiar_consola():
            editor_sql.delete("1.0", "end")
            tabla.delete(*tabla.get_children())
            tabla["columns"] = ()
            _set_estado("sql_est_esp", tipo="muted")

        def renderizar_resultados(columnas, filas):
            tabla.delete(*tabla.get_children())
            tabla["columns"] = columnas

            for col in columnas:
                tabla.heading(col, text=col.upper())
                tabla.column(col, width=130, minwidth=80)

            for idx, fila in enumerate(filas):
                valores = [
                    fila.get(col) if fila.get(col) is not None else "NULL"
                    for col in columnas
                ]
                tag = "par" if idx % 2 == 0 else "impar"
                tabla.insert("", "end", iid=str(idx), values=valores, tags=(tag,))

        def ejecutar_consulta():
            query_cruda = editor_sql.get("1.0", "end").strip()
            if not query_cruda:
                return

            # 1. Validación RBAC activa contra la API REST.
            try:
                perfil_operador = cliente_http.obtener_perfil(self.id_actual)
                if perfil_operador.get("rol") != "Administrador":
                    messagebox.showerror(gestor_ui.t("err_acc_tit"), gestor_ui.t("sql_solo_admin"))
                    _set_estado("sql_est_rbac", tipo="error")
                    return
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_com_tit"), str(e))
                return

            # 2. Filtro restrictivo de solo lectura (Sandboxing).
            if self.PATRON_PROHIBIDO.search(query_cruda):
                messagebox.showerror(gestor_ui.t("sql_bloq_tit"), gestor_ui.t("sql_bloq_msg"))
                _set_estado("sql_est_sbx", tipo="error")
                return

            query_limpia = query_cruda.rstrip(";").strip()
            if not re.match(r"^SELECT\b", query_limpia, re.IGNORECASE):
                _set_estado("sql_solo_sel", tipo="error")
                return

            try:
                # 3. Recuperación de catálogos vivos desde el Backend HTTP.
                usuarios = cliente_http.listar_perfiles()
                productos = cliente_http.listar_productos()
                facturacion = cliente_http.listar_facturas()

                tablas_auditables = {
                    "usuarios": usuarios,
                    "perfiles": usuarios,
                    "productos": productos,
                    "facturacion": facturacion,
                    "facturas": facturacion,
                    "roles": [
                        {"id": 1, "rol": "Administrador", "habilitado": 1},
                        {"id": 2, "rol": "Gerente", "habilitado": 1},
                        {"id": 3, "rol": "Empleado - Ventas", "habilitado": 1},
                        {"id": 4, "rol": "Empleado - Compras", "habilitado": 1},
                        {"id": 5, "rol": "Proveedor", "habilitado": 1},
                        {"id": 6, "rol": "Cliente", "habilitado": 1},
                    ],
                }

                match_tabla = re.search(r"\bFROM\s+([a-zA-Z0-9_]+)", query_limpia, re.IGNORECASE)
                if not match_tabla:
                    raise ValueError("Sintaxis inválida: falta especificar la cláusula FROM <tabla>.")

                nombre_tabla = match_tabla.group(1).lower()
                if nombre_tabla not in tablas_auditables:
                    raise ValueError(f"Tabla no encontrada en el esquema auditable: {nombre_tabla}")

                filas = list(tablas_auditables[nombre_tabla])

                match_limit = re.search(r"\bLIMIT\s+(\d+)", query_limpia, re.IGNORECASE)
                limite = min(int(match_limit.group(1)), 1000) if match_limit else 1000
                filas = filas[:limite]

                match_cols = re.search(r"^SELECT\s+(.+?)\s+FROM\b", query_limpia, re.IGNORECASE)
                cols_raw = match_cols.group(1).strip() if match_cols else "*"

                nombres_columnas = []
                if filas:
                    todas = list(filas[0].keys())
                    if cols_raw == "*":
                        nombres_columnas = todas
                    else:
                        nombres_columnas = [c.strip().split(".")[-1] for c in cols_raw.split(",")]

                renderizar_resultados(nombres_columnas, filas)
                _set_estado("sql_est_ok", tipo="ok", n=len(filas))
            except (ErrorClienteAPI, ValueError) as e:
                _set_estado(texto_libre=f"Error SQL: {e}", tipo="error")

        # ========================
        #  3. INTERFAZ DE USUARIO
        # ========================

        header = ctk.CTkFrame(self, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        lbl_header = ctk.CTkLabel(header, text=gestor_ui.t("sql_header"))
        lbl_header.pack(side="left", padx=20)

        btn_cerrar = ctk.CTkButton(
            header, text=gestor_ui.t("btn_cerrar"), command=self.destroy,
            width=86, height=30, fg_color="#475569", hover_color="#334155"
        )
        btn_cerrar.pack(side="right", padx=(4, 16))

        botones_pref = gestor_ui.crear_barra_preferencias(header)

        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=18, pady=12)

        # Tarjeta de Editor SQL.
        card_editor = ctk.CTkFrame(cuerpo, corner_radius=12)
        card_editor.pack(fill="x", pady=(0, 12))

        barra_chips = ctk.CTkFrame(card_editor, fg_color="transparent")
        barra_chips.pack(fill="x", padx=16, pady=(12, 6))

        lbl_rapidas = ctk.CTkLabel(barra_chips, text=gestor_ui.t("sql_rapidas"))
        lbl_rapidas.pack(side="left", padx=(0, 10))

        ejemplos = [
            ("SELECT * FROM usuarios", "SELECT * FROM usuarios"),
            ("SELECT * FROM productos LIMIT 20", "SELECT * FROM productos LIMIT 20"),
            ("SELECT * FROM facturacion LIMIT 20", "SELECT * FROM facturacion LIMIT 20"),
            ("SELECT * FROM roles", "SELECT * FROM roles"),
        ]
        chips_btns = []
        for etiqueta, sql in ejemplos:
            chip = ctk.CTkButton(
                barra_chips,
                text=etiqueta,
                command=lambda q=sql: cargar_ejemplo(q),
                height=26,
                corner_radius=14
            )
            chip.pack(side="left", padx=(0, 8))
            chips_btns.append(chip)

        editor_sql = ctk.CTkTextbox(card_editor, height=115, corner_radius=8)
        editor_sql.pack(fill="x", padx=16, pady=6)

        barra_acciones = ctk.CTkFrame(card_editor, fg_color="transparent")
        barra_acciones.pack(fill="x", padx=16, pady=(6, 12))

        btn_ejecutar = ctk.CTkButton(
            barra_acciones, text=gestor_ui.t("sql_btn_ejec"), command=ejecutar_consulta,
            fg_color="#16A34A", hover_color="#15803D", height=34, width=155
        )
        btn_ejecutar.pack(side="left", padx=(0, 10))

        btn_limpiar = ctk.CTkButton(
            barra_acciones, text=gestor_ui.t("sql_btn_limp"), command=limpiar_consola,
            fg_color="#64748B", hover_color="#475569", height=34, width=140
        )
        btn_limpiar.pack(side="left")

        lbl_estado = ctk.CTkLabel(barra_acciones, text="")
        lbl_estado.pack(side="right", padx=6)

        # Tarjeta de Resultados.
        card_res = ctk.CTkFrame(cuerpo, corner_radius=12)
        card_res.pack(fill="both", expand=True)

        cont_tree = ctk.CTkFrame(card_res, fg_color="transparent")
        cont_tree.pack(fill="both", expand=True, padx=14, pady=14)
        cont_tree.grid_rowconfigure(0, weight=1)
        cont_tree.grid_columnconfigure(0, weight=1)

        tabla = ttk.Treeview(cont_tree, show="headings", style="Frankie.Treeview")
        scroll_y = ctk.CTkScrollbar(cont_tree, orientation="vertical", command=tabla.yview)
        scroll_x = ctk.CTkScrollbar(cont_tree, orientation="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        tabla.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        def _aplicar_ui():
            p = gestor_ui.paleta()
            self.title(gestor_ui.t("sql_win"))
            self.configure(fg_color=p["bg_app"])
            header.configure(fg_color=p["bg_header"])
            lbl_header.configure(text=gestor_ui.t("sql_header"), text_color=p["fg_header"], font=gestor_ui.fuente(15, "bold"))
            btn_cerrar.configure(text=gestor_ui.t("btn_cerrar"), font=gestor_ui.fuente(11, "bold"))
            gestor_ui.actualizar_barra_preferencias(botones_pref)

            card_editor.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])
            card_res.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])

            lbl_rapidas.configure(text=gestor_ui.t("sql_rapidas"), text_color=p["fg_label"], font=gestor_ui.fuente(11, "bold"))
            for chip in chips_btns:
                chip.configure(
                    fg_color=p["chip_bg"],
                    hover_color=p["chip_hover"],
                    text_color=p["chip_fg"],
                    font=gestor_ui.fuente(10, family="Consolas")
                )

            editor_sql.configure(
                fg_color=p["consola_bg"],
                text_color=p["consola_fg"],
                border_color=p["border"],
                border_width=p["border_width"],
                font=gestor_ui.fuente(12, family="Consolas")
            )

            btn_ejecutar.configure(text=gestor_ui.t("sql_btn_ejec"), font=gestor_ui.fuente(12, "bold"))
            btn_limpiar.configure(text=gestor_ui.t("sql_btn_limp"), font=gestor_ui.fuente(12, "bold"))
            _actualizar_label_estado()

            gestor_ui.aplicar_estilo_treeview(self)
            gestor_ui.aplicar_tags_tabla(tabla)

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Control-Return>", lambda e: ejecutar_consulta())

        gestor_ui.suscribir(self, _aplicar_ui)
        _aplicar_ui()


# Alias de compatibilidad en caso de importaciones previas como 'Consola'.
Consola = ConsolaSQL