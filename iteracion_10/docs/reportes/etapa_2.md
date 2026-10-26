# 📄 Reporte de Ejecución - Etapa 2: Casos de Uso, Persistencia y Tests de Integración

## 📌 Resumen de la Etapa

Se construyeron y validaron con éxito la **Capa de Aplicación (Capa 2)** y la **Capa de Infraestructura (Capa 3)**, respetando el flujo de dependencias de la Arquitectura Hexagonal. Logramos persistir datos en un esquema relacional 3FN estricto interactuando con SQLite en memoria RAM, orquestando las reglas de negocio sin acoplar los casos de uso al motor de base de datos.


## ⚙️ Componentes Desarrollados

*   **`src/aplicacion/`**: Se implementaron los servicios orquestadores (`casos_uso_perfiles.py`, `casos_uso_inventario.py`, `casos_uso_comercial.py`). Estos servicios aplican las políticas RBAC y coordinan transacciones complejas (ej. facturar y descontar stock simultáneamente) delegando el trabajo físico a la Unidad de Trabajo.

*   **`src/infraestructura/persistencia/gestor_sqlite.py`**: Implementación del Patrón *Unit of Work*. Controla el ciclo de vida transaccional (ACID), ejecutando `commit` si todo fluye o `rollback` automático ante cualquier excepción de lógica o integridad.

*   **`src/infraestructura/persistencia/utilidades_sql.py`**: Refactorización clave para aislar la función `obtener_o_crear`, aplicando SRP y eliminando los cuellos de botella de importación circular entre los distintos repositorios.

*   **`src/infraestructura/persistencia/repositorio_*.py`**: Adaptadores que traducen las entidades de dominio a sentencias SQL sobre un esquema 3FN (resolviendo catálogos satélites, validación de claves foráneas y tablas puente de muchos a muchos).

*   **`src/infraestructura/seguridad/adaptador_bcrypt.py`**: Implementación concreta del puerto de hashing, aislando la lógica criptográfica del núcleo del sistema.


## 🧪 Estrategia de Testing y Configuración (TDD)

*   Se configuró el fixture `conexion_sqlite_memoria` en `tests/conftest.py` para inicializar el esquema físico completo (DDL, Vistas, Triggers) dinámicamente en un entorno aislado (`:memory:`) antes de cada test de integración.

*   Se refactorizaron las fases de preparación (*Arrange*) inyectando semillas físicas para satisfacer las restricciones rígidas de SQLite (`PRAGMA foreign_keys = ON`) y se validó la correcta normalización de cadenas de texto (mayúsculas/minúsculas) procesada por el motor.


## 🚀 Resultados de Ejecución en Consola

La batería de integración demostró que los adaptadores se comunican sin fricción con la base de datos y que los Triggers actúan como última línea de defensa infalible:

*   **Pruebas de Integración (Etapa 2):** 4 casos de uso técnico.

*   **Suite Completa (Dominio + Infraestructura):** 16 casos de análisis ejecutados.

*   **Resultado Final:** 100% PASSED (0 fallos, 0 errores).

*   **Tiempo de Ejecución Global:** 0.27 segundos.


## 🧠 Análisis Analítico y Arquitectónico

Demostramos empíricamente la solidez del Patrón Unidad de Trabajo. Al mantener las reglas de negocio en el Dominio y el control transaccional en la Infraestructura, evitamos colisiones de concurrencia y garantizamos que operaciones críticas (como `actualizar_stock`) sean rigurosamente atómicas. La corrección del diseño para evitar la importación circular probó que la arquitectura es escalable y maleable sin romper contratos previos. El Backend y la Base de Datos están blindados; la infraestructura está lista para exponerse vía endpoints en la Etapa 3.