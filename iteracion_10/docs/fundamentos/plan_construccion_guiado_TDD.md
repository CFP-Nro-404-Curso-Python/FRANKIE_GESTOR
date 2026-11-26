# 🧪 Plan de Construcción Guiado por Pruebas (Metodología TDD)

El desarrollo del sistema se ejecuta de adentro hacia afuera (*Inside-Out*), escribiendo los casos de prueba antes o en simultáneo con cada capa arquitectónica para garantizar cobertura total de reglas de negocio, persistencia relacional y contratos HTTP antes de desplegar las interfaces gráficas.


## Etapa 1: El Núcleo de Dominio y Tests Unitarios (TDD Ciclo 1)

* **Objetivo:** Modelar las entidades de negocio puras, excepciones personalizadas, contratos abstractos (Puertos) y el motor polimórfico de seguridad RBAC sin dependencias externas.

* **Archivos a construir:**

  * `requirements.txt`
  * `pytest.ini`
  * `tests/unitarios/test_politicas_rbac.py`
  * `tests/unitarios/test_logica_inventario.py`
  * `src/dominio/excepciones.py`
  * `src/dominio/entidades.py`
  * `src/dominio/politicas_rbac.py`
  * `src/dominio/puertos.py`

* **Criterio de Aceptación TDD:** Ejecución en milisegundos en memoria RAM verificando que un Gerente no pueda crear/modificar/eliminar a un Administrador, que no pueda darse de baja a sí mismo (auto-despido), y que las validaciones matemáticas de stock, precios y descuentos rechacen valores fuera de rango.


## Etapa 2: Casos de Uso, Persistencia 3FN y Tests de Integración SQL (TDD Ciclo 2)

* **Objetivo:** Implementar la orquestación de negocio, el cifrado con Bcrypt y los repositorios SQLite sobre un entorno de pruebas aislado en memoria (`:memory:`), validando la integridad referencial, la Tercera Forma Normal (3FN) y los *Triggers* de base de datos.

* **Archivos a construir:**

  * `tests/conftest.py`
  * `tests/integracion/test_repositorios_sql.py`
  * `src/infraestructura/seguridad/adaptador_bcrypt.py`
  * `src/infraestructura/persistencia/utilidades_sql.py`
  * `src/infraestructura/persistencia/gestor_sqlite.py`
  * `src/infraestructura/persistencia/repositorio_perfiles_sql.py`
  * `src/infraestructura/persistencia/repositorio_productos_sql.py`
  * `src/infraestructura/persistencia/repositorio_ventas_sql.py`
  * `src/aplicacion/casos_uso_perfiles.py`
  * `src/aplicacion/casos_uso_inventario.py`
  * `src/aplicacion/casos_uso_comercial.py`

* **Criterio de Aceptación TDD:** Verificación de no duplicidad en catálogos satélites (`obtener_o_crear`), baja lógica en cascada, disparo efectivo del *Trigger* `trg_proteger_ultimo_admin` ante intento de baja del último administrador, bloqueo de borrado físico (`Hard Delete Lock`) y descuento/restitución exacta de inventario al facturar o anular.


## Etapa 3: Adaptador API REST (FastAPI), Contratos 3FN y Tests HTTP (TDD Ciclo 3)

* **Objetivo:** Exponer los casos de uso a través de endpoints RESTful con validación automática mediante Pydantic, manejo centralizado de errores de dominio y motor SQLite a códigos HTTP (`400`, `401`, `403`, `404`, `422`) y configuración CORS para tráfico en red local (LAN).

* **Archivos a construir:**

  * `tests/integracion/test_api_rest.py`
  * `src/infraestructura/api/esquemas_validacion.py`
  * `src/infraestructura/api/inyector_dependencias.py`
  * `src/infraestructura/api/rutas_perfiles.py`
  * `src/infraestructura/api/rutas_operaciones.py`
  * `src/infraestructura/api/servidor.py`
  * `semillas/generador_semilla_bi.py`

* **Criterio de Aceptación TDD:** Pruebas automatizadas con `TestClient` simulando peticiones de clientes externos y regresiones completas tras cada auditoría del contrato (lecturas generales `GET`, normalización de roles, persistencia 3FN de contactos/domicilios/ubicaciones de stock y restitución atómica de inventario al anular facturas). Al cerrar el ciclo de validación, **el Backend queda sellado como única fuente de verdad para todas las vistas**.


