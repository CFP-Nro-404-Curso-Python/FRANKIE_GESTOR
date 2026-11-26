# 🏛️ FRANKIE GESTOR — Arquitectura Hexagonal, API RESTful, TDD y Ecosistema Multi-Cliente (CustomTkinter + Web LAN)

## 📌 1. Resumen Ejecutivo

**Frankie Gestor** es un sistema integral de gestión comercial (CRM, Inventario, RRHH, Facturación, Auditoría SQL e Inteligencia de Negocios) construido bajo una **Arquitectura Hexagonal (Puertos y Adaptadores)** distribuida en **4 capas concéntricas**, gobernada por principios **S.O.L.I.D.**, **GRASP**, **KISS**, **DRY** y **YAGNI**, y respaldada por una suite de **37 pruebas automatizadas (TDD)** con `pytest`.

El núcleo de negocio y la persistencia relacional en **Tercera Forma Normal (3FN)** —27 tablas físicas, vista consolidada y 5 triggers de seguridad— se exponen a través de un servidor **API RESTful (FastAPI)** que abastece simultáneamente como única fuente de verdad a dos clientes con paridad estética y funcional 1:1:

1. **Cliente de Escritorio en CustomTkinter (`src/presentacion/escritorio/`)**: 10 módulos visuales acotados a `<= 1280x720`, conectados exclusivamente mediante HTTP (`ClienteAPI`) y gobernados reactivamente por `GestorUI` (**Patrón Observador**).
2. **Cliente Web SPA Responsive (`src/presentacion/web/`)**: Aplicación de Página Única adaptativa para teléfonos móviles, tablets y PCs en red local (LAN), sin `localStorage` para datos maestros (usando `sessionStorage` solo para preferencias visuales efímeras de la pestaña).

Ambas interfaces comparten el *Design System* **Slate/Blue**, soporte de **Modo Claro/Oscuro**, **Alto Contraste WCAG**, **Zoom tipográfico (`100% / 115% / 125%`)**, **Internacionalización bilingüe (ES/EN)** con mapeo canónico de roles, buscadores en vivo, semáforo de stock, gráficos BI renderizados nativamente sobre Canvas y **vista previa e impresión/PDF dual de comprobantes** (por defecto **Tabla Completa + Descuento Global**, con selector rápido hacia **Ítem Seleccionado** y legajo 3FN del cliente), implementada íntegramente en la Capa 4 sin modificar el Backend.

---

## 🧱 2. Arquitectura en 4 Capas y Regla de Dependencia

El código fuente se organiza bajo el principio de que **las dependencias siempre apuntan hacia el interior (el Dominio)**:

* **Capa 1 — Núcleo de Dominio (`src/dominio/`)**: Entidades puras (`PerfilUsuario` con legajo 3FN, `Producto` con ubicación física, `Factura`), excepciones de negocio (`ErrorJerarquiaRBAC`, `ErrorStockInsuficiente`, `ErrorCredencialesInvalidas`, `ErrorEntidadNoEncontrada`), motor polimórfico de permisos (`politicas_rbac.py`) y contratos abstractos (`puertos.py`: `PuertoHashing`, `PuertoRepositorioPerfiles`, `PuertoRepositorioProductos`, `PuertoRepositorioVentas`, `PuertoUnidadDeTrabajo`). Posee **cero dependencias de librerías externas**.
* **Capa 2 — Casos de Uso / Aplicación (`src/aplicacion/`)**: Orquesta los flujos operativos en tres servicios cohesivos (`ServicioPerfiles`, `ServicioInventario`, `ServicioComercial`), incluyendo coexistencia IAM/RRHH por actualización parcial y restitución atómica de inventario al anular comprobantes. Recibe sus colaboradores por Inyección de Dependencias.
* **Capa 3 — Infraestructura y Adaptadores Técnicos (`src/infraestructura/`)**:
  * **Persistencia SQL 3FN (`persistencia/`)**: Unidad de Trabajo ACID (`GestorSQLite`), helper desacoplado (`utilidades_sql.py`) y repositorios concretos (`RepositorioPerfilesSQL`, `RepositorioProductosSQL`, `RepositorioVentasSQL`).
  * **Seguridad Criptográfica (`seguridad/`)**: `AdaptadorBcrypt` para hashing con *salt* y verificación segura.
  * **Servidor API REST (`api/`)**: 9 DTOs Pydantic (`esquemas_validacion.py`), fábrica IoC (`inyector_dependencias.py`), controladores ligeros (`rutas_perfiles.py`, `rutas_operaciones.py`) y servidor central con manejo global de excepciones de dominio/SQLite y CORS LAN (`servidor.py`).
