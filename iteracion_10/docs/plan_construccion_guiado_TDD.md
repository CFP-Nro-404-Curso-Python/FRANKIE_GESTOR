# 🧪 Plan de Construcción Guiado por Pruebas (Metodología TDD)

El desarrollo de la **Iteración 10** se ejecuta de adentro hacia afuera (*Inside-Out*), escribiendo los casos de prueba antes o en simultáneo con cada capa arquitectónica para garantizar cobertura total de reglas de negocio antes de construir las interfaces gráficas.


## Etapa 1: El Núcleo de Dominio y Tests Unitarios (TDD Ciclo 1)

* **Objetivo:** Modelar las entidades de negocio, excepciones personalizadas, contratos abstractos (Puertos) y el motor polimórfico de seguridad RBAC sin dependencias externas.

* **Archivos a construir:**

  * `requirements.txt`
  * `tests/unitarios/test_politicas_rbac.py`
  * `tests/unitarios/test_logica_inventario.py`
  * `src/dominio/excepciones.py`
  * `src/dominio/entidades.py`
  * `src/dominio/politicas_rbac.py`
  * `src/dominio/puertos.py`

* **Criterio de Aceptación TDD:** Ejecución en milisegundos en memoria RAM verificando que un Gerente no pueda crear/modificar/eliminar a un Administrador, que no pueda darse de baja a sí mismo (auto-despido), y que las validaciones matemáticas de stock, precios y descuentos rechacen valores fuera de rango.


## Etapa 2: Casos de Uso, Persistencia 3FN y Tests de Integración SQL (TDD Ciclo 2)

* **Objetivo:** Implementar la orquestación de negocio, el cifrado con Bcrypt y los repositorios SQLite sobre un entorno de pruebas aislado en memoria (`:memory:`), validando la integridad referencial y los *Triggers* de base de datos.

* **Archivos a construir:**

  * `tests/conftest.py`
  * `tests/integracion/test_repositorios_sql.py`
  * `src/infraestructura/seguridad/adaptador_bcrypt.py`
  * `src/infraestructura/persistencia/gestor_sqlite.py`
  * `src/infraestructura/persistencia/repositorio_perfiles_sql.py`
  * `src/infraestructura/persistencia/repositorio_productos_sql.py`
  * `src/infraestructura/persistencia/repositorio_ventas_sql.py`
  * `src/aplicacion/casos_uso_perfiles.py`
  * `src/aplicacion/casos_uso_inventario.py`
  * `src/aplicacion/casos_uso_comercial.py`

* **Criterio de Aceptación TDD:** Verificación de no duplicidad en catálogos satélites (`obtener_o_crear`), baja lógica en cascada, disparo efectivo del *Trigger* `trg_proteger_ultimo_admin` ante intento de baja del último administrador, bloqueo de borrado físico (`Hard Delete Lock`) y descuento/restitución exacta de inventario al facturar o anular.


## Etapa 3: Adaptador API REST (FastAPI) y Tests de Contrato HTTP (TDD Ciclo 3)

* **Objetivo:** Exponer los casos de uso a través de endpoints RESTful con validación automática mediante Pydantic, manejo centralizado de errores de dominio a códigos HTTP (`400`, `401`, `403`, `422`) y configuración CORS.

* **Archivos a construir:**

  * `tests/integracion/test_api_rest.py`
  * `src/infraestructura/api/esquemas_validacion.py`
  * `src/infraestructura/api/inyector_dependencias.py`
  * `src/infraestructura/api/rutas_perfiles.py`
  * `src/infraestructura/api/rutas_operaciones.py`
  * `src/infraestructura/api/servidor.py`
  * `semillas/generador_semilla_bi.py`

* **Criterio de Aceptación TDD:** Pruebas automatizadas con `TestClient` simulando peticiones de clientes externos. Al finalizar esta etapa, **el Backend y la Base de Datos quedan 100% cerrados e inmutables**.


## Etapa 4: Adaptadores de Presentación (Cliente Escritorio Tkinter + Cliente Web)

* **Objetivo:** Conectar las dos interfaces de usuario independientes consumiendo exactamente los mismos endpoints de la API REST sin acoplamiento con la lógica ni con SQLite.

* **Archivos a construir:**

  * **Cliente Escritorio:** `src/presentacion/escritorio/cliente_api.py` y refactorización de las 10 vistas en `src/presentacion/escritorio/vistas/` (`login.py`, `panel_control.py`, `usuarios.py`, `empleados.py`, `clientes.py`, `proveedores.py`, `stock.py`, `facturacion.py`, `consola.py`, `analitica.py`).

  * **Cliente Web:** `src/presentacion/web/index.html`, `src/presentacion/web/estilos.css` y `src/presentacion/web/app_web.js`.

* **Criterio de Aceptación:** Sincronización en tiempo real entre ambas plataformas (un registro creado o modificado en la Web se refleja instantáneamente al actualizar la grilla en Tkinter y viceversa).


## Etapa 5: Documentación de Ingeniería (`docs/desarrollo.md`)

* **Objetivo:** Consolidar el entregable académico final detallando la aplicación de principios S.O.L.I.D., GRASP, KISS, YAGNI, los patrones GoF implementados, el reporte de la suite TDD y la simulación de consola.