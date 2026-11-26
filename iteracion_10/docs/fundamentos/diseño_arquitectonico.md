# 🧠 Justificación Analítica del Diseño Arquitectónico

## 1. Aislamiento Total e Inmutabilidad del Núcleo (Arquitectura Hexagonal + API REST)

El objetivo central de esta arquitectura es garantizar que las capas de **Dominio**, **Aplicación** y **Persistencia (Base de Datos)** sean completamente agnósticas de las interfaces de usuario.

* **Desacople Físico y Lógico:** Ninguna vista (`escritorio` en CustomTkinter o `web` en HTML/JS) posee acceso al motor `sqlite3`, al archivo `frankie_gestor.db`, ni a la librería criptográfica `bcrypt`. La comunicación ocurre exclusivamente a través de contratos JSON sobre HTTP expuestos por `src/infraestructura/api/`.
* **Única Fuente de Verdad (Sin Cachés de Negocio):** Todos los datos operativos —incluyendo el árbol completo de contactos, domicilios en 3FN y la ubicación física de stock— viajan por los endpoints REST y se persisten en SQLite. El cliente Web prescinde por completo de `localStorage` para datos maestros (utilizando `sessionStorage` únicamente para preferencias visuales efímeras de la pestaña), garantizando sincronización bidireccional en tiempo real entre el cliente de escritorio y múltiples dispositivos conectados por red local (PC y móviles).
* **Inmutabilidad ante Nuevas Vistas y Funcionalidades UI:** Si se elimina la interfaz de escritorio, se rediseña la interfaz web, se incorporan capacidades de presentación (como la vista previa e impresión/PDF dual de comprobantes) o se suma un tercer cliente (ej. aplicación móvil nativa o CLI), los directorios `db/`, `src/dominio/`, `src/aplicacion/` y `src/infraestructura/` permanecen intactos.
* **Bootstrap e Infraestructura Centralizada:** La inicialización del esquema relacional (`esquema.sql`), la inyección de la semilla criptográfica (`admin`), la generación de copias de seguridad (Backups JSON vía API), los lanzadores operativos (`.bat`) y el motor de Sandboxing SQL se ejecutan de forma controlada sin mezclar lógica de negocio con el renderizado visual.

---

## 2. Unificación Polimórfica y Separación IAM vs. Legajo (GRASP y DRY)

En iteraciones previas, cuatro módulos distintos (`clientes.py`, `empleados.py`, `proveedores.py` y `usuarios.py`) duplicaban la lógica de inserción escalonada sobre tablas maestras y puentes.

