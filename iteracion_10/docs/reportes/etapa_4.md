# 📄 Reporte de Ejecución - Etapa 4: Adaptadores de Presentación (CustomTkinter + Web SPA), Accesibilidad, i18n, Impresión/PDF y Tests E2E

## 📌 Resumen de la Etapa

Se construyó, evolucionó y validó con éxito la **Capa de Presentación (Capa 4)** compuesta por dos clientes independientes con paridad estética y funcional 1:1 que consumen en simultáneo la misma API RESTful (`src/infraestructura/api/`):

1. **Cliente de Escritorio (`src/presentacion/escritorio/`)**: Migración integral de las 10 ventanas a **CustomTkinter** acotadas a resolución `<= 1280x720`, completamente desacopladas de `sqlite3` y `bcrypt`, y gobernadas por `ClienteAPI` + `GestorUI` (Patrón Observador).

2. **Cliente Web SPA Responsive (`src/presentacion/web/`)**: Aplicación de Página Única (HTML5, CSS3 fluido y JavaScript Vanilla) bajo enfoque *Mobile-First* para operar desde celulares, tablets y PCs en red local (LAN), compartiendo exactamente el mismo *Design System* **Slate/Blue**, accesibilidad WCAG, soporte bilingüe y vista previa imprimible/PDF que el cliente de escritorio.

3. **Automatización Operativa (`*.bat`)**: Creación de lanzadores en la raíz del proyecto para ejecución normal (`iniciar_frankie_gestor.bat`) y ciclo efímero de pruebas con semillas BI (`iniciar_con_semillas.bat`).


## ⚙️ Componentes Desarrollados

### 1. Adaptador de Escritorio (CustomTkinter + HTTP + Patrón Observador)
* **`src/presentacion/escritorio/cliente_api.py`**:
  * **`ClienteAPI`**: Cliente HTTP centralizado sobre `requests` que gestiona la sesión activa, inyecta la cabecera RBAC `X-Operador-Id` y normaliza errores HTTP (`400`, `401`, `403`, `404`, `422`) en `ErrorClienteAPI`.
  * **`GestorUI` (Patrón Observador - GoF)**: Centraliza los 4 perfiles visuales (**Claro**, **Oscuro**, **Claro Alto Contraste**, **Oscuro Alto Contraste**), el escalado tipográfico (`100%`, `115%`, `125%`) y el diccionario bilingüe **ES / EN**. Propaga cualquier cambio en vivo a todas las ventanas abiertas —incluyendo widgets híbridos como `ttk.Treeview`, gráficos `tk.Canvas` y el pop-up de impresión— y traduce etiquetas de roles en frontera (`"Sales Employee"` ↔ `"Empleado - Ventas"`) sin alterar el contrato canónico del Backend.

* **`src/presentacion/escritorio/vistas/login.py`**: Nodo de arranque que verifica `frankie_gestor.db` mediante los adaptadores del Backend, levanta automáticamente FastAPI (`0.0.0.0:8000`) y el servidor Web LAN (`0.0.0.0:8080`) con cierre limpio vía `atexit`, y expone la barra de preferencias visuales desde el acceso inicial.

