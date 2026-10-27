import os
import sqlite3
import pytest
from fastapi.testclient import TestClient

from src.infraestructura.api.servidor import app
from src.infraestructura.api.inyector_dependencias import obtener_uow
from src.infraestructura.persistencia.gestor_sqlite import GestorSQLite
from src.infraestructura.seguridad.adaptador_bcrypt import AdaptadorBcrypt

# ======================================================================================
#  PRUEBAS DE INTEGRACIÓN: CONTRATOS HTTP Y API REST (TDD CICLO 3)
# ======================================================================================
#  DECISIÓN DE DISEÑO (INVERSIÓN DE DEPENDENCIAS EN TESTING):
#
#   Usamos 'TestClient' de FastAPI para simular peticiones HTTP reales (POST, GET)
#   sin necesidad de levantar un servidor Uvicorn en un puerto físico.
#
#   Mediante 'dependency_overrides', interceptamos la Unidad de Trabajo para que 
#   la API apunte a una base de datos temporal aislada en lugar de 'frankie_gestor.db'.
# ======================================================================================



@pytest.fixture
def cliente_api(tmp_path):
    """
     Fixture que prepara un entorno HTTP completo y aislado para cada test.
     Crea una base de datos temporal, carga 'esquema.sql', inyecta usuarios 
     semilla (Admin y Gerente) y reemplaza la dependencia de base de datos en FastAPI.
    """
    # 1. Creamos un archivo SQLite efímero exclusivo para el test actual.
    ruta_db_test = str(tmp_path / "test_api_frankie.db")
    
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    directorio_raiz = os.path.dirname(os.path.dirname(directorio_actual))
    ruta_esquema = os.path.join(directorio_raiz, "db", "esquema.sql")

    # 2. Construimos las tablas, vistas y triggers desde el DDL oficial.
    conexion = sqlite3.connect(ruta_db_test)
    conexion.execute("PRAGMA foreign_keys = ON;")
    with open(ruta_esquema, "r", encoding="utf-8") as archivo_sql:
        conexion.executescript(archivo_sql.read())

    # 3. Sembramos datos iniciales mínimos (Arrange global para las pruebas HTTP).
    hasher = AdaptadorBcrypt()
    hash_admin = hasher.hashear_password("admin123")
    hash_gerente = hasher.hashear_password("gerente123")

    cursor = conexion.cursor()
    # Insertamos Roles base.
    cursor.execute("INSERT INTO roles (id, rol) VALUES (1, 'Administrador')")
    cursor.execute("INSERT INTO roles (id, rol) VALUES (2, 'Gerente')")
    
    # Insertamos Usuario 1 (Administrador) y Usuario 2 (Gerente).
    cursor.execute('''
        INSERT INTO usuarios (id, nombres, apellidos, dni, usuario, password, habilitado)
        VALUES (1, 'Admin', 'Sistema', '10000001', 'admin', ?, 1)
    ''', (hash_admin,))
    cursor.execute("INSERT INTO usuxroles (id_usuario, id_rol) VALUES (1, 1)")

    cursor.execute('''
        INSERT INTO usuarios (id, nombres, apellidos, dni, usuario, password, habilitado)
        VALUES (2, 'Gustavo', 'Cerati', '20000002', 'gcerati', ?, 1)
    ''', (hash_gerente,))
    cursor.execute("INSERT INTO usuxroles (id_usuario, id_rol) VALUES (2, 2)")

    conexion.commit()
    conexion.close()

    # 4. Redirigimos FastAPI para que use nuestra base temporal en cada petición.
    def override_obtener_uow():
        return GestorSQLite(ruta_db_test)

    app.dependency_overrides[obtener_uow] = override_obtener_uow
    
    # 5. Entregamos el cliente HTTP listo para disparar peticiones.
    with TestClient(app) as cliente:
        yield cliente

    # 6. Limpiamos los overrides al terminar el test.
    app.dependency_overrides.clear()


# -----------------------------------------------------
#  1. TESTS DE AUTENTICACIÓN Y SEGURIDAD RBAC VÍA HTTP
# -----------------------------------------------------

