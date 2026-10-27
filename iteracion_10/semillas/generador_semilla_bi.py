import os
import sqlite3
import random
from datetime import datetime, timedelta

# =============================================================================
#  GENERADOR DE SEMILLAS PARA BUSINESS INTELLIGENCE (CAPA 3 - INFRAESTRUCTURA)
# =============================================================================
#  DECISIÓN DE DISEÑO (ETL Y DATOS DE PRUEBA):
#
#   Este script es independiente de la aplicación. Su objetivo es tomar la 
#   base de datos oficial vacía (frankie_gestor.db) y poblarla masivamente con 
#   1000 productos y cientos de facturas, respetando la 3FN, Triggers y la 
#   jerarquía RBAC del sistema para poder probar el módulo de analítica 
#   (Consola BI y Pandas) sin tener que tipear a mano.
# =============================================================================



DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_RAIZ = os.path.dirname(DIRECTORIO_ACTUAL)
RUTA_DB_OFICIAL = os.path.join(DIRECTORIO_RAIZ, "db", "frankie_gestor.db")


def sembrar_datos():
    """Conecta a la base y ejecuta el plan de siembra masivo."""
    if not os.path.exists(RUTA_DB_OFICIAL):
        print(f"❌ Error: No se encontró la base de datos en {RUTA_DB_OFICIAL}.")
        return

    conexion = sqlite3.connect(RUTA_DB_OFICIAL)
    cursor = conexion.cursor()
    
    # 1. Habilitamos integridad referencial (no queremos que falle silenciosamente).
    conexion.execute("PRAGMA foreign_keys = ON;")
    
    try:
        print("🌱 Iniciando siembra de datos de Business Intelligence...")
        
        # 2. INYECTAR PROVEEDOR BASE
        # Necesitamos un Proveedor para satisfacer la Foreign Key (id_proveedor) 
        # en la tabla 'productos' (Regla 3FN).
        
        # Primero buscamos si ya existe el rol 'Proveedor'.
        cursor.execute("SELECT id FROM roles WHERE rol = 'Proveedor'")
        resultado = cursor.fetchone()
        
        if not resultado:
            cursor.execute("INSERT INTO roles (rol) VALUES ('Proveedor')")
            id_rol_prov = cursor.lastrowid
        else:
            id_rol_prov = resultado[0]

        # Inyectamos al usuario Proveedor (Asumimos ID 999 para no pisar usuarios del sistema).
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios (id, nombres, apellidos, dni, usuario, password, habilitado)
            VALUES (999, 'Distribuidora', 'Mayorista', '00000000', NULL, NULL, 1)
        ''')
        cursor.execute("INSERT OR IGNORE INTO usuxroles (id_usuario, id_rol) VALUES (999, ?)", (id_rol_prov,))
        

        # 3. GENERAR 1000 PRODUCTOS E INYECTARLOS
        # Categorías basadas en la semilla original.
        categorias = [
            'Informatica', 'Perifericos', 'Monitores', 'Muebles', 
            'Accesorios', 'Almacenamiento', 'Audio', 'Redes', 
            'Impresion', 'Componentes'
        ]
        
        print("📦 Sembrando 1000 productos...")
        for i in range(1, 1001):
            codigo = f"PROD-{str(i).zfill(4)}"
            descripcion = f"Producto Genérico {str(i).zfill(4)}"
            cat = random.choice(categorias)
            
            # Cálculo comercial simulado (Rentabilidad del 40%).
            costo = round(random.uniform(5000.0, 500000.0), 2)
            venta = round(costo * 1.40, 2)
            stock = random.randint(10, 500)
            
            cursor.execute('''
                INSERT OR IGNORE INTO productos (
                    codigo, descripcion, categoria, id_proveedor, 
                    precio_costo, precio_venta, stock_actual, stock_minimo, vencimiento, habilitado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (codigo, descripcion, cat, 999, costo, venta, float(stock), 5.0, "S/D"))

            # Vinculamos al estado 'Disponible' para respetar 3FN.
            id_prod = cursor.lastrowid
            if id_prod:
                cursor.execute("INSERT OR IGNORE INTO estados (estado) VALUES ('Disponible')")
                cursor.execute("SELECT id FROM estados WHERE estado = 'Disponible'")
                id_estado = cursor.fetchone()[0]
                
                cursor.execute('''
                    INSERT INTO productoxestados (id_producto, id_estado) 
                    VALUES (?, ?)
                ''', (id_prod, id_estado))


        # 4. PREPARAR ACTORES PARA LA FACTURACIÓN (VENDEDOR Y CLIENTE).
        cursor.execute("INSERT OR IGNORE INTO roles (rol) VALUES ('Empleado')")
        cursor.execute("SELECT id FROM roles WHERE rol = 'Empleado'")
        id_rol_emp = cursor.fetchone()[0]
        
        cursor.execute("INSERT OR IGNORE INTO roles (rol) VALUES ('Cliente')")
        cursor.execute("SELECT id FROM roles WHERE rol = 'Cliente'")
        id_rol_cli = cursor.fetchone()[0]

        # Vendedor (ID 888).
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios (id, nombres, apellidos, dni, usuario, password, habilitado)
            VALUES (888, 'Vendedor', 'BI', '88888888', 'vendedor_bi', '123', 1)
        ''')
        cursor.execute("INSERT OR IGNORE INTO usuxroles (id_usuario, id_rol) VALUES (888, ?)", (id_rol_emp,))

        # Cliente (ID 777).
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios (id, nombres, apellidos, dni, usuario, password, habilitado)
            VALUES (777, 'Cliente', 'BI', '77777777', NULL, NULL, 1)
        ''')
        cursor.execute("INSERT OR IGNORE INTO usuxroles (id_usuario, id_rol) VALUES (777, ?)", (id_rol_cli,))


        # 5. GENERAR FACTURAS HISTÓRICAS (Últimos 3 años).
        print("🧾 Sembrando 500 facturas históricas para BI...")
        
        fecha_inicio = datetime(2024, 1, 1)
        fecha_fin = datetime(2026, 12, 31)
        dias_diferencia = (fecha_fin - fecha_inicio).days

        for i in range(500):
            # Producto aleatorio.
            id_prod = random.randint(1, 1000)
            
            # Buscar el precio actual del producto seleccionado.
            cursor.execute("SELECT precio_venta FROM productos WHERE id = ?", (id_prod,))
            resultado_precio = cursor.fetchone()
            precio = resultado_precio[0] if resultado_precio else 50000.0

            cantidad = random.randint(1, 15)
            descuento = float(random.choice([0, 0, 0, 5, 10, 15])) # Más prob. de no tener descuento.
            
            # Fecha aleatoria en el rango
            dias_aleatorios = random.randint(0, dias_diferencia)
            fecha_random = fecha_inicio + timedelta(days=dias_aleatorios)
            fecha_str = fecha_random.strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('''
                INSERT INTO facturacion (
                    fecha, id_vendedor, id_cliente, id_producto, cantidad, valor, descuento, habilitado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ''', (fecha_str, 888, 777, id_prod, float(cantidad), precio, descuento))

        # Confirmamos la transacción masiva (Unit of Work manual).
        conexion.commit()
        print("✅ Siembra finalizada con éxito. Base de datos lista para Analítica.")
        
    except sqlite3.Error as error:
        conexion.rollback()
        print(f"❌ Error durante la siembra de datos: {error}")
    finally:
        conexion.close()

if __name__ == "__main__":
    sembrar_datos()