* **Vistas Operativas y Gerenciales (`panel_control.py`, `usuarios.py`, `empleados.py`, `clientes.py`, `proveedores.py`, `stock.py`, `facturacion.py`, `consola.py`, `analitica.py`)**:
  * **Usabilidad y Accesibilidad:** Barra de preferencias reactiva (`EN/ES`, `Oscuro/Claro`, `A-`, `A+`, `HC`), atajos de teclado (`Esc`, `F5`, `Ctrl+F`, `Ctrl+Enter` en SQL), *zebra striping*, buscadores instantáneos y contadores de registros visibles.
  * **Semáforo de Inventario (`stock.py`):** Resaltado automático de filas con stock agotado (`<= 0`) y stock bajo (`<= stock_minimo`) adaptado a los 4 perfiles cromáticos.
  * **Facturación e Impresión / PDF Dual (`facturacion.py`):** Emisión y anulación delegando la restitución atómica de stock al Backend, recálculo limpio de `TOTAL FACTURA` bajo descuentos globales sin acumulación compuesta y botón **Imprimir Factura** que abre un pop-up `CTkToplevel` legible (por defecto **Tabla Completa + Descuento Global**, con selector rápido hacia **Ítem Seleccionado** y legajo 3FN del cliente). Desde el pop-up se genera un comprobante `.html` temporal autocontenido con `@media print` y se abre en el navegador mediante `webbrowser` para imprimir o guardar como `.pdf` sin sumar librerías externas.
  * **Analítica BI (`analitica.py`):** Renderizado nativo sobre 3 `tk.Canvas` livianos (bajo consumo de RAM) con escala numérica compacta en eje Y (`$1.2M`, `$450k`), rotación diagonal con acortamiento inteligente en Top 10, submuestreo dinámico de meses anti-superposición y redibujado inmediato al alternar tema o contraste.

### 2. Adaptador Web SPA Multi-Dispositivo (LAN / Móvil)
* **`src/presentacion/web/index.html`**: Maquetado semántico de las 10 vistas con barra superior persistente de preferencias UI/WCAG, buscadores instantáneos en las 7 grillas, modal de vista previa de comprobantes (`#modal-impresion-factura`) con aislamiento `.no-print`, atributos `data-i18n` / `data-i18n-ph` y soporte ARIA (`role="toolbar"`, `aria-live="polite"`, `aria-pressed`, `aria-modal`).

* **`src/presentacion/web/estilos.css`**: Implementa el *Design System* **Slate/Blue** unificado (`#F1F5F9`, `#1E293B`, `#2563EB`, `#16A34A`, `#DC2626`, `#D97706`, `#7C3AED`, `#0D9488`, `#475569`) con 4 perfiles vía atributos en `<html>` (`data-theme`, `data-contrast`, `data-scale`), anillos `:focus-visible`, clases de semáforo de stock (`.fila-stock-bajo`, `.fila-stock-agotado`), *Media Queries* móviles (`@media (max-width: 640px)`) con controles táctiles `>= 44px` y hoja de salida limpia `@media print` (`print-color-adjust: exact`).

* **`src/presentacion/web/app_web.js`**: Cliente `fetch` asíncrono con detección automática de IP en red local (`window.location.hostname`), persistencia 3FN sin `localStorage` (usando `sessionStorage` únicamente para preferencias visuales de la pestaña), motor i18n ES/EN, vista previa e impresión/PDF dual (`window.print()`) con modo por defecto `Tabla Completa + Descuento Global`, atajos de teclado (`Esc`, `Ctrl+F`, `Ctrl+Enter`), consola SQL en sandbox y gráficos `<canvas>` HTML5 con la misma lógica anti-superposición y adaptación cromática de escritorio.

### 3. Lanzadores Operativos
* **`iniciar_frankie_gestor.bat`**: Activa `.venv`, configura `PYTHONPATH`, ejecuta `login.py` y desactiva el entorno al finalizar.
* **`iniciar_con_semillas.bat`**: Automatiza el ciclo de pruebas efímero: elimina la base previa, inicializa el esquema 3FN + roles + `admin` sin abrir ventanas intermedias, ejecuta `semillas/generador_semilla_bi.py`, lanza `login.py` para pruebas y limpia `db/frankie_gestor.db` al cerrar la aplicación.


## 🧪 Estrategia de Testing E2E y Sincronización Multi-Cliente (TDD)

Para validar todas las ventanas, la persistencia 3FN real sin cachés, las capacidades de accesibilidad/i18n y el flujo completo de impresión/PDF, se consolidaron dos suites de integración automatizadas:

