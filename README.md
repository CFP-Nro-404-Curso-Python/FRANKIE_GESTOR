# 🛒 Sistema de Gestión Comercial en Python (Frankie Gestor)

**Centro de Formación Profesional N° 404**

**Alumno:** David Hernan Bravo  
---

## 📌 Descripción del Proyecto

El desarrollo se estructura en múltiples etapas incrementales que documentan la evolución completa de un sistema de software comercial: desde un prototipo visual en memoria hasta una **Arquitectura Hexagonal distribuida con API RESTful (FastAPI), Analítica de Negocios (BI), Suite TDD de 32 pruebas automatizadas y doble interfaz sincronizada en tiempo real (Escritorio Tkinter + Web SPA Responsive para dispositivos móviles en red local)**.

Cada carpeta contiene el código fuente de la iteración y su respectivo análisis técnico detallado en el archivo `descripcion.md`.


## 📂 Estructura del Proyecto e Iteraciones

El desarrollo abarca once etapas evolutivas (Iteraciones 0 a 10). Cada directorio preserva su independencia y documentación técnica:

| Iteración | Foco del Desarrollo | Análisis Detallado | 
| ----- | ----- | ----- | 
| **Iteración 0** | Esqueleto arquitectónico, jerarquía de Toplevels y sistema de navegación. | [📖 Ver descripcion.md](./iteracion_00/docs/descripcion.md) | 
| **Iteración 1** | Maquetado de Interfaz de Usuario (UI), Layouts y grillas Treeview. | [📖 Ver descripcion.md](./iteracion_01/docs/descripcion.md) | 
| **Iteración 2** | Lógica CRUD en memoria RAM (volátil), DOM de Tkinter y manejo de eventos. | [📖 Ver descripcion.md](./iteracion_02/docs/descripcion.md) | 
| **Iteración 3** | Persistencia mediante archivos planos (CSV) y sincronización destructiva. | [📖 Ver descripcion.md](./iteracion_03/docs/descripcion.md) | 
| **Iteración 4** | Integridad referencial cruzada entre CSVs, motor transaccional simulado y manejo de excepciones visuales. | [📖 Ver descripcion.md](./iteracion_04/docs/descripcion.md) | 
| **Iteración 5** | Migración definitiva a motor relacional (SQLite3), identificadores ocultos (IID), operaciones ACID y anclaje estricto de rutas. | [📖 Ver descripcion.md](./iteracion_05/docs/descripcion.md) | 
| **Iteración 6** | Ecosistema centralizado, Autenticación (Login), Seguridad RBAC, Consola SQL (Sandboxing) y Backups. | [📖 Ver descripcion.md](./iteracion_06/docs/descripcion.md) | 
| **Iteración 7** | Criptografía (Bcrypt), Entornos Virtuales (.venv), UX Global (DRY) y Filtros Relacionales. | [📖 Ver descripcion.md](./iteracion_07/docs/descripcion.md) | 
| **Iteración 8** | Normalización Extrema (3FN), Borrado Lógico, Triggers (Hard Delete Lock) y Transacciones Escalonadas. | [📖 Ver descripcion.md](./iteracion_08/docs/descripcion.md) | 
| **Iteración 9** | Inteligencia de Negocios (BI / OLAP), procesamiento vectorizado con Pandas, gráficos Matplotlib y pipeline ETL de semillas masivas. | [📖 Ver descripcion.md](./iteracion_09/docs/descripcion.md) | 
| **Iteración 10** | **Arquitectura Hexagonal (4 Capas), Principios S.O.L.I.D., API REST (FastAPI), Suite TDD (32 tests) y Doble Cliente Sincronizado (Tkinter + Web SPA Móvil LAN).** | [📖 Ver descripcion.md](./iteracion_10/docs/descripcion.md) | 
|  |  |  |

> 💡 **Nota sobre la Persistencia, Semillas y Arquitectura:** Entre las **Iteraciones 5 y 8** se consolidó la base relacional `db/frankie_gestor.db` en Tercera Forma Normal (3FN) gobernada por `db/esquema.sql` y aislada en un entorno virtual (`.venv`). En la **Iteración 9** se incorporó el motor analítico OLAP y el generador ETL de semillas (`semillas/generador_semilla_bi.py`). Finalmente, en la **Iteración 10**, el acceso a datos y la lógica de negocio se desacoplaron por completo de las pantallas mediante una **API REST en FastAPI**, permitiendo operar indistintamente con o sin semillas desde el escritorio y desde navegadores móviles en la misma red local.


## 🛠️ Evolución y Análisis Técnico

El enfoque principal de este proyecto es evidenciar el análisis crítico y la escalabilidad detrás de cada decisión de ingeniería de software:

* **Mitigación de Acoplamiento (Lazy Imports):** Se evitó el clásico error de *Circular Import* cargando los submódulos de la interfaz únicamente en memoria local al momento de ser requeridos por la interacción del usuario, reduciendo el tiempo de arranque a cero.

* **Del Texto Libre a la Restricción:** Evolución clara desde el uso de simples `tk.Entry` (propensos a errores de tipeo humano) hacia menús `ttk.Combobox` en estado `readonly`, garantizando que el operador solo procese entidades validadas y preexistentes en los maestros.

* **Gestión de Claves Primarias (IID Oculto):** En lugar de exponer un ID de base de datos visualmente al usuario (un antipatrón UI), el sistema inyecta la Primary Key de SQLite en el parámetro interno `iid` del Treeview de Tkinter. Esto permite apuntar sentencias `UPDATE` y `DELETE` con precisión milimétrica sin ensuciar la interfaz gráfica.

