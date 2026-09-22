# 🏗️ Iteración 00: Esqueleto Arquitectónico y Sistema de Navegación

## 📌 Resumen de la Iteración
Esta iteración representa el **cómputo cero** del desarrollo. No hay lógica de negocio, no hay persistencia de datos y no hay formularios. Es estrictamente el **esqueleto de navegación** intermodular basado en la librería gráfica `tkinter`. Desde la perspectiva del Análisis de Sistemas, establecer el mapa de enrutamiento antes de inyectar variables de estado es una decisión pragmática para garantizar la escalabilidad y aislar los componentes.

---

## ⚙️ Análisis Técnico del Código

### 1. Jerarquía de Ventanas (Root vs Toplevel)
El sistema implementa un diseño de ventana primaria con subventanas dependientes:
*   **`clientes.py` (Módulo Raíz):** Instancia el objeto principal `tk.Tk()` y ejecuta el `mainloop()`. Actúa como el punto de entrada y proceso padre de la aplicación.
*   **Módulos Secundarios (`empleados.py`, `proveedores.py`, `stock.py`, `facturacion.py`):** Instancian objetos `tk.Toplevel()` pasándoles el argumento `parent`. Al heredar la raíz, se garantiza que si el sistema se cierra desde clientes, la destrucción en cascada limpie todas las ventanas hijas de la memoria.

### 2. Prevención de Importaciones Circulares (Lazy Imports)
Uno de los mayores aciertos de esta base estructural es la mitigación del acoplamiento.
*   La importación de los submódulos se realiza **exclusivamente dentro del scope de las funciones** que disparan los botones (por ejemplo, `from empleados import Empleado` dentro de `abrir_empleados()`).
*   Este patrón evita un error crítico de *Circular Import* (donde dos archivos intentan leerse mutuamente antes de inicializarse), logrando que el intérprete de Python cargue el módulo en memoria RAM solo ante el requerimiento explícito del usuario. Eficiencia pura.

### 3. Manejo de Focos y Superposición
*   Para retornar a la ventana de Clientes desde cualquier módulo secundario, el código no comete el error de volver a instanciar la clase (lo que generaría un bucle de ventanas superpuestas y una inminente fuga de memoria).
*   En su lugar, emplea los métodos `parent.lift()` y `parent.focus_force()` para traer el proceso original al primer plano del sistema operativo.

---

## 🛠️ Estructura de Archivos Actual

*   📄 **`clientes.py`**: Interfaz raíz seteada en `400x300` píxeles. Posee únicamente los cuatro botones de navegación mediante el método `.grid()`.
*   📄 **`empleados.py`**: Clase `Empleado` (Toplevel) seteada en `400x300` píxeles.
*   📄 **`proveedores.py`**: Clase `Proveedor` (Toplevel) seteada en `400x300` píxeles.
*   📄 **`stock.py`**: Clase `Stock` (Toplevel) seteada en `400x300` píxeles.
*   📄 **`facturacion.py`**: Clase `Facturacion` (Toplevel) seteada en `400x300` píxeles.

---