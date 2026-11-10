# 📄 Reporte de Auditoría y Refactorización - Etapa 3 a Etapa 4 (Backend y Contratos HTTP)

## 📌 Contexto y Diagnóstico General

Durante la transición hacia la **Etapa 4 (Adaptadores de Presentación Tkinter y Web)** y las primeras pruebas empíricas de integración cliente-servidor (con y sin datos semilla), se detectaron dos grupos de hallazgos técnicos que requerían ajustes en la Capa de Infraestructura y Persistencia sin alterar las reglas puras del Dominio:

1. **Fase 1 (Ausencia de Consultas Generales `GET`):** La batería TDD inicial validaba mutaciones (`POST`, `PUT`, `DELETE`), pero carecía de métodos `listar_todos()` para poblar las grillas generales de usuarios, catálogo de stock e historial de facturación.
2. **Fase 2 (Desajustes en Tiempo de Ejecución con Clientes Reales):** Al conectar las vistas de escritorio con el servidor Uvicorn en vivo, emergieron errores de contexto en lecturas directas (`HTTP 500`), discrepancias de capitalización entre los catálogos SQLite (`UPPERCASE`) y la matriz RBAC de las vistas, excepciones nativas de triggers sin traducir a HTTP y un desajuste de rol/hashing en el script de semillas BI (`vendedor_bi`).

---

## 🛠️ Fase 1: Refactorización Vertical de Lecturas y Endpoints GET

Para habilitar la carga de tablas en las interfaces gráficas respetando la **Regla de Dependencia**, se implementaron las consultas desde el núcleo hacia afuera:

### 1. Capa 1: Dominio (Puertos)
* **`src/dominio/puertos.py`**: Se añadieron las firmas abstractas `listar_todos()` en `PuertoRepositorioPerfiles`, `PuertoRepositorioProductos` y `PuertoRepositorioVentas`.

### 2. Capa 3: Infraestructura (Persistencia SQL)
* **`repositorio_perfiles_sql.py`**: Implementación de `listar_todos()` filtrando por `u.habilitado = 1` y resolviendo el rol mediante `LEFT JOIN`.
* **`repositorio_productos_sql.py`**: Implementación de `listar_todos()` sobre el catálogo activo.
* **`repositorio_ventas_sql.py`**: Implementación de `listar_todos()` sobre la tabla física `facturacion`, delegando el cálculo de la columna virtual/almacenada `total` a la cláusula `GENERATED ALWAYS AS` de SQLite.

### 3. Capa 2: Aplicación (Casos de Uso)
* **`casos_uso_perfiles.py`**, **`casos_uso_inventario.py`** y **`casos_uso_comercial.py`**: Se expusieron los métodos orquestadores `listar_perfiles()`, `listar_productos()` y `listar_facturas()`.

### 4. Capa 3: Infraestructura (Enrutadores FastAPI)
* **`rutas_perfiles.py`** y **`rutas_operaciones.py`**: Se habilitaron los endpoints `GET /api/perfiles`, `GET /api/productos` y `GET /api/facturas`, estandarizando el envío de payloads hacia la Capa 2 mediante `.model_dump()`.

---

## 🔧 Fase 2: Correcciones de Integración Cliente-Servidor y Normalización

Al auditar el comportamiento de las vistas reales frente al Backend, se aplicaron cinco correcciones estructurales:

### 1. Apertura Explícita del Contexto `Unit of Work` en Endpoints de Lectura Puntual
* **Causa:** En `GestorSQLite` (`gestor_sqlite.py`), los repositorios (`self.perfiles`, `self.productos`, `self.ventas`) se instancian al entrar al administrador de contexto (`__enter__`). Tres endpoints de lectura puntual invocaban `servicio.uow.perfiles...` o `servicio.uow.productos...` fuera de un bloque `with`, provocando `AttributeError` y respuestas `HTTP 500`.
* **Solución (`rutas_perfiles.py` y `rutas_operaciones.py`):** Se encapsularon las consultas de `GET /api/perfiles/rol/{rol}`, `GET /api/perfiles/{id_perfil}` y `GET /api/productos/{id_producto}` dentro de bloques `with servicio.uow:`, garantizando la apertura y cierre limpio de la conexión SQLite.

