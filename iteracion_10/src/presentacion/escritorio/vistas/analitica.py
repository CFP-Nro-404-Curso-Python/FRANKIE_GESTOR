import os
import sys
import math
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


class Analitica(ctk.CTkToplevel):
    """
     Tablero de Inteligencia de Negocios (BI / OLAP).
     Procesa el historial comercial desde la API REST y redibuja dinámicamente
     los 3 gráficos Canvas al alternar Modo Claro/Oscuro, Alto Contraste o ES/EN.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.title(gestor_ui.t("bi_win"))
        self.geometry("1240x695")
        self.minsize(1040, 620)
        self.after(80, self.lift)

        # Estado analítico en memoria para redibujar sin peticiones HTTP extra al cambiar tema/idioma.
        self._registros_bi = []
        self._top_10 = []
        self._serie_mensual = []
        self._serie_cat = []
        self._prod_estrella = None
        self._cat_top = None

        # ============================================
        #  2. MOTOR DE GRÁFICOS NATIVOS EN TK.CANVAS
        # ============================================

        def _formatear_eje_y(valor: float) -> str:
            if valor >= 1_000_000:
                return f"${valor / 1_000_000:.1f}M"
            if valor >= 1_000:
                return f"${valor / 1_000:.0f}k"
            return f"${valor:.0f}"

        def _acortar_etiqueta(texto: str, max_len: int = 11) -> str:
            limpio = str(texto).strip()
            if len(limpio) <= max_len:
                return limpio
            inicio = max_len - 6
            return f"{limpio[:inicio]}..{limpio[-4:]}"

        def _dibujar_grilla_y(canvas: tk.Canvas, pad_izq: int, pad_der: int, pad_arr: int, pad_aba: int, ancho: int, alto: int, max_val: float):
            p = gestor_ui.paleta()
            tam_eje = min(gestor_ui.tam(8), 10)
            alto_util = alto - pad_arr - pad_aba
            for fraccion in (0.0, 0.5, 1.0):
                y = alto - pad_aba - (fraccion * alto_util)
                if fraccion > 0:
                    canvas.create_line(pad_izq, y, ancho - pad_der, y, fill=p["canvas_grid"], dash=(2, 3))
                canvas.create_text(
                    pad_izq - 6, y,
                    text=_formatear_eje_y(max_val * fraccion),
                    anchor="e", fill=p["canvas_muted"], font=("Segoe UI", tam_eje)
                )
            canvas.create_line(pad_izq, pad_arr, pad_izq, alto - pad_aba, fill=p["canvas_axis"])
            canvas.create_line(pad_izq, alto - pad_aba, ancho - pad_der, alto - pad_aba, fill=p["canvas_axis"])

        def _dibujar_barras(canvas: tk.Canvas, datos):
            p = gestor_ui.paleta()
            tam_eje = min(gestor_ui.tam(8), 10)
            canvas.configure(bg=p["canvas_bg"])
            canvas.delete("all")
            ancho, alto = 370, 210
            if not datos:
                canvas.create_text(ancho // 2, alto // 2, text=gestor_ui.t("bi_sin_datos"), fill=p["canvas_muted"], font=("Segoe UI", 10))
                return

            pad_izq, pad_der, pad_arr, pad_aba = 52, 12, 14, 60
            ancho_util = ancho - pad_izq - pad_der
            alto_util = alto - pad_arr - pad_aba
            max_val = max(d[1] for d in datos) or 1.0

            _dibujar_grilla_y(canvas, pad_izq, pad_der, pad_arr, pad_aba, ancho, alto, max_val)

            paso_x = ancho_util / len(datos)
            ancho_barra = max(paso_x * 0.60, 10)
            color_barra = "#38BDF8" if gestor_ui.tema == "dark" else "#2563EB"

            for i, (etiqueta, valor) in enumerate(datos):
                alto_barra = (valor / max_val) * alto_util
                x0 = pad_izq + i * paso_x + (paso_x - ancho_barra) / 2
                y0 = alto - pad_aba - alto_barra
                x1 = x0 + ancho_barra
                y1 = alto - pad_aba

                canvas.create_rectangle(x0, y0, x1, y1, fill=color_barra, outline="")
                canvas.create_text(
                    (x0 + x1) / 2, y1 + 6,
                    text=_acortar_etiqueta(etiqueta, 11),
                    fill=p["canvas_text"],
                    font=("Segoe UI", tam_eje),
                    angle=38,
                    anchor="ne"
                )

        def _dibujar_lineas(canvas: tk.Canvas, datos):
            p = gestor_ui.paleta()
            tam_eje = min(gestor_ui.tam(8), 10)
            canvas.configure(bg=p["canvas_bg"])
            canvas.delete("all")
            ancho, alto = 370, 210
            if not datos:
                canvas.create_text(ancho // 2, alto // 2, text=gestor_ui.t("bi_sin_datos"), fill=p["canvas_muted"], font=("Segoe UI", 10))
                return

            pad_izq, pad_der, pad_arr, pad_aba = 52, 18, 14, 60
            ancho_util = ancho - pad_izq - pad_der
            alto_util = alto - pad_arr - pad_aba
            max_val = max(d[1] for d in datos) or 1.0

            _dibujar_grilla_y(canvas, pad_izq, pad_der, pad_arr, pad_aba, ancho, alto, max_val)

            n = len(datos)
            puntos = []
            for i, (mes, valor) in enumerate(datos):
                x = pad_izq + ancho_util / 2 if n == 1 else pad_izq + (i / (n - 1)) * ancho_util
                y = alto - pad_aba - (valor / max_val) * alto_util
                puntos.append((x, y, mes))

            color_linea = "#4ADE80" if gestor_ui.tema == "dark" else "#16A34A"
            if n > 1:
                for i in range(n - 1):
                    canvas.create_line(
                        puntos[i][0], puntos[i][1],
                        puntos[i + 1][0], puntos[i + 1][1],
                        fill=color_linea, width=2.2
                    )

            radio = 2.5 if n > 14 else 3.8
            for x, y, _ in puntos:
                canvas.create_oval(
                    x - radio, y - radio, x + radio, y + radio,
                    fill=color_linea, outline=p["canvas_bg"], width=1
                )

            if n == 1:
                indices_visibles = [0]
            else:
                max_etiquetas = max(2, int(ancho_util // 52))
                paso = max(1, math.ceil((n - 1) / (max_etiquetas - 1)))
                indices_visibles = list(range(0, n, paso))
                if indices_visibles[-1] != n - 1:
                    if (puntos[-1][0] - puntos[indices_visibles[-1]][0]) < 36:
                        indices_visibles[-1] = n - 1
                    else:
                        indices_visibles.append(n - 1)

            y_eje = alto - pad_aba
            for idx in indices_visibles:
                x, _, mes = puntos[idx]
                canvas.create_line(x, y_eje, x, y_eje + 4, fill=p["canvas_axis"])
                canvas.create_text(
                    x, y_eje + 8,
                    text=mes[-5:] if len(mes) >= 7 else mes,
                    fill=p["canvas_text"],
                    font=("Segoe UI", tam_eje),
                    angle=35,
                    anchor="ne"
                )

        def _dibujar_torta(canvas: tk.Canvas, datos):
            p = gestor_ui.paleta()
            tam_eje = min(gestor_ui.tam(8), 10)
            canvas.configure(bg=p["canvas_bg"])
            canvas.delete("all")
            ancho, alto = 370, 210
            if not datos:
                canvas.create_text(ancho // 2, alto // 2, text=gestor_ui.t("bi_sin_datos"), fill=p["canvas_muted"], font=("Segoe UI", 10))
                return

            colores = [
                "#2563EB", "#16A34A", "#D97706", "#7C3AED", "#0D9488",
                "#DC2626", "#475569", "#0284C7", "#CA8A04", "#9333EA"
            ]
            total = sum(d[1] for d in datos) or 1.0
            cx, cy, radio = 102, 105, 74

            if len(datos) == 1:
                canvas.create_oval(cx - radio, cy - radio, cx + radio, cy + radio, fill=colores[0], outline=p["canvas_bg"])
            else:
                angulo_inicio = 90.0
                for i, (_, valor) in enumerate(datos):
                    extension = -(valor / total) * 360.0
                    canvas.create_arc(
                        cx - radio, cy - radio, cx + radio, cy + radio,
                        start=angulo_inicio, extent=extension,
                        fill=colores[i % len(colores)], outline=p["canvas_bg"], width=1
                    )
                    angulo_inicio += extension

            for i, (cat, valor) in enumerate(datos[:7]):
                y = 22 + i * 24
                pct = (valor / total) * 100.0
                canvas.create_rectangle(198, y - 5, 210, y + 7, fill=colores[i % len(colores)], outline="")
                canvas.create_text(
                    216, y + 1,
                    text=f"{cat[:12]} ({pct:.1f}%)",
                    anchor="w", fill=p["canvas_text"], font=("Segoe UI", tam_eje)
                )

        def _redibujar_graficos():
            _dibujar_barras(canvas_barras, self._top_10)
            _dibujar_lineas(canvas_lineas, self._serie_mensual)
            _dibujar_torta(canvas_torta, self._serie_cat)

        def _renderizar_tabla_bi():
            for item in tabla.get_children():
                tabla.delete(item)

            filtro = caja_busqueda.get().strip().lower()
            visibles = 0
            for r in self._registros_bi:
                valores = (
                    r["id_venta"],
                    r["producto"],
                    r["categoria"],
                    f"$ {r['precio']:,.2f}",
                    f"{r['cantidad']:g}",
                    r["fecha"],
                    f"$ {r['facturacion']:,.2f}"
                )
                texto_busq = " ".join(str(v) for v in valores).lower()
                if filtro and filtro not in texto_busq:
                    continue

                tag = "par" if visibles % 2 == 0 else "impar"
                tabla.insert("", "end", iid=str(r["id_venta"]), values=valores, tags=(tag,))
                visibles += 1

            lbl_contador.configure(
                text=gestor_ui.t("contador_filas", visibles=visibles, total=len(self._registros_bi))
            )

        # ============================================
        #  3. CARGA Y PROCESAMIENTO ANALÍTICO (OLAP)
        # ============================================

        def cargar_datos_bi():
            try:
                facturas = cliente_http.listar_facturas()
                productos = cliente_http.listar_productos()
                mapa_prod = {p["id"]: p for p in productos}

                registros = []
                for f in facturas:
                    prod = mapa_prod.get(f["id_producto"], {})
                    cantidad = float(f["cantidad"])
                    precio = float(f["valor"])
                    descuento = float(f.get("descuento") or 0.0)
                    total_cobrado = (
                        float(f["total"])
                        if f.get("total") is not None
                        else (cantidad * precio) * (1.0 - (descuento / 100.0))
                    )
                    registros.append({
                        "id_venta": f["id"],
                        "producto": prod.get("descripcion", f"Producto ID {f['id_producto']}"),
                        "categoria": prod.get("categoria") or "S/D",
                        "precio": precio,
                        "cantidad": cantidad,
                        "fecha": str(f.get("fecha") or "")[:10] or "S/D",
                        "facturacion": total_cobrado
                    })

                registros.sort(key=lambda r: r["fecha"])
                self._registros_bi = registros

                if not registros:
                    self._top_10 = []
                    self._serie_mensual = []
                    self._serie_cat = []
                    self._prod_estrella = None
                    self._cat_top = None
                    lbl_kpi_facturacion.configure(text="$ 0.00")
                    lbl_kpi_operaciones.configure(text="0")
                    lbl_kpi_unidades.configure(text="0")
                    lbl_kpi_ticket.configure(text="$ 0.00")
                    lbl_subtitulo.configure(text=gestor_ui.t("bi_sub_vacio"))
                    _redibujar_graficos()
                    _renderizar_tabla_bi()
                    return

                total_facturacion = sum(r["facturacion"] for r in registros)
                total_operaciones = len(registros)
                total_unidades = sum(r["cantidad"] for r in registros)
                ticket_promedio = total_facturacion / total_operaciones

                lbl_kpi_facturacion.configure(text=f"$ {total_facturacion:,.2f}")
                lbl_kpi_operaciones.configure(text=f"{total_operaciones:,}")
                lbl_kpi_unidades.configure(text=f"{int(round(total_unidades)):,}")
                lbl_kpi_ticket.configure(text=f"$ {ticket_promedio:,.2f}")

                cant_por_prod = {}
                fact_por_prod = {}
                fact_por_mes = {}
                fact_por_cat = {}

                for r in registros:
                    cant_por_prod[r["producto"]] = cant_por_prod.get(r["producto"], 0.0) + r["cantidad"]
                    fact_por_prod[r["producto"]] = fact_por_prod.get(r["producto"], 0.0) + r["facturacion"]
                    mes = r["fecha"][:7]
                    fact_por_mes[mes] = fact_por_mes.get(mes, 0.0) + r["facturacion"]
                    fact_por_cat[r["categoria"]] = fact_por_cat.get(r["categoria"], 0.0) + r["facturacion"]

                self._prod_estrella = max(cant_por_prod.items(), key=lambda x: x[1])[0]
                self._cat_top = max(fact_por_cat.items(), key=lambda x: x[1])[0]
                lbl_subtitulo.configure(
                    text=gestor_ui.t("bi_sub_top", prod=self._prod_estrella, cat=self._cat_top)
                )

                self._top_10 = sorted(fact_por_prod.items(), key=lambda x: x[1], reverse=True)[:10]
                self._serie_mensual = sorted(fact_por_mes.items(), key=lambda x: x[0])
                self._serie_cat = sorted(
                    [(k, v) for k, v in fact_por_cat.items() if v > 0],
                    key=lambda x: x[1],
                    reverse=True
                )

                _redibujar_graficos()
                _renderizar_tabla_bi()
            except ErrorClienteAPI as e:
                messagebox.showerror(gestor_ui.t("err_com_tit"), str(e))

        # ========================
        #  4. INTERFAZ DE USUARIO
        # ========================

        header = ctk.CTkFrame(self, corner_radius=0, height=58)
        header.pack(fill="x")
        header.pack_propagate(False)

        bloque_titulo = ctk.CTkFrame(header, fg_color="transparent")
        bloque_titulo.pack(side="left", padx=20, pady=6)

        lbl_header = ctk.CTkLabel(bloque_titulo, text=gestor_ui.t("bi_header"), anchor="w")
        lbl_header.pack(anchor="w")

        lbl_subtitulo = ctk.CTkLabel(bloque_titulo, text=gestor_ui.t("bi_sub_ini"), anchor="w")
        lbl_subtitulo.pack(anchor="w")

        btn_cerrar = ctk.CTkButton(
            header, text=gestor_ui.t("btn_cerrar"), command=self.destroy,
            width=86, height=30, fg_color="#475569", hover_color="#334155"
        )
        btn_cerrar.pack(side="right", padx=(4, 16))

        btn_actualizar = ctk.CTkButton(
            header, text=gestor_ui.t("bi_btn_act"), command=cargar_datos_bi,
            width=140, height=30, fg_color="#0D9488", hover_color="#0F766E"
        )
        btn_actualizar.pack(side="right", padx=4)

        botones_pref = gestor_ui.crear_barra_preferencias(header)

        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=16, pady=10)

        # Fila 1: 4 Tarjetas KPI.
        fila_kpis = ctk.CTkFrame(cuerpo, fg_color="transparent")
        fila_kpis.pack(fill="x", pady=(0, 8))
        for i in range(4):
            fila_kpis.grid_columnconfigure(i, weight=1)

        kpis_meta = []

        def _crear_kpi(col, clave_titulo, color_acento):
            card = ctk.CTkFrame(fila_kpis, corner_radius=10)
            card.grid(row=0, column=col, padx=5, sticky="ew")
            franja = ctk.CTkFrame(card, fg_color=color_acento, width=5, corner_radius=4)
            franja.pack(side="left", fill="y", padx=(0, 10), pady=8)
            cont = ctk.CTkFrame(card, fg_color="transparent")
            cont.pack(side="left", fill="both", expand=True, pady=8, padx=(0, 10))
            lbl_tit = ctk.CTkLabel(cont, text=gestor_ui.t(clave_titulo), anchor="w")
            lbl_tit.pack(anchor="w")
            lbl_val = ctk.CTkLabel(cont, text="0", anchor="w")
            lbl_val.pack(anchor="w")
            kpis_meta.append((card, lbl_tit, clave_titulo, lbl_val))
            return lbl_val

        lbl_kpi_facturacion = _crear_kpi(0, "bi_kpi_fac", "#2563EB")
        lbl_kpi_operaciones = _crear_kpi(1, "bi_kpi_ops", "#0D9488")
        lbl_kpi_unidades = _crear_kpi(2, "bi_kpi_uni", "#16A34A")
        lbl_kpi_ticket = _crear_kpi(3, "bi_kpi_tkt", "#7C3AED")

        # Fila 2: 3 Gráficos en Canvas.
        fila_graficos = ctk.CTkFrame(cuerpo, fg_color="transparent")
        fila_graficos.pack(fill="x", pady=(0, 8))
        for i in range(3):
            fila_graficos.grid_columnconfigure(i, weight=1)

        graficos_meta = []

        def _crear_tarjeta_grafico(col, clave_titulo):
            card = ctk.CTkFrame(fila_graficos, corner_radius=10)
            card.grid(row=0, column=col, padx=5, sticky="ew")
            lbl = ctk.CTkLabel(card, text=gestor_ui.t(clave_titulo))
            lbl.pack(pady=(6, 2))
            canvas = tk.Canvas(card, width=370, height=210, bg="#FFFFFF", highlightthickness=0)
            canvas.pack(padx=6, pady=(0, 6))
            graficos_meta.append((card, lbl, clave_titulo))
            return canvas

        canvas_barras = _crear_tarjeta_grafico(0, "bi_graf_top10")
        canvas_lineas = _crear_tarjeta_grafico(1, "bi_graf_mensual")
        canvas_torta = _crear_tarjeta_grafico(2, "bi_graf_cat")

        # Fila 3: Tabla histórica de detalle con buscador.
        card_tabla = ctk.CTkFrame(cuerpo, corner_radius=12)
        card_tabla.pack(fill="both", expand=True)

        barra_tabla = ctk.CTkFrame(card_tabla, fg_color="transparent")
        barra_tabla.pack(fill="x", padx=12, pady=(8, 4))

        lbl_contador = ctk.CTkLabel(barra_tabla, text="", anchor="w")
        lbl_contador.pack(side="left")

        caja_busqueda = ctk.CTkEntry(
            barra_tabla, width=260, height=28, corner_radius=8,
            placeholder_text=gestor_ui.t("buscar_ph")
        )
        caja_busqueda.pack(side="right")
        caja_busqueda.bind("<KeyRelease>", lambda e: _renderizar_tabla_bi())

        cont_tree = ctk.CTkFrame(card_tabla, fg_color="transparent")
        cont_tree.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        cont_tree.grid_rowconfigure(0, weight=1)
        cont_tree.grid_columnconfigure(0, weight=1)

        columnas = ("ID Venta", "Producto", "Categoría", "Precio Congelado", "Cantidad", "Fecha", "Total Cobrado")
        claves_cols = {
            "ID Venta": "col_id_venta",
            "Producto": "col_prod",
            "Categoría": "col_cat",
            "Precio Congelado": "col_precio_cong",
            "Cantidad": "col_cant",
            "Fecha": "col_fecha",
            "Total Cobrado": "col_total_cob"
        }
        tabla = ttk.Treeview(cont_tree, columns=columnas, show="headings", style="Frankie.Treeview")
        anchos = {
            "ID Venta": 75, "Producto": 260, "Categoría": 150,
            "Precio Congelado": 135, "Cantidad": 85, "Fecha": 110, "Total Cobrado": 145
        }
        for col in columnas:
            tabla.heading(col, text=gestor_ui.t(claves_cols[col]))
            tabla.column(col, width=anchos[col], minwidth=70)

        scroll_y = ctk.CTkScrollbar(cont_tree, orientation="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=scroll_y.set)

        tabla.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")

        def _aplicar_ui():
            p = gestor_ui.paleta()
            self.title(gestor_ui.t("bi_win"))
            self.configure(fg_color=p["bg_app"])
            header.configure(fg_color=p["bg_header"])
            lbl_header.configure(text=gestor_ui.t("bi_header"), text_color=p["fg_header"], font=gestor_ui.fuente(14, "bold"))

            if self._prod_estrella and self._cat_top:
                sub = gestor_ui.t("bi_sub_top", prod=self._prod_estrella, cat=self._cat_top)
            elif self._registros_bi == []:
                sub = gestor_ui.t("bi_sub_vacio")
            else:
                sub = gestor_ui.t("bi_sub_ini")
            lbl_subtitulo.configure(text=sub, text_color=p["fg_header_sub"], font=gestor_ui.fuente(10))

            btn_cerrar.configure(text=gestor_ui.t("btn_cerrar"), font=gestor_ui.fuente(11, "bold"))
            btn_actualizar.configure(text=gestor_ui.t("bi_btn_act"), font=gestor_ui.fuente(11, "bold"))
            gestor_ui.actualizar_barra_preferencias(botones_pref)

            for card, lbl_tit, clave, lbl_val in kpis_meta:
                card.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])
                lbl_tit.configure(text=gestor_ui.t(clave), text_color=p["fg_muted"], font=gestor_ui.fuente(10, "bold"))
                lbl_val.configure(text_color=p["fg_text"], font=gestor_ui.fuente(16, "bold"))

            for card, lbl, clave in graficos_meta:
                card.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])
                lbl.configure(text=gestor_ui.t(clave), text_color=p["fg_text"], font=gestor_ui.fuente(11, "bold"))

            card_tabla.configure(fg_color=p["bg_card"], border_color=p["border"], border_width=p["border_width"])
            gestor_ui.estilizar_entry(caja_busqueda)
            if not caja_busqueda.get():
                caja_busqueda.configure(placeholder_text=gestor_ui.t("buscar_ph"))

            gestor_ui.aplicar_estilo_treeview(self)
            gestor_ui.aplicar_tags_tabla(tabla)
            for col in columnas:
                tabla.heading(col, text=gestor_ui.t(claves_cols[col]))

            lbl_contador.configure(text_color=p["fg_muted"], font=gestor_ui.fuente(10))
            _redibujar_graficos()
            _renderizar_tabla_bi()

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<F5>", lambda e: cargar_datos_bi())
        self.bind("<Control-f>", lambda e: caja_busqueda.focus_set())
        self.bind("<Control-F>", lambda e: caja_busqueda.focus_set())

        gestor_ui.suscribir(self, _aplicar_ui)
        _aplicar_ui()
        cargar_datos_bi()


# Alias de compatibilidad.
AnaliticaBI = Analitica