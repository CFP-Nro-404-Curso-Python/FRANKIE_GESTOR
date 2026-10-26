# 🧠 Justificación Analítica del Diseño Arquitectónico

## 1. Aislamiento Total e Inmutabilidad del Núcleo (Arquitectura Hexagonal + API REST)

El objetivo central de esta arquitectura es garantizar que las capas de **Dominio**, **Aplicación** y **Persistencia (Base de Datos)** sean completamente agnósticas de las interfaces de usuario.

* **Desacople Físico y Lógico:** Ninguna vista (`escritorio` en Tkinter o `web` en HTML/JS) posee acceso al motor `sqlite3`, al archivo `frankie_gestor.db`, ni a la librería criptográfica `bcrypt`. La comunicación ocurre exclusivamente a través de contratos JSON sobre HTTP expuestos por `src/infraestructura/api/`.

* **Inmutabilidad ante Nuevas Vistas:** Si se elimina la interfaz de escritorio, se rediseña la interfaz web o se incorpora un tercer cliente (ej. aplicación móvil o CLI), los directorios `db/`, `src/dominio/`, `src/aplicacion/` y `src/infraestructura/` permanecen **100% intactos (cero líneas modificadas)**.

* **Bootstrap e Infraestructura Centralizada:** La inicialización del esquema relacional (`esquema.sql`), la inyección de la semilla criptográfica (`admin`), la generación de copias de seguridad (Backups) y el motor de Sandboxing SQL se ejecutan en el ciclo de vida del servidor backend, eliminando toda dependencia operativa de las vistas.


## 2. Eliminación de Código Duplicado mediante Alta Cohesión (GRASP y KISS)

En las iteraciones previas, cuatro módulos distintos (`clientes.py`, `empleados.py`, `proveedores.py` y `usuarios.py`) duplicaban la función auxiliar `obtener_o_crear` y repetían transacciones de hasta 10 sentencias `INSERT` sobre las tablas centrales y puentes (`usuarios`, `usuxroles`, `usuarioxcontactos`, `usuarioxubicaciones`).

