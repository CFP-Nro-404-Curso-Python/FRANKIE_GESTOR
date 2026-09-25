# 🏗️ Iteración 07: Criptografía Empresarial, UX Global y Filtros de Negocio

## 📌 Resumen de la Iteración
En esta etapa saldamos la deuda técnica más crítica de ciberseguridad: erradicamos las contraseñas en texto plano implementando estándares de la industria (`Bcrypt`) dentro de un entorno virtual aislado (`.venv`). Además, dimos un salto de calidad en la Experiencia de Usuario (UX) personalizando el entorno con datos reales y aplicando un refactoring estructural bajo el principio DRY para dotar a todo el sistema de atajos de teclado y menús contextuales de forma centralizada.

---

## ⚙️ Análisis Técnico y Decisiones de Arquitectura

### 1. Criptografía y Aislamiento del Entorno (Bcrypt)
*   **Entorno Virtual:** El proyecto ahora opera como un paquete de software profesional. Se aisló el entorno mediante `.venv` y se documentó la dependencia en `requirements.txt`, evitando contaminar el sistema operativo global.
*   **Hashing con Sal (Salt):** Se abandonó el texto plano. Las contraseñas ahora pasan por el algoritmo de `bcrypt`, el cual genera una "sal" aleatoria y un hash unidireccional. Esto protege la base de datos contra ataques de fuerza bruta y *Rainbow Tables*. La validación asíncrona (`bcrypt.checkpw`) se realiza sin que la base de datos vuelva a ver la contraseña cruda.

### 2. Inyección Global de Eventos (Principio DRY)
*   Había un fallo crítico de usabilidad: las cajas de texto de Tkinter no respondían a atajos básicos (Ctrl+C, Ctrl+V) ni al clic derecho.
*   En lugar de programar eventos widget por widget (violando la escalabilidad), se inyectó la solución directamente en el nodo raíz (`login.py`) utilizando el método `bind_class`. Al enlazar el menú contextual dinámico y los eventos virtuales (`<<Copy>>`, `<<Paste>>`) directamente a las clases `Entry`, `TCombobox` y `Text`, todo el ecosistema de ventanas secundarias heredó este comportamiento automáticamente.

### 3. Personalización y Ruteo de Datos
*   **DDL Actualizado:** Se modificó la estructura de la tabla `usuarios` para alojar `nombres` y `apellidos`. 
*   **Paso de Parámetros:** El Login ahora extrae estos datos de la base y los inyecta en caliente al constructor de `PanelControl`, logrando que la interfaz reciba al operador por su nombre real, mejorando la trazabilidad y la pertenencia del usuario.

### 4. Filtrado Estricto por Lógica de Negocio
*   En el módulo `facturacion.py`, el menú de vendedores arrastraba un fallo lógico: mostraba a todo el personal (incluyendo administradores y personal de compras).
*   Se corrigió pivotando la consulta desde el backend. La cláusula `WHERE rol = 'Empleado - Ventas'` delega el filtrado al motor SQL, garantizando la segregación de funciones e impidiendo que una factura quede registrada a nombre de un rol no autorizado.

---

## 🛠️ Estado Actual de los Módulos

*   🔐 **Seguridad (`login.py` & `usuarios.py`):** Operan con criptografía Bcrypt. El CRUD de usuarios bifurca inteligentemente las sentencias `UPDATE` para mantener hashes viejos o generar nuevos según la interacción del administrador.
*   🎛️ **Nodo Central (`panel_control.py`):** Interfaz personalizada con datos reales.
*   🧾 **Facturación (`facturacion.py`):** Menús desplegables protegidos por validaciones relacionales estrictas.
*   👥 **Módulos Transaccionales:** `clientes.py`, `empleados.py`, `proveedores.py` y `stock.py` heredan los atajos de teclado y la usabilidad nativa gracias al Application-wide Binding inyectado desde la raíz.

---

## 🛑 Evaluación Crítica

El verdadero valor de esta iteración reside en cómo consolida la madurez de la base de datos relacional. Diseñar un esquema SQL de forma profesional no se trata solo de crear tablas, sino de pensar en la **integridad, la seguridad y la escalabilidad de la arquitectura**. 

Al separar la autenticación (RBAC) del padrón de empleados operativos, al normalizar los datos inyectando nombres/apellidos en las credenciales, y al forzar consultas estrictas (como el `WHERE` en facturación), logramos un ecosistema altamente cohesivo. 

Esta estructura relacional ya está curada. Si el día de mañana el volumen de negocio exige concurrencia masiva, acceso remoto simultáneo o triggers en la base de datos, la migración de SQLite3 a un motor cliente-servidor de grado empresarial (como PostgreSQL o MySQL) será un proceso de transición natural y casi transparente, porque las reglas de normalización y la lógica transaccional ya están perfectamente cimentadas en tu código.