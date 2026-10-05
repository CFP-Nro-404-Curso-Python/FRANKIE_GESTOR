import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os



class Stock(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("FORMULARIO STOCK")
        self.geometry("1005x550")



        # =======================================
        #  ANCLAJE DE DIRECTORIO Y BASE DE DATOS
        # =======================================
        
        # CAMBIO: Adaptación de la ruta a la nueva estructura de carpetas (vistas -> raíz -> db).
        DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
        DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_VISTAS)
        DB_PATH = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")



        # =======================================
        #  FUNCIONALIDADES DE "FORMULARIO STOCK"
        # =======================================

        # CAMBIO: Se eliminó la función "crear_tabla_stock". La base de datos ahora está 
        # centralizada y se construye íntegramente mediante el archivo 'esquema.sql'.

        # CAMBIO HELPER: Función auxiliar para atomizar datos en los catálogos.
        def obtener_o_crear_catalogo(cursor, tabla, columna, valor):
            if not valor:
                valor = "-"
            cursor.execute(f"SELECT id FROM {tabla} WHERE {columna} = ?", (valor,))
            resultado = cursor.fetchone()
            if resultado:
                return resultado[0]
            cursor.execute(f"INSERT INTO {tabla} ({columna}) VALUES (?)", (valor,))
            return cursor.lastrowid

        def obtener_proveedores():
            lista_provs = []
            if os.path.exists(DB_PATH):
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                try:
                    # CAMBIO: Ya no existe la tabla proveedores aislada. Consultamos la tabla 
                    # central de usuarios y filtramos estrictamente por el rol 'Proveedor'.
                    cursor.execute('''
                        SELECT u.nombres FROM usuarios u
                        JOIN usuxroles ur ON u.id = ur.id_usuario
                        JOIN roles r ON ur.id_rol = r.id
                        WHERE r.rol = 'Proveedor' AND u.habilitado = 1
                    ''')
                    filas = cursor.fetchall()
                    for fila in filas:
                        lista_provs.append(fila[0])
                except sqlite3.OperationalError:
                    pass
                conexion.close()
            return lista_provs

        def cargar_datos_db():
            for item in tabla.get_children():
                tabla.delete(item)
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # CAMBIO: Reconstrucción de la información del producto mediante JOINs.
            # Se extrae el nombre del proveedor desde 'usuarios' y la ubicación desde su catálogo.
            cursor.execute('''
                SELECT p.id, p.codigo, p.descripcion, p.categoria, u.nombres, 
                       p.stock_actual, p.stock_minimo, p.precio_costo, p.precio_venta, 
                       us.ubicacion, p.vencimiento
                FROM productos p
                JOIN usuarios u ON p.id_proveedor = u.id
                LEFT JOIN productoxubicaciones pu ON p.id = pu.id_producto
                LEFT JOIN ubicaciones_stock us ON pu.id_ubicacion = us.id
                WHERE p.habilitado = 1
            ''')
            filas = cursor.fetchall()
            
            for fila in filas:
                # Reemplazamos posibles nulos generados por el LEFT JOIN con cadenas vacías para la UI.
                valores_limpios = [str(val) if val is not None else "" for val in fila[1:]]
                tabla.insert("", "end", iid=fila[0], values=valores_limpios)
            conexion.close()

        def limpiar_campos():
            cajas = [caja_codigo, caja_descripcion, caja_categoria, caja_stock_actual, caja_stock_minimo, caja_precio_costo, 
                     caja_precio_venta, caja_ubicacion, caja_vencimiento]
                     
            for caja in cajas:
                caja.delete(0, tk.END)
            
            caja_proveedor.set("")
            caja_codigo.focus_set()
        
        def guardar():
            codigo = caja_codigo.get().strip()
            descripcion = caja_descripcion.get().strip()
            categoria = caja_categoria.get().strip()
            proveedor = caja_proveedor.get().strip()
            stock_actual = caja_stock_actual.get().strip() or 0
            stock_minimo = caja_stock_minimo.get().strip() or 0
            precio_costo = caja_precio_costo.get().strip() or 0
            precio_venta = caja_precio_venta.get().strip() or 0
            ubicacion = caja_ubicacion.get().strip()
            vencimiento = caja_vencimiento.get().strip()

            if not proveedor or not codigo or not descripcion:
                messagebox.showwarning("Validación", "Código, Descripción y Proveedor son obligatorios.")
                return

            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            try:
                # CAMBIO: Extracción de la clave foránea (FK) del proveedor seleccionado.
                cursor.execute('''
                    SELECT u.id FROM usuarios u
                    JOIN usuxroles ur ON u.id = ur.id_usuario
                    JOIN roles r ON ur.id_rol = r.id
                    WHERE u.nombres = ? AND r.rol = 'Proveedor' AND u.habilitado = 1
                ''', (proveedor,))
                res_proveedor = cursor.fetchone()
                
                if not res_proveedor:
                    messagebox.showerror("Error", "El proveedor seleccionado no es válido o ha sido dado de baja.")
                    return
                id_proveedor = res_proveedor[0]

                # 1. Inserción del producto principal referenciando al proveedor.
                cursor.execute('''
                    INSERT INTO productos (codigo, descripcion, categoria, id_proveedor, stock_actual, stock_minimo, precio_costo, precio_venta, vencimiento)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (codigo, descripcion, categoria, id_proveedor, stock_actual, stock_minimo, precio_costo, precio_venta, vencimiento))
                
                id_producto = cursor.lastrowid

                # 2. Creación y vinculación del catálogo de ubicación en tabla pivot.
                id_ubicacion = obtener_o_crear_catalogo(cursor, "ubicaciones_stock", "ubicacion", ubicacion)
                cursor.execute("INSERT INTO productoxubicaciones (id_producto, id_ubicacion) VALUES (?, ?)", (id_producto, id_ubicacion))
                
                conexion.commit()

            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "El código del producto ya existe. Verifique el inventario.")
            except sqlite3.Error as e:
                messagebox.showerror("Error de Transacción", f"No se pudo guardar el producto:\n{e}")
            finally:
                conexion.close()

            limpiar_campos()
            cargar_datos_db()

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            valores = tabla.item(seleccion[0], "values")

            cajas = [caja_codigo, caja_descripcion, caja_categoria, caja_stock_actual, caja_stock_minimo, caja_precio_costo, 
                     caja_precio_venta, caja_ubicacion, caja_vencimiento]
            indices = [0, 1, 2, 4, 5, 6, 7, 8, 9]
                     
            for caja, idx in zip(cajas, indices):
                caja.delete(0, tk.END)
                caja.insert(0, valores[idx])

            caja_proveedor.set(valores[3])

        def modificar():
            seleccion = tabla.selection()
            if not seleccion:
                return
            
            id_producto = seleccion[0]
            
            codigo = caja_codigo.get().strip()
            descripcion = caja_descripcion.get().strip()
            categoria = caja_categoria.get().strip()
            proveedor = caja_proveedor.get().strip()
            stock_actual = caja_stock_actual.get().strip() or 0
            stock_minimo = caja_stock_minimo.get().strip() or 0
            precio_costo = caja_precio_costo.get().strip() or 0
            precio_venta = caja_precio_venta.get().strip() or 0
            ubicacion = caja_ubicacion.get().strip()
            vencimiento = caja_vencimiento.get().strip()

            if not proveedor or not codigo or not descripcion:
                messagebox.showwarning("Validación", "Código, Descripción y Proveedor son obligatorios.")
                return

            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            try:
                # CAMBIO: Extracción del nuevo ID del proveedor para actualizar la clave foránea.
                cursor.execute('''
                    SELECT u.id FROM usuarios u
                    JOIN usuxroles ur ON u.id = ur.id_usuario
                    JOIN roles r ON ur.id_rol = r.id
                    WHERE u.nombres = ? AND r.rol = 'Proveedor' AND u.habilitado = 1
                ''', (proveedor,))
                res_proveedor = cursor.fetchone()
                
                if not res_proveedor:
                    messagebox.showerror("Error", "El proveedor seleccionado no es válido.")
                    return
                id_proveedor = res_proveedor[0]

                # 1. Actualización de la tabla maestra de productos.
                cursor.execute('''
                    UPDATE productos SET 
                    codigo=?, descripcion=?, categoria=?, id_proveedor=?, stock_actual=?, stock_minimo=?, precio_costo=?, precio_venta=?, vencimiento=?
                    WHERE id=?
                ''', (codigo, descripcion, categoria, id_proveedor, stock_actual, stock_minimo, precio_costo, precio_venta, vencimiento, id_producto))
                
                # 2. Actualización de la ubicación a través de tabla pivot.
                id_ubicacion_nueva = obtener_o_crear_catalogo(cursor, "ubicaciones_stock", "ubicacion", ubicacion)
                
                cursor.execute("SELECT id FROM productoxubicaciones WHERE id_producto=?", (id_producto,))
                if cursor.fetchone():
                    cursor.execute("UPDATE productoxubicaciones SET id_ubicacion=? WHERE id_producto=?", (id_ubicacion_nueva, id_producto))
                else:
                    cursor.execute("INSERT INTO productoxubicaciones (id_producto, id_ubicacion) VALUES (?, ?)", (id_producto, id_ubicacion_nueva))

                conexion.commit()

            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Ese código de producto ya está en uso.")
            except sqlite3.Error as e:
                messagebox.showerror("Error de Actualización", f"No se pudo modificar el producto:\n{e}")
            finally:
                conexion.close()

            limpiar_campos()
            cargar_datos_db()
        
        def eliminar():
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # CAMBIO: Aplicación de Baja Lógica estricta en todo el árbol del producto.
            try:
                for item in seleccion:
                    cursor.execute("UPDATE productos SET habilitado = 0 WHERE id = ?", (item,))
                    cursor.execute("UPDATE productoxubicaciones SET habilitado = 0 WHERE id_producto = ?", (item,))
                    cursor.execute("UPDATE productoxestados SET habilitado = 0 WHERE id_producto = ?", (item,))

                conexion.commit()

            except sqlite3.Error as e:
                messagebox.showerror("Error", f"No se pudo dar de baja al producto:\n{e}")
            finally:
                conexion.close()
            
            limpiar_campos()
            cargar_datos_db()



        # ===============================
        #  CAMPOS DEL "FORMULARIO STOCK"
        # ===============================

        tk.Label(self, text="Código").grid(row=1, column=0, pady=5, sticky="e", padx=5)
        caja_codigo = tk.Entry(self)
        caja_codigo.grid(row=1, column=1)

        tk.Label(self, text="Descripción").grid(row=2, column=0, pady=5, sticky="e", padx=5)
        caja_descripcion = tk.Entry(self)
        caja_descripcion.grid(row=2, column=1)

        tk.Label(self, text="Categoría").grid(row=3, column=0, pady=5, sticky="e", padx=5)
        caja_categoria = tk.Entry(self)
        caja_categoria.grid(row=3, column=1)

        tk.Label(self, text="Proveedor").grid(row=4, column=0, pady=5, sticky="e", padx=5)
        lista_proveedores = obtener_proveedores()
        caja_proveedor = ttk.Combobox(self, values=lista_proveedores, state="readonly", width=17)
        caja_proveedor.grid(row=4, column=1)

        tk.Label(self, text="Stock Actual").grid(row=5, column=0, pady=5, sticky="e", padx=5)
        caja_stock_actual = tk.Entry(self)
        caja_stock_actual.grid(row=5, column=1)

        tk.Label(self, text="Stock Mínimo").grid(row=6, column=0, pady=5, sticky="e", padx=5)
        caja_stock_minimo = tk.Entry(self)
        caja_stock_minimo.grid(row=6, column=1)

        tk.Label(self, text="Precio Costo").grid(row=7, column=0, pady=5, sticky="e", padx=5)
        caja_precio_costo = tk.Entry(self)
        caja_precio_costo.grid(row=7, column=1)

        tk.Label(self, text="Precio Venta").grid(row=8, column=0, pady=5, sticky="e", padx=5)
        caja_precio_venta = tk.Entry(self)
        caja_precio_venta.grid(row=8, column=1)

        tk.Label(self, text="Ubicación").grid(row=9, column=0, pady=5, sticky="e", padx=5)
        caja_ubicacion = tk.Entry(self)
        caja_ubicacion.grid(row=9, column=1)

        tk.Label(self, text="Vencimiento").grid(row=10, column=0, pady=5, sticky="e", padx=5)
        caja_vencimiento = tk.Entry(self)
        caja_vencimiento.grid(row=10, column=1)



        # =========================================================
        #  BOTONES "GUARDAR, MODIFICAR, ELIMINAR Y CERRAR VENTANA"
        # =========================================================

        boton_guardar = tk.Button(self, text="Guardar Producto", command=guardar, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=16)
        boton_guardar.grid(row=3, column=3, padx=20)

        boton_modificar = tk.Button(self, text="Modificar Producto", command=modificar, bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=16)
        boton_modificar.grid(row=5, column=3, padx=20)

        boton_eliminar = tk.Button(self, text="Eliminar Producto", command=eliminar, bg="#F44336", fg="white", font=("Arial", 9, "bold"), width=16)
        boton_eliminar.grid(row=7, column=3, padx=20)

        boton_cerrar_ventana = tk.Button(self, text="Cerrar Ventana", command=self.destroy, bg="#9E9E9E", fg="white", font=("Arial", 9, "bold"), width=16)
        boton_cerrar_ventana.grid(row=9, column=3, padx=20)



        # =========================
        #  TABLA DE DATOS DE STOCK
        # =========================

        columnas = ("Código", "Descripción", "Categoría", "Proveedor", "Stock Actual", "Stock Mínimo", "Precio Costo", "Precio Venta", "Ubicación", "Vencimiento")

        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=100)

        tabla.grid(row=11, column=0, columnspan=5, pady=20, padx=10)
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)



        # ========================
        #  CARGA INICIAL DE DATOS
        # ========================
        
        cargar_datos_db()