* **Unificación Polimórfica:** Respetando los principios **DRY (Don't Repeat Yourself)** y **KISS (Keep It Simple, Stupid)**, se evitó la sobreingeniería de crear cuatro repositorios y cuatro servicios separados. Todas las entidades humanas o jurídicas convergen en la entidad de dominio `PerfilUsuario` y son gestionadas por un único repositorio transaccional (`repositorio_perfiles_sql.py`) y un único orquestador (`casos_uso_perfiles.py`).

* **Mantenibilidad (Bajo Acoplamiento):** Cualquier ajuste futuro en el árbol geográfico o de contactos en Tercera Forma Normal (3FN) requiere modificar un único método en toda la aplicación.


## 3. Erradicación de Condicionales Anidados con el Patrón Estrategia (`politicas_rbac.py`)

Para eliminar las estructuras condicionales anidadas (`if/else`) que validaban permisos jerárquicos acoplados a ventanas emergentes (`messagebox`), se implementó el **Patrón de Comportamiento Estrategia (GoF)** en conjunto con el **Principio de Abierto/Cerrado (OCP - S.O.L.I.D.)**:

* **Polimorfismo de Permisos:** Se define la interfaz abstracta `PoliticaAcceso` con los contratos `validar_creacion()`, `validar_modificacion()` y `validar_baja()`.

* **Encapsulamiento Jerárquico:** Las clases concretas `EstrategiaAdministrador`, `EstrategiaGerente` y `EstrategiaOperador` encapsulan las reglas de negocio de cada rol sin anidamientos lógicos. Ante una violación de privilegios (como el intento de auto-baja de un Gerente o la edición de un superior), la estrategia lanza la excepción de dominio `ErrorJerarquiaRBAC`, la cual es interceptada por la capa HTTP y traducida en un estado `403 Forbidden`.


## 4. Inversión de Dependencias (DIP) y Patrón Unidad de Trabajo (ACID)

* **Principio de Inversión de Dependencias (DIP - S.O.L.I.D.):** Las capas internas (`src/dominio/` y `src/aplicacion/`) no importan frameworks ni drivers externos (`sqlite3`, `bcrypt`, `fastapi`). Dependen exclusivamente de abstracciones puras (interfaces `ABC`) declaradas en `src/dominio/puertos.py`.

* **Unidad de Trabajo (`gestor_sqlite.py`):** Las transacciones escalonadas en 3FN se encapsulan mediante un Administrador de Contexto (*Context Manager* `__enter__` / `__exit__`) que garantiza atomicidad ACID. Si falla el último eslabón de una inserción múltiple o salta un *Trigger* de seguridad en SQLite (`RAISE(ABORT)`), el gestor ejecuta un `rollback()` automático evitando registros huérfanos en los catálogos satélites.


## 5. Estructura de Carpetas

```
📂 iteracion_10/
├── 📁 db/                                       # Persistencia física aislada.
│   ├── 📜 esquema.sql                           # DDL relacional 3FN, Vistas y Triggers.
│   └── 🗄️ frankie_gestor.db                     # Base de datos generada en tiempo de ejecución.
├── 📁 docs/                                     # Documentación técnica de ingeniería.
│   └── 📝 desarrollo.md                         # Entregable final: justificación S.O.L.I.D., patrones y TDD.
├── 📁 semillas/                                 # Pipeline ETL de datos de prueba.
│   ├── 📜 empresa_ventas_1000.sql
│   └── 🐍 generador_semilla_bi.py
│
├── 📁 src/                                      # Código fuente de producción.
│   ├── 🐍 __init__.py
│   ├── 📁 dominio/                              # CAPA 1: Núcleo de Negocio (Cero librerías externas).
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 entidades.py                      # Objetos de dominio (PerfilUsuario, Producto, Factura).
│   │   ├── 🐍 excepciones.py                    # Errores de dominio (ErrorJerarquiaRBAC, ErrorStockInsuficiente).
│   │   ├── 🐍 politicas_rbac.py                 # Patrón Estrategia: erradica los if/else anidados de permisos.
│   │   └── 🐍 puertos.py                        # Clases Base Abstractas (Interfaces de Repositorios y Hash).
│   │
│   ├── 📁 aplicacion/                           # CAPA 2: Casos de Uso (Orquestación pura).
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 casos_uso_perfiles.py             # Lógica unificada de Login, Usuarios, RRHH, Clientes y Proveedores.
│   │   ├── 🐍 casos_uso_inventario.py           # Gestión de catálogo, alertas de stock mínimo y estados.
│   │   └── 🐍 casos_uso_comercial.py            # Emisión de facturación, restitución de stock y cálculos BI.
│   │
│   ├── 📁 infraestructura/                      # CAPA 3: Adaptadores Técnicos (SQLite, Bcrypt, FastAPI, Pandas).
│   │   ├── 🐍 __init__.py
│   │   ├── 📁 persistencia/
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 gestor_sqlite.py              # Unidad de Trabajo ACID y helper único obtener_o_crear.
│   │   │   ├── 🐍 repositorio_perfiles_sql.py   # Transacciones escalonadas sobre tabla 'usuarios' y puentes.
│   │   │   ├── 🐍 repositorio_productos_sql.py  # Persistencia de productos, estados y ubicaciones.
│   │   │   └── 🐍 repositorio_ventas_sql.py     # Persistencia de facturación, auditoría y consultas Pandas.
│   │   ├── 📁 seguridad/
│   │   │   ├── 🐍 __init__.py
│   │   │   └── 🐍 adaptador_bcrypt.py           # Implementación concreta de hashing criptográfico.
│   │   └── 📁 api/                              # Servidor REST (Punto de contacto para cualquier vista).
│   │       ├── 🐍 __init__.py
│   │       ├── 🐍 esquemas_validacion.py        # Objetos de Transferencia de Datos (DTOs con Pydantic).
│   │       ├── 🐍 inyector_dependencias.py      # Fábrica de servicios e intercepción de cabeceras RBAC.
│   │       ├── 🐍 rutas_perfiles.py             # Endpoints HTTP para autenticación y entidades humanas.
│   │       ├── 🐍 rutas_operaciones.py          # Endpoints HTTP para stock, facturación, consola y BI.
│   │       └── 🐍 servidor.py                   # Instancia FastAPI, manejo global de excepciones y CORS.
│   │
│   └── 📁 presentacion/                         # CAPA 4: Adaptadores de Interfaz de Usuario (Clientes HTTP).
│       ├── 📁 escritorio/                       # Vista 1: Cliente pesado en Tkinter (Cero SQL y cero Bcrypt).
│       │   ├── 🐍 cliente_api.py                # Cliente HTTP centralizado (encapsula librería requests).
│       │   └── 📁 vistas/
│       │       ├── 🐍 login.py
│       │       ├── 🐍 panel_control.py
│       │       ├── 🐍 usuarios.py
│       │       ├── 🐍 empleados.py
│       │       ├── 🐍 clientes.py
│       │       ├── 🐍 proveedores.py
│       │       ├── 🐍 stock.py
│       │       ├── 🐍 facturacion.py
│       │       ├── 🐍 consola.py
│       │       └── 🐍 analitica.py
│       └── 📁 web/                              # Vista 2: Cliente ligero Web (HTML5 + CSS + JS Vanilla).
│           ├── 🌐 index.html                    # Aplicación de Página Única (SPA).
│           ├── 🎨 estilos.css
│           └── 📜 app_web.js                    # Consumo asíncrono (fetch) de los mismos endpoints REST.
│
├── 📁 tests/                                    # Suite de Pruebas Automatizadas (Metodología TDD).
│   ├── 🐍 __init__.py
│   ├── 🐍 conftest.py                           # Configuración de entorno aislado (SQLite en RAM :memory:).
│   ├── 📁 unitarios/
│   │   ├── 🐍 test_politicas_rbac.py            # Verifica jerarquías Admin/Gerente/Empleado en milisegundos.
│   │   └── 🐍 test_logica_inventario.py         # Verifica reglas de negocio de stock y descuentos.
│   └── 📁 integracion/
│       ├── 🐍 test_repositorios_sql.py          # Verifica transacciones 3FN y disparo de Triggers SQLite.
│       └── 🐍 test_api_rest.py                  # Verifica respuestas HTTP, validaciones y bloqueos de seguridad.
│
├── 📁 .venv/
├── 📄 pytest.ini                                # Configuración de rutas para entorno de testing (Pytest).
└── 📄 requirements.txt                          # Manifiesto de paquetes (agrega fastapi, uvicorn, requests, pytest, httpx).
```