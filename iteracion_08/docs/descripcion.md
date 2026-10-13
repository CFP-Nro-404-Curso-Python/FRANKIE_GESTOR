# 🏗️ Iteración 08: Normalización Extrema, Borrado Lógico y Arquitectura Transaccional

## 📌 Resumen de la Iteración

Esta etapa representa el salto arquitectónico más profundo del proyecto. Abandonamos el modelo de tablas planas y redundantes para implementar un esquema de **Normalización Extrema** exigido por requerimientos académicos, adaptándolo a las capacidades de SQLite. El sistema ahora opera sobre un ecosistema altamente relacional con catálogos atomizados, tablas intermedias para relaciones Muchos a Muchos (N:M), delegación matemática al motor de base de datos y un blindaje estricto de auditoría mediante **Borrado Lógico (Soft Deletes)**.

---

## ⚙️ Análisis Técnico y Decisiones de Arquitectura

### 1. Centralización de Entidades y Catálogos Satélites

*   **Adiós a la Redundancia:** Se eliminaron las tablas aisladas de clientes, empleados y proveedores. Ahora existe una única tabla maestra `usuarios`. El tipo de usuario se define dinámicamente mediante la tabla puente `usuxroles`.

*   **Atomización de Datos:** Los textos libres (ciudades, mails, teléfonos, direcciones) se reemplazaron por catálogos independientes. Si 100 clientes son de "Berazategui", la palabra se guarda una sola vez en la tabla `ciudades` y se vincula mediante su ID. Esto erradica los errores de tipeo y optimiza el almacenamiento a costa de mayor complejidad transaccional.

### 2. Transacciones Escalonadas (El Helper `obtener_o_crear`)

*   Dado el nuevo nivel de normalización, guardar un cliente ya no es un simple `INSERT`. El backend de Python (Tkinter) debió refactorizarse para manejar **Transacciones Escalonadas**.

*   Se desarrolló la función `obtener_o_crear(cursor, tabla, columna, valor)` que busca si un dato satélite ya existe; si existe recupera su ID, y si no, lo inserta. Gracias a esto, un solo clic en "Guardar" dispara una cascada coordinada de hasta 10 sentencias SQL sin perder la integridad referencial.

### 3. Borrado Lógico y Blindaje Físico (Hard Delete Lock)

*   **Implementación de `habilitado`:** Se inyectó la columna `habilitado INTEGER DEFAULT 1` en todas las tablas. Las operaciones de "Eliminar" en la interfaz gráfica ahora ejecutan un `UPDATE tabla SET habilitado = 0`, preservando el historial para auditoría contable.

*   **Seguridad a Nivel Motor:** Para garantizar que ni un error de código ni un ataque por inyección destruyan datos, se programaron `TRIGGERS BEFORE DELETE` directamente en SQLite. Si alguien intenta ejecutar un `DELETE` real, la base de datos aborta la transacción instantáneamente lanzando una excepción `RAISE(ABORT)`.

### 4. Delegación Lógica al Motor SQL (Views y Computed Columns)

*   **Desacoplamiento con Vistas:** Reconstruir un empleado requería un `JOIN` de 12 tablas. Para no contaminar el backend de Python con esta lógica pesada, se creó la vista precompilada `vista_empleados_activos` en la base de datos. Python simplemente ejecuta `SELECT * FROM vista_empleados_activos`.

*   **Campos Autocalculados:** El cálculo del "Total" en facturación se eliminó del código Python. Ahora SQLite utiliza la cláusula `GENERATED ALWAYS AS ((cantidad * valor) * (1 - (descuento / 100.0))) STORED`, calculando y almacenando el valor automáticamente a nivel motor.

### 5. RBAC y Auditoría de Identidad

*   Al separar el frontend en la carpeta `/vistas`, el sistema de navegación mejoró. `panel_control.py` ahora captura y propaga el `id_usuario` físico a todos los módulos hijos.
 
*   Esto permitió tapar una brecha lógica de seguridad: ahora el sistema impide activamente que un Gerente se despida a sí mismo (auto-borrado) o escale sus propios privilegios.

---

## 🛑 Evaluación Crítica

El diseño implementado en esta iteración responde fielmente a los estándares de **Tercera Forma Normal (3FN)** y requerimientos pedagógicos de diseño de bases de datos. Sin embargo, desde una óptica pragmática de ingeniería de software, presenta un nivel de **sobreingeniería** para el contexto de una aplicación de escritorio.

Fragmentar una simple dirección postal en 5 tablas puente distintas genera un overhead computacional inmenso: el motor SQLite se ve obligado a procesar docenas de `JOINs` masivos solo para mostrar la grilla principal de la interfaz. 

A pesar de este costo de rendimiento (que en SQLite local es casi imperceptible, pero en red sería un cuello de botella), el beneficio arquitectónico es innegable: **la base de datos ahora es indestructible**. Las reglas de negocio, los cálculos de facturación, la prevención de borrado y la integridad geográfica residen en el motor. Si el día de mañana se decide descartar Python (Tkinter) y reescribir el frontend en formato Web o Móvil, la base de datos `frankie_gestor.db` funcionará perfectamente sin necesidad de reescribir ni una sola regla de validación.