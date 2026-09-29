# 🗺️ Mapa de Ruta - Iteración 08: Refactorización a Normalización Extrema

## Fase 1: Arquitectura de Base de Datos
*   **Paso 1.1:** Creación del archivo `esquema.sql`. Traducción y adaptación del modelo relacional de la cátedra (MySQL) a la sintaxis estricta de SQLite, eliminando referencias circulares y definiendo las jerarquías de claves foráneas.
*   **Paso 1.2:** Modificación del módulo `login.py`. Eliminar las antiguas funciones DDL en código Python e implementar un motor de inicialización que lea, parsee y ejecute el archivo `esquema.sql` en el primer arranque del sistema.

## Fase 2: Unificación del Core (Usuarios y Roles)
*   **Paso 2.1:** Refactorización de `usuarios.py`. Adaptar la interfaz y las funciones CRUD para que alimenten simultáneamente las tablas maestras de datos personales y la tabla puente `usuxroles`.
*   **Paso 2.2:** Integración de Bajas Lógicas. Reemplazar todas las sentencias `DELETE` por sentencias `UPDATE habilitado = 0` en la lógica de eliminación.

## Fase 3: Gestión de Ubicaciones y Contactos (Atomización)
*   **Paso 3.1:** Creación de lógica transaccional en Python. Al guardar un usuario nuevo, el sistema deberá evaluar e insertar datos en cascada: buscar/crear país, buscar/crear provincia, ciudad, dirección, etc., recolectando los `LAST_INSERT_ID` para poblar las tablas `usuarioxubicaciones` y `usuarioxcontactos`.
*   **Paso 3.2:** Reescritura de los módulos `clientes.py`, `empleados.py` y `proveedores.py`. Como ahora todos son "usuarios", estas ventanas dejarán de tener bases de datos aisladas y pasarán a ser "Vistas Filtradas" (JOINs) que interactúan con la gran tabla central `usuarios` según su rol.

## Fase 4: Refactorización de Inventario (Productos)
*   **Paso 4.1:** Adaptación de `stock.py`. Implementar las tablas de categorización propuestas por la cátedra (`estados`, `ubicaciones`, `productoxestados`, `productoxubicaciones`).
*   **Paso 4.2:** Enlazar el campo `id_proveedor` del producto directamente con un registro de la nueva tabla unificada `usuarios` (filtrado por rol Proveedor).

## Fase 5: Integración Transaccional y UI
*   **Paso 5.1:** Modificación de `facturacion.py`. Actualizar las consultas SQL (`SELECT`) de los `Combobox` para que extraigan los datos correctamente desde el nuevo esquema normalizado utilizando sentencias `JOIN`.
*   **Paso 5.2:** Testing de Integridad Relacional. Verificar que la creación, modificación, baja lógica y facturación funcionen sin romper las dependencias de claves foráneas impuestas por el nuevo modelo.