* **`tests/integracion/test_vistas_escritorio.py` (9 pruebas E2E)**: Instancia las 9 ventanas secundarias de CustomTkinter en modo *Headless* (`root.withdraw()`), intercepta `messagebox` y conecta `requests` de `cliente_api.py` al `TestClient` de FastAPI sobre una base SQLite temporal. Verifica cota `<= 1280x720`, matriz RBAC en `PanelControl`, coexistencia IAM/RRHH sin pisar credenciales ni legajos 3FN, ABM de Clientes/Proveedores/Stock con `ubicaciones_stock`, emisión y anulación de facturas con restitución exacta de stock, Sandboxing SQL, Tablero BI, Modo Oscuro/Alto Contraste/Zoom 125%/i18n ES-EN/semáforo/buscador (`test_8`) y el pop-up dual de impresión + exportación HTML/PDF interceptando `webbrowser.open` (`test_9`).

* **`tests/integracion/test_sincronizacion_web_escritorio.py` (8 pruebas de sincronización y paridad)**: Audita la estructura de `index.html`, `estilos.css` y `app_web.js` verificando cero invocaciones a `localStorage.`, valida *Preflight CORS* (`OPTIONS`) desde orígenes móviles LAN (`http://192.168.1.38:8080`), comprueba la sincronización bidireccional 3FN (incluyendo el flujo crítico Admin Escritorio → Gerente Web edita legajo 3FN de Vendedor → CustomTkinter RRHH refleja todos los campos), audita la paridad 1:1 de temas, WCAG, i18n, buscadores y BI (`test_7`) y valida el modal de impresión dual + `@media print` / `window.print()` (`test_8`).


## 🚀 Resultados de Ejecución en Consola (Suite Final Sellada)

```text
(.venv) D:\Repositorios de GitHub\Proyectos Personales\FRANKIE_GESTOR>pytest tests/ -v
======================================= test session starts =======================================
platform win32 -- Python 3.14.8, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\Repositorios de GitHub\Proyectos Personales\FRANKIE_GESTOR
configfile: pytest.ini
plugins: anyio-4.16.0
collected 37 items

tests\integracion\test_api_rest.py ....                                                      [ 10%]
tests\integracion\test_repositorios_sql.py ....                                              [ 21%]
tests\integracion\test_sincronizacion_web_escritorio.py ........                             [ 43%]
tests\integracion\test_vistas_escritorio.py .........                                        [ 67%]
tests\unitarios\test_logica_inventario.py .....                                              [ 81%]
tests\unitarios\test_politicas_rbac.py .......                                               [ 100%]

======================================== warnings summary =========================================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\Repositorios de GitHub\Proyectos Personales\FRANKIE_GESTOR\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: [https://docs.pytest.org/en/stable/how-to/capture-warnings.html](https://docs.pytest.org/en/stable/how-to/capture-warnings.html)
============================ 37 passed, 1 warning in 231.66s (0:03:51) ============================
```

* **Total de Pruebas Ejecutadas:** 37 casos automatizados (12 Unitarios de Dominio + 4 Integración SQL 3FN/Triggers + 4 API REST + 9 GUI CustomTkinter E2E + 8 Sincronización y Paridad Web/Escritorio).
* **Resultado Final:** `100% PASSED` (0 fallos, 0 errores).
* **Tiempo de Ejecución Global:** `231.66 segundos (0:03:51)`.


## 🧠 Análisis Analítico y Arquitectónico

La Etapa 4 valida empíricamente las promesas centrales de la **Arquitectura Hexagonal**: pudimos migrar por completo el cliente de escritorio a CustomTkinter, incorporar una segunda interfaz Web SPA responsive para red local, sumar Modo Oscuro, Alto Contraste WCAG, Zoom, internacionalización bilingüe ES/EN y agregar un módulo completo de vista previa e impresión/PDF dual de facturas **sin modificar una sola línea del Dominio, la Aplicación ni la Persistencia**. Además, la auditoría E2E permitió detectar y resolver defectos reales antes de producción (restitución atómica de stock al anular comprobantes y recálculo limpio de `TOTAL FACTURA` bajo descuento global), dejando ambos clientes operando como ciudadanos de primera clase sobre una única fuente de verdad.