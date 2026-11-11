import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import sys
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt



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


class AnaliticaBI(tk.Toplevel):
    """
     Tablero de Control de Inteligencia de Negocios (OLAP / BI).
     Opera 100% como cliente HTTP: consume las facturas y el catálogo de productos 
     desde la API REST y procesa las métricas vectorizadas en memoria con Pandas.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.title("ANALÍTICA DE VENTAS (BUSINESS INTELLIGENCE)")
        self.geometry("1200x800")
        self.minsize(950, 650)
        
        # Protocolo de cierre para liberar la memoria RAM de los gráficos de Matplotlib.
        self.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)

        self.df = pd.DataFrame()

        # Inicialización de la interfaz y carga de datos desde el Backend.
        self.crear_interfaz()
        self.cargar_datos()



    # ==========================================================
    #  2. CONSTRUCCIÓN DE LA INTERFAZ GRÁFICA (KPIs Y GRÁFICOS)
    # ==========================================================

    def crear_interfaz(self):
        # Panel superior con título y botón de actualización.
        superior = ttk.Frame(self, padding=10)
        superior.pack(fill="x")

        ttk.Label(superior, text="TABLERO DE CONTROL - OLAP", font=("Arial", 18, "bold")).pack(side="left")
        ttk.Button(superior, text="Actualizar Análisis", command=self.cargar_datos).pack(side="right")

        # Contenedor para las tarjetas de KPIs (Indicadores).
        self.estadisticas = ttk.Frame(self, padding=10)
        self.estadisticas.pack(fill="x")

        self.indicadores = {}
        nombres_kpi = ["Facturación Total", "Operaciones", "Unidades Vendidas", "Ticket Promedio"]

        for i, nombre in enumerate(nombres_kpi):
            tarjeta = ttk.LabelFrame(self.estadisticas, text=nombre, padding=12)
            tarjeta.grid(row=0, column=i, sticky="nsew", padx=5)
            
            etiqueta = ttk.Label(tarjeta, text="Cargando...", font=("Arial", 15, "bold"))
            etiqueta.pack()
            
            self.indicadores[nombre] = etiqueta
            self.estadisticas.columnconfigure(i, weight=1)

        # Lienzo de Matplotlib para los gráficos (3 subgráficos en 1 fila).
        self.figura = Figure(figsize=(12, 4.2), dpi=90)
        self.grafico_barras = self.figura.add_subplot(131)
        self.grafico_lineas = self.figura.add_subplot(132)
        self.grafico_torta = self.figura.add_subplot(133)

        self.canvas = FigureCanvasTkAgg(self.figura, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

        # Contenedor para la tabla de datos históricos.
        frame_tabla = ttk.LabelFrame(self, text="Detalle Histórico de Ventas", padding=8)
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

        columnas = ("id_venta", "producto", "categoria", "precio", "cantidad", "fecha", "facturacion")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=8)

        encabezados = {
            "id_venta": "ID Venta",
            "producto": "Producto",
            "categoria": "Categoría",
            "precio": "Precio Congelado",
            "cantidad": "Cantidad",
            "fecha": "Fecha",
            "facturacion": "Total Cobrado"
        }

        for columna in columnas:
            self.tabla.heading(columna, text=encabezados[columna])
            self.tabla.column(columna, width=120, anchor="center")

        scroll = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")



    # =======================================================
    #  3. EXTRACCIÓN VÍA API REST Y PROCESAMIENTO CON PANDAS
    # =======================================================

    def cargar_datos(self):
        """
         Obtiene las facturas (GET /api/facturas) y los productos (GET /api/productos),
         cruza ambos conjuntos en memoria y construye el DataFrame analítico.
        """
        try:
            facturas = cliente_http.listar_facturas()
            productos = cliente_http.listar_productos()

            # Diccionario rápido para cruzar cada factura con los datos de su producto.
            mapa_productos = {p["id"]: p for p in productos}

            registros = []
            for f in facturas:
                prod = mapa_productos.get(f["id_producto"], {})
                
                total_cobrado = f.get("total")
                if total_cobrado is None:
                    total_cobrado = (float(f["cantidad"]) * float(f["valor"])) * (1.0 - (float(f.get("descuento", 0.0)) / 100.0))

                registros.append({
                    "id_venta": f["id"],
                    "producto": prod.get("descripcion", f"Producto ID {f['id_producto']}"),
                    "categoria": prod.get("categoria", "S/D"),
                    "precio": float(f["valor"]),
                    "cantidad": float(f["cantidad"]),
                    "fecha": f.get("fecha") or pd.Timestamp.now().strftime("%Y-%m-%d"),
                    "facturacion": float(total_cobrado)
                })

            self.df = pd.DataFrame(registros)

            if self.df.empty:
                # Si se ejecuta sin semillas y aún no hay ventas, dejamos los KPIs en cero.
                self.indicadores["Facturación Total"].config(text="$ 0.00")
                self.indicadores["Operaciones"].config(text="0")
                self.indicadores["Unidades Vendidas"].config(text="0")
                self.indicadores["Ticket Promedio"].config(text="$ 0.00")
                self.tabla.delete(*self.tabla.get_children())
                self.grafico_barras.clear()
                self.grafico_lineas.clear()
                self.grafico_torta.clear()
                self.canvas.draw()
                messagebox.showinfo("Información", "No hay ventas registradas para analizar.")
                return

            # Limpieza, tipado numérico y ordenamiento cronológico con Pandas.
            self.df["precio"] = pd.to_numeric(self.df["precio"])
            self.df["cantidad"] = pd.to_numeric(self.df["cantidad"])
            self.df["facturacion"] = pd.to_numeric(self.df["facturacion"])
            self.df["fecha"] = pd.to_datetime(self.df["fecha"])
            self.df = self.df.sort_values(by="fecha", ascending=True).reset_index(drop=True)

            # Disparamos las rutinas de renderizado visual.
            self.mostrar_estadisticas()
            self.mostrar_graficos()
            self.mostrar_tabla()

        except ErrorClienteAPI as error_red:
            messagebox.showerror("Error de Comunicación", str(error_red))
        except Exception as error:
            messagebox.showerror("Error Analítico", f"Fallo al procesar los datos: {str(error)}")

    def mostrar_estadisticas(self):

        # Cálculos matemáticos vectorizados en memoria RAM.
        total = self.df["facturacion"].sum()
        operaciones = len(self.df)
        unidades = self.df["cantidad"].sum()
        ticket = total / operaciones if operaciones > 0 else 0

        valores = {
            "Facturación Total": f"$ {total:,.2f}",
            "Operaciones": f"{operaciones:,}",
            "Unidades Vendidas": f"{unidades:,.0f}",
            "Ticket Promedio": f"$ {ticket:,.2f}"
        }

        for nombre, valor in valores.items():
            self.indicadores[nombre].config(text=valor)

        # Extracción del producto y categoría estrella.
        producto_estrella = self.df.groupby("producto")["cantidad"].sum().idxmax()
        categoria_estrella = self.df.groupby("categoria")["facturacion"].sum().idxmax()

        self.title(f"ANALÍTICA DE VENTAS | Más Vendido: {producto_estrella} | Categoría Top: {categoria_estrella}")

    def mostrar_graficos(self):
        self.grafico_barras.clear()
        self.grafico_lineas.clear()
        self.grafico_torta.clear()

        # 1. Gráfico de Barras: Top 10 Productos por Facturación.
        productos = self.df.groupby("producto")["facturacion"].sum().nlargest(10)
        productos.plot.bar(ax=self.grafico_barras, color="#2196F3")
        self.grafico_barras.set_title("Top 10 Productos (Facturación)")
        self.grafico_barras.set_ylabel("Facturación ($)")
        self.grafico_barras.tick_params(axis="x", labelrotation=45, labelsize=8)
        self.grafico_barras.grid(axis="y", alpha=0.3)

        # 2. Gráfico de Líneas: Evolución Mensual de Ingresos.
        mensual = self.df.copy()
        mensual["mes"] = mensual["fecha"].dt.to_period("M").astype(str)
        mensual = mensual.groupby("mes")["facturacion"].sum().sort_index()
        
        self.grafico_lineas.plot(mensual.index, mensual.values, marker="o", color="#4CAF50", linewidth=2)
        self.grafico_lineas.set_title("Evolución Mensual")
        self.grafico_lineas.set_ylabel("Facturación ($)")
        self.grafico_lineas.tick_params(axis="x", labelrotation=45, labelsize=8)
        self.grafico_lineas.grid(alpha=0.3)

        # 3. Gráfico de Torta: Participación por Categorías.
        categorias = self.df.groupby("categoria")["facturacion"].sum()
        categorias = categorias[categorias > 0]
        self.grafico_torta.set_title("Facturación por Categoría")
        
        if not categorias.empty:
            self.grafico_torta.pie(categorias.values, labels=categorias.index, autopct="%1.1f%%", startangle=90)

        # Redibuja el lienzo ajustando los márgenes.
        self.figura.tight_layout()
        self.canvas.draw()

    def mostrar_tabla(self):
        self.tabla.delete(*self.tabla.get_children())

        # Recorrido optimizado con itertuples() para poblar la grilla visual.
        for fila in self.df.itertuples(index=False):
            self.tabla.insert("", "end", values=(
                fila.id_venta,
                fila.producto,
                fila.categoria,
                f"$ {fila.precio:,.2f}",
                fila.cantidad,
                fila.fecha.strftime("%Y-%m-%d"),
                f"$ {fila.facturacion:,.2f}"
            ))

    def cerrar_ventana(self):
        
        # Destruye los objetos de Matplotlib para liberar la memoria antes de cerrar la ventana.
        self.figura.clear()
        plt.close(self.figura)
        self.destroy()