* **Capa 4 — Presentación Multi-Cliente (`src/presentacion/`)**: Adaptadores gráficos de Escritorio (**CustomTkinter**, con pop-up `CTkToplevel` + salida HTML/`webbrowser` para impresión/PDF) y **Web SPA** (con modal imprimible + `window.print()` / `@media print`) que consumen los mismos contratos JSON sobre HTTP sin acceder a SQLite ni a Bcrypt.

---

## 🧩 3. Principios de Ingeniería y Patrones de Diseño Implementados

| Principio / Patrón | Implementación Concreta en Frankie Gestor | Beneficio Técnico Obtenido | Plano UML |
| :--- | :--- | :--- | :--- |
| **Patrón Estrategia (GoF) + OCP** | `src/dominio/politicas_rbac.py` (`EstrategiaAdministrador`, `EstrategiaGerente`, `EstrategiaOperador`). | Erradicación total de `if/else` anidados para validar jerarquías y bloqueo de auto-baja de Gerentes (`HTTP 403`). | [Ver Diagrama 03](../diagramas/03_patron_estrategia_rbac.svg) |
| **Patrón Unidad de Trabajo (UoW)** | `src/infraestructura/persistencia/gestor_sqlite.py` (`__enter__` / `__exit__`). | Atomicidad ACID garantizada en altas 3FN, facturación y anulación con restitución de stock (`commit()` / `rollback()`). | [Ver Diagrama 04](../diagramas/04_patron_unidad_de_trabajo.svg) |
| **Patrón Observador (GoF)** | `GestorUI` en `src/presentacion/escritorio/cliente_api.py` (`suscribir` / `_notificar`). | Propagación en caliente de Modo Claro/Oscuro, Alto Contraste WCAG, Zoom e i18n ES/EN a todas las ventanas abiertas (incluidos `Treeview`, `Canvas` y el pop-up de impresión). | [Ver Diagrama 07](../diagramas/07_patron_observador_gestor_ui.svg) |
| **Patrón Adaptador (GoF) + Repositorio (DDD) + DIP** | `src/dominio/puertos.py`, `Repositorio*SQL`, `AdaptadorBcrypt` y `ClienteAPI`. | El Dominio y la Aplicación son inmunes a cambios en el motor SQL, la librería criptográfica o la interfaz gráfica. | [Ver Diagrama 08](../diagramas/08_patron_adaptador_y_repositorio.svg) |
| **Inyección de Dependencias (IoC) + DTO + Thin Controller** | `inyector_dependencias.py` (`Depends` + `X-Operador-Id`), `esquemas_validacion.py` y `rutas_*.py`. | Validación estricta en frontera (`HTTP 422`) y sustitución transparente de la base productiva mediante `dependency_overrides` en Pytest. | [Ver Diagrama 09](../diagramas/09_patron_inyeccion_dependencias_y_dto.svg) |

---

## 📐 4. Catálogo de Modelado Visual (`diagramas/*.svg`)

Todos los planos de arquitectura, datos y patrones fueron modelados en **PlantUML** y exportados a formato vectorial **`.svg`** en la carpeta raíz `diagramas/`:

