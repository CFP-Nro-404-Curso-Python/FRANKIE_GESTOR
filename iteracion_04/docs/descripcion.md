# 🏗️ Iteración 04: Integridad Referencial, Motor Transaccional y Validaciones Cruzadas

## 📌 Resumen de la Iteración
Acá es donde el sistema deja de ser una simple agenda y se convierte en un **verdadero software de gestión comercial**. En esta iteración, abandonamos los "silos de información" y conectamos los módulos entre sí para lograr la integridad referencial que nos faltaba. Fabricamos "a mano" el comportamiento de una base de datos relacional sobre archivos planos (CSV), controlando el inventario en tiempo real, bloqueando el error humano y estableciendo un manejo estricto de las excepciones mediante interfaces gráficas (Pop-ups). 

---

## ⚙️ Análisis Técnico y Decisiones de Arquitectura

### 1. Eliminación del Error Humano (Data Binding)
*   **Adiós al texto libre:** Los campos críticos que actúan como "claves foráneas" (Proveedor en Stock; Vendedor, Cliente y Producto en Facturación) pasaron de ser `tk.Entry` a `ttk.Combobox` con el parámetro `state="readonly"`. 
*   **Lectura de Maestros:** Se programaron funciones de extracción (`obtener_proveedores`, `obtener_clientes`, etc.) que leen los CSVs maestros en el arranque y pueblan estas listas desplegables, garantizando que el usuario solo pueda elegir entidades que realmente existen en el sistema.

### 2. Eventos Asíncronos y Autocompletado
*   Se enlazó el evento `<<ComboboxSelected>>` al menú de Productos en la ventana de Facturación.
*   Al elegir un ítem, la función `autocompletar_precio()` busca el código en el inventario físico, inyecta el "Precio de Venta" oficial y **bloquea la caja** pasándola a `readonly`. Esto anula la posibilidad de que el cajero manipule el precio unitario de forma manual o fraudulenta.

### 3. Motor Transaccional y Control de Stock (El Core del Sistema)
El módulo de Facturación ahora actúa como el "cerebro" orquestador mediante la función `gestionar_stock()`:
*   **Deducción Dinámica:** Al guardar una factura, el sistema va silenciosamente a `datos_stock.csv`, busca el código y resta la cantidad vendida.
*   **Restitución:** Al eliminar una fila de la factura, el sistema suma la cantidad y devuelve los productos a la estantería virtual.
*   **Rollback Lógico (Modificación):** Modificar un registro es la operación más crítica. El algoritmo primero devuelve el stock viejo; luego intenta restar el stock nuevo. Si la nueva cantidad solicitada supera el inventario disponible, el sistema hace un *rollback* (deshace el primer paso) y aborta la transacción para no corromper los datos.

### 4. Manejo Visual de Excepciones (UX/UI)
*   Se erradicaron los fantasmales `print()` en consola. Se implementó el submódulo `tkinter.messagebox`.
*   **Barreras Duras (`showerror`):** Frena operaciones no válidas como ingresos de letras en campos numéricos, descuentos mayores al 100%, o intentos de vender sin stock suficiente.
*   **Alertas Tempranas (`showwarning`):** Al procesar un descuento de inventario, si el stock actual perfora el "Stock Mínimo" parametrizado, el sistema permite la venta pero arroja una "Alerta de Reposición" amarilla para notificar al usuario.

### 5. Consolidación de Rutas Cruzadas (Cohesión Espacial)
*   Al confinar todos los archivos `.csv` en un directorio unificado, las operaciones de lectura cruzada (ej. Facturación leyendo el maestro de Stock) corrían riesgo de fallar si se ejecutaban desde distintos contextos.
*   Se implementó la declaración temprana de **verdaderas rutas absolutas dinámicas** ancladas al script mediante `os.path.dirname(os.path.abspath(__file__))`. Al combinar esto con `os.path.join()` en las cabeceras operativas (`RUTA_EMPLEADOS`, `RUTA_STOCK`, etc.), se garantiza la cohesión espacial de los datos. Esto asegura que el sistema siempre encuentre los archivos maestros, independientemente de cuál sea el Directorio de Trabajo Actual (CWD) del sistema operativo.

---

## 🛠️ Estado Actual de los Módulos

*   🧑‍💼 **Clientes (`clientes.py`):** Actúa como maestro de datos. Totalmente estable y persistente.
*   👔 **Empleados (`empleados.py`):** Actúa como maestro de datos. Totalmente estable y persistente.
*   🏢 **Proveedores (`proveedores.py`):** Actúa como maestro de datos. Totalmente estable y persistente.
*   📦 **Stock (`stock.py`):** Integrado. Lee proveedores dinámicamente. Lógica de limpieza de cajas ajustada para soportar Comboboxes de solo lectura mediante el método `.set()`.
*   🧾 **Facturación (`facturacion.py`):** Nodo central de integración. Realiza validaciones matemáticas cruzadas, gestiona el archivo físico de stock en segundo plano y despliega interfaces de alerta.

---

## 🛑 Evaluación Crítica
Se logró exprimir al máximo las capacidades de los archivos planos (CSV). El sistema es robusto, valida límites lógicos, bloquea ingresos anómalos y mantiene el inventario al día. Cumple al 100% con los requerimientos de un trabajo académico.

Sin embargo, acá está el límite del pragmatismo. **En un entorno de producción real, este diseño es altamente ineficiente e inseguro**. Abrir, iterar, reescribir y cerrar archivos de texto múltiples veces por cada click en la interfaz genera un cuello de botella enorme y no soporta concurrencia (dos vendedores facturando al mismo tiempo destruirían el archivo `datos_stock.csv`). 

El próximo y último paso evolutivo para que este proyecto pase de ser un "prototipo académico" a un "producto de grado empresarial" es **migrar la persistencia a un motor de base de datos relacional puro (como SQLite o PostgreSQL)**, delegando la integridad referencial y las operaciones ACID al motor en lugar de programarlas a mano en Python.