# 🏛️ Iteración 10: Arquitectura Hexagonal, API RESTful, TDD y Ecosistema Multi-Cliente (Tkinter + Web LAN)

## 📌 1. Resumen Ejecutivo

La **Iteración 10** representa la culminación de ingeniería del sistema **Frankie Gestor**. El proyecto evoluciona desde una aplicación monolítica de escritorio hacia una **Arquitectura Hexagonal (Puertos y Adaptadores)** distribuida en **4 capas concéntricas**, gobernada por principios **S.O.L.I.D.**, **GRASP**, **KISS**, **DRY** y **YAGNI**, y respaldada por una suite de **32 pruebas automatizadas (TDD)** con `pytest`.

El núcleo de negocio y la persistencia relacional en Tercera Forma Normal (3FN) se exponen a través de un servidor **API RESTful (FastAPI)** que abastece simultáneamente a dos clientes desacoplados en tiempo real:

1. **Cliente de Escritorio en Tkinter (`src/presentacion/escritorio/`)**: 10 módulos visuales conectados exclusivamente mediante HTTP (`cliente_api.py`).

2. **Cliente Web SPA Responsive (`src/presentacion/web/`)**: Interfaz adaptativa para teléfonos móviles, tablets y PCs dentro de la red local (LAN), con soporte táctil y tablero de Business Intelligence en vivo.

---


## 🧱 2. Arquitectura en 4 Capas y Regla de Dependencia

El código fuente se organiza bajo el principio de que **las dependencias siempre apuntan hacia el interior (el Dominio)**:

* **Capa 1 — Núcleo de Dominio (`src/dominio/`)**: Contiene las entidades puras (`PerfilUsuario`, `Producto`, `Factura`), las excepciones de negocio (`ErrorJerarquiaRBAC`, `ErrorStockInsuficiente`, `ErrorCredencialesInvalidas`, `ErrorEntidadNoEncontrada`), el motor polimórfico de permisos (`politicas_rbac.py`) y los contratos abstractos (`puertos.py`). Posee **cero dependencias de librerías externas**.

* **Capa 2 — Casos de Uso / Aplicación (`src/aplicacion/`)**: Orquesta los flujos operativos en tres servicios cohesivos (`ServicioPerfiles`, `ServicioInventario`, `ServicioComercial`). Recibe sus colaboradores mediante Inyección de Dependencias sin conocer si la base de datos es SQLite o el algoritmo criptográfico es Bcrypt.

* **Capa 3 — Infraestructura y Adaptadores Técnicos (`src/infraestructura/`)**: Implementa los contratos del dominio en tres frentes:

  * **Persistencia SQL 3FN (`persistencia/`)**: Unidad de Trabajo ACID (`GestorSQLite`), helper desacoplado (`utilidades_sql.py`) y repositorios concretos (`RepositorioPerfilesSQL`, `RepositorioProductosSQL`, `RepositorioVentasSQL`).

  * **Seguridad Criptográfica (`seguridad/`)**: `AdaptadorBcrypt` para hashing con *salt* y verificación segura.

  * **Servidor API REST (`api/`)**: DTOs de validación con Pydantic (`esquemas_validacion.py`), fábrica de inyección (`inyector_dependencias.py`), controladores ligeros (`rutas_perfiles.py`, `rutas_operaciones.py`) y servidor central con manejo global de excepciones y CORS (`servidor.py`).

* **Capa 4 — Presentación Multi-Cliente (`src/presentacion/`)**: Interfaces gráficas de Escritorio (Tkinter) y Web (HTML5/CSS3/JS) que consumen los mismos endpoints JSON sin tocar la base de datos ni encriptar claves localmente.

---


## 🧩 3. Principios de Ingeniería y Patrones de Diseño Implementados

| Principio / Patrón | Implementación Concreta en Frankie Gestor | Beneficio Técnico Obtenido |
| :--- | :--- | :--- |
| **Patrón Estrategia (GoF) + OCP** | `src/dominio/politicas_rbac.py` (`EstrategiaAdministrador`, `EstrategiaGerente`, `EstrategiaOperador`). | Erradicación total de condicionales `if/else` anidados para validar jerarquías y bloqueo de auto-baja de Gerentes. |
| **Inversión de Dependencias (DIP)** | `src/dominio/puertos.py` (Interfaces `ABC` para Repositorios, Hashing y UoW). | El Dominio y la Aplicación son inmunes a cambios en el motor SQL o en el framework web. |
| **Patrón Unidad de Trabajo (UoW)** | `src/infraestructura/persistencia/gestor_sqlite.py` (`__enter__` / `__exit__`). | Atomicidad ACID garantizada: ejecuta `commit()` al finalizar con éxito o `rollback()` automático ante fallos o *Triggers*. |
| **Patrón Repositorio + DRY / KISS** | `repositorio_perfiles_sql.py` y `utilidades_sql.py` (`obtener_o_crear`). | Unifica en un solo módulo las transacciones escalonadas en 3FN de Usuarios, Empleados, Clientes y Proveedores. |
| **Patrón DTO + Thin Controller** | `esquemas_validacion.py`, `rutas_perfiles.py` y `rutas_operaciones.py`. | Barrera de entrada que rechaza tipos inválidos con `HTTP 422` antes de tocar el Dominio. |
| **Inyección de Dependencias (IoC)** | `inyector_dependencias.py` (`Depends` de FastAPI + cabecera `X-Operador-Id`). | Permite intercambiar la base de producción por bases efímeras aisladas durante la ejecución de `pytest`. |