### 2. Armonización entre el Contrato `UPPERCASE` de SQLite y los Roles Canónicos del Dominio
* **Causa:** El helper `obtener_o_crear` (`utilidades_sql.py`) normaliza por diseño (y por contrato TDD) los catálogos satélites a mayúsculas (`"ADMINISTRADOR"`, `"GERENTE"`, `"PROVEEDOR"`). Al modificar un usuario o su contraseña, el rol persistido en mayúsculas retornaba literalmente hacia el cliente, provocando que `PanelControl` y los filtros por rol no reconocieran la jerarquía y deshabilitaran los botones de acceso.
* **Solución (`repositorio_perfiles_sql.py`):** Se mantuvo intacto el almacenamiento en mayúsculas en `utilidades_sql.py` y se incorporó el traductor privado `_normalizar_rol()` en `RepositorioPerfilesSQL` (aplicado en `_mapear_a_entidad` y `obtener_rol_por_id`), junto con comparaciones `UPPER(r.rol) = UPPER(?)` en `listar_por_rol`. De esta manera, la base de datos conserva su normalización en mayúsculas mientras el Dominio y las Vistas reciben siempre los nombres canónicos (`"Administrador"`, `"Gerente"`, `"Empleado - Ventas"`, `"Empleado - Compras"`, `"Proveedor"`, `"Cliente"`).

### 3. Traducción Global de Errores de SQLite (Triggers) y Entidades No Encontradas
* **Causa:** Cuando se disparaba un *Trigger* de protección en SQLite (ej. `trg_proteger_ultimo_admin`) o se buscaba un registro inexistente en una mutación, las excepciones `sqlite3.Error` y `ErrorEntidadNoEncontrada` no tenían un manejador específico en FastAPI.
* **Solución (`servidor.py`):** Se registraron dos `@app.exception_handler` adicionales que traducen `ErrorEntidadNoEncontrada` a `HTTP 404` y `sqlite3.Error` a `HTTP 400`, devolviendo el mensaje exacto del motor en la clave JSON `"detalle"` para su visualización en la interfaz.

### 4. Alineación del Script de Semillas BI (`vendedor_bi`)
* **Causa:** El script `semillas/generador_semilla_bi.py` creaba al actor `vendedor_bi` con el rol genérico `'Empleado'` y clave `'123'` en texto plano, impidiendo su listado como vendedor en Facturación y su autenticación con Bcrypt.
* **Solución (`generador_semilla_bi.py` y `repositorio_perfiles_sql.py`):** Se actualizó la semilla para asignarle el rol `'Empleado - Ventas'` y contraseña hasheada con `bcrypt`, además de contemplar la equivalencia de `'EMPLEADO'` hacia `'Empleado - Ventas'` en las consultas del repositorio.

---

## 🧪 Resultados de la Regresión (Suite TDD Completa)

```text
(.venv) D:\Repositorios de GitHub\CFP N°404\Curso de Python\FRANKIE_GESTOR\iteracion_10>pytest tests/ -v
======================================= test session starts =======================================
platform win32 -- Python 3.14.8, pytest-9.1.1, pluggy-1.7.0
rootdir: D:\Repositorios de GitHub\CFP N°404\Curso de Python\FRANKIE_GESTOR\iteracion_10
configfile: pytest.ini
plugins: anyio-4.15.1
collected 20 items

tests\integracion\test_api_rest.py ....                                                      [ 20%]
tests\integracion\test_repositorios_sql.py ....                                              [ 40%]
tests\unitarios\test_logica_inventario.py .....                                              [ 65%]
tests\unitarios\test_politicas_rbac.py .......                                               [100%]

======================================== warnings summary =========================================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\Repositorios de GitHub\CFP N°404\Curso de Python\FRANKIE_GESTOR\iteracion_10\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================================== 20 passed, 1 warning in 5.46s ==================================
```

* **Total de pruebas ejecutadas:** 20 casos (Unitarios de Dominio, Integración SQL 3FN/Triggers e Integración API REST).
* **Resultado:** `100% PASSED` en `5.46s`.
* **Conclusión:** El Backend mantiene el 100% de compatibilidad con la especificación TDD y resuelve de forma transparente la comunicación con los clientes gráficos en escenarios con y sin semillas.