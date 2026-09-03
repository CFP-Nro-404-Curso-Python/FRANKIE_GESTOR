# 🚀 Iteración 05: Migración a SQLite, Identificadores Ocultos y Anclaje de Rutas Absolutas

## 📌 Resumen de la Iteración
El sistema evolucionó de un prototipo basado en archivos planos (CSV) a una arquitectura cliente-servidor embebida con **SQLite**. Se eliminó la sincronización destructiva (borrar y reescribir todo un archivo ante cada cambio) para dar paso a un motor transaccional real que soporta operaciones atómicas. Toda la persistencia de datos ahora se concentra en un único archivo binario relacional (`frankie_gestor.db`) alojado en el directorio estricto `/db`.

---

## ⚙️ Análisis Técnico y Decisiones de Arquitectura

### 1. Migración al Motor Relacional (SQLite3)
*   **Abandono de CSV:** Se eliminó el uso del módulo `csv`. La persistencia ahora recae sobre sentencias DDL (`CREATE TABLE`) y DML (`INSERT`, `UPDATE`, `DELETE`, `SELECT`).
*   **Consultas Parametrizadas:** Toda la interacción con la base de datos se realiza mediante paso de parámetros `(?, ?, ?)` en el objeto `cursor`, blindando al sistema contra ataques de Inyección SQL.

### 2. Gestión de Claves Primarias (IID Oculto)
*   **Problema de Diseño UI:** Exponer IDs autoincrementales al usuario final es un antipatrón. 
*   **Solución Técnica:** Se inyecta el campo `id` de SQLite directamente en el parámetro interno `iid` del widget `Treeview` de Tkinter. El usuario interactúa visualmente con la fila, pero el sistema captura el `iid` por detrás para ejecutar los `UPDATE` y `DELETE` con precisión milimétrica sobre la Clave Primaria correcta.

### 3. Anclaje Dinámico de Directorios (Pathing Estricto)
*   **Prevención de Errores de Contexto:** Ejecutar el programa desde distintas terminales o accesos directos solía crear carpetas en directorios equivocados.
*   **Refactorización:** Se implementó `os.path.dirname(os.path.abspath(__file__))`. Esta instrucción obliga a la aplicación a construir la carpeta `/db` y buscar el archivo `frankie_gestor.db` exactamente en la misma ruta absoluta donde residen los scripts de Python.

### 4. Lectura Cruzada Eficiente (Facturación y Stock)
*   En lugar de abrir múltiples archivos de texto, la integración entre módulos ahora se resuelve con consultas SQL directas (`SELECT razon_social FROM proveedores`, `SELECT precio_venta FROM stock WHERE codigo=?`). El motor de base de datos se encarga de la búsqueda y devuelve únicamente el dato necesario.

---

## 🛠️ Estado Definitivo de los Módulos

*   🧑‍💼 **Clientes (`clientes.py`):** DDL y DML estructurados. Operaciones atómicas por ID oculto.
*   👔 **Empleados (`empleados.py`):** DDL y DML estructurados. Operaciones atómicas por ID oculto.
*   🏢 **Proveedores (`proveedores.py`):** DDL y DML estructurados. Operaciones atómicas por ID oculto.
*   📦 **Stock (`stock.py`):** Integra lectura SQL a la tabla de `proveedores` para poblar el Combobox dinámicamente.
*   🧾 **Facturación (`facturacion.py`):** Nodo orquestador. Ejecuta validaciones dinámicas y dispara sentencias `UPDATE` sobre la tabla `stock` para deducir o restituir inventario en tiempo real.

---

## 🛑 Evaluación Crítica y Cierre del Proyecto
Con esta iteración, el desarrollo alcanza un estándar técnico profesional. Pasamos de manejar cadenas de texto frágiles a delegar la integridad de los datos en un motor ACID (Atomicidad, Consistencia, Aislamiento y Durabilidad). 

El uso del `iid` en Tkinter demuestra madurez en la separación entre la Vista (lo que ve el usuario) y el Modelo (lo que procesa la base de datos). El sistema es escalable, cohesivo y está listo para ser compilado en un ejecutable final para producción.