def test_login_exitoso_y_rechazo_credenciales_invalidas(cliente_api):
    """
     Verifica que el endpoint de login valide correctamente el hash Bcrypt 
     devolviendo 200 OK, y que rechace claves erróneas con código 401 Unauthorized.
    """
    # Caso exitoso.
    respuesta_ok = cliente_api.post("/api/perfiles/login", json={
        "usuario": "admin",
        "password": "admin123"
    })
    assert respuesta_ok.status_code == 200
    datos = respuesta_ok.json()
    assert datos["usuario"] == "admin"
    assert datos["id"] == 1

    # Caso fallido (contraseña incorrecta).
    respuesta_fallida = cliente_api.post("/api/perfiles/login", json={
        "usuario": "admin",
        "password": "clave_falsa"
    })
    assert respuesta_fallida.status_code == 401


def test_rbac_gerente_no_puede_crear_administrador_via_http(cliente_api):
    """
     Verifica que si un Gerente (ID 2 en cabecera 'X-Operador-Id') intenta crear 
     un perfil con rol 'Administrador', el servidor atrape la excepción de 
     dominio 'ErrorJerarquiaRBAC' y la traduzca a un estado HTTP 403 Forbidden.
    """
    respuesta = cliente_api.post(
        "/api/perfiles",
        headers={"X-Operador-Id": "2"},
        json={
            "nombres": "Intruso",
            "apellidos": "Malicioso",
            "dni": "99887766",
            "rol": "Administrador",
            "usuario": "intruso",
            "password_plana": "123456"
        }
    )
    assert respuesta.status_code == 403
    assert "detalle" in respuesta.json()


# ----------------------------------------------------------------
#  2. TESTS DE OPERACIONES COMERCIALES (INVENTARIO Y FACTURACIÓN)
# ----------------------------------------------------------------

def test_flujo_completo_alta_producto_y_facturacion_exitosa(cliente_api):
    """
     Verifica el ciclo comercial punta a punta: dar de alta un producto vía POST 
     y luego emitir una factura que descuente su stock automáticamente.
    """
    # 1. Alta de producto (usando el ID 1 como proveedor válido).
    resp_prod = cliente_api.post("/api/productos", json={
        "codigo": "API-PROD-01",
        "descripcion": "Monitor 24 Pulgadas",
        "categoria": "Monitores",
        "id_proveedor": 1,
        "precio_costo": 100000.0,
        "precio_venta": 150000.0,
        "stock_actual": 10.0,
        "stock_minimo": 2.0
    })
    assert resp_prod.status_code == 201
    id_producto = resp_prod.json()["id"]

    # 2. Emisión de factura por 3 unidades.
    resp_fac = cliente_api.post("/api/facturas", json={
        "id_vendedor": 1,
        "id_cliente": 2,
        "id_producto": id_producto,
        "cantidad": 3.0,
        "descuento": 10.0
    })
    assert resp_fac.status_code == 201
    assert "id_factura" in resp_fac.json()


def test_facturacion_bloqueada_por_stock_insuficiente_retorna_400(cliente_api):
    """
     Verifica que si se intenta facturar más cantidad de la que existe en el 
     inventario, la excepción 'ErrorStockInsuficiente' se traduzca a HTTP 400 Bad Request.
    """
    # 1. Creamos un producto con solo 2 unidades en stock.
    resp_prod = cliente_api.post("/api/productos", json={
        "codigo": "API-PROD-02",
        "descripcion": "Placa de Video",
        "categoria": "Hardware",
        "id_proveedor": 1,
        "precio_costo": 200000.0,
        "precio_venta": 300000.0,
        "stock_actual": 2.0,
        "stock_minimo": 1.0
    })
    id_producto = resp_prod.json()["id"]

    # 2. Intentamos vender 5 unidades (debe abortar y devolver 400).
    resp_fac = cliente_api.post("/api/facturas", json={
        "id_vendedor": 1,
        "id_cliente": 2,
        "id_producto": id_producto,
        "cantidad": 5.0,
        "descuento": 0.0
    })
    assert resp_fac.status_code == 400
    assert "Stock insuficiente" in resp_fac.json()["detalle"]