| # | Plano Vectorial | Alcance del Modelo |
| :---: | :--- | :--- |
| **01** | [Casos de Uso y Jerarquía RBAC](../diagramas/01_casos_de_uso_rbac.svg) | Actores (`Administrador`, `Gerente`, `Empleado - Ventas`, `Empleado - Compras`), herencia jerárquica y permisos por módulo. |
| **02** | [Clases — Arquitectura Hexagonal (4 Capas)](../diagramas/02_clases_arquitectura_hexagonal.svg) | Mapa estructural completo de las 4 capas, adaptadores primarios/secundarios y Regla de Dependencia. |
| **03** | [Patrón Estrategia (RBAC)](../diagramas/03_patron_estrategia_rbac.svg) | Polimorfismo de `PoliticaAcceso`, estrategias concretas y traducción global a `HTTP 403`. |
| **04** | [Patrón Unidad de Trabajo (UoW — ACID)](../diagramas/04_patron_unidad_de_trabajo.svg) | Coordinación transaccional de `GestorSQLite` y sus 3 repositorios en `emitir_factura` y `anular_factura`. |
| **05** | [Secuencia Multi-Cliente LAN](../diagramas/05_secuencia_multicliente_lan.svg) | Flujo E2E: Gerente Web LAN crea/edita legajo 3FN de Vendedor y Escritorio CustomTkinter lo refleja al instante sin cachés. |
| **06** | [DER Físico en 3FN (SQLite)](../diagramas/06_der_base_datos_3fn.svg) | 27 tablas normalizadas, catálogos satélites, `facturacion` con columna `GENERATED STORED`, vista `vista_empleados_activos` y 5 triggers. |
| **07** | [Patrón Observador (`GestorUI`)](../diagramas/07_patron_observador_gestor_ui.svg) | Suscripción/desuscripción segura (`<Destroy>`) y difusión reactiva de temas, i18n y accesibilidad WCAG. |
| **08** | [Patrones Adaptador + Repositorio (DIP)](../diagramas/08_patron_adaptador_y_repositorio.svg) | Contratos abstractos de `puertos.py` implementados por adaptadores SQLite, Bcrypt y HTTP. |
| **09** | [Inyección de Dependencias (IoC) + DTOs](../diagramas/09_patron_inyeccion_dependencias_y_dto.svg) | 9 esquemas Pydantic, fábricas `Depends()` de FastAPI y aislamiento TDD vía `dependency_overrides`. |

---

## 🧪 5. Desarrollo Guiado por Pruebas (TDD) — Cobertura de 37 Casos

El sistema cuenta con una suite automatizada dividida en pruebas unitarias de alta velocidad en RAM y pruebas de integración sobre esquemas SQLite reales, endpoints HTTP y clientes gráficos:

1. **`tests/unitarios/test_politicas_rbac.py` (7 tests)**: Verifica permisos jerárquicos de creación, edición, baja y prohibición de auto-despido.
2. **`tests/unitarios/test_logica_inventario.py` (5 tests)**: Verifica disponibilidad de stock, cálculo matemático de subtotales con descuentos y validaciones de negocio.
3. **`tests/integracion/test_repositorios_sql.py` (4 tests)**: Valida transacciones escalonadas 3FN, estados automáticos de productos, disparo del trigger `trg_proteger_ultimo_admin` y reversión atómica (`Rollback`).
4. **`tests/integracion/test_api_rest.py` (4 tests)**: Audita endpoints de login (`200`/`401`), bloqueo jerárquico (`403`), alta de catálogo (`201`) y rechazo de facturación sin stock (`400`).
5. **`tests/integracion/test_vistas_escritorio.py` (9 tests)**: Ejecuta en modo *Headless* las 9 ventanas secundarias de CustomTkinter (`<= 1280x720`) conectadas a `TestClient`, verificando RBAC, coexistencia IAM/RRHH, persistencia 3FN, facturación con restitución exacta de stock, Consola SQL, Tablero BI, Modo Oscuro/Alto Contraste/Zoom 125%/i18n ES-EN con roles canónicos/semáforo/buscador (`test_8`) y el pop-up dual de vista previa e impresión/PDF exportando HTML imprimible vía `webbrowser` (`test_9`).
6. **`tests/integracion/test_sincronizacion_web_escritorio.py` (8 tests)**: Audita la SPA Web responsive, cero uso de `localStorage.`, soporte CORS para móviles LAN, sincronización bidireccional 3FN entre Web y CustomTkinter, paridad 1:1 de temas/WCAG/i18n/buscadores/BI (`test_7`) y el modal de impresión dual con reglas `@media print` y `window.print()` (`test_8`).

