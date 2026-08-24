# 🛒 Sistema de Gestión Comercial en Python (Tkinter)

**Centro de Formación Profesional N° 404**  
**Alumno:** David Hernan Bravo  

---

## 📌 Descripción del Proyecto

Este repositorio contiene el desarrollo progresivo de una aplicación de escritorio para la gestión comercial (Clientes, Empleados, Proveedores, Stock y Facturación). El proyecto está estructurado en iteraciones evolutivas, demostrando cómo un sistema crece desde un esqueleto visual estático hasta convertirse en un nodo transaccional funcional con persistencia de datos y validaciones de negocio complejas.

---

## 📂 Estructura del Proyecto e Iteraciones

El desarrollo se divide en cinco etapas incrementales. Cada carpeta contiene el código fuente de la iteración y su respectivo análisis técnico detallado en el archivo `DESCRIPCION.md`.

| Iteración | Foco del Desarrollo | Análisis Detallado |
| :--- | :--- | :--- |
| **Iteración 0** | Esqueleto arquitectónico, jerarquía de Toplevels y sistema de navegación. | [📖 Ver DESCRIPCION.md](./iteracion_00/DESCRIPCION.md) |
| **Iteración 1** | Maquetado de Interfaz de Usuario (UI), Layouts y grillas Treeview. | [📖 Ver DESCRIPCION.md](./iteracion_01/DESCRIPCION.md) |
| **Iteración 2** | Lógica CRUD en memoria RAM (volátil), DOM de Tkinter y manejo de eventos. | [📖 Ver DESCRIPCION.md](./iteracion_02/DESCRIPCION.md) |
| **Iteración 3** | Persistencia de datos mediante sincronización destructiva de archivos planos (CSV). | [📖 Ver DESCRIPCION.md](./iteracion_03/DESCRIPCION.md) |
| **Iteración 4** | Integridad referencial cruzada, motor transaccional, control de stock y manejo de excepciones visuales. | [📖 Ver DESCRICION.md](./iteracion_04/DESCRIPCION.md) |

> 💡 **Nota sobre los archivos `.csv`:** Las bases de datos planas generadas durante las pruebas de integración residen en el directorio raíz. Son estrictamente necesarias para el correcto funcionamiento de las **Iteraciones 3 y 4**, ya que alimentan los menús desplegables maestros y mantienen el estado físico del inventario.

---

## 🛠️ Evolución y Análisis Técnico

El enfoque principal de este proyecto es evidenciar el análisis crítico y la escalabilidad detrás de cada decisión de programación:

* **Mitigación de Acoplamiento (Lazy Imports):** Se evitó el clásico error de *Circular Import* cargando los submódulos de la interfaz únicamente en memoria local al momento de ser requeridos por la interacción del usuario.
* **Del Texto Libre a la Restricción:** Evolución clara desde el uso de simples `tk.Entry` (propensos a errores de tipeo humano) hacia menús `ttk.Combobox` en estado `readonly`, garantizando que el operador solo procese entidades validadas y preexistentes en los maestros.
* **Motor Transaccional "Manual":** Se simuló el comportamiento de una base de datos relacional utilizando Python puro. El módulo de facturación orquesta lecturas y escrituras cruzadas, deducción de inventario en tiempo real, e incluso lógica de *Rollback* en caso de que una modificación de factura exija más stock del físicamente disponible.
* **Experiencia de Usuario (UX) Defensiva:** Erradicación de errores silenciosos en consola mediante la implementación estricta del módulo `tkinter.messagebox`. El sistema despliega alertas preventivas (stock mínimo perforado) y bloqueos duros (intentos de vender sin disponibilidad o con formatos inválidos).

---

## 🚀 Ejecución y Entorno de Pruebas

Para correr el sistema, cloná el repositorio, abrí tu terminal y ejecutá el módulo principal de la iteración que desees auditar. Por convención arquitectónica, el archivo `clientes.py` actúa como la ventana raíz (Parent) de la aplicación, aunque los módulos secundarios (`facturacion.py`, `stock.py`) son completamente independientes gracias a su diseño modular.

**Requisitos del Sistema:**
* Python 3.x instalado.
* Librerías nativas (`tkinter`, `csv`, `os`) habilitadas en el entorno (no requiere `pip install`).

**Instrucciones por Terminal:**
```bash
# Navegar a la última iteración
cd iteracion_4

# Ejecutar el nodo principal del programa
python clientes.py