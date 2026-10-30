# 📄 Reporte de Auditoría y Refactorización - Etapa 3 (Lecturas y Endpoints GET)

## 📌 Contexto y Diagnóstico

Durante la transición hacia la Etapa 4 (Conexión de Interfaces Gráficas), se detectó un "punto ciego" arquitectónico. La batería de pruebas TDD de las etapas 1 y 2 se había centrado exclusivamente en operaciones de mutación crítica (transacciones ACID, alta, baja, y validaciones RBAC). Sin embargo, se habían omitido los métodos de lectura general (listar todos). 
**Problema:** Sin estos métodos, las vistas (Tkinter/Web) no tenían forma de recuperar el catálogo de productos, el historial de ventas o la nómina de usuarios para poblar sus grillas (Treeviews/Tablas).


## 🛠️ Refactorización Vertical (Regla de Dependencia)

Para resolver esta deuda técnica respetando la Arquitectura Hexagonal, la implementación se realizó desde el centro hacia afuera:

### 1. Capa 1: Dominio (Puertos)

*   **`src/dominio/puertos.py`**: Se añadieron las firmas abstractas `listar_todos()` a los puertos `PuertoRepositorioPerfiles`, `PuertoRepositorioProductos` y `PuertoRepositorioVentas`.

### 2. Capa 3: Infraestructura (Persistencia SQL)

Se implementaron los contratos abstractos en los repositorios SQLite físicos, devolviendo listas de entidades puras:
*   **`repositorio_perfiles_sql.py`**: Nuevo método `listar_todos()` filtrando por `habilitado = 1` y resolviendo la tabla intermedia de roles.

*   **`repositorio_productos_sql.py`**: Nuevo método `listar_todos()` para extraer el catálogo completo activo.

*   **`repositorio_ventas_sql.py`**: Nuevo método `listar_todos()` para extraer el historial contable, vital para el módulo BI. Adicionalmente, se corrigió una colisión DDL (se cambió la tabla `facturas` por `facturacion` y se eliminó la inyección manual de la columna autocalculada `total`).

### 3. Capa 2: Aplicación (Casos de Uso)

*   **`casos_uso_perfiles.py`**: Se agregó `listar_perfiles()`.

*   **`casos_uso_inventario.py`**: Se agregó `listar_productos()`.

*   **`casos_uso_comercial.py`**: Se agregó `listar_facturas()`.

### 4. Capa 3: Infraestructura (API REST)

*   **`rutas_perfiles.py`**: Se expuso el endpoint `GET /api/perfiles`. Se corrigieron llamadas a métodos (`autenticar_usuario` y `dar_de_baja_perfil`) y se ajustaron las inyecciones de datos (usando `model_dump()` para diccionarios crudos).

*   **`rutas_operaciones.py`**: Se expusieron los endpoints `GET /api/productos` y `GET /api/facturas`. Se corrigieron inyecciones y nombres de métodos (`registrar_ingreso_stock`, `dar_de_baja_producto`).

*   **`servidor.py`**: Se inyectó un `exception_handler` específico para atrapar `ErrorCredencialesInvalidas` y traducirlo a un estado HTTP 401.

## 🧪 Resultados de la Regresión (Testing)

```
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
================================== 20 passed, 1 warning in 6.36s ==================================
```

Tras la refactorización integral, se corrió nuevamente la suite de pruebas automatizadas:
*   **Total de pruebas ejecutadas:** 20
*   **Resultado:** 100% PASSED.
*   **Conclusión:** Las capas externas fueron adaptadas exitosamente sin corromper el núcleo de negocio. El backend está oficialmente sellado y listo para ser consumido.