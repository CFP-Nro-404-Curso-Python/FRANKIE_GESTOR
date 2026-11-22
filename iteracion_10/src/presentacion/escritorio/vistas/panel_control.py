import os
import sys
import json
import socket
from datetime import datetime
from tkinter import messagebox
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


def _obtener_ip_lan() -> str:
    """Detecta la dirección IPv4 local para mostrar el acceso Web LAN al operador."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


class PanelControl(ctk.CTkToplevel):
    """
     Menú principal del sistema con control de acceso basado en roles (RBAC).
     Soporta Modo Claro/Oscuro, Alto Contraste, Zoom tipográfico e i18n ES/EN en vivo.
    """

    def __init__(self, parent, id_usuario, rol_usuario, nombres_usuario, apellidos_usuario):
        super().__init__(parent)

        self.parent = parent
        self.id_usuario = id_usuario
        self.rol_usuario = rol_usuario
        self.nombres_usuario = nombres_usuario
        self.apellidos_usuario = apellidos_usuario

        cliente_http.id_operador = id_usuario

        self.title(gestor_ui.t("panel_win"))
        self.minsize(740, 580)

        ancho_win, alto_win = 860, 640
        pos_x = max((self.winfo_screenwidth() - ancho_win) // 2, 0)
        pos_y = max((self.winfo_screenheight() - alto_win) // 2, 0)
        self.geometry(f"{ancho_win}x{alto_win}+{pos_x}+{pos_y}")

        self.protocol("WM_DELETE_WINDOW", self._salir_aplicacion)
        self.after(80, self.lift)

        # ============================================
        #  2. PERMISOS RBAC (ESPEJO EXACTO DE LA WEB)
        # ============================================

        p_clientes = rol_usuario in ("Administrador", "Gerente", "Empleado - Ventas")
        p_facturacion = rol_usuario in ("Administrador", "Gerente", "Empleado - Ventas")
        p_proveedores = rol_usuario in ("Administrador", "Gerente", "Empleado - Compras")
        p_stock = rol_usuario in ("Administrador", "Gerente", "Empleado - Compras")
        p_empleados = rol_usuario in ("Administrador", "Gerente")
        p_usuarios = rol_usuario in ("Administrador", "Gerente")
        p_root = rol_usuario == "Administrador"
        p_analitica = rol_usuario in ("Administrador", "Gerente")

        # =============================================
        #  3. NAVEGACIÓN LAZY IMPORTS Y BACKUP VÍA API
        # =============================================

        def abrir_clientes():
            from clientes import Cliente
            Cliente(self)

        def abrir_facturacion():
            from facturacion import Facturacion
            Facturacion(self)

        def abrir_proveedores():
            from proveedores import Proveedor
            Proveedor(self)

        def abrir_stock():
            from stock import Stock
            Stock(self)

        def abrir_empleados():
            from empleados import Empleado
            Empleado(self, id_actual=self.id_usuario, rol_actual=self.rol_usuario)

        def abrir_usuarios():
            from usuarios import Usuario
            Usuario(self, id_actual=self.id_usuario, rol_actual=self.rol_usuario)

        def abrir_consola():
            from consola import ConsolaSQL
            ConsolaSQL(self, id_actual=self.id_usuario)

        def abrir_analitica():
            from analitica import Analitica
            Analitica(self)

        def generar_backup():
            try:
                perfiles = cliente_http.listar_perfiles()
                productos = cliente_http.listar_productos()
                facturas = cliente_http.listar_facturas()

                carpeta_backups = os.path.join(DIRECTORIO_RAIZ, "backups")
                os.makedirs(carpeta_backups, exist_ok=True)

                marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
                ruta_archivo = os.path.join(carpeta_backups, f"backup_frankie_{marca_tiempo}.json")

                respaldo = {
                    "sistema": "Frankie Gestor",
                    "fecha_exportacion": datetime.now().isoformat(),
                    "operador_id": self.id_usuario,
                    "datos": {
                        "perfiles": perfiles,
                        "productos": productos,
                        "facturas": facturas
                    }
                }

                with open(ruta_archivo, "w", encoding="utf-8") as archivo:
                    json.dump(respaldo, archivo, ensure_ascii=False, indent=2)

                messagebox.showinfo(
                    gestor_ui.t("bkp_ok_tit"),
                    gestor_ui.t("bkp_ok_msg", ruta=ruta_archivo)
                )
            except (ErrorClienteAPI, OSError) as e:
                messagebox.showerror(
                    gestor_ui.t("bkp_err_tit"),
                    gestor_ui.t("bkp_err_msg", err=e)
                )

        def cerrar_sesion():
            cliente_http.datos_sesion = None
            self.destroy()
            self.parent.deiconify()

        # ========================
        #  4. INTERFAZ DE USUARIO
        # ========================

        header = ctk.CTkFrame(self, corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        info_izq = ctk.CTkFrame(header, fg_color="transparent")
        info_izq.pack(side="left", padx=18, pady=8)

        lbl_marca = ctk.CTkLabel(info_izq, text="FRANKIE GESTOR", anchor="w")
        lbl_marca.pack(anchor="w")

        lbl_op = ctk.CTkLabel(info_izq, text="", anchor="w")
        lbl_op.pack(anchor="w")

        ip_lan = _obtener_ip_lan()
        badge_lan = ctk.CTkLabel(
            header,
            text=f"Web LAN: http://{ip_lan}:8080",
            fg_color="#0F766E",
            text_color="#FFFFFF",
            corner_radius=8,
            padx=10,
            pady=4
        )
        badge_lan.pack(side="right", padx=(6, 16))

        botones_pref = gestor_ui.crear_barra_preferencias(header)

        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=26, pady=18)

        lbl_bienvenida = ctk.CTkLabel(cuerpo, text="")
        lbl_bienvenida.pack(pady=(0, 2))

        lbl_subtitulo = ctk.CTkLabel(cuerpo, text="")
        lbl_subtitulo.pack(pady=(0, 14))

        card_menu = ctk.CTkFrame(cuerpo, corner_radius=14)
        card_menu.pack(fill="both", expand=True)

        grilla = ctk.CTkFrame(card_menu, fg_color="transparent")
        grilla.pack(fill="both", expand=True, padx=20, pady=18)
        grilla.grid_columnconfigure(0, weight=1)
        grilla.grid_columnconfigure(1, weight=1)

        modulos_meta = []

        def _crear_boton_modulo(fila, col, clave_i18n, comando, habilitado, color, hover, colspan=1):
            btn = ctk.CTkButton(
                grilla,
                text=gestor_ui.t(clave_i18n),
                command=comando,
                height=52,
                corner_radius=10,
                state="normal" if habilitado else "disabled"
            )
            btn.grid(row=fila, column=col, columnspan=colspan, padx=8, pady=7, sticky="ew")
            modulos_meta.append((btn, clave_i18n, habilitado, color, hover))
            return btn

        _crear_boton_modulo(0, 0, "panel_clientes", abrir_clientes, p_clientes, "#2563EB", "#1D4ED8")
        _crear_boton_modulo(0, 1, "panel_facturacion", abrir_facturacion, p_facturacion, "#2563EB", "#1D4ED8")
        _crear_boton_modulo(1, 0, "panel_proveedores", abrir_proveedores, p_proveedores, "#0284C7", "#0369A1")
        _crear_boton_modulo(1, 1, "panel_stock", abrir_stock, p_stock, "#0284C7", "#0369A1")
        _crear_boton_modulo(2, 0, "panel_empleados", abrir_empleados, p_empleados, "#D97706", "#B45309")
        _crear_boton_modulo(2, 1, "panel_usuarios", abrir_usuarios, p_usuarios, "#7C3AED", "#6D28D9")
        _crear_boton_modulo(3, 0, "panel_consola", abrir_consola, p_root, "#475569", "#334155")
        _crear_boton_modulo(3, 1, "panel_backup", generar_backup, p_root, "#334155", "#1E293B")
        _crear_boton_modulo(4, 0, "panel_analitica", abrir_analitica, p_analitica, "#0D9488", "#0F766E", colspan=2)

        pie = ctk.CTkFrame(cuerpo, fg_color="transparent")
        pie.pack(fill="x", pady=(12, 0))

        btn_salir = ctk.CTkButton(
            pie,
            text=gestor_ui.t("panel_salir"),
            command=cerrar_sesion,
            width=165,
            height=38,
            corner_radius=8,
            fg_color="#DC2626",
            hover_color="#B91C1C"
        )
        btn_salir.pack()

        def _aplicar_ui():
            p = gestor_ui.paleta()
            rol_vis = gestor_ui.rol_a_ui(self.rol_usuario)

            self.title(gestor_ui.t("panel_win"))
            self.configure(fg_color=p["bg_app"])
            header.configure(fg_color=p["bg_header"])
            lbl_marca.configure(text_color=p["fg_header"], font=gestor_ui.fuente(16, "bold"))
            lbl_op.configure(
                text=gestor_ui.t("panel_op", nombre=self.nombres_usuario, apellido=self.apellidos_usuario, rol=rol_vis),
                text_color=p["fg_header_sub"],
                font=gestor_ui.fuente(11)
            )
            badge_lan.configure(font=gestor_ui.fuente(10, "bold", family="Consolas"))
            gestor_ui.actualizar_barra_preferencias(botones_pref)

            lbl_bienvenida.configure(
                text=gestor_ui.t("panel_bienv", nombre=self.nombres_usuario.upper(), apellido=self.apellidos_usuario.upper()),
                text_color=p["fg_text"],
                font=gestor_ui.fuente(17, "bold")
            )
            lbl_subtitulo.configure(
                text=gestor_ui.t("panel_sub", rol=rol_vis),
                text_color=p["fg_muted"],
                font=gestor_ui.fuente(11)
            )

            card_menu.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])

            for btn, clave, hab, color, hover in modulos_meta:
                btn.configure(
                    text=gestor_ui.t(clave),
                    fg_color=color if hab else p["btn_dis_bg"],
                    hover_color=hover if hab else p["btn_dis_bg"],
                    text_color="#FFFFFF" if hab else p["btn_dis_fg"],
                    font=gestor_ui.fuente(13, "bold")
                )

            btn_salir.configure(text=gestor_ui.t("panel_salir"), font=gestor_ui.fuente(12, "bold"))

        gestor_ui.suscribir(self, _aplicar_ui)
        _aplicar_ui()

    def _salir_aplicacion(self):
        """Cierra la aplicación completa al cerrar la ventana principal con la X."""
        self.destroy()
        self.parent.destroy()