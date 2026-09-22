# 🛒 Sistema de Gestión Comercial en Python (Tkinter)

**Centro de Formación Profesional N° 404**  
**Alumno:** David Hernan Bravo  

---

## 📌 Descripción del Proyecto

Este repositorio contiene el desarrollo progresivo de una aplicación de escritorio para la gestión comercial (Clientes, Empleados, Proveedores, Stock y Facturación). El proyecto está estructurado en iteraciones evolutivas, demostrando cómo un sistema crece desde un esqueleto visual estático hasta convertirse en un nodo transaccional funcional con persistencia de datos relacional (SQLite) y validaciones de negocio complejas.

---

## 📂 Estructura del Proyecto e Iteraciones

El desarrollo se divide en seis etapas incrementales. Cada carpeta contiene el código fuente de la iteración y su respectivo análisis técnico detallado en el archivo `descripcion.md`.

| Iteración | Foco del Desarrollo | Análisis Detallado |
| :--- | :--- | :--- |
| **Iteración 0** | Esqueleto arquitectónico, jerarquía de Toplevels y sistema de navegación. | [📖 Ver descripcion.md](./iteracion_00/docs/descripcion.md) |
| **Iteración 1** | Maquetado de Interfaz de Usuario (UI), Layouts y grillas Treeview. | [📖 Ver descripcion.md](./iteracion_01/docs/descripcion.md) |
| **Iteración 2** | Lógica CRUD en memoria RAM (volátil), DOM de Tkinter y manejo de eventos. | [📖 Ver descripcion.md](./iteracion_02/docs/descripcion.md) |
| **Iteración 3** | Persistencia mediante archivos planos (CSV) y sincronización destructiva. | [📖 Ver descripcion.md](./iteracion_03/docs/descripcion.md) |
| **Iteración 4** | Integridad referencial cruzada entre CSVs, motor transaccional simulado y manejo de excepciones visuales. | [📖 Ver descripcion.md](./iteracion_04/docs/descripcion.md) |
| **Iteración 5** | Migración definitiva a motor relacional (SQLite3), identificadores ocultos (IID), operaciones ACID y anclaje estricto de rutas. | [📖 Ver descripcion.md](./iteracion_05/docs/descripcion.md) |
| **Iteración 6** | Ecosistema centralizado, Autenticación (Login), Seguridad RBAC, Consola SQL (Sandboxing) y Backups. | [📖 Ver descripcion.md](./iteracion_06/docs/descripcion.md) |

> 💡 **Nota sobre la Persistencia:** A partir de la Iteración 3, el sistema encapsula sus datos. Las iteraciones 3 y 4 generan y consumen archivos `.csv` alojados en una carpeta `/persistencia`. Las **Iteraciones 5 y 6** automatizan la creación de un directorio estricto `/db` donde compilan la base de datos relacional `frankie_gestor.db`. La **Iteración 6** suma además un directorio `/backups` autogestionado.

---

## 🛠️ Evolución y Análisis Técnico

El enfoque principal de este proyecto es evidenciar el análisis crítico y la escalabilidad detrás de cada decisión de programación:

* **Mitigación de Acoplamiento (Lazy Imports):** Se evitó el clásico error de *Circular Import* cargando los submódulos de la interfaz únicamente en memoria local al momento de ser requeridos por la interacción del usuario, reduciendo el tiempo de arranque a cero.
* **Del Texto Libre a la Restricción:** Evolución clara desde el uso de simples `tk.Entry` (propensos a errores de tipeo humano) hacia menús `ttk.Combobox` en estado `readonly`, garantizando que el operador solo procese entidades validadas y preexistentes en los maestros.
* **Gestión de Claves Primarias (IID Oculto):** En lugar de exponer un ID de base de datos visualmente al usuario (un antipatrón UI), el sistema inyecta la Primary Key de SQLite en el parámetro interno `iid` del Treeview de Tkinter. Esto permite apuntar sentencias `UPDATE` y `DELETE` con precisión milimétrica sin ensuciar la interfaz gráfica.
* **Experiencia de Usuario (UX) Defensiva:** Erradicación de errores silenciosos en consola mediante la implementación estricta del módulo `tkinter.messagebox`. El sistema despliega alertas preventivas (stock mínimo perforado) y bloqueos duros (intentos de vender sin disponibilidad o con formatos inválidos).
* **Anclaje Dinámico de Directorios:** Uso de `os.path.dirname(os.path.abspath(__file__))` para garantizar que el sistema encuentre siempre la base de datos independientemente de la ruta desde la cual la consola de comandos haya ejecutado el script.
* **Arquitectura de Seguridad (RBAC):** Implementación de un flujo de acceso cerrado. El sistema arranca desde un Login que inyecta los privilegios del usuario (Administrador, Gerente, Empleado) a un Panel de Control central, limitando dinámicamente la interfaz gráfica y bloqueando transacciones no autorizadas en el backend para prevenir ataques de escalada de privilegios.
* **Sandboxing SQL y Auditoría:** Desarrollo de una consola de ejecución aislada con filtros de expresiones regulares (Regex) que bloquea sentencias destructivas (`DELETE`, `UPDATE`, `DROP`) e inyecta límites de paginación forzados para proteger la memoria, permitiendo realizar consultas de lectura en tiempo real de forma segura.

---

## 🚀 Ejecución y Entorno de Pruebas

Para correr el sistema en su versión final y más estable, cloná el repositorio, abrí tu terminal y ejecutá el módulo de seguridad de la Iteración 6. Por convención arquitectónica, el archivo `login.py` actúa ahora como el nodo raíz (Parent) que orquesta la carga en memoria del `panel_control.py` y despliega los demás submódulos de forma perezosa (Lazy Import) según los permisos del usuario activo.

**Requisitos del Sistema:**
* Python 3.x instalado.
* Librerías nativas (`tkinter`, `sqlite3`, `csv`, `os`, `re`, `shutil`) habilitadas en el entorno. **No requiere base de datos externa ni instalaciones vía pip.**

**Instrucciones por Terminal:**
```bash
# Navegar a la versión definitiva del sistema
cd iteracion_06

# Ejecutar el nodo raíz de seguridad
python login.py

# Credenciales por defecto (Primer despliegue):
# Usuario: admin
# Clave: admin123