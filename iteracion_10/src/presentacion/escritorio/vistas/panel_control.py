import tkinter as tk
from tkinter import messagebox
import os
import sys
import shutil
from datetime import datetime



# ==========================================================
#  1. ANCLAJE DE DIRECTORIOS E INTEGRACIÓN CON CLIENTE HTTP
# ==========================================================

# Subimos 4 niveles desde src/presentacion/escritorio/vistas/ hasta la raíz del proyecto (iteracion_10).
DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_ESCRITORIO = os.path.dirname(DIRECTORIO_VISTAS)
DIRECTORIO_PRESENTACION = os.path.dirname(DIRECTORIO_ESCRITORIO)
DIRECTORIO_SRC = os.path.dirname(DIRECTORIO_PRESENTACION)
DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_SRC)

for ruta in (DIRECTORIO_RAIZ, DIRECTORIO_ESCRITORIO, DIRECTORIO_VISTAS):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

from src.presentacion.escritorio.cliente_api import cliente_http


class PanelControl(tk.Toplevel):
    """
     Menú principal del sistema. Habilita o bloquea el acceso a cada módulo 
     según el rol del usuario que inició sesión (RBAC en interfaz).
    """

    def __init__(self, parent, id_usuario, rol_usuario, nombres_usuario, apellidos_usuario):
        super().__init__(parent)
        
        # Guardamos los datos del operador activo en la ventana y en el cliente HTTP.
        self.id_usuario = id_usuario
        self.rol_usuario = rol_usuario
        self.nombres_usuario = nombres_usuario
        self.apellidos_usuario = apellidos_usuario
        cliente_http.id_operador = id_usuario

        self.title(f"PANEL DE CONTROL - {rol_usuario.upper()}")
        self.geometry("750x620")
        self.resizable(False, False)
        self.configure(bg="#f0f2f5")

        # Si el usuario cierra el panel con la 'X', se cierra toda la aplicación.
        self.protocol("WM_DELETE_WINDOW", parent.destroy)



        # =========================================
        #  2. RUTINAS DE NAVEGACIÓN (LAZY IMPORTS)
        # =========================================

        def abrir_clientes():
            from clientes import Cliente
            Cliente(self)

        def abrir_empleados():
            from empleados import Empleado
            Empleado(self, id_usuario, rol_usuario)

        def abrir_proveedores():
            from proveedores import Proveedor
            Proveedor(self)

        def abrir_stock():
            from stock import Stock
            Stock(self)

        def abrir_facturacion():
            from facturacion import Facturacion
            Facturacion(self)
            
        def abrir_usuarios():
            from usuarios import Usuario
            Usuario(self, id_usuario, rol_usuario)
            
        def abrir_consola():
            from consola import ConsolaSQL
            ConsolaSQL(self)
            
        def abrir_analitica():
            from analitica import AnaliticaBI
            AnaliticaBI(self)
            
        def generar_backup():
            """
             Crea una copia de resguardo del archivo físico frankie_gestor.db 
             en la carpeta /backups de la raíz del proyecto.
            """
            try:
                ruta_db = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")
                
                if not os.path.exists(ruta_db):
                    messagebox.showerror("Error", "No se encontró la base de datos para respaldar.")
                    return
                
                carpeta_backup = os.path.join(DIRECTORIO_RAIZ, "backups")
                os.makedirs(carpeta_backup, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre_backup = f"backup_frankie_{timestamp}.db"
                ruta_destino = os.path.join(carpeta_backup, nombre_backup)
                
                shutil.copy2(ruta_db, ruta_destino)
                messagebox.showinfo("Backup Exitoso", f"Copia de seguridad guardada como:\n{nombre_backup}")
            except Exception as e:
                messagebox.showerror("Error de Backup", f"Fallo al generar la copia: {e}")

        def cerrar_sesion():
            """Limpia la sesión activa y regresa a la pantalla de Login."""
            cliente_http.datos_sesion = None
            self.destroy()
            parent.deiconify() 



        # ==============================
        #  3. MATRIZ DE PERMISOS (RBAC)
        # ==============================

        p_clientes = tk.NORMAL if rol_usuario in ["Administrador", "Gerente", "Empleado - Ventas"] else tk.DISABLED
        p_facturacion = tk.NORMAL if rol_usuario in ["Administrador", "Gerente", "Empleado - Ventas"] else tk.DISABLED
        
        p_proveedores = tk.NORMAL if rol_usuario in ["Administrador", "Gerente", "Empleado - Compras"] else tk.DISABLED
        p_stock = tk.NORMAL if rol_usuario in ["Administrador", "Gerente", "Empleado - Compras"] else tk.DISABLED
        
        p_empleados = tk.NORMAL if rol_usuario in ["Administrador", "Gerente"] else tk.DISABLED
        p_usuarios = tk.NORMAL if rol_usuario in ["Administrador", "Gerente"] else tk.DISABLED
        
        p_root = tk.NORMAL if rol_usuario == "Administrador" else tk.DISABLED
        p_analitica = tk.NORMAL if rol_usuario in ["Administrador", "Gerente"] else tk.DISABLED



        # ===============================
        #  4. INTERFAZ GRÁFICA Y ESTILOS
        # ===============================

        tk.Label(
            self,
            text=f"BIENVENIDO/A, {nombres_usuario.upper()} {apellidos_usuario.upper()}",
            font=("Arial", 16, "bold"),
            bg="#f0f2f5",
            fg="#333333"
        ).pack(pady=(20, 5))
        
        tk.Label(
            self,
            text=f"Rol Activo: {rol_usuario}",
            font=("Arial", 11, "italic"),
            bg="#f0f2f5",
            fg="#666666"
        ).pack(pady=(0, 20))

        frame_botones = tk.Frame(self, bg="#f0f2f5")
        frame_botones.pack(expand=True)

        estilo_btn = {"font": ("Arial", 11, "bold"), "bg": "#2196F3", "fg": "white", "width": 20, "height": 2}
        
        # Fila 1: Operaciones de Ventas.
        tk.Button(frame_botones, text="Gestión de Clientes", command=abrir_clientes, state=p_clientes, **estilo_btn).grid(row=0, column=0, padx=15, pady=15)
        tk.Button(frame_botones, text="Facturación", command=abrir_facturacion, state=p_facturacion, **estilo_btn).grid(row=0, column=1, padx=15, pady=15)

        # Fila 2: Operaciones de Compras.
        tk.Button(frame_botones, text="Gestión de Proveedores", command=abrir_proveedores, state=p_proveedores, **estilo_btn).grid(row=1, column=0, padx=15, pady=15)
        tk.Button(frame_botones, text="Control de Stock", command=abrir_stock, state=p_stock, **estilo_btn).grid(row=1, column=1, padx=15, pady=15)

        # Fila 3: Recursos Humanos y Accesos.
        tk.Button(frame_botones, text="Recursos Humanos", command=abrir_empleados, state=p_empleados, font=("Arial", 11, "bold"), bg="#FF9800", fg="white", width=20, height=2).grid(row=2, column=0, padx=15, pady=15)
        tk.Button(frame_botones, text="Gestión de Usuarios", command=abrir_usuarios, state=p_usuarios, font=("Arial", 11, "bold"), bg="#9C27B0", fg="white", width=20, height=2).grid(row=2, column=1, padx=15, pady=15)

        # Fila 4: Herramientas ROOT.
        tk.Button(frame_botones, text="Consola SQL (Auditoría)", command=abrir_consola, state=p_root, font=("Arial", 11, "bold"), bg="#607D8B", fg="white", width=20, height=2).grid(row=3, column=0, padx=15, pady=15)
        tk.Button(frame_botones, text="Generar Backup DB", command=generar_backup, state=p_root, font=("Arial", 11, "bold"), bg="#37474F", fg="white", width=20, height=2).grid(row=3, column=1, padx=15, pady=15)

        # Fila 5: Inteligencia de Negocios (BI).
        tk.Button(frame_botones, text="Analítica de Ventas (Tablero BI)", command=abrir_analitica, state=p_analitica, font=("Arial", 11, "bold"), bg="#009688", fg="white", width=45, height=2).grid(row=4, column=0, columnspan=2, padx=15, pady=15)

        tk.Button(self, text="Cerrar Sesión", command=cerrar_sesion, font=("Arial", 10, "bold"), bg="#F44336", fg="white", width=15).pack(pady=20)