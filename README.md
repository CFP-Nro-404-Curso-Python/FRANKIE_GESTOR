# 🛒 FRANKIE GESTOR — Sistema de Gestión Comercial Multi-Cliente en Python

**Autor:** David Hernan Bravo  
**Stack:** Python 3.13 / 3.14 · FastAPI · SQLite3 (3FN + Triggers) · CustomTkinter · HTML5 / CSS3 / JS Vanilla · Bcrypt · Pytest (TDD)

---

## 📌 Descripción General

**Frankie Gestor** es un sistema comercial completo (Clientes, Proveedores, Stock, Facturación, Recursos Humanos, Gestión de Usuarios IAM, Consola SQL de Auditoría y Tablero BI/OLAP) diseñado bajo **Arquitectura Hexagonal (4 capas)**, principios **S.O.L.I.D.** y **Desarrollo Guiado por Pruebas (35 tests en verde con Pytest)**.

Su núcleo de negocio y base de datos relacional en **Tercera Forma Normal (3FN)** se exponen a través de una **API REST en FastAPI**, permitiendo operar simultáneamente en red local (LAN) desde dos interfaces sincronizadas en tiempo real con paridad visual y funcional 1:1:

* **Escritorio (`CustomTkinter`):** 10 ventanas diseñadas bajo *Design System* **Slate/Blue** (`<= 1280x720`), gestionadas reactivamente por `GestorUI` (**Patrón Observador**).
* **Web SPA Responsive (`HTML5 + CSS3 + JS Vanilla`):** Interfaz *Mobile-First* para PCs, tablets y smartphones conectados al mismo WiFi, sin `localStorage` para datos maestros.

Ambas interfaces incorporan **Modo Claro/Oscuro**, **Alto Contraste WCAG**, **Escalado Tipográfico (`100% / 115% / 125%`)**, **soporte bilingüe Español/Inglés (ES/EN)**, atajos de teclado, buscadores instantáneos, **semáforo visual de inventario** y gráficos BI nativos en Canvas.

---

## 🏛️ Arquitectura y Catálogo de Diagramas (`diagramas/*.svg`)

![Arquitectura Hexagonal de Frankie Gestor](./diagramas/02_clases_arquitectura_hexagonal.svg)

| # | Plano Vectorial (SVG) | Descripción |
| :---: | :--- | :--- |
| **01** | [Casos de Uso y Jerarquía RBAC](./diagramas/01_casos_de_uso_rbac.svg) | Actores, herencia jerárquica y matriz de acceso a módulos. |
| **02** | [Clases — Arquitectura Hexagonal](./diagramas/02_clases_arquitectura_hexagonal.svg) | Organización de las 4 capas y Regla de Dependencia. |
| **03** | [Patrón Estrategia (RBAC)](./diagramas/03_patron_estrategia_rbac.svg) | Validación polimórfica de privilegios (`PoliticaAcceso`). |
| **04** | [Patrón Unidad de Trabajo (UoW — ACID)](./diagramas/04_patron_unidad_de_trabajo.svg) | Transacciones atómicas en `GestorSQLite` (facturación y anulación). |
| **05** | [Secuencia Multi-Cliente LAN](./diagramas/05_secuencia_multicliente_lan.svg) | Sincronización en tiempo real Web SPA ↔ FastAPI ↔ CustomTkinter. |
| **06** | [DER Físico en 3FN (SQLite)](./diagramas/06_der_base_datos_3fn.svg) | 27 tablas normalizadas, vista activa y 5 triggers de integridad. |
| **07** | [Patrón Observador (`GestorUI`)](./diagramas/07_patron_observador_gestor_ui.svg) | Propagación reactiva de temas, i18n ES/EN y accesibilidad WCAG. |
| **08** | [Patrones Adaptador + Repositorio (DIP)](./diagramas/08_patron_adaptador_y_repositorio.svg) | Puertos abstractos (`puertos.py`) y sus adaptadores técnicos. |
| **09** | [Inyección de Dependencias (IoC) + DTOs](./diagramas/09_patron_inyeccion_dependencias_y_dto.svg) | Contenedor `Depends()` de FastAPI, esquemas Pydantic y `dependency_overrides`. |

---

## 📈 Historia Evolutiva del Proyecto (Iteraciones 0 a 10)

El sistema consolidado en este repositorio es el resultado de once etapas progresivas de ingeniería de software:

| Iteración | Hito Técnico Consolidado |
| :--- | :--- |
| **Iteración 0** | Esqueleto arquitectónico, jerarquía de ventanas `Toplevel` y sistema de navegación. |
| **Iteración 1** | Maquetado de Interfaz de Usuario (UI), layouts estructurados y grillas `Treeview`. |
| **Iteración 2** | Lógica CRUD en memoria RAM, manejo de eventos y flujo de formularios. |
| **Iteración 3** | Persistencia inicial mediante archivos planos (`CSV`). |
| **Iteración 4** | Integridad referencial cruzada, validaciones defensivas y alertas visuales (`messagebox`). |
| **Iteración 5** | Migración definitiva a motor relacional **SQLite3**, identificadores ocultos (`iid`), operaciones ACID y anclaje dinámico de rutas. |
| **Iteración 6** | Autenticación (`Login`), matriz de seguridad **RBAC**, Consola SQL en *Sandboxing* y Backups. |
| **Iteración 7** | Criptografía con **Bcrypt** (hashing con *salt*), aislamiento en entorno virtual (`.venv`) y atajos globales (DRY). |
| **Iteración 8** | Normalización estricta en **3FN** (27 tablas), borrado lógico (`habilitado`), **Triggers** (`Hard Delete Lock` + `trg_proteger_ultimo_admin`), vistas y columnas `GENERATED ALWAYS AS ... STORED`. |
| **Iteración 9** | Módulo de **Inteligencia de Negocios (BI / OLAP)** y pipeline ETL de semillas (`semillas/generador_semilla_bi.py` con 1.000 productos y 500 facturas históricas). |
| **Iteración 10 (Actual)** | **Arquitectura Hexagonal (4 capas), S.O.L.I.D., Patrones GoF/DDD, API REST (FastAPI), migración a CustomTkinter + Web SPA LAN con paridad 1:1 (Modo Oscuro, Alto Contraste WCAG, Zoom, i18n ES/EN, semáforo de stock), lanzadores `.bat` y suite TDD de 35 tests.** |

