# 📄 Reporte de Ejecución - Etapa 3: Adaptador API REST, Tests HTTP y Auditoría de Refactorización del Backend

## 📌 Resumen de la Etapa

Se construyó y validó con éxito la **Capa Externa de Infraestructura API (Capa 3)**. Se expusieron los casos de uso del núcleo de negocio a través de endpoints RESTful utilizando FastAPI. La arquitectura demostró su solidez tanto en el despliegue inicial como en las auditorías posteriores de integración con clientes reales (CustomTkinter y Web LAN), permitiendo evolucionar contratos, persistencia 3FN y atomicidad comercial sin romper la Regla de Dependencia ni la batería TDD.


## ⚙️ Componentes Desarrollados

* **`src/infraestructura/api/esquemas_validacion.py`**: Implementación de DTOs (Data Transfer Objects) con Pydantic. Actúan como una barrera de entrada estricta, validando tipos de datos (strings, enteros, floats) antes de que la petición alcance la lógica de negocio.

* **`src/infraestructura/api/inyector_dependencias.py`**: Aplicación del patrón de Inversión de Control. Actúa como fábrica central, instanciando la Unidad de Trabajo (SQLite) y el motor criptográfico (Bcrypt), inyectándolos en los servicios y desacoplando las rutas HTTP de las herramientas físicas.

* **`src/infraestructura/api/rutas_*.py`**: Controladores ligeros (*Thin Controllers*). Se limitan a recibir peticiones HTTP, extraer la identidad del operador (cabecera `X-Operador-Id` para RBAC) y delegar la orquestación a la Capa 2.

* **`src/infraestructura/api/servidor.py`**: Instancia principal de FastAPI con configuración CORS y un **Manejador Global de Excepciones**. Intercepta errores puros del Dominio (`ErrorJerarquiaRBAC`, `ErrorStockInsuficiente`, `ErrorCredencialesInvalidas`, `ErrorEntidadNoEncontrada`) y bloqueos de `sqlite3.Error`, traduciéndolos dinámicamente a códigos HTTP (`400`, `401`, `403`, `404`).

* **`semillas/generador_semilla_bi.py`**: Script ETL autónomo para poblar la base de datos de producción con 1000 productos y 500 facturas históricas, preparando el terreno para el módulo de Business Intelligence (Etapa 4).


## 🧪 Estrategia de Testing y Configuración (TDD)

* Se utilizó `TestClient` de FastAPI para simular el ciclo de vida completo de las peticiones HTTP (Request/Response) sin levantar un servidor físico.

* Se aplicó el mecanismo `dependency_overrides` para interceptar la inyección de dependencias en tiempo de ejecución. Esto permitió que los tests HTTP no tocaran la base de datos de producción (`frankie_gestor.db`), sino que operaran sobre un clon efímero con su propio esquema y datos semilla, garantizando aislamiento total.


## 🚀 Resultados de Ejecución en Consola (Ciclo Inicial Etapa 3)

La batería de integración HTTP demostró que la API valida, enruta y traduce excepciones correctamente:

* **Pruebas HTTP (Etapa 3):** 4 ciclos completos (Login, RBAC, Alta de Producto y Facturación).
* **Suite Completa (Dominio + BD + API):** 20 casos de análisis ejecutados.
* **Resultado Final:** 100% PASSED (0 fallos, 0 errores).
* **Tiempo de Ejecución Global:** ~5.9 segundos.


## 🧠 Análisis Analítico y Arquitectónico (Cierre Inicial)

La integración inicial del backend fue un éxito rotundo. El uso de un manejador de excepciones global en el servidor eliminó la necesidad de plagar los casos de uso con bloques `try/except` vinculados a la web, manteniendo el código limpio y enfocado. La validación matemática del dominio, la persistencia atómica de la infraestructura y el enrutamiento HTTP quedaron operando en sincronía para enfrentar la integración con clientes reales.

---

# 🔄 Auditoría y Refactorización - Etapa 3 a Etapa 4 (Backend, Contratos HTTP y Persistencia 3FN)

## 📌 Contexto y Diagnóstico General

Durante la transición hacia la **Etapa 4 (Adaptadores de Presentación CustomTkinter y Web LAN)** y las pruebas empíricas cruzadas entre múltiples dispositivos en red local (con y sin datos semilla), se detectaron **cuatro grupos de hallazgos técnicos** que se resolvieron mediante refactorizaciones incrementales verificadas por regresión TDD:

1. **Fase 1 (Ausencia de Consultas Generales `GET`):** La batería TDD inicial validaba mutaciones (`POST`, `PUT`, `DELETE`), pero carecía de métodos `listar_todos()` para poblar las grillas generales de usuarios, catálogo de stock e historial de facturación.

