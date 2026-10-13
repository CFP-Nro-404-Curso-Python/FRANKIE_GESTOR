import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os



class Stock(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("FORMULARIO STOCK E INVENTARIO")
        self.geometry("1020x550")



        # ======================================================
        #  ANCLAJE DE DIRECTORIOS (ADAPTADO A NUEVA ESTRUCTURA)
        # ======================================================

        DIRECTORIO_VISTAS = os.path.dirname(os.path.abspath(__file__))
        DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_VISTAS)
        DB_PATH = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")



        # =====================================================
        #  MÓDULO DE NORMALIZACIÓN EXTREMA (HELPERS DE FASE 1)
        # =====================================================
        
        # Helper para evitar redundancia en catálogos satélites.
        def obtener_o_crear(cursor, tabla, columna, valor):
            valor_limpio = str(valor).strip() if valor else "S/D"
            if not valor_limpio:
                valor_limpio = "S/D"
                
            cursor.execute(f"SELECT id FROM {tabla} WHERE {columna}=?", (valor_limpio,))
            resultado = cursor.fetchone()
            
            if resultado:
                return resultado[0]
            
            cursor.execute(f"INSERT INTO {tabla} ({columna}) VALUES (?)", (valor_limpio,))
            return cursor.lastrowid



        # =======================================
        #  FUNCIONALIDADES DE "FORMULARIO STOCK"
        # =======================================

        def obtener_proveedores():
            lista_provs = []
            if os.path.exists(DB_PATH):
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                try:
                    # CAMBIO: El proveedor ahora se extrae de la tabla central 
                    # 'usuarios'aplicando filtros relacionales estrictos por rol.
                    cursor.execute('''
                        SELECT u.nombres FROM usuarios u
                        JOIN usuxroles ur ON u.id = ur.id_usuario
                        JOIN roles r ON ur.id_rol = r.id
                        WHERE r.rol = 'Proveedor' AND u.habilitado = 1 AND ur.habilitado = 1
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
            
            # CAMBIO: Extracción mediante JOIN para recomponer la vista del producto.
            # Trae la ubicación desde la tabla puente y el proveedor desde la tabla de usuarios.
            cursor.execute('''
                SELECT p.id, p.codigo, p.descripcion, p.categoria, u.nombres, 
                       p.stock_actual, p.stock_minimo, p.precio_costo, p.precio_venta, 
                       us.ubicacion, p.vencimiento
                FROM productos p
                JOIN usuarios u ON p.id_proveedor = u.id
                LEFT JOIN productoxubicaciones pu ON p.id = pu.id_producto AND pu.habilitado = 1
                LEFT JOIN ubicaciones_stock us ON pu.id_ubicacion = us.id
                WHERE p.habilitado = 1
            ''')
            filas = cursor.fetchall()
            
            for fila in filas:
                # fila[0] es el ID de SQLite. El resto son los 10 valores visuales.
                valores_limpios = ["S/D" if v is None else v for v in fila[1:]]
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
            stock_actual = caja_stock_actual.get().strip()
            stock_minimo = caja_stock_minimo.get().strip()
            precio_costo = caja_precio_costo.get().strip()
            precio_venta = caja_precio_venta.get().strip()
            ubicacion = caja_ubicacion.get().strip()
            vencimiento = caja_vencimiento.get().strip()

            if not codigo or not descripcion or not proveedor:
                messagebox.showwarning("Validación", "Código, Descripción y Proveedor son campos obligatorios.")
                return

            try:
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                
                # 1. Recuperamos el ID del proveedor seleccionado.
                cursor.execute('''
                    SELECT u.id FROM usuarios u
                    JOIN usuxroles ur ON u.id = ur.id_usuario
                    JOIN roles r ON ur.id_rol = r.id
                    WHERE u.nombres = ? AND r.rol = 'Proveedor' AND u.habilitado = 1
                ''', (proveedor,))
                res_prov = cursor.fetchone()
                
                if not res_prov:
                    messagebox.showerror("Error", "El proveedor seleccionado no es válido o fue dado de baja.")
                    conexion.close()
                    return
                id_proveedor = res_prov[0]
                
                # Formateo numérico para SQLite.
                st_act = float(stock_actual) if stock_actual else 0.0
                st_min = float(stock_minimo) if stock_minimo else 0.0
                p_cost = float(precio_costo) if precio_costo else 0.0
                p_vent = float(precio_venta) if precio_venta else 0.0

                # 2. Inserción en tabla central de productos.
                cursor.execute('''
                    INSERT INTO productos (codigo, descripcion, categoria, id_proveedor, stock_actual, stock_minimo, precio_costo, precio_venta, vencimiento)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (codigo, descripcion, categoria, id_proveedor, st_act, st_min, p_cost, p_vent, vencimiento))
                
                id_producto = cursor.lastrowid
                
                # 3. Lógica Automática de Estado.
                estado_calc = "Disponible" if st_act > 0 else "Agotado"
                id_estado = obtener_o_crear(cursor, "estados", "estado", estado_calc)
                cursor.execute("INSERT INTO productoxestados (id_producto, id_estado) VALUES (?, ?)", (id_producto, id_estado))
                
                # 4. Inserción de Ubicación Normalizada.
                id_ubicacion = obtener_o_crear(cursor, "ubicaciones_stock", "ubicacion", ubicacion)
                cursor.execute("INSERT INTO productoxubicaciones (id_producto, id_ubicacion) VALUES (?, ?)", (id_producto, id_ubicacion))

                conexion.commit()
            except ValueError:
                messagebox.showerror("Error de Formato", "Asegúrese de ingresar valores numéricos válidos en precios y stock.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Código Duplicado", "El código ingresado ya pertenece a otro producto en catálogo.")
            except Exception as e:
                messagebox.showerror("Error Transaccional", f"Fallo al guardar: {e}")
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
                valor_mostrar = valores[idx] if valores[idx] != "S/D" else ""
                caja.insert(0, valor_mostrar)

            # proveedor está en el índice 3 visual de la grilla.
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
            stock_actual = caja_stock_actual.get().strip()
            stock_minimo = caja_stock_minimo.get().strip()
            precio_costo = caja_precio_costo.get().strip()
            precio_venta = caja_precio_venta.get().strip()
            ubicacion = caja_ubicacion.get().strip()
            vencimiento = caja_vencimiento.get().strip()

            if not codigo or not descripcion or not proveedor:
                messagebox.showwarning("Validación", "Código, Descripción y Proveedor son campos obligatorios.")
                return

            try:
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                
                # 1. Recuperamos el ID del proveedor seleccionado.
                cursor.execute('''
                    SELECT u.id FROM usuarios u
                    JOIN usuxroles ur ON u.id = ur.id_usuario
                    JOIN roles r ON ur.id_rol = r.id
                    WHERE u.nombres = ? AND r.rol = 'Proveedor' AND u.habilitado = 1
                ''', (proveedor,))
                res_prov = cursor.fetchone()
                
                if not res_prov:
                    messagebox.showerror("Error", "El proveedor seleccionado no es válido o fue dado de baja.")
                    conexion.close()
                    return
                id_proveedor = res_prov[0]
                
                st_act = float(stock_actual) if stock_actual else 0.0
                st_min = float(stock_minimo) if stock_minimo else 0.0
                p_cost = float(precio_costo) if precio_costo else 0.0
                p_vent = float(precio_venta) if precio_venta else 0.0

                # 2. Actualizamos la tabla central de productos.
                cursor.execute('''
                    UPDATE productos SET 
                    codigo=?, descripcion=?, categoria=?, id_proveedor=?, stock_actual=?, stock_minimo=?, precio_costo=?, precio_venta=?, vencimiento=?
                    WHERE id=?
                ''', (codigo, descripcion, categoria, id_proveedor, st_act, st_min, p_cost, p_vent, vencimiento, id_producto))
                
                # 3. Mantenemos el historial de ubicaciones (Borrado Lógico) y asignamos nueva ubicación.
                cursor.execute("UPDATE productoxubicaciones SET habilitado=0 WHERE id_producto=?", (id_producto,))
                id_ubicacion = obtener_o_crear(cursor, "ubicaciones_stock", "ubicacion", ubicacion)
                cursor.execute("INSERT INTO productoxubicaciones (id_producto, id_ubicacion) VALUES (?, ?)", (id_producto, id_ubicacion))

                # 4. Actualización Automática de Estado.
                cursor.execute("UPDATE productoxestados SET habilitado=0 WHERE id_producto=?", (id_producto,))
                estado_calc = "Disponible" if st_act > 0 else "Agotado"
                id_estado = obtener_o_crear(cursor, "estados", "estado", estado_calc)
                cursor.execute("INSERT INTO productoxestados (id_producto, id_estado) VALUES (?, ?)", (id_producto, id_estado))

                conexion.commit()
            except ValueError:
                messagebox.showerror("Error de Formato", "Asegúrese de ingresar valores numéricos válidos en precios y stock.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Código Duplicado", "El código ingresado ya pertenece a otro producto en catálogo.")
            except Exception as e:
                messagebox.showerror("Error Transaccional", f"Fallo al actualizar: {e}")
            finally:
                conexion.close()

            limpiar_campos()
            cargar_datos_db()
        
        def eliminar():
            seleccion = tabla.selection()
            if not seleccion:
                return
                
            try:
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                
                for item in seleccion:

                    # CAMBIO: Borrado Lógico en Cascada.
                    cursor.execute("UPDATE productos SET habilitado=0 WHERE id=?", (item,))
                    cursor.execute("UPDATE productoxubicaciones SET habilitado=0 WHERE id_producto=?", (item,))
                    cursor.execute("UPDATE productoxestados SET habilitado=0 WHERE id_producto=?", (item,))
                    
                conexion.commit()
            except sqlite3.Error as e:
                messagebox.showerror("Operación Bloqueada", str(e))
            finally:
                conexion.close()
            
            limpiar_campos()
            cargar_datos_db()



        # ===============================
        #  CAMPOS DEL "FORMULARIO STOCK"
        # ===============================

        tk.Label(self, text="Código").grid(row=1, column=0, pady=5, sticky="e", padx=5)
        caja_codigo = tk.Entry(self, width=30)
        caja_codigo.grid(row=1, column=1)

        tk.Label(self, text="Descripción").grid(row=2, column=0, pady=5, sticky="e", padx=5)
        caja_descripcion = tk.Entry(self, width=30)
        caja_descripcion.grid(row=2, column=1)

        tk.Label(self, text="Categoría").grid(row=3, column=0, pady=5, sticky="e", padx=5)
        caja_categoria = tk.Entry(self, width=30)
        caja_categoria.grid(row=3, column=1)

        tk.Label(self, text="Proveedor").grid(row=4, column=0, pady=5, sticky="e", padx=5)
        lista_proveedores = obtener_proveedores()
        caja_proveedor = ttk.Combobox(self, values=lista_proveedores, state="readonly", width=27)
        caja_proveedor.grid(row=4, column=1)

        tk.Label(self, text="Stock Actual").grid(row=5, column=0, pady=5, sticky="e", padx=5)
        caja_stock_actual = tk.Entry(self, width=30)
        caja_stock_actual.grid(row=5, column=1)

        tk.Label(self, text="Stock Mínimo").grid(row=6, column=0, pady=5, sticky="e", padx=5)
        caja_stock_minimo = tk.Entry(self, width=30)
        caja_stock_minimo.grid(row=6, column=1)

        tk.Label(self, text="Precio Costo").grid(row=7, column=0, pady=5, sticky="e", padx=5)
        caja_precio_costo = tk.Entry(self, width=30)
        caja_precio_costo.grid(row=7, column=1)

        tk.Label(self, text="Precio Venta").grid(row=8, column=0, pady=5, sticky="e", padx=5)
        caja_precio_venta = tk.Entry(self, width=30)
        caja_precio_venta.grid(row=8, column=1)

        tk.Label(self, text="Ubicación").grid(row=9, column=0, pady=5, sticky="e", padx=5)
        caja_ubicacion = tk.Entry(self, width=30)
        caja_ubicacion.grid(row=9, column=1)

        tk.Label(self, text="Vencimiento").grid(row=10, column=0, pady=5, sticky="e", padx=5)
        caja_vencimiento = tk.Entry(self, width=30)
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

        tabla.grid(row=11, column=0, columnspan=5, pady=20, padx=10, sticky="nsew")
        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)



        # ========================
        #  CARGA INICIAL DE DATOS
        # ========================
        
        cargar_datos_db()