import sqlite3
import os
import re



# ========================
#  ANCLAJE DE DIRECTORIOS
# ========================

# Este script reside en /semillas. Debemos subir un nivel para llegar a la raíz.
DIRECTORIO_SEMILLAS = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_SEMILLAS)

DB_PATH = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")
SQL_CATEDRA_PATH = os.path.join(DIRECTORIO_SEMILLAS, "empresa_ventas_1000.sql")

def generar_semilla():
    print("==================================================")
    print(" INICIANDO PROCESO DE MIGRACIÓN ETL (SEMILLA BI) ")
    print("==================================================")
    
    if not os.path.exists(DB_PATH):
        print(f"[!] ERROR CRÍTICO: No se encontró la base de datos maestra en:\n{DB_PATH}")
        print("Asegurate de haber ejecutado login.py al menos una vez para generar el esquema.")
        return
        
    if not os.path.exists(SQL_CATEDRA_PATH):
        print(f"[!] ERROR CRÍTICO: No se encontró el archivo de la cátedra en:\n{SQL_CATEDRA_PATH}")
        return

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    


    try:
        # =========================================================
        #  FASE 1: PREPARACIÓN DEL ECOSISTEMA (ENTIDADES FANTASMA)
        # =========================================================

        # Dado que nuestro esquema exige Normalización Extrema (3FN), no podemos inyectar ventas al aire. 
        # Necesitamos un Vendedor, un Cliente y un Proveedor genéricos.
        
        print("[*] Verificando/Creando usuarios genéricos para cumplir claves foráneas...")
        
        # 1. Recuperamos los IDs de los roles necesarios.
        roles_requeridos = {'Proveedor': None, 'Empleado - Ventas': None, 'Cliente': None}
        for rol in roles_requeridos.keys():
            cursor.execute("SELECT id FROM roles WHERE rol=?", (rol,))
            resultado = cursor.fetchone()
            if not resultado:
                raise Exception(f"Falta el rol '{rol}' en la tabla 'roles'. Base corrupta o vacía.")
            roles_requeridos[rol] = resultado[0]

        # Función Helper para inyectar un usuario fantasma y su rol asociado.
        def inyectar_usuario_fantasma(nombre, rol_str):
            cursor.execute("SELECT id FROM usuarios WHERE nombres=? AND habilitado=1", (nombre,))
            res = cursor.fetchone()
            if res: return res[0]
            
            cursor.execute("INSERT INTO usuarios (nombres, apellidos, dni) VALUES (?, ?, ?)", (nombre, 'Semilla BI', '00000000'))
            id_nuevo = cursor.lastrowid
            cursor.execute("INSERT INTO usuxroles (id_usuario, id_rol) VALUES (?, ?)", (id_nuevo, roles_requeridos[rol_str]))
            return id_nuevo

        # Creamos las entidades y capturamos sus IDs (Primary Keys).
        id_proveedor = inyectar_usuario_fantasma('Proveedor Importador Genérico', 'Proveedor')
        id_vendedor = inyectar_usuario_fantasma('Vendedor Sistema BI', 'Empleado - Ventas')
        id_cliente = inyectar_usuario_fantasma('Consumidor Final Genérico', 'Cliente')
        
        print("    -> Usuarios fantasma creados exitosamente.")



        # ======================================================
        #  FASE 2: PARSEO Y MIGRACIÓN DEL CATÁLOGO DE PRODUCTOS
        # ======================================================

        print("\n[*] Parseando archivo SQL de la cátedra...")
        
        with open(SQL_CATEDRA_PATH, 'r', encoding='utf-8') as file:
            contenido_sql = file.read()
            
        # Extraemos el bloque de INSERT INTO productos usando Regex.
        # Busca todo lo que esté entre "INSERT INTO productos... VALUES" y el primer ";"
        patron_productos = re.compile(r'INSERT INTO productos[^V]+VALUES\s*(.*?);', re.DOTALL | re.IGNORECASE)
        match_productos = patron_productos.search(contenido_sql)
        
        if not match_productos:
            raise Exception("No se encontró el bloque INSERT INTO productos en el archivo SQL.")
            
        bloque_valores_prod = match_productos.group(1)
        
        # Parseamos las tuplas crudas de SQL.
        # Las convierte en una lista de listas de Python para poder iterarlas.
        tuplas_productos = re.findall(r'\((.*?)\)', bloque_valores_prod)
        
        print(f"[*] Migrando {len(tuplas_productos)} productos al esquema relacional...")
        
        productos_insertados = 0
        for tupla in tuplas_productos:
            # Separamos los valores por coma (teniendo cuidado con comillas simples).
            valores = [v.strip().strip("'") for v in tupla.split(',')]
            
            # Formato origen: (id_producto, nombre, categoria, precio).
            id_orig = valores[0]
            codigo = f"PROD-BI-{id_orig.zfill(4)}"  # Generamos un código único requerido por nuestro esquema.
            descripcion = valores[1]
            categoria = valores[2]
            precio_costo = float(valores[3]) * 0.70  # Simulamos un margen de ganancia del 30%.
            precio_venta = float(valores[3])
            
            # Verificamos si el producto ya fue inyectado en una ejecución anterior.
            cursor.execute("SELECT id FROM productos WHERE codigo=?", (codigo,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO productos (codigo, descripcion, categoria, id_proveedor, stock_actual, precio_costo, precio_venta)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (codigo, descripcion, categoria, id_proveedor, 500.0, precio_costo, precio_venta))
                
                # Regla de negocio de la Iteración 08: Obliga a registrar el estado del stock.
                id_nuevo_prod = cursor.lastrowid
                cursor.execute("SELECT id FROM estados WHERE estado='Disponible'")
                id_estado = cursor.fetchone()[0]
                cursor.execute("INSERT INTO productoxestados (id_producto, id_estado) VALUES (?, ?)", (id_nuevo_prod, id_estado))
                productos_insertados += 1
                
        print(f"    -> Se insertaron {productos_insertados} productos nuevos.")



        # ====================================================
        #  FASE 3: PARSEO Y MIGRACIÓN DEL HISTORIAL DE VENTAS
        # ====================================================

        # Extraemos el bloque de INSERT INTO ventas.
        patron_ventas = re.compile(r'INSERT INTO ventas[^V]+VALUES\s*(.*?);', re.DOTALL | re.IGNORECASE)
        match_ventas = patron_ventas.search(contenido_sql)
        
        if not match_ventas:
            raise Exception("No se encontró el bloque INSERT INTO ventas en el archivo SQL.")
            
        bloque_valores_ventas = match_ventas.group(1)
        tuplas_ventas = re.findall(r'\((.*?)\)', bloque_valores_ventas)
        
        print(f"\n[*] Migrando {len(tuplas_ventas)} transacciones de venta...")
        
        # Validamos cuántas ventas hay actualmente para evitar duplicar el bloque entero si el usuario ejecuta 
        # este script dos veces por error.
        cursor.execute("SELECT COUNT(*) FROM facturacion WHERE id_vendedor=?", (id_vendedor,))
        ventas_existentes = cursor.fetchone()[0]
        
        if ventas_existentes > 0:
            print("    [!] Abortando inyección de ventas: Ya existen transacciones semilla en la base de datos.")
        else:
            ventas_insertadas = 0
            for tupla in tuplas_ventas:
                valores = [v.strip().strip("'") for v in tupla.split(',')]
                
                # Formato origen: (id_producto, cantidad, fecha).
                id_prod_origen = valores[0]
                codigo_busqueda = f"PROD-BI-{id_prod_origen.zfill(4)}"
                cantidad = float(valores[1])
                fecha_historica = f"{valores[2]} 12:00:00" # Concatenamos hora falsa para cumplir con DATETIME.
                
                # Buscamos el ID real que SQLite le asignó al producto y su precio.
                cursor.execute("SELECT id, precio_venta FROM productos WHERE codigo=?", (codigo_busqueda,))
                res_prod = cursor.fetchone()
                
                if res_prod:
                    id_producto_real = res_prod[0]
                    valor_congelado = res_prod[1]
                    
                    # Inyección en la tabla transaccional (El campo 'total' lo calcula y guarda SQLite solo).
                    cursor.execute('''
                        INSERT INTO facturacion (fecha, id_vendedor, id_cliente, id_producto, cantidad, valor)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (fecha_historica, id_vendedor, id_cliente, id_producto_real, cantidad, valor_congelado))
                    ventas_insertadas += 1
            
            print(f"    -> Se insertaron {ventas_insertadas} comprobantes históricos exitosamente.")
        
        # Ejecutamos el COMMIT final consolidando la transacción ETL completa.
        conexion.commit()
        print("\n==================================================")
        print(" MIGRACIÓN ETL COMPLETADA. BASE LISTA PARA BI. ")
        print("==================================================")

    except Exception as e:
        print(f"\n[!] SE PRODUJO UN ERROR DURANTE LA MIGRACIÓN: {e}")
        print("Ejecutando ROLLBACK para revertir cambios corruptos...")
        conexion.rollback()
    finally:
        conexion.close()

if __name__ == "__main__":
    generar_semilla()