2. **Fase 2 (Desajustes en Tiempo de Ejecución con Clientes Reales):** Al conectar las vistas de escritorio con el servidor Uvicorn en vivo, emergieron errores de contexto en lecturas directas (`HTTP 500`), discrepancias de capitalización entre los catálogos SQLite (`UPPERCASE`) y la matriz RBAC de las vistas, excepciones nativas de triggers sin traducir a HTTP y un desajuste de rol/hashing en el script de semillas BI (`vendedor_bi`).

3. **Fase 3 (Estado Dividido en Datos de Contacto y Ubicación):** Al probar flujos cruzados reales (alta de un vendedor desde la Web por un Gerente y posterior edición de sus datos personales para visualizarlos en Escritorio), se comprobó que `telefono`, `email`, `direccion`, `ciudad`, `provincia`, `cp` (en Perfiles) y `ubicacion` (en Stock) quedaban retenidos en cachés locales del cliente porque no estaban modelados en el contrato JSON ni en la persistencia activa del Backend.

4. **Fase 4 (Anulación de Facturas sin Restitución Atómica de Stock):** Al validar la anulación de comprobantes vía `DELETE /api/facturas/{id_factura}` mediante la suite E2E, se verificó que el contrato respondía que el stock había sido restituido, pero `ServicioComercial.anular_factura()` solo ejecutaba el borrado lógico (`habilitado = 0`) por carecer de `obtener_por_id()` en `RepositorioVentasSQL`.

---

## 🛠️ Fase 1: Refactorización Vertical de Lecturas y Endpoints GET

Para habilitar la carga de tablas en las interfaces gráficas respetando la **Regla de Dependencia**, se implementaron las consultas desde el núcleo hacia afuera:

### 1. Capa 1: Dominio (Puertos)
* **`src/dominio/puertos.py`**: Se añadieron las firmas abstractas `listar_todos()` en `PuertoRepositorioPerfiles`, `PuertoRepositorioProductos` y `PuertoRepositorioVentas`.

### 2. Capa 3: Infraestructura (Persistencia SQL)
* **`repositorio_perfiles_sql.py`**: Implementación de `listar_todos()` filtrando por `u.habilitado = 1` y resolviendo el rol mediante `LEFT JOIN`.
* **`repositorio_productos_sql.py`**: Implementación de `listar_todos()` sobre el catálogo activo.
* **`repositorio_ventas_sql.py`**: Implementación de `listar_todos()` sobre la tabla física `facturacion`, delegando el cálculo de la columna almacenada `total` a la cláusula `GENERATED ALWAYS AS` de SQLite.

### 3. Capa 2: Aplicación (Casos de Uso)
* **`casos_uso_perfiles.py`**, **`casos_uso_inventario.py`** y **`casos_uso_comercial.py`**: Se expusieron los métodos orquestadores `listar_perfiles()`, `listar_productos()` y `listar_facturas()`.

### 4. Capa 3: Infraestructura (Enrutadores FastAPI)
* **`rutas_perfiles.py`** y **`rutas_operaciones.py`**: Se habilitaron los endpoints `GET /api/perfiles`, `GET /api/productos` y `GET /api/facturas`, estandarizando el envío de payloads hacia la Capa 2 mediante `.model_dump()`.

---

## 🔧 Fase 2: Correcciones de Integración Cliente-Servidor y Normalización

Al auditar el comportamiento de las vistas reales frente al Backend, se aplicaron cuatro correcciones estructurales clave:

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

### 🧪 Validación de Regresión (Cierre Fase 2)
* **Pruebas ejecutadas:** 20 casos (Unitarios de Dominio, Integración SQL 3FN/Triggers e Integración API REST).
* **Resultado:** `20 passed` en `5.46s`.

---

## 🧩 Fase 3: Ampliación del Contrato 3FN (Legajo Completo de Perfiles y Ubicación de Stock)

Para erradicar las cachés locales y establecer a SQLite como única fuente de verdad en red local (LAN), se realizó un corte vertical completo respetando la Arquitectura Hexagonal y manteniendo compatibilidad total con la suite de pruebas existente:

### 1. Capa 1: Dominio (`src/dominio/entidades.py`)
* Se incorporaron `telefono`, `email`, `direccion`, `ciudad`, `provincia` y `cp` (default `"S/D"`) en `PerfilUsuario`, y `ubicacion` (default `"S/D"`) en `Producto`.

