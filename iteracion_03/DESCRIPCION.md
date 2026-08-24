# 🏗️ Iteración 03: Persistencia de Datos y Sincronización en Archivos Planos (CSV)

## 📌 Resumen de la Iteración
En esta fase, la aplicación da el salto más crítico para cualquier sistema de gestión: **la cura contra la amnesia digital**. Dejamos atrás el prototipo volátil en memoria RAM e implementamos una capa de persistencia de datos utilizando archivos de texto plano separados por comas (CSV). Desde la óptica del Análisis de Sistemas, ahora el software tiene estado y durabilidad, garantizando que las operaciones de los usuarios sobrevivan al cierre de los procesos.

---

## ⚙️ Análisis Técnico y Decisiones de Arquitectura

### 1. Inyección de Módulos Nativos
*   Se importaron las librerías `csv` y `os` en la cabecera de los cinco módulos principales.
*   El uso del submódulo `os.path.exists()` es una excelente práctica defensiva: evita que el sistema lance un `FileNotFoundError` y crashee si el archivo `.csv` todavía no fue creado en la primera ejecución del programa.

### 2. Flujo de Inicialización (Lectura)
*   Se definió una constante global en cada módulo (ej. `ARCHIVO_CSV = "datos_clientes.csv"`). 
*   La función `cargar_datos_csv()` actúa como el motor de arranque: abre el archivo en modo lectura (`mode="r"`), itera sobre las filas y las inyecta en el widget `ttk.Treeview`. Esto convierte a la grilla visual en una representación exacta de la base de datos física al momento del despliegue.

### 3. Sincronización Destructiva (Escritura)
*   En lugar de buscar y modificar líneas específicas dentro del archivo de texto (lo cual es algorítmicamente costoso en Python puro sin librerías externas), optaste por un enfoque de **sincronización destructiva**.
*   La función `sobrescribir_csv()` abre el archivo en modo escritura (`mode="w"`), lo que borra todo su contenido previo, y vuelca iterativamente la "foto" actual del `Treeview`. 
*   **Acierto:** Al añadir `newline=""`, solucionaste el clásico bug de Windows donde el módulo CSV intercala filas en blanco entre los registros.

### 4. Integración al Ciclo CRUD
*   Las funciones operativas de la interfaz (`guardar`, `modificar`, `eliminar`) ahora operan en dos tiempos: primero actualizan el DOM visual (la tabla) y luego disparan la función `sobrescribir_csv()` de manera transparente (en background). 
*   Esta arquitectura asegura que lo que el usuario ve en pantalla es siempre lo que está guardado en el disco.

---

## 🛠️ Estado Actual de los Módulos

*   🧑‍💼 **Clientes (`clientes.py`):** Vinculado a `datos_clientes.csv`. Mantiene estado persistente.
*   👔 **Empleados (`empleados.py`):** Vinculado a `datos_empleados.csv`. Mantiene estado persistente.
*   🏢 **Proveedores (`proveedores.py`):** Vinculado a `datos_proveedores.csv`. Mantiene estado persistente.
*   📦 **Stock (`stock.py`):** Vinculado a `datos_stock.csv`. Mantiene estado persistente.
*   🧾 **Facturación (`facturacion.py`):** Vinculado a `datos_facturacion.csv`. Mantiene estado persistente y recalcula el Gran Total dinámicamente al leer los datos iniciales o modificar la tabla.

---

## 🛑 Evaluación Crítica (Ojo de Analista)
Lograste la persistencia, pero ahora tu sistema se enfrenta al problema de la **Fragmentación y Falta de Integridad Referencial**.

1.  **Silos de Información:** Tenés cinco bases de datos totalmente aisladas. Si en el módulo Facturación[cite: 50] el usuario tipea el nombre de un cliente que no existe en `datos_clientes.csv`, el sistema lo permite sin problemas. 
2.  **Entradas Libres Peligrosas:** Todos los campos de relación (ej. "Vendedor", "Cliente", "Producto" en Facturación; "Proveedor" en Stock) siguen siendo `tk.Entry`. Esto es una bomba de tiempo para la calidad de los datos, ya que da pie a errores de tipeo y desincronización.

**Próximo paso ineludible (Iteración 04):** Transformar esos campos clave en listas desplegables restrictivas (`ttk.Combobox`) y programar la lógica para que los módulos empiecen a leerse entre sí, cruzando los datos para garantizar la integridad referencial.