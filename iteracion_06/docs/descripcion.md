# 🏗️ Iteración 06: Migración SQL, Autenticación RBAC y Arquitectura Centralizada

## 📌 Resumen de la Iteración
El sistema acaba de dar el salto definitivo de un prototipo académico a un **software de gestión de grado empresarial**. Al abandonar la persistencia plana (CSV) y migrar a un motor de base de datos relacional (SQLite3), resolvimos los cuellos de botella de entrada/salida (I/O) y habilitamos operaciones transaccionales seguras (ACID). Además, pasamos de una arquitectura de "ventanas sueltas" a un ecosistema centralizado mediante un Panel de Control protegido por Autenticación y un Control de Acceso Basado en Roles (RBAC).

---

## ⚙️ Análisis Técnico y Decisiones de Arquitectura

### 1. Migración a Motor Relacional (SQLite3)
*   **Eficiencia de I/O:** Reemplazaste la reescritura destructiva de archivos de texto por sentencias SQL atómicas (`INSERT`, `UPDATE`, `DELETE`). Esto reduce drásticamente el consumo de memoria y el riesgo de corrupción de datos.
*   **Inicialización Autónoma (DDL):** Los módulos están programados para ejecutar sentencias `CREATE TABLE IF NOT EXISTS` en el arranque, garantizando que el sistema pueda reconstruir su propia estructura de datos en cualquier entorno virgen sin intervención manual.

### 2. Autenticación y Control de Acceso Basado en Roles (RBAC)
*   **Login Restrictivo:** Implementaste una barrera de entrada con un límite estricto de 3 intentos fallidos antes de aniquilar el proceso. El uso de `ventana.withdraw()` permite ocultar el login sin matar el hilo principal (`tk.Tk()`), delegando el control a la ventana hija.
*   **Despliegue Condicional de UI:** El `panel_control.py` lee el rol del usuario inyectado desde el login y usa el estado `tk.DISABLED` para bloquear el acceso a módulos fuera de su jurisdicción (ej. Ventas no puede tocar Compras ni Recursos Humanos).

### 3. Seguridad Anti-Escalada y Gestión de Credenciales
*   En el módulo `usuarios.py`, aplicaste una regla de negocio crítica en el backend (además del filtrado visual): un rol intermedio (Gerente) no puede crear, modificar ni eliminar perfiles de igual o mayor jerarquía (Administrador/Gerente). Esto evita ataques de escalada de privilegios horizontales y verticales.
*   **Protección de Integridad:** Delegaste la validación de duplicados al motor de base de datos capturando la excepción nativa `sqlite3.IntegrityError` cuando se intenta registrar un usuario ya existente.

### 4. Sandboxing SQL (Auditoría Segura)
*   La creación de `consola.py` es una excelente herramienta de auditoría, pero abrir una consola SQL directa a la base de datos es un riesgo enorme.
*   **Acierto Arquitectónico:** Implementaste un motor de expresiones regulares (`re.search`) que intercepta la consulta cruda y bloquea cualquier instrucción destructiva (`DROP`, `DELETE`, `UPDATE`, etc.). Además, inyectás dinámicamente un `LIMIT 1000` para evitar que un `SELECT *` malicioso o mal formulado desborde la memoria RAM de la aplicación.

### 5. Gestión del Ciclo de Vida y Respaldo
*   **Backup Funcional:** El módulo de copias de seguridad utiliza la librería nativa `shutil` para clonar en caliente la base de datos, estampándole un *timestamp* (`datetime`) para evitar sobrescrituras y mantener un histórico limpio.
*   **Cierre de Procesos (Kill Switch):** La inyección del protocolo `WM_DELETE_WINDOW` en el panel de control garantiza que, si el usuario cierra el programa desde la "X" del sistema operativo, el proceso raíz muera por completo, liberando los puertos y la memoria.

---

## 🛠️ Estado Actual de los Módulos

*   🔐 **Seguridad (`login.py` & `usuarios.py`):** Autenticación de estado, validación de intentos y gestión jerárquica de credenciales.
*   🎛️ **Nodo Central (`panel_control.py`):** Hub de operaciones. Distribuye los accesos mediante Lazy Imports, garantizando que los módulos pesados solo se carguen en memoria cuando son explícitamente requeridos.
*   📦 **Entidades Transaccionales (`clientes`, `empleados`, `proveedores`, `stock`, `facturacion`):** Completamente refactorizados. Operan con tuplas de SQLite. Facturación mantiene su capacidad de orquestar el descuento de inventario en tiempo real.
*   🛡️ **Auditoría (`consola.py`):** Entorno aislado y sanitizado para consultas de lectura.

---

## 🛑 Evaluación Crítica

A nivel de arquitectura de software de escritorio monousuario o de red local pequeña, el sistema es extremadamente robusto, predecible y escalable. Se resolvió la cohesión espacial encapsulando la base de datos y los backups en carpetas autogeneradas, haciendo que el software sea 100% portable (Plug & Play).

Sin embargo, para considerar que el proyecto cumple con los estándares de ciberseguridad actuales en un entorno de producción real, **existe una vulnerabilidad crítica que resolver:**

**Contraseñas en Texto Plano:** Guardar las credenciales legibles en la base de datos (`admin123`) es una práctica obsoleta y peligrosa. Si un actor malicioso o un empleado extrae el archivo `.db`, tiene acceso total e inmediato al sistema. 

**Deuda Técnica a saldar:** La próxima y definitiva refactorización debe incluir la librería `hashlib` o `bcrypt`. Al momento de guardar un usuario, la contraseña debe pasar por una función de hash unidireccional (con *salt*). El login, en lugar de comparar textos planos, debe hashear el input del usuario y comparar los hashes resultantes.