---

## 🛠️ Decisiones Clave de Ingeniería

* **Desacople Total (Arquitectura Hexagonal + DIP):** El Dominio (`src/dominio/`) y los Casos de Uso (`src/aplicacion/`) no importan `sqlite3`, `bcrypt` ni `fastapi`; dependen solo de interfaces abstractas (`ABC`).
* **Unificación Polimórfica e IAM vs. Legajo 3FN:** Empleados, Usuarios, Clientes y Proveedores convergen en `PerfilUsuario`. Gestión de Usuarios actualiza credenciales IAM y RRHH actualiza el legajo personal (`PUT` parcial con `exclude_unset=True`) sin pisarse mutuamente.
* **Seguridad en Profundidad (3 Capas):** Validación de entrada con DTOs Pydantic (`422`), políticas jerárquicas polimórficas con Patrón Estrategia (`403`) y triggers físicos en SQLite (`RAISE ABORT` contra borrado físico y eliminación del último Administrador).
* **Atomicidad Comercial (ACID):** Emitir o anular una factura ejecuta el alta/baja lógica y el descuento/restitución exacta de inventario dentro de una misma transacción de `GestorSQLite`.
* **Capa 4 Reactiva y Accesible (Paridad 1:1):** `GestorUI` (Escritorio) y CSS Tokens + `sessionStorage` (Web) ofrecen 4 perfiles cromáticos (Claro, Oscuro y ambos en Alto Contraste), 3 niveles de zoom, traducción ES/EN en frontera (sin alterar los roles canónicos del Backend), atajos de teclado (`Esc`, `F5`, `Ctrl+F`, `Ctrl+Enter`), buscadores en vivo y gráficos BI nativos anti-superposición.

---

## 🚀 Instalación, Ejecución y Pruebas

### Requisitos
* Python **3.10 o superior** (validado en Python 3.13 y 3.14.8).

### 1. Preparación del entorno virtual (primera vez)

```bash
# Crear y activar el entorno virtual (Windows)
python -m venv .venv
.venv\Scripts\activate

# Instalar todas las dependencias
pip install -r requirements.txt
```

### 2. Lanzamiento rápido con scripts `.bat` (Windows)

* **Modo Operativo (conserva la base de datos `db/frankie_gestor.db`):**
  ```bat
  iniciar_frankie_gestor.bat
  ```
* **Modo Pruebas / Demo con Semillas BI (entorno efímero):**
  ```bat
  iniciar_con_semillas.bat
  ```
  *Elimina una DB previa si existiera, crea el esquema 3FN + roles + `admin`, siembra 1.000 productos y 500 facturas históricas, abre la aplicación y borra automáticamente la base temporal al cerrarla.*

### 3. Lanzamiento manual (Windows / Linux)

```bash
# (Opcional) Poblar con datos históricos para probar el Tablero BI
python semillas/generador_semilla_bi.py

# Iniciar cliente de escritorio + API REST (:8000) + Servidor Web LAN (:8080)
python src/presentacion/escritorio/vistas/login.py
```

* **Credenciales iniciales por defecto:** Usuario `admin` · Contraseña `admin123`.

### 4. Acceso Web desde PC o Celular en Red Local (LAN)

* **En la misma PC:** `http://localhost:8080`
* **En un celular o tablet (mismo WiFi):** Consultar la URL LAN mostrada en la barra superior del Panel de Control de Escritorio (ej. `http://192.168.1.XX:8080`).

### 5. Ejecución de la Suite de Pruebas Automatizadas (TDD — 35 Tests)

```bash
pytest tests/ -v
```

Resultado de referencia verificado: **`35 passed` (100% éxito)** cubriendo Dominio (12), Persistencia SQL 3FN y Triggers (4), API REST (4), Vistas CustomTkinter E2E + Temas/i18n/WCAG (8) y Sincronización/Paridad Web SPA LAN (7).

---

## 📚 Documentación Técnica Completa

* [📘 Descripción Integral del Sistema (Entregable Técnico)](./docs/descripcion.md)
* [🧠 Justificación Analítica del Diseño Arquitectónico y Árbol de Carpetas](./docs/fundamentos/diseño_arquitectonico.md)
* [🧪 Plan de Construcción Guiado por Pruebas (TDD)](./docs/fundamentos/plan_construccion_guiado_TDD.md)
* **Reportes por Etapa:** [Etapa 1](./docs/reportes/etapa_1.md) · [Etapa 2](./docs/reportes/etapa_2.md) · [Etapa 3](./docs/reportes/etapa_3.md) · [Etapa 4](./docs/reportes/etapa_4.md)