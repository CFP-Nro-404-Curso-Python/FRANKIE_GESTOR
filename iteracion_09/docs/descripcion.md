# 📈 Iteración 09: Business Intelligence (OLAP), ETL y Análisis Vectorial

## 📌 Resumen de la Iteración

Esta etapa marca la evolución del sistema desde un enfoque puramente transaccional (OLTP) hacia el **Procesamiento Analítico en Línea (OLAP)**. Se integró un Tablero de Control (Dashboard) interactivo de Business Intelligence utilizando `pandas` y `matplotlib`. Para dotar al módulo de sentido estadístico inmediato, se desarrolló un **Script ETL (Extract, Transform, Load)** que migra y adapta 1.000 registros históricos en bruto hacia nuestra estricta base de datos normalizada, demostrando la escalabilidad y robustez de la arquitectura implementada en la Iteración 08.

---

## ⚙️ Análisis Técnico y Decisiones de Arquitectura

### 1. Procesamiento Vectorial (Pandas) vs. Bucles Nativos

*   **Delegación Analítica:** En lugar de saturar el motor SQLite con cálculos estadísticos complejos o usar bucles `for` en Python para sumar totales, la consulta `SELECT` extrae el historial mediante `JOINs` limpios y transfiere los datos a un `DataFrame` de Pandas.
*   **Operaciones en Memoria RAM:** Las agrupaciones por categoría (`groupby`), la extracción de productos estrella (`idxmax`) y el agrupamiento de series temporales mensuales se resuelven de forma vectorial en milisegundos gracias a la optimización en C de la librería Pandas.

### 2. Pipeline ETL y Semillas (Seeders)

*   **El Desafío de la Tercera Forma Normal (3FN):** Los datos crudos de la cátedra consistían en tablas planas. No se podían inyectar directamente en `frankie_gestor.db` porque nuestra arquitectura exige integridad referencial (todo producto requiere un proveedor, toda factura requiere vendedor y cliente, y los stocks requieren estados).
*   **Solución (Script de Migración):** Se creó `generar_semilla_bi.py`. Este script extrae (Extract) las tuplas usando expresiones regulares, transforma (Transform) los datos inyectando "usuarios fantasma" (Proveedor, Vendedor, Cliente genéricos) y calculando estados ("Disponible"), y finalmente carga (Load) la información respetando las claves foráneas.

### 3. Optimización de Renderizado Gráfico y Gestión de Memoria

*   **Prevención de Fugas de Memoria (Memory Leaks):** Los gráficos de `matplotlib` incrustados en Tkinter (`FigureCanvasTkAgg`) pueden consumir la memoria RAM si no se destruyen correctamente. Se implementó un protocolo de cierre (`WM_DELETE_WINDOW`) que limpia explícitamente la figura del lienzo antes de destruir la ventana.
*   **Rendimiento Visual (Anti-Colapso):** 
    *   Se reemplazó el ineficiente iterador `.iterrows()` por `.itertuples()`, logrando que la tabla visual (Treeview) de 1.000 registros se pueble hasta 10 veces más rápido.
    *   Se aplicó el filtro `.nlargest(10)` al gráfico de barras para mostrar únicamente el "Top 10" de productos. Graficar 1.000 productos simultáneos hubiera generado un colapso visual ilegible.

### 4. Seguridad RBAC en Módulos Estratégicos

*   Se modificó el ruteo del Panel de Control (`panel_control.py`). El acceso al Tablero BI está estrictamente condicionado por la matriz de permisos, habilitando el botón *únicamente* para los roles **Administrador** y **Gerente**, protegiendo la información sensible del flujo de caja corporativo.

---

## 🛑 Evaluación Crítica

La adopción de scripts de análisis independientes (como el propuesto originalmente por la cátedra) en un ecosistema preexistente requiere un riguroso análisis de impacto. El código original calculaba la facturación multiplicando dinámicamente `precio * cantidad` en tiempo de consulta. Este enfoque **destruye la integridad contable**, ya que si un producto cambia de precio hoy, alteraría la facturación de los meses anteriores.

Al adaptar este módulo a nuestra arquitectura, se corrigió esta falla contable forzando a Pandas a leer la columna `valor` (precio congelado al momento de la venta) y la columna `total` autocalculada y almacenada por SQLite (`GENERATED ALWAYS AS ... STORED`). De esta manera, garantizamos que las estadísticas gerenciales reflejen la realidad histórica exacta, combinando lo mejor de un motor relacional estricto con la potencia de análisis de datos científicos.

---

## 🚀 Guía de Ejecución y Poblamiento de Datos (Semilla)

Debido al salto arquitectónico, es **crítico** respetar el orden de ejecución para que la base de datos se inicialice correctamente antes de inyectar los 1.000 registros históricos.

**Paso 1: Preparación del Entorno**
Asegurate de estar en el directorio raíz (`iteracion_09`) con el entorno virtual activo y las librerías científicas instaladas:
```bash
# Activar entorno virtual (Windows)
.venv\Scripts\activate

# Instalar dependencias (Bcrypt, Pandas, Matplotlib)
pip install -r requirements.txt