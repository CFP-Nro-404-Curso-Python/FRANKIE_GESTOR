# 🏗️ Iteración 02: Estado en Memoria (CRUD Volátil), Eventos y Reglas de Negocio

## 📌 Resumen de la Iteración
En esta fase, la aplicación deja de ser una maqueta estática para convertirse en un **prototipo funcional en memoria RAM**. Se programó el comportamiento de los botones y se habilitó el flujo bidireccional de datos entre las cajas de texto (`tk.Entry`) y la grilla de visualización (`ttk.Treeview`). Desde la perspectiva del Análisis de Sistemas, acá establecemos el flujo lógico (Input -> Proceso -> Output) aislando la vista del controlador, aunque todavía sin atacar la capa de persistencia.

---

## ⚙️ Análisis Técnico y Lógica de Procesamiento

### 1. Manipulación del DOM en Tkinter (Treeview)
Se implementaron las funciones estructurales de un CRUD para operar directamente sobre la tabla visual:
*   **Create (`guardar`):** Captura los datos mediante el método `.get()` de las cajas Entry y los inyecta al final de la tabla usando `tabla.insert("", "end", values=(...))`.
*   **Update (`modificar`):** Verifica el índice de la fila seleccionada y sobrescribe la tupla de valores usando `tabla.item(seleccion[0], values=(...))`.
*   **Delete (`eliminar`):** Itera sobre las selecciones activas (soportando borrado múltiple por diseño) y las remueve con `tabla.delete(item)`.

### 2. Enrutamiento de Eventos (Event Binding)
*   Se resolvió la interactividad de la interfaz enlazando el evento nativo de selección de Tkinter (`<<TreeviewSelect>>`) con la función `seleccionar_fila`.
*   Esta función extrae los valores de la fila (`tabla.item(..., "values")`) y utiliza un bucle con `enumerate()` para limpiar e inyectar ordenadamente los datos de vuelta a las cajas `tk.Entry`, permitiendo su edición rápida. 

### 3. Implementación de Reglas de Negocio (Módulo Facturación)
El archivo `facturacion.py` empieza a destacarse como el nodo de procesamiento matemático del sistema:
*   **Cálculo por Línea:** Al guardar, se evalúa la operación aritmética `total_linea = (cantidad * valor) * (1 - (descuento / 100))` y se formatea la salida a dos decimales (`f"{total_linea:.2f}"`).
*   **Sincronización de Estado Global:** Se creó la función `actualizar_total_factura()`, la cual lee de forma agnóstica el estado actual del `Treeview` (iterando sobre `tabla.get_children()`), suma la columna de totales y actualiza dinámicamente el `Label` inferior. Es una excelente decisión aislar esta lógica para evitar desincronizaciones al modificar o eliminar filas.
*   **Manejo de Excepciones Básico:** Se envolvió la carga matemática en un bloque `try/except ValueError` para evitar que el programa crashee (lance una excepción fatal) si el usuario tipea letras en campos numéricos (como Cantidad o Valor). Sin embargo, la advertencia actual es un mero `print()` en consola.

---

## 🛠️ Evolución por Módulo

*   🧑‍💼 **Clientes (`clientes.py`):** Lógica CRUD completa en memoria. Sin control de tipos de datos.
*   👔 **Empleados (`empleados.py`):** Lógica CRUD completa en memoria. Sin control de tipos de datos.
*   🏢 **Proveedores (`proveedores.py`):** Lógica CRUD completa en memoria. Sin control de tipos de datos.
*   📦 **Stock (`stock.py`):** Lógica CRUD completa en memoria. Admite strings en campos que deberían ser numéricos (Stock, Precio).
*   🧾 **Facturación (`facturacion.py`):** Único módulo con *Type Casting* (`float()`), manejo de errores de valor (`ValueError`) y procesamiento de lógica de negocio en tiempo real.

---

## 🛑 Evaluación Crítica (Ojo de Analista)
Como analista, te marco las dos falencias sistémicas más graves de esta iteración:

1.  **Volatilidad Total de Datos (Amnesia del Sistema):**
    Toda la información se aloja en el árbol visual (`ttk.Treeview`). Al no existir una capa de persistencia (archivo físico o base de datos relacional), el ciclo de vida de los datos es idéntico al del proceso. Si el usuario cierra el programa (o hay un corte de energía), la pérdida de información es absoluta y catastrófica. 
2.  **Validación Asimétrica:**
    Mientras que el módulo de Facturación castea las variables a `float` y maneja errores, los módulos de Stock, Clientes y Empleados capturan todos los datos como `strings` por defecto (`.get()`). Esto significa que un usuario podría guardar "veinte" en la columna de Stock Mínimo sin que el sistema rechace la entrada.

**El próximo paso evolutivo es obligatorio:** Inyectar persistencia. Hay que sacar los datos de la memoria volátil y escribirlos permanentemente en el disco rígido (archivos CSV).