---


## 🧪 4. Desarrollo Guiado por Pruebas (TDD) — Cobertura de 32 Casos

El sistema cuenta con una suite automatizada dividida en pruebas unitarias de alta velocidad en RAM y pruebas de integración sobre esquemas SQLite reales, endpoints HTTP y clientes gráficos:

1. **`tests/unitarios/test_politicas_rbac.py` (7 tests)**: Verifica permisos jerárquicos de creación, edición, baja y prohibición de auto-despido.

2. **`tests/unitarios/test_logica_inventario.py` (5 tests)**: Verifica disponibilidad de stock, cálculo matemático de subtotales con descuentos y validaciones de negocio.

3. **`tests/integracion/test_repositorios_sql.py` (4 tests)**: Valida transacciones escalonadas 3FN, estados automáticos de productos, disparo del trigger `trg_proteger_ultimo_admin` y reversión atómica (`Rollback`).

4. **`tests/integracion/test_api_rest.py` (4 tests)**: Audita endpoints de login (`200`/`401`), bloqueo jerárquico (`403`), alta de catálogo (`201`) y rechazo de facturación sin stock (`400`).

5. **`tests/integracion/test_vistas_escritorio.py` (7 tests)**: Ejecuta en modo *Headless* las 9 ventanas de Tkinter conectadas al `TestClient`, verificando flujos completos de UI, Consola SQL y Tablero BI.

6. **`tests/integracion/test_sincronizacion_web_escritorio.py` (5 tests)**: Verifica la estructura responsive de la SPA web, el soporte CORS para móviles en LAN y la sincronización bidireccional en tiempo real entre Web y Escritorio.


```
(.venv) D:\Repositorios de GitHub\CFP N°404\Curso de Python\FRANKIE_GESTOR\iteracion_10>pytest tests/ -v
======================================= test session starts =======================================
platform win32 -- Python 3.14.8, pytest-9.1.1, pluggy-1.7.0
rootdir: D:\Repositorios de GitHub\CFP N°404\Curso de Python\FRANKIE_GESTOR\iteracion_10
configfile: pytest.ini
plugins: anyio-4.15.1
collected 32 items

tests\integracion\test_api_rest.py ....                                                      [ 12%]
tests\integracion\test_repositorios_sql.py ....                                              [ 25%]
tests\integracion\test_sincronizacion_web_escritorio.py .....                                [ 40%]
tests\integracion\test_vistas_escritorio.py .......                                          [ 62%]
tests\unitarios\test_logica_inventario.py .....                                              [ 78%]
tests\unitarios\test_politicas_rbac.py .......                                               [100%]

======================================== warnings summary =========================================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\Repositorios de GitHub\CFP N°404\Curso de Python\FRANKIE_GESTOR\iteracion_10\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================================= 32 passed, 1 warning in 52.17s ==================================
```

---


## 📱 5. Despliegue en Red Local (LAN) y Sincronización en Tiempo Real

Al iniciar `src/presentacion/escritorio/vistas/login.py`, el sistema verifica e inicializa `db/frankie_gestor.db` (compatible tanto con arranque en limpio como con el lote masivo de `semillas/generador_semilla_bi.py`) y levanta automáticamente dos demonios en red:

* **Servidor API REST (FastAPI / Uvicorn):** Escucha en `http://0.0.0.0:8000`.

* **Servidor Cliente Web SPA:** Escucha en `http://0.0.0.0:8080`.

Cualquier dispositivo conectado a la misma red WiFi (teléfono móvil, tablet o notebook) puede ingresar desde su navegador a `http://<IP_LOCAL_PC>:8080`. El cliente web detecta dinámicamente la IP del host mediante `window.location.hostname` y opera en simultáneo con la interfaz de escritorio sobre la misma base de datos transaccional.

---

## 📚 6. Índice de Documentación de Ingeniería (Iteración 10)

* **Fundamentos Arquitectónicos y Planificación:**

  * [🧠 Justificación Analítica del Diseño Arquitectónico](./fundamentos/diseño_arquitectonico.md)

  * [🧪 Plan de Construcción Guiado por Pruebas (TDD)](./fundamentos/plan_construccion_guiado_TDD.md)

* **Bitácora de Reportes de Ejecución por Etapa:**

  * [📄 Reporte Etapa 1: Núcleo de Dominio y Pruebas Unitarias](./reportes/etapa_1.md)

  * [📄 Reporte Etapa 2: Casos de Uso, Persistencia 3FN y Tests de Integración](./reportes/etapa_2.md)

  * [📄 Reporte Etapa 3: Adaptador API REST y Tests HTTP](./reportes/etapa_3.md)
  
  * [📄 Reporte Etapa 4: Adaptadores de Presentación (Tkinter + Web SPA) y Sincronización](./reportes/etapa_4.md)