* **Experiencia de Usuario (UX) Defensiva:** Erradicación de errores silenciosos en consola mediante la implementación estricta del módulo `tkinter.messagebox`. El sistema despliega alertas preventivas (stock mínimo perforado) y bloqueos duros (intentos de vender sin disponibilidad o con formatos inválidos).

* **Anclaje Dinámico de Directorios:** Uso de `os.path.dirname(os.path.abspath(__file__))` para garantizar que el sistema encuentre siempre la base de datos independientemente de la ruta desde la cual la consola de comandos haya ejecutado el script.

* **Arquitectura de Seguridad (RBAC):** Implementación de un flujo de acceso cerrado. El sistema arranca desde un Login que inyecta los privilegios del usuario (Administrador, Gerente, Empleado) a un Panel de Control central, limitando dinámicamente la interfaz gráfica y bloqueando transacciones no autorizadas en el backend para prevenir ataques de escalada de privilegios.

* **Sandboxing SQL y Auditoría:** Desarrollo de una consola de ejecución aislada con filtros de expresiones regulares (Regex) y modo de solo lectura estricto (`mode=ro` + `PRAGMA query_only`) que bloquea sentencias destructivas (`DELETE`, `UPDATE`, `DROP`) e inyecta límites de paginación forzados para proteger la memoria.

* **Criptografía y Aislamiento de Entorno:** Erradicación de contraseñas en texto plano migrando al estándar empresarial Bcrypt (hashing con salt). Esto transformó el proyecto en un paquete de software formal, aislando sus dependencias en un entorno virtual (`.venv`) documentado en un manifiesto `requirements.txt`.

* **Usabilidad Global (Principio DRY):** Implementación de Application-wide Binding (`bind_class`). En lugar de programar atajos de teclado (Copiar/Pegar) y menús contextuales widget por widget, se inyectaron a nivel de clase en el nodo raíz, propagando el comportamiento automáticamente a toda la interfaz sin duplicar código.

* **Normalización Extrema (3FN) y Transacciones Escalonadas:** Migración de tablas planas hacia un esquema de catálogos atomizados y tablas puente (relaciones N:M). El backend de Python ejecuta inserciones en cascada manejando múltiples PKs y FKs en una sola transacción unificada.

* **Delegación al Motor SQL y Borrado Lógico:** Reemplazo de sentencias `DELETE` por `UPDATE habilitado=0` para preservar el historial contable. Implementación de Triggers `BEFORE DELETE` y `trg_proteger_ultimo_admin` con `RAISE(ABORT)` para blindar la base de datos contra borrados físicos o pérdida del último Administrador, junto con Vistas (`VIEWS`) y Columnas Calculadas (`GENERATED ALWAYS AS`).

* **Inteligencia de Negocios (BI / OLAP):** Integración de `pandas` y `matplotlib` para transformar el historial transaccional en tableros gerenciales con KPIs vectorizados (Facturación Total, Operaciones, Unidades Vendidas, Ticket Promedio) y gráficos de barras, líneas y torta.

* **Arquitectura Hexagonal, S.O.L.I.D. y Patrones GoF (Iteración 10):** Desacople total en 4 capas (Dominio, Aplicación, Infraestructura y Presentación). Reemplazo de condicionales de permisos por el **Patrón Estrategia**, manejo transaccional mediante **Unidad de Trabajo (Unit of Work)**, abstracción de persistencia con **Repositorios** e **Inyección de Dependencias** sobre **FastAPI**.

* **Desarrollo Guiado por Pruebas (TDD) y Sincronización Multi-Cliente LAN:** Validación automatizada mediante **32 tests con Pytest** (unitarios, integración SQL, contratos HTTP, ventanas Tkinter en modo *Headless* y sincronización multi-cliente). Incorporación de una **Web SPA Responsive** que permite operar en simultáneo desde celulares y PCs en la red local reflejando los cambios al instante en todas las pantallas.


## 🚀 Ejecución y Entorno de Pruebas (Iteración 10 — Versión Final)

Para correr el sistema en su versión final desacoplada (**Iteración 10**), configurá el entorno virtual e instalá las dependencias del manifiesto. Al ejecutar `login.py`, el sistema inicializa automáticamente la base de datos (si no existe) y levanta en segundo plano tanto el servidor **API REST (puerto 8000)** como el **Servidor Web LAN (puerto 8080)**.

**Requisitos del Sistema:**

* Python 3.10 o superior instalado.

**1. Instalación y Puesta en Marcha:**

```
# Navegar a la iteración final del sistema
cd iteracion_10

# Crear y activar el entorno virtual aislado (Windows)
python -m venv .venv
.venv\Scripts\activate

# Instalar todas las dependencias (FastAPI, Uvicorn, Bcrypt, Pandas, Matplotlib, Requests, Pytest)
pip install -r requirements.txt

# (Opcional) Poblar la base de datos con 1000 productos y 500 facturas históricas para BI
python semillas/generador_semilla_bi.py

# Iniciar la aplicación de Escritorio y los servidores en segundo plano
python src/presentacion/escritorio/vistas/login.py

# Credenciales por defecto (Primer despliegue):
# Usuario: admin
# Clave: admin123
```

**2. Acceso desde el Navegador Web (PC y Dispositivos Móviles en Red Local):**

* **Desde la misma PC:** Abrir el navegador en `http://localhost:8080`.

* **Desde un Celular o Tablet conectado al mismo WiFi:** Consultar la dirección IPv4 de la PC ejecutando `ipconfig` en CMD (ej. `192.168.1.XX`) e ingresar desde el navegador móvil a `http://192.168.1.XX:8080`.

**3. Ejecución de la Suite de Pruebas Automatizadas (TDD):**

```
# Desde la carpeta iteracion_10 con el entorno virtual activo
pytest tests/ -v
```