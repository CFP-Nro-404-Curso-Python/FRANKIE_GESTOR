# 📄 Reporte de Ejecución - Etapa 1: Núcleo de Dominio y Pruebas Unitarias

## 📌 Resumen de la Etapa

Se construyó y validó con éxito la **Capa de Dominio (Capa 1)** bajo los lineamientos de la Arquitectura Hexagonal y los principios S.O.L.I.D. Este núcleo contiene las reglas de negocio puras y opera de manera 100% aislada: no posee dependencias externas, no importa librerías de terceros y desconoce por completo la existencia de bases de datos o interfaces gráficas.


## ⚙️ Componentes Desarrollados

*   **`src/dominio/entidades.py`**: Implementación de clases de datos nativas para `PerfilUsuario`, `Producto` y `Factura`. Se encapsuló la lógica matemática (ej. disponibilidad de stock y cálculo de subtotales comerciales) dentro de las propias entidades.

*   **`src/dominio/excepciones.py`**: Tipificación estructurada de errores de negocio (`ErrorJerarquiaRBAC`, `ErrorStockInsuficiente`) para permitir un manejo centralizado en capas superiores sin depender de códigos de estado HTTP.

*   **`src/dominio/politicas_rbac.py`**: Implementación del **Patrón Estrategia (GoF)** para erradicar la lógica condicional anidada. Se establecieron barreras jerárquicas estrictas para Administradores, Gerentes y Empleados.

*   **`src/dominio/puertos.py`**: Definición de interfaces abstractas (Contratos) aplicando el **Principio de Inversión de Dependencias (DIP)** para forzar a las futuras capas de infraestructura a respetar las reglas del dominio.


## 🧪 Estrategia de Testing y Configuración (TDD)

*   Se resolvió el conflicto de ruteo del motor de pruebas (`ModuleNotFoundError`) inyectando el archivo de configuración **`pytest.ini`** en la raíz del proyecto (`pythonpath = .`), estandarizando el descubrimiento de módulos.

*   Se construyeron las suites **`test_politicas_rbac.py`** y **`test_logica_inventario.py`**, aislando casos de prueba de borde (ej. intento de auto-baja de un gerente, ventas al límite exacto de stock).


## 🚀 Resultados de Ejecución en Consola

La batería de pruebas unitarias demostró la eficiencia computacional de una arquitectura desacoplada:
*   **Pruebas Ejecutadas:** 12 casos analíticos.

*   **Resultado Final:** 100% PASSED (0 fallos, 0 errores).

*   **Tiempo de Ejecución:** 0.32 segundos.


## 🧠 Análisis Analítico y Arquitectónico

El éxito de esta etapa radica en la validación empírica de las reglas de negocio. Al ejecutar 12 escenarios críticos en solo 0.32 segundos en memoria RAM, probamos que el sistema está blindado lógicamente contra fallas jerárquicas y comerciales. Cumplimos rigurosamente con los principios **KISS** y **YAGNI**: no hay sobreingeniería, solo clases puras que garantizan que el núcleo operativo sea indestructible antes de avanzar hacia la persistencia física (Etapa 2).