* **Unificación en `PerfilUsuario`:** Respetando los principios **DRY (Don't Repeat Yourself)** y **KISS (Keep It Simple, Stupid)**, todas las entidades humanas o jurídicas convergen en la entidad de dominio `PerfilUsuario` y son gestionadas por un único repositorio transaccional (`repositorio_perfiles_sql.py`) y un único servicio orquestador (`casos_uso_perfiles.py`).
* **Coexistencia Operativa entre Usuarios (IAM) y RRHH (Legajo):** Ambos módulos actúan sobre el mismo registro físico en `usuarios` mediante actualizaciones parciales (`PUT /api/perfiles/{id}` con `exclude_unset=True`):
  * **Gestión de Usuarios** administra la identidad de acceso (`usuario`, `password_plana` hasheada con Bcrypt y `rol`) sin sobrescribir el legajo personal.
  * **Recursos Humanos (RRHH), Clientes y Proveedores** completan y actualizan los datos filiatorios, de contacto y domicilio (`dni`, `telefono`, `email`, `direccion`, `ciudad`, `provincia`, `cp`) en las tablas puente 3FN sin alterar las credenciales de inicio de sesión.
* **Normalización Física Completa (3FN):** `RepositorioPerfilesSQL` sincroniza atómicamente los árboles de `usuarioxcontactos` (`telefonos`, `mails`) y `usuarioxubicaciones` (`direcciones`, `ciudades`, `codigopostales`, `provincias`, `paises`), mientras que `RepositorioProductosSQL` vincula cada artículo con su ubicación física en `productoxubicaciones` y `ubicaciones_stock`.

---

## 3. Erradicación de Condicionales Anidados con el Patrón Estrategia (`politicas_rbac.py`)

Para eliminar las estructuras condicionales anidadas (`if/else`) que validaban permisos jerárquicos acoplados a ventanas emergentes (`messagebox`), se implementó el **Patrón de Comportamiento Estrategia (GoF)** en conjunto con el **Principio de Abierto/Cerrado (OCP - S.O.L.I.D.)**:

* **Polimorfismo de Permisos:** Se define la interfaz abstracta `PoliticaAcceso` con los contratos `validar_creacion()`, `validar_modificacion()` y `validar_baja()`.
* **Encapsulamiento Jerárquico:** Las clases concretas `EstrategiaAdministrador`, `EstrategiaGerente` y `EstrategiaOperador` encapsulan las reglas de negocio de cada rol sin anidamientos lógicos. Ante una violación de privilegios (como el intento de auto-baja de un Gerente o la edición de un superior), la estrategia lanza la excepción de dominio `ErrorJerarquiaRBAC`, interceptada por el manejador global de FastAPI y traducida a `HTTP 403 Forbidden`.

---

## 4. Inversión de Dependencias (DIP), Adaptadores y Patrón Unidad de Trabajo (ACID)

* **Principio de Inversión de Dependencias (DIP - S.O.L.I.D.):** Las capas internas (`src/dominio/` y `src/aplicacion/`) no importan frameworks ni drivers externos (`sqlite3`, `bcrypt`, `fastapi`). Dependen exclusivamente de interfaces abstractas (`ABC`) declaradas en `src/dominio/puertos.py`.
* **Adaptadores e Inyección de Dependencias (IoC):** `inyector_dependencias.py` ensambla en tiempo de ejecución los adaptadores concretos (`Repositorio*SQL`, `AdaptadorBcrypt`) y valida los contratos de entrada/salida con DTOs de Pydantic (`esquemas_validacion.py`). Durante las pruebas TDD, `dependency_overrides` sustituye la base física por instancias temporales aisladas sin modificar código de producción.
* **Unidad de Trabajo (`gestor_sqlite.py`):** Las transacciones escalonadas en 3FN y las operaciones compuestas (como emitir o anular una factura junto con el descuento o restitución atómica de inventario) se encapsulan mediante un Administrador de Contexto (*Context Manager* `__enter__` / `__exit__`) que garantiza atomicidad ACID. Si falla cualquier paso o salta un *Trigger* de seguridad en SQLite (`RAISE(ABORT)`), el gestor ejecuta un `rollback()` automático evitando registros huérfanos o descuadres de stock.

---

## 5. Capa 4 Reactiva: Patrón Observador (`GestorUI`), i18n, Accesibilidad (WCAG) e Impresión/PDF

Para lograr paridad estética y funcional 1:1 entre el cliente de escritorio (**CustomTkinter**, acotado a `<= 1280x720`) y el cliente **Web SPA responsive**, se unificó el *Design System* **Slate/Blue** bajo cuatro pilares:

* **Patrón Observador (`GestorUI` en `cliente_api.py`):** Centraliza las paletas de temas, el catálogo bilingüe ES/EN y los parámetros de accesibilidad en un único sujeto observable (`suscribir()` / `_notificar()`), evitando duplicar diccionarios y estilos en las 10 vistas (DRY) sin alterar el árbol de directorios oficial. Al alternar tema, idioma, contraste o escala desde cualquier pantalla, todas las ventanas abiertas —incluyendo widgets híbridos como `ttk.Treeview`, gráficos `tk.Canvas` y el pop-up de impresión— se reconfiguran en caliente.
* **Internacionalización Segura en Frontera (ES / EN):** La traducción opera estrictamente sobre etiquetas visuales. Los selectores de roles convierten la etiqueta mostrada al usuario (`"Sales Employee"` ↔ `"Empleado - Ventas"`) hacia el valor canónico en español antes de emitir cualquier petición HTTP, preservando inmutable el contrato RBAC del Backend.
* **Accesibilidad (WCAG 2.1 AA / AAA):** Ambas interfaces ofrecen **Modo Claro/Oscuro**, **Alto Contraste** (4 perfiles cromáticos con bordes reforzados y relación de contraste elevada), **Escalado Tipográfico** (`100%` / `115%` / `125%`), navegación por teclado (`Esc`, `Ctrl+F`, `F5`, `Ctrl+Enter`) y atributos semánticos ARIA (`role="toolbar"`, `aria-live="polite"`, `aria-pressed`, `:focus-visible`) en la Web.
* **Usabilidad Operativa e Impresión / PDF Multi-Cliente:** Buscadores instantáneos con contadores en vivo en todas las grillas, *zebra striping*, semáforo visual de inventario (`stock_actual <= stock_minimo` y agotado `<= 0`), gráficos BI con escala numérica en eje Y y submuestreo anti-superposición, y **vista previa imprimible de facturas en modo dual** (por defecto **Tabla Completa + Descuento Global**, con conmutador hacia **Ítem Seleccionado** y legajo 3FN del cliente): implementada sin dependencias pesadas mediante pop-up `CTkToplevel` + HTML temporal con `webbrowser` en escritorio y modal + `window.print()` / `@media print` en la Web SPA.

---

## 6. Modelado Visual y Carpeta `diagramas/` (Ingeniería de Software)

Para facilitar el mantenimiento evolutivo, la auditoría académica y el estudio de la arquitectura implementada, se formaliza el directorio **`diagramas/`** en la raíz del proyecto como repositorio versionado de planos técnicos modelados en **PlantUML** y renderizados en formato vectorial **`.svg`** para su visualización directa en GitHub:

* **Vista de Comportamiento y Seguridad:**
  * `01_casos_de_uso_rbac.svg`: Actores, jerarquía RBAC y casos de uso habilitados por rol.
  * `05_secuencia_multicliente_lan.svg`: Flujo de secuencia E2E de sincronización bidireccional Web LAN + CustomTkinter sobre SQLite 3FN.
* **Vista Estructural y de Datos:**
  * `02_clases_arquitectura_hexagonal.svg`: Diagrama de clases UML completo de las 4 capas y la Regla de Dependencia.
  * `06_der_base_datos_3fn.svg`: Diagrama Entidad-Relación físico en Tercera Forma Normal (3FN), tablas puente, vistas y triggers.
* **Catálogo de Patrones de Diseño Implementados:**
  * `03_patron_estrategia_rbac.svg`: **Patrón Estrategia (GoF)** para validación polimórfica de permisos jerárquicos.
  * `04_patron_unidad_de_trabajo.svg`: **Patrón Unidad de Trabajo (UoW - ACID)** coordinando repositorios transaccionales.
  * `07_patron_observador_gestor_ui.svg`: **Patrón Observador (GoF)** en `GestorUI` propagando temas, i18n y accesibilidad a las vistas CustomTkinter.
  * `08_patron_adaptador_y_repositorio.svg`: **Patrón Adaptador (GoF) + Repositorio (DDD)** materializando la Inversión de Dependencias (DIP) entre Puertos y Adaptadores.
  * `09_patron_inyeccion_dependencias_y_dto.svg`: **Inyección de Dependencias (IoC) + DTO (Pydantic)** en FastAPI y aislamiento de pruebas mediante `dependency_overrides`.

---

## 7. Estructura de Carpetas

```text
📂 FRANKIE_GESTOR/
├── 📁 db/                                            # Persistencia física aislada.
│   ├── 📜 esquema.sql                                # DDL relacional 3FN, Vistas y Triggers.
│   └── 🗄️ frankie_gestor.db                          # Base de datos generada en tiempo de ejecución.
├── 📁 diagramas/                                     # Planos UML/DER modelados en PlantUML y renderizados en SVG.
│   ├── 📐 01_casos_de_uso_rbac.svg                   # Actores, jerarquía RBAC y casos de uso.
│   ├── 📐 02_clases_arquitectura_hexagonal.svg       # Diagrama de clases UML de las 4 capas.
│   ├── 📐 03_patron_estrategia_rbac.svg              # Patrón Estrategia (GoF) para permisos jerárquicos.
│   ├── 📐 04_patron_unidad_de_trabajo.svg            # Patrón Unit of Work (ACID) y Repositorios.
│   ├── 📐 05_secuencia_multicliente_lan.svg          # Secuencia E2E de sincronización Web LAN + CustomTkinter.
│   ├── 📐 06_der_base_datos_3fn.svg                  # Diagrama Entidad-Relación completo en 3FN.
│   ├── 📐 07_patron_observador_gestor_ui.svg         # Patrón Observador (GoF) en GestorUI (Temas, i18n, WCAG).
│   ├── 📐 08_patron_adaptador_y_repositorio.svg      # Patrones Adaptador + Repositorio e Inversión de Dependencias.
│   └── 📐 09_patron_inyeccion_dependencias_y_dto.svg # IoC (FastAPI), DTOs Pydantic y dependency_overrides en Pytest.
├── 📁 docs/                                          # Documentación técnica de ingeniería.
│   ├── 📝 descripcion.md                             # Entregable final: justificación S.O.L.I.D., patrones y TDD.
│   ├── 📁 fundamentos/                               # Bases analíticas y de planificación.
│   │   ├── 📝 diseño_arquitectonico.md
│   │   └── 📝 plan_construccion_guiado_TDD.md
│   └── 📁 reportes/                                  # Bitácora de pruebas y progreso por etapas.
│       ├── 📝 etapa_1.md                             # Núcleo de Dominio y pruebas unitarias.
│       ├── 📝 etapa_2.md                             # Casos de Uso, Persistencia 3FN y Triggers.
│       ├── 📝 etapa_3.md                             # API REST, contratos 3FN y restitución atómica de stock.
│       └── 📝 etapa_4.md                             # Clientes CustomTkinter/Web LAN, WCAG/i18n, Impresión/PDF y E2E.
├── 📁 semillas/                                      # Pipeline ETL de datos de prueba.
│   ├── 📜 empresa_ventas_1000.sql
│   └── 🐍 generador_semilla_bi.py
│
├── 📁 src/                                           # Código fuente de producción.
│   ├── 🐍 __init__.py
│   ├── 📁 dominio/                                   # CAPA 1: Núcleo de Negocio (Cero librerías externas).
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 entidades.py                           # Entidades puras (PerfilUsuario 3FN, Producto con ubicación, Factura).
│   │   ├── 🐍 excepciones.py                         # Errores de dominio (ErrorJerarquiaRBAC, ErrorStockInsuficiente, etc.).
│   │   ├── 🐍 politicas_rbac.py                      # Patrón Estrategia: erradica los if/else anidados de permisos.
│   │   └── 🐍 puertos.py                             # Clases Base Abstractas (Interfaces de Repositorios, UoW y Hashing).
│   │
│   ├── 📁 aplicacion/                                # CAPA 2: Casos de Uso (Orquestación pura).
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 casos_uso_perfiles.py                  # Orquestación IAM + Legajo 3FN (Usuarios, RRHH, Clientes, Proveedores).
│   │   ├── 🐍 casos_uso_inventario.py                # Gestión de catálogo, ubicación física y ajustes atómicos de stock.
│   │   └── 🐍 casos_uso_comercial.py                 # Emisión y anulación atómica de facturas (con restitución de stock).
│   │
│   ├── 📁 infraestructura/                           # CAPA 3: Adaptadores Técnicos (SQLite, Bcrypt, FastAPI).
│   │   ├── 🐍 __init__.py
│   │   ├── 📁 persistencia/
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 gestor_sqlite.py                   # Unidad de Trabajo ACID para control de transacciones.
│   │   │   ├── 🐍 utilidades_sql.py                  # Módulo puro con el helper obtener_o_crear (SRP).
│   │   │   ├── 🐍 repositorio_perfiles_sql.py        # Persistencia 3FN completa (usuarios, roles, contactos y ubicaciones).
│   │   │   ├── 🐍 repositorio_productos_sql.py       # Persistencia de productos, estados y ubicaciones_stock.
│   │   │   └── 🐍 repositorio_ventas_sql.py          # Persistencia de facturación, lectura puntual y auditoría BI.
│   │   ├── 📁 seguridad/
│   │   │   ├── 🐍 __init__.py
│   │   │   └── 🐍 adaptador_bcrypt.py                # Implementación concreta de hashing criptográfico.
│   │   └── 📁 api/                                   # Servidor REST (Punto de contacto para cualquier vista).
│   │       ├── 🐍 __init__.py
│   │       ├── 🐍 esquemas_validacion.py             # DTOs con Pydantic (incluyendo legajo 3FN y ubicación de stock).
│   │       ├── 🐍 inyector_dependencias.py           # Fábrica de servicios e intercepción de cabeceras RBAC.
│   │       ├── 🐍 rutas_perfiles.py                  # Endpoints HTTP para autenticación y entidades humanas.
│   │       ├── 🐍 rutas_operaciones.py               # Endpoints HTTP para stock, facturación y BI.
│   │       └── 🐍 servidor.py                        # Instancia FastAPI, manejo global de excepciones y CORS.
│   │
│   └── 📁 presentacion/                              # CAPA 4: Adaptadores de Interfaz de Usuario (Clientes HTTP).
│       ├── 📁 escritorio/                            # Vista 1: Cliente de escritorio en CustomTkinter (<= 1280x720, cero SQL/Bcrypt).
│       │   ├── 🐍 cliente_api.py                     # Cliente HTTP (requests) + GestorUI (Observador: Temas, i18n ES/EN, WCAG).
│       │   └── 📁 vistas/
│       │       ├── 🐍 login.py
│       │       ├── 🐍 panel_control.py
│       │       ├── 🐍 usuarios.py
│       │       ├── 🐍 empleados.py
│       │       ├── 🐍 clientes.py
│       │       ├── 🐍 proveedores.py
│       │       ├── 🐍 stock.py
│       │       ├── 🐍 facturacion.py                 # Facturación + pop-up dual de vista previa e impresión/PDF vía navegador.
│       │       ├── 🐍 consola.py
│       │       └── 🐍 analitica.py
│       └── 📁 web/                                   # Vista 2: Cliente ligero Web Responsive (HTML5 + CSS + JS Vanilla).
│           ├── 🌐 index.html                         # SPA PC/Móvil con barra WCAG, i18n, buscadores y modal de impresión.
│           ├── 🎨 estilos.css                        # Design System Slate/Blue: 4 perfiles, Zoom, Semáforo y @media print.
│           └── 📜 app_web.js                         # Consumo fetch, i18n, impresión PDF dual, Canvas BI y sessionStorage UI.
│
├── 📁 tests/                                         # Suite de Pruebas Automatizadas (Metodología TDD - 37 tests).
│   ├── 🐍 __init__.py
│   ├── 🐍 conftest.py                                # Configuración de entorno aislado (SQLite en RAM :memory:).
│   ├── 📁 unitarios/
│   │   ├── 🐍 test_politicas_rbac.py                 # Verifica jerarquías Admin/Gerente/Empleado en milisegundos.
│   │   └── 🐍 test_logica_inventario.py              # Verifica reglas de negocio de stock y descuentos.
│   └── 📁 integracion/
│       ├── 🐍 test_repositorios_sql.py               # Verifica transacciones 3FN y disparo de Triggers SQLite.
│       ├── 🐍 test_api_rest.py                       # Verifica respuestas HTTP, validaciones y bloqueos de seguridad.
│       ├── 🐍 test_vistas_escritorio.py              # Verifica E2E 9 ventanas CustomTkinter, WCAG/i18n e impresión/PDF.
│       └── 🐍 test_sincronizacion_web_escritorio.py  # Verifica SPA Web, paridad WCAG/i18n/@media print, CORS y sincronía 3FN.
│
├── 📁 .venv/
├── ⚙️ iniciar_frankie_gestor.bat                     # Lanzador operativo: activa .venv, inicia login.py y desactiva al cerrar.
├── ⚙️ iniciar_con_semillas.bat                       # Lanzador de pruebas efímero: crea DB, siembra BI, ejecuta y limpia al salir.
├── 📄 pytest.ini                                     # Configuración de rutas para entorno de testing (Pytest).
└── 📄 requirements.txt                               # Manifiesto de paquetes (bcrypt, fastapi, uvicorn, requests, customtkinter, pytest, httpx, etc.).
```