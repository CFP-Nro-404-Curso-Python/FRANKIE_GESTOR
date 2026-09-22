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
| **Iteración 3** | Persistencia mediante archivos planos (CSV) y sincronización destructiva. | [📖 Ver descripcion.md](./iteracion_03/descripcion.md) |
| **Iteración 4** | Integridad referencial cruzada entre CSVs, motor transaccional simulado y manejo de excepciones visuales. | [📖 Ver descripcion.md](./iteracion_04/descripcion.md) |
| **Iteración 5** | Migración definitiva a motor relacional (SQLite3), identificadores ocultos (IID), operaciones ACID y anclaje estricto de rutas. | [📖 Ver descripcion.md](./iteracion_05/descripcion.md) |

> 💡 **Nota sobre la Persistencia:** A partir de la Iteración 3, el sistema encapsula sus datos. Las iteraciones 3 y 4 generan y consumen archivos `.csv` alojados en una carpeta `/persistencia`. La **Iteración 5** (versión definitiva) automatiza la creación de un directorio estricto `/db` donde compila la base de datos relacional `frankie_gestor.db`.

---

## 🛠️ Evolución y Análisis Técnico

El enfoque principal de este proyecto es evidenciar el análisis crítico y la escalabilidad detrás de cada decisión de programación:

* **Mitigación de Acoplamiento (Lazy Imports):** Se evitó el clásico error de *Circular Import* cargando los submódulos de la interfaz únicamente en memoria local al momento de ser requeridos por la interacción del usuario, reduciendo el tiempo de arranque a cero.
* **Del Texto Libre a la Restricción:** Evolución clara desde el uso de simples `tk.Entry` (propensos a errores de tipeo humano) hacia menús `ttk.Combobox` en estado `readonly`, garantizando que el operador solo procese entidades validadas y preexistentes en los maestros.
* **Gestión de Claves Primarias (IID Oculto):** En lugar de exponer un ID de base de datos visualmente al usuario (un antipatrón UI), el sistema inyecta la Primary Key de SQLite en el parámetro interno `iid` del Treeview de Tkinter. Esto permite apuntar sentencias `UPDATE` y `DELETE` con precisión milimétrica sin ensuciar la interfaz gráfica.
* **Experiencia de Usuario (UX) Defensiva:** Erradicación de errores silenciosos en consola mediante la implementación estricta del módulo `tkinter.messagebox`. El sistema despliega alertas preventivas (stock mínimo perforado) y bloqueos duros (intentos de vender sin disponibilidad o con formatos inválidos).
* **Anclaje Dinámico de Directorios:** Uso de `os.path.dirname(os.path.abspath(__file__))` para garantizar que el sistema encuentre siempre la base de datos independientemente de la ruta desde la cual la consola de comandos haya ejecutado el script.

---

## 🚀 Ejecución y Entorno de Pruebas

Para correr el sistema en su versión final y más estable, cloná el repositorio, abrí tu terminal y ejecutá el módulo principal de la Iteración 5. Por convención arquitectónica, el archivo `clientes.py` actúa como la ventana raíz (Parent) de la aplicación, aunque los módulos secundarios (`facturacion.py`, `stock.py`) son independientes gracias a su diseño modular.

**Requisitos del Sistema:**
* Python 3.x instalado.
* Librerías nativas (`tkinter`, `sqlite3`, `csv`, `os`) habilitadas en el entorno. **No requiere base de datos externa ni instalaciones vía pip.**

**Instrucciones por Terminal:**
```bash
# Navegar a la versión definitiva del sistema
cd iteracion_05

# Ejecutar el nodo principal del programa
python clientes.py