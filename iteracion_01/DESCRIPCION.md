# 🏗️ Iteración 01: Maquetado de Interfaz de Usuario (UI) y Formularios de Registro

## 📌 Resumen de la Iteración
En esta etapa, dejamos atrás el esqueleto básico y le damos volumen visual al sistema. La iteración se enfoca exclusivamente en el **maquetado de los formularios de carga de datos (UI)** y la estructuración de las grillas de visualización. Desde la óptica del Análisis de Sistemas, acá estamos definiendo el "contrato visual" con el usuario, estableciendo qué datos le vamos a pedir y cómo se los vamos a mostrar, aunque la capa lógica (backend/persistencia) todavía esté desconectada.

---

## ⚙️ Análisis Técnico y Decisiones de Diseño

### 1. Reestructuración Geométrica
*   **Adaptación al contenido:** Notaste que el tamaño inicial de `550x550` era insuficiente para la cantidad de datos requeridos en los módulos maestros. Por ende, las ventanas de Clientes, Empleados, Proveedores y Stock se redimensionaron a `1005x550` píxeles. 
*   **Excepción controlada:** El módulo de Facturación se ajustó a `550x600`, una decisión coherente dado que su diseño es más vertical por la calculadora inferior.

### 2. Implementación de Formularios de Entrada (Inputs)
*   En todos los módulos se implementó un sistema de grilla bidimensional (`grid`) alineando etiquetas (`tk.Label`) en la columna 0 y cajas de texto (`tk.Entry`) en la columna 1.
*   **Abstracción visual:** Se prepararon las interfaces para las cuatro operaciones fundamentales de un CRUD (Create, Read, Update, Delete) añadiendo los botones de *Guardar*, *Modificar* y *Eliminar*. Sin embargo, carecen de parámetros `command=`, por lo que actualmente son elementos estáticos (mockups).

### 3. Integración del Componente de Visualización (Data Grid)
*   Se introdujo el widget avanzado `ttk.Treeview` en todos los archivos. 
*   Se configuraron las cabeceras de columnas iterando sobre tuplas de strings, asignando un ancho estándar de 100 píxeles por columna y parametrizando `show="headings"` para una apariencia de tabla limpia y tabular.

---

## 🛠️ Detalle Paramétrico por Módulo

*   🧑‍💼 **Clientes (`clientes.py`):** Despliega 10 campos de ingreso. Incluye datos demográficos y de contacto (Nombres, Apellidos, DNI, Edad, Teléfono, Email, Domicilio, Ciudad, Provincia, Código Postal).
*   👔 **Empleados (`empleados.py`):** Configurado con 10 campos. A los datos personales básicos se le suma la carga corporativa (Legajo, Cargo, Sector, Sueldo).
*   🏢 **Proveedores (`proveedores.py`):** Presenta 10 campos orientados a entidades comerciales (Razón Social, CUIT, Rubro, Contacto, además de los datos de localización).
*   📦 **Stock (`stock.py`):** Estructurado con 10 variables logísticas y financieras (Código, Descripción, Categoría, Proveedor, Stock Actual, Stock Mínimo, Precio Costo, Precio Venta, Ubicación, Vencimiento).
*   🧾 **Facturación (`facturacion.py`):** Maqueta la cabecera de la factura (Vendedor, Cliente), el detalle de línea (Producto, Cantidad, Valor en $, Descuento) y un pie de página dedicado a una "Calculadora de Descuentos" global.

---

## 🛑 Evaluación Crítica (Ojo de Analista)
Como tu mentor, te aplaudo el orden lógico de la interfaz, pero te levanto una bandera roja enorme a nivel arquitectura: **Absolutamente todos los inputs son `tk.Entry` de texto libre**. 

En Análisis de Sistemas, permitir texto libre en campos que requieren validación numérica (Sueldo, DNI, Stock) o en campos que actúan como claves foráneas relacionales (Proveedor, Cliente, Producto) es la receta perfecta para corromper la integridad de tus datos. Un usuario podría escribir "diez" en lugar de "10" en el campo Cantidad, o errar al tipear el CUIT del Proveedor. 

**Próximo paso ineludible:** Esta iteración es un "cascarón vacío". El siguiente objetivo debe ser inyectar la persistencia de datos (conectar este front-end a archivos CSV o una base de datos) y empezar a escribir las funciones internas (`def guardar()`, `def modificar()`) para que el sistema cobre vida.