```text
(.venv) D:\Repositorios de GitHub\Proyectos Personales\FRANKIE_GESTOR>pytest tests/ -v
======================================= test session starts =======================================
platform win32 -- Python 3.14.8, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\Repositorios de GitHub\Proyectos Personales\FRANKIE_GESTOR
configfile: pytest.ini
plugins: anyio-4.16.0
collected 37 items

tests\integracion\test_api_rest.py ....                                                      [ 10%]
tests\integracion\test_repositorios_sql.py ....                                              [ 21%]
tests\integracion\test_sincronizacion_web_escritorio.py ........                             [ 43%]
tests\integracion\test_vistas_escritorio.py .........                                        [ 67%]
tests\unitarios\test_logica_inventario.py .....                                              [ 81%]
tests\unitarios\test_politicas_rbac.py .......                                               [ 100%]

======================================== warnings summary =========================================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\Repositorios de GitHub\Proyectos Personales\FRANKIE_GESTOR\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: [https://docs.pytest.org/en/stable/how-to/capture-warnings.html](https://docs.pytest.org/en/stable/how-to/capture-warnings.html)
============================ 37 passed, 1 warning in 231.66s (0:03:51) ============================
```

---

## 📱 6. Despliegue en Red Local (LAN) y Lanzadores Operativos

El sistema ofrece dos scripts de arranque automatizados en la raíz del proyecto (Windows):

* **`iniciar_frankie_gestor.bat`**: Activa `.venv`, ejecuta `src/presentacion/escritorio/vistas/login.py` y desactiva el entorno al salir.
* **`iniciar_con_semillas.bat`**: Entorno efímero de demostración y pruebas — elimina una base previa si existe, inicializa el esquema 3FN + roles + `admin`, ejecuta `semillas/generador_semilla_bi.py` (1.000 productos y 500 facturas históricas), abre `login.py` y borra la base temporal automáticamente al cerrar la aplicación.

Al iniciarse `login.py`, levanta automáticamente dos servicios de red con cierre limpio vía `atexit`:

* **Servidor API REST (FastAPI / Uvicorn):** `http://0.0.0.0:8000`
* **Servidor Cliente Web SPA:** `http://0.0.0.0:8080`

Cualquier dispositivo conectado a la misma red WiFi (teléfono móvil, tablet o notebook) puede ingresar desde su navegador a `http://<IP_LOCAL_PC>:8080`. El cliente web detecta dinámicamente la IP del servidor mediante `window.location.hostname` y opera en simultáneo con CustomTkinter sobre la misma base SQLite 3FN.

---

## 📚 7. Índice de Documentación de Ingeniería

* **Fundamentos Arquitectónicos y Planificación:**
  * [🧠 Justificación Analítica del Diseño Arquitectónico](./fundamentos/diseño_arquitectonico.md)
  * [🧪 Plan de Construcción Guiado por Pruebas (TDD)](./fundamentos/plan_construccion_guiado_TDD.md)
* **Bitácora de Reportes de Ejecución por Etapa:**
  * [📄 Reporte Etapa 1: Núcleo de Dominio y Pruebas Unitarias](./reportes/etapa_1.md)
  * [📄 Reporte Etapa 2: Casos de Uso, Persistencia 3FN y Tests de Integración](./reportes/etapa_2.md)
  * [📄 Reporte Etapa 3: Adaptador API REST, Contratos 3FN y Restitución Atómica](./reportes/etapa_3.md)
  * [📄 Reporte Etapa 4: Adaptadores de Presentación (CustomTkinter + Web SPA), WCAG/i18n, Impresión/PDF y Tests E2E](./reportes/etapa_4.md)