## Etapa 4: Adaptadores de Presentación (CustomTkinter + Web LAN), Accesibilidad/i18n, Impresión/PDF y Tests E2E (TDD Ciclo 4)

* **Objetivo:** Conectar dos interfaces de usuario independientes con paridad 1:1 bajo un *Design System* **Slate/Blue** unificado (cliente de escritorio en CustomTkinter con ventanas `<= 1280x720` y SPA web responsive para PC y móviles en red local), consumiendo exactamente los mismos endpoints de la API REST, sin cachés locales de datos maestros ni acoplamiento con SQLite o Bcrypt. Incorporar soporte reactivo de **Modo Claro/Oscuro**, **Alto Contraste WCAG**, **Zoom Tipográfico**, **Internacionalización ES/EN**, buscadores en vivo, semáforo de stock, **vista previa e impresión/PDF dual de facturas** (100% en Capa 4) y scripts de ejecución operativa.

* **Archivos a construir:**

  * **Cliente Escritorio:** `src/presentacion/escritorio/cliente_api.py` (`ClienteAPI` + `GestorUI` bajo Patrón Observador) y las 10 vistas migradas a CustomTkinter en `src/presentacion/escritorio/vistas/` (`login.py`, `panel_control.py`, `usuarios.py`, `empleados.py`, `clientes.py`, `proveedores.py`, `stock.py`, `facturacion.py`, `consola.py`, `analitica.py`).
  * **Cliente Web Responsive (LAN):** `src/presentacion/web/index.html`, `src/presentacion/web/estilos.css` (con `@media print`) y `src/presentacion/web/app_web.js` (preferencias visuales únicamente en `sessionStorage`, cero `localStorage`).
  * **Scripts Lanzadores (Windows):** `iniciar_frankie_gestor.bat` (ejecución operativa) e `iniciar_con_semillas.bat` (ciclo efímero de pruebas con semillas BI y limpieza automática).
  * **Suite de Pruebas E2E:** `tests/integracion/test_vistas_escritorio.py` (9 casos en CustomTkinter *headless*, incluyendo temas, WCAG, i18n con roles canónicos, semáforo, filtro y vista previa/exportación HTML-PDF de facturas) y `tests/integracion/test_sincronizacion_web_escritorio.py` (8 casos de auditoría SPA, paridad WCAG/i18n/`@media print`, CORS LAN, ausencia de `localStorage` y sincronización bidireccional 3FN).

* **Criterio de Aceptación:** Ejecución en verde de la suite completa (**37 tests**) y sincronización real entre plataformas: cualquier registro o modificación de legajo personal, contacto, domicilio, ubicación de stock o comprobante ejecutado desde la Web (PC o móvil) se persiste en SQLite y se refleja instantáneamente en CustomTkinter y viceversa, manteniendo los roles canónicos intactos al operar en español o inglés y permitiendo imprimir o exportar a PDF comprobantes legibles desde ambos clientes.


## Etapa 5: Documentación de Ingeniería y Modelado Visual (`docs/` y `diagramas/`)

* **Objetivo:** Consolidar la documentación técnica y arquitectónica del repositorio, detallando la aplicación de principios S.O.L.I.D., GRASP, KISS, YAGNI, los patrones de diseño implementados, los planos vectoriales de arquitectura/patrones/datos y la evidencia de ejecución de la suite TDD.

* **Archivos a construir:**

  * `README.md` (presentación ejecutiva integradora de las iteraciones 0 a 10, instalación y operación con lanzadores `.bat`).
  * `docs/descripcion.md` (entregable técnico integrador con referencias a los 9 diagramas).
  * `docs/fundamentos/diseño_arquitectonico.md` y `docs/fundamentos/plan_construccion_guiado_TDD.md`.
  * `docs/reportes/etapa_1.md`, `etapa_2.md`, `etapa_3.md` y `etapa_4.md`.
  * `diagramas/*.svg` (9 planos modelados con PlantUML: `01_casos_de_uso_rbac`, `02_clases_arquitectura_hexagonal`, `03_patron_estrategia_rbac`, `04_patron_unidad_de_trabajo`, `05_secuencia_multicliente_lan`, `06_der_base_datos_3fn`, `07_patron_observador_gestor_ui`, `08_patron_adaptador_y_repositorio` y `09_patron_inyeccion_dependencias_y_dto`).