### 2. Capa 2: Aplicación (`casos_uso_perfiles.py` y `casos_uso_inventario.py`)
* Se habilitaron todos los campos nuevos en el alta (`registrar_perfil`, `registrar_producto`) y en la edición parcial (`modificar_perfil`, `modificar_producto`).
* Esta separación permite que **Gestión de Usuarios (IAM)** gestione credenciales de acceso (`usuario`, `password_plana`, `rol`) sin sobrescribir el legajo de **RRHH**, y que **RRHH** complete los datos personales y de contacto sin alterar las credenciales de login.

### 3. Capa 3: Persistencia SQLite 3FN (`repositorio_perfiles_sql.py` y `repositorio_productos_sql.py`)
* **Perfiles:** Se implementó `_sincronizar_contacto_y_ubicacion()` aplicando baja lógica a los vínculos previos (`habilitado = 0`) e insertando en los árboles 3FN (`usuarioxcontactos`, `contactoxtelefonos`, `telefonos`, `contactoxmails`, `mails`, `usuarioxubicaciones`, `ubicacionxdireccion`, `direcciones`, `ubicacionxlocalidades`, `localidadxciudades`, `ciudades`, `codigopostales`, `localidadxprovincias`, `provincias`, `localidadxpaises`, `paises`) mediante `_obtener_o_crear_literal()`. Todas las consultas reconstruyen el perfil unificado a través de `_SELECT_PERFIL_3FN`.
* **Productos:** Se implementó `_sincronizar_ubicacion_stock()` sobre `productoxubicaciones` y `ubicaciones_stock`, recuperando la ubicación física en `_SELECT_PRODUCTO_3FN`.

### 4. Capa 3: API REST (`esquemas_validacion.py`, `rutas_perfiles.py` y `rutas_operaciones.py`)
* Se ampliaron los DTOs de entrada y salida de Pydantic (`EsquemaPerfilCrear`, `EsquemaPerfilModificar`, `EsquemaPerfilRespuesta`, `EsquemaProductoCrear`, `EsquemaProductoModificar`, `EsquemaProductoRespuesta`).
* Se centralizó el armado de respuestas de perfil en el helper `_serializar_perfil()` dentro de `rutas_perfiles.py` y se expuso `ubicacion` en los endpoints `GET /api/productos` y `GET /api/productos/{id_producto}`.

---

## 🔄 Fase 4: Restitución Atómica de Stock en Anulación de Facturas (ACID)

Para garantizar que ninguna vista tenga que manipular inventario manualmente al anular o reemplazar una factura (evitando condiciones de carrera o duplicaciones de stock), se cerró el ciclo transaccional completo dentro del Backend:

* **`src/infraestructura/persistencia/repositorio_ventas_sql.py`**: Se implementó `obtener_por_id(id_factura)` filtrando estrictamente por `habilitado = 1` para recuperar el comprobante activo y evitar re-anulaciones duplicadas.
* **`src/aplicacion/casos_uso_comercial.py`**: Se refactorizó `anular_factura(id_factura)` dentro del bloque `with self.uow:` para consultar primero la factura activa (lanzando `ErrorEntidadNoEncontrada` → `HTTP 404` si no existe o ya fue anulada), aplicar el borrado lógico (`self.uow.ventas.eliminar(id_factura)`) y restituir atómicamente las unidades vendidas (`self.uow.productos.actualizar_stock(factura.id_producto, factura.cantidad)`).

---

## 🧪 Resultados de la Regresión Final del Backend (Sellado Post-Fase 4)

```text
(.venv) D:\Repositorios de GitHub\Proyectos Personales\FRANKIE_GESTOR>pytest tests/ -v
======================================= test session starts =======================================
platform win32 -- Python 3.14.8, pytest-9.1.1, pluggy-1.7.0
rootdir: D:\Repositorios de GitHub\Proyectos Personales\FRANKIE_GESTOR
configfile: pytest.ini
plugins: anyio-4.15.1
collected 33 items

tests\integracion\test_api_rest.py ....                                                      [ 12%]
tests\integracion\test_repositorios_sql.py ....                                              [ 24%]
tests\integracion\test_sincronizacion_web_escritorio.py ......                               [ 42%]
tests\integracion\test_vistas_escritorio.py .......                                          [ 63%]
tests\unitarios\test_logica_inventario.py .....                                              [ 78%]
tests\unitarios\test_politicas_rbac.py .......                                               [ 100%]

======================================== warnings summary =========================================
..\..\CFP N°404\Curso de Python\FRANKIE_GESTOR\iteracion_10\.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\Repositorios de GitHub\CFP N°404\Curso de Python\FRANKIE_GESTOR\iteracion_10\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: [https://docs.pytest.org/en/stable/how-to/capture-warnings.html](https://docs.pytest.org/en/stable/how-to/capture-warnings.html)
================================= 33 passed, 1 warning in 32.52s ==================================