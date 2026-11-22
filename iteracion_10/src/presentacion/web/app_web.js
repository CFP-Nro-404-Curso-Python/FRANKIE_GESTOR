// ==============================================================================
//  CLIENTE WEB SPA Y ADAPTADOR FETCH (CAPA 4 - PRESENTACIÓN WEB)
// ==============================================================================
//  DECISIÓN DE DISEÑO (PARIDAD 1:1 CON CUSTOMTKINTER Y CERO CACHÉS DE NEGOCIO):
//
//   1. Detecta automáticamente la IP del servidor en la red WiFi usando
//      'window.location.hostname', permitiendo operar desde PCs y celulares.
//   2. Consume exactamente los mismos endpoints FastAPI (puerto 8000) que
//      CustomTkinter enviando 'X-Operador-Id' para validación RBAC.
//   3. Cero almacenamiento persistente para datos de negocio: todo legajo 3FN y
//      ubicación de stock se persiste y lee directamente desde SQLite vía API.
//   4. Preferencias visuales de sesión (Tema, Alto Contraste WCAG, Zoom e i18n)
//      almacenadas únicamente en sessionStorage de la pestaña activa.
// ==============================================================================

const HOST_LAN = window.location.hostname || "127.0.0.1";
const URL_BASE_API = `http://${HOST_LAN}:8000`;

// Estado global de la sesión activa en el navegador.
let sesionActiva = {
    id: null,
    usuario: null,
    rol: null,
    nombres: null,
    apellidos: null
};

let intentosFallidosLogin = 0;

// Estado de preferencias visuales y accesibilidad (espejo de GestorUI).
const ESCALAS_WEB = ["1", "1.15", "1.25"];
const prefUI = {
    tema: "light",
    altoContraste: false,
    idioma: "es",
    escala: "1"
};

// Cachés en RAM de la vista actual (para filtrado instantáneo y redibujado i18n/tema).
let cacheUsuarios = [];
let cacheEmpleados = [];
let cacheClientes = [];
let cacheProveedores = [];
let cacheProductos = [];
let cacheFacturas = [];
let cacheRegistrosBI = [];
let cacheTop10BI = [];
let cacheMensualBI = [];
let cacheCategoriasBI = [];
let biEstrella = { producto: null, categoria: null };

// Mapas efímeros de traducción ID <-> Etiqueta para selects de Stock y Facturación.
let mapaProveedoresNombreAId = {};
let mapaProveedoresIdANombre = {};
let mapaProductosCodigoAObj = {};
let mapaProductosIdAObj = {};
let stockPrevioPorId = {};
let facturaSeleccionadaCache = null;
let totalAcumuladoFacturacion = 0.0;
let porcentajeGlobalActivo = 0.0;
let estadoSQLMeta = { clave: "sql_est_esp", kwargs: {}, textoLibre: null, tipo: "muted" };


// ==============================================================================
//  1. MOTOR DE INTERNACIONALIZACIÓN (ES / EN), TEMAS Y ACCESIBILIDAD (WCAG)
// ==============================================================================

const ROLES_A_EN = {
    "Administrador": "Administrator",
    "Gerente": "Manager",
    "Empleado - Ventas": "Sales Employee",
    "Empleado - Compras": "Purchasing Employee",
    "Proveedor": "Supplier",
    "Cliente": "Customer"
};

const TRADUCCIONES_WEB = {
    es: {
        // Preferencias y comunes
        btn_idioma: "EN",
        btn_tema_oscuro: "Oscuro",
        btn_tema_claro: "Claro",
        btn_volver_panel: "⬅ Panel Principal",
        btn_aceptar: "Aceptar",
        btn_actualizar: "Actualizar",
        btn_cerrar: "Cerrar",
        btn_guardar: "Guardar",
        btn_modificar: "Modificar",
        btn_eliminar: "Eliminar",
        btn_limpiar: "Limpiar",
        buscar_ph: "Buscar en la tabla (Ctrl+F)...",
        contador_filas: "Mostrando {visibles} de {total} registros",
        atajos_web: "Atajos: Ctrl+F Buscar | Esc Volver",
        sin_dato: "S/D",
        sin_cred: "[Sin Credenciales]",
        sel_rol: "Seleccione un rol...",

        // Alertas comunes
        val_tit: "Validación",
        err_com_tit: "Error de Comunicación",
        err_tx_tit: "Error de Transacción",
        err_act_tit: "Error al Actualizar",
        err_gua_tit: "Error al Guardar",
        err_acc_tit: "Acceso Denegado",
        err_acc_err_tit: "Acceso Denegado / Error",
        err_bloq_tit: "Operación Bloqueada",
        err_fmt_tit: "Error de Formato",
        err_sel_tit: "Selección Requerida",

        // Login
        login_sub: "Sistema de Gestión Comercial — Acceso LAN",
        login_usu: "Usuario",
        login_usu_ph: "Ej: admin",
        login_pass: "Contraseña",
        login_btn: "Ingresar al Sistema",
        login_intentos: "Intentos disponibles: {n}",
        login_bloqueado: "Acceso bloqueado por seguridad.",
        login_completar: "Completá todos los campos.",
        login_ok_tit: "Acceso Concedido",
        login_ok_msg: "Bienvenido/a, {nombre} {apellido}.\nRol: {rol}",
        login_err_tit: "Error de Autenticación",
        login_err_msg: "Credenciales incorrectas o usuario inhabilitado. Intentos restantes: {n}",
        login_bloq_tit: "Bloqueo de Seguridad",
        login_bloq_msg: "Superaste el límite de intentos fallidos. Recargá la página o contactá al Administrador.",

        // Panel
        panel_saludo: "BIENVENIDO/A, {nombre}",
        panel_sub: "Panel Operativo — Permisos habilitados para: {rol}",
        panel_clientes: "Gestión de Clientes",
        panel_facturacion: "Facturación",
        panel_proveedores: "Gestión de Proveedores",
        panel_stock: "Control de Stock",
        panel_empleados: "Recursos Humanos (RRHH)",
        panel_usuarios: "Gestión de Usuarios (IAM)",
        panel_consola: "Consola SQL (Auditoría)",
        panel_backup: "Generar Backup JSON",
        panel_analitica: "Analítica de Ventas (Tablero BI / OLAP)",
        panel_salir: "Cerrar Sesión",
        bkp_ok_tit: "Backup Exitoso",
        bkp_ok_msg: "Copia de seguridad descargada en tu dispositivo como:\n{archivo}",
        bkp_err_tit: "Error de Backup",

        // Usuarios
        usu_header: "GESTIÓN DE USUARIOS Y CREDENCIALES (IAM)",
        usu_nombres: "Nombres *",
        usu_nombres_ph: "Nombre del usuario",
        usu_apellidos: "Apellidos *",
        usu_apellidos_ph: "Apellido del usuario",
        usu_login: "Usuario (Login) *",
        usu_login_ph: "Cuenta de acceso",
        usu_pass: "Contraseña",
        usu_pass_ph: "Vacío al editar para conservar",
        usu_rol: "Rol Asignado *",
        usu_ayuda: "Tocá una fila para editar credenciales o cambiar el rol asignado.",
        usu_todos_req: "Todos los campos son obligatorios en este módulo.",
        usu_priv_err: "Privilegios insuficientes para crear perfiles de esta jerarquía.",
        usu_sel_req: "Tocá primero un usuario de la tabla.",
        usu_mod_req: "Nombres, Apellidos, Usuario y Rol son obligatorios.",
        col_usuario: "Usuario",
        col_rol_sis: "Rol del Sistema",
        col_nombres: "Nombres",
        col_apellidos: "Apellidos",

        // Empleados
        emp_header: "RECURSOS HUMANOS — LEGAJOS DE EMPLEADOS",
        emp_dni: "DNI",
        emp_tel: "Teléfono",
        emp_email: "Email",
        emp_dir: "Dirección",
        emp_ciudad: "Ciudad",
        emp_prov: "Provincia",
        emp_cp: "Cód. Postal",
        emp_rol: "Rol Organizacional *",
        emp_btn_guardar: "Guardar Perfil",
        emp_btn_modificar: "Modificar Perfil",
        emp_btn_eliminar: "Eliminar Perfil",
        emp_ayuda: "Tocá un empleado de la nómina para completar o actualizar su legajo 3FN.",
        emp_req: "Nombres, Apellidos y Rol Organizacional son obligatorios.",
        emp_priv_err: "Privilegios insuficientes para crear perfiles de esta jerarquía organizativa.",
        emp_sel_req: "Tocá primero un empleado de la tabla.",
        col_dni: "DNI",
        col_tel: "Teléfono",
        col_email: "Email",
        col_dir: "Dirección",
        col_ciudad: "Ciudad",
        col_prov: "Provincia",
        col_cp: "CP",
        col_rol: "Rol",

        // Clientes
        cli_header: "GESTIÓN DE CLIENTES",
        cli_cp: "Código Postal",
        cli_btn_guardar: "Guardar Cliente",
        cli_btn_modificar: "Modificar Cliente",
        cli_btn_eliminar: "Eliminar Cliente",
        cli_ayuda: "Tocá un cliente en la tabla para cargarlo en el formulario.",
        cli_req: "Nombres y Apellidos son obligatorios.",
        cli_sel_req: "Tocá primero un cliente de la tabla.",

        // Proveedores
        prov_header: "GESTIÓN DE PROVEEDORES",
        prov_razon: "Razón Social *",
        prov_cuit: "CUIT",
        prov_contacto: "Contacto (Rep.)",
        prov_btn_guardar: "Guardar Proveedor",
        prov_btn_modificar: "Modificar Proveedor",
        prov_btn_eliminar: "Eliminar Proveedor",
        prov_ayuda: "Tocá un proveedor en la tabla para editar sus datos.",
        prov_req: "La Razón Social es obligatoria.",
        prov_sel_req: "Tocá primero un proveedor de la tabla.",
        col_razon: "Razón Social",
        col_cuit: "CUIT",
        col_contacto: "Contacto",

        // Stock
        stk_header: "CONTROL DE STOCK E INVENTARIO",
        stk_codigo: "Código *",
        stk_desc: "Descripción *",
        stk_cat: "Categoría",
        stk_prov: "Proveedor *",
        stk_ubic: "Ubicación",
        stk_act: "Stock Actual",
        stk_min: "Stock Mínimo",
        stk_costo: "Precio Costo ($)",
        stk_venta: "Precio Venta ($)",
        stk_venc: "Vencimiento",
        stk_sel_prov: "Seleccione proveedor...",
        stk_btn_guardar: "Guardar Producto",
        stk_btn_modificar: "Modificar Producto",
        stk_btn_eliminar: "Eliminar Producto",
        stk_semaforo: "Referencias: Amarillo = Stock Bajo (<= Mínimo) | Rojo = Agotado (0)",
        stk_req: "Código, Descripción y Proveedor son campos obligatorios.",
        stk_prov_inv: "El proveedor seleccionado no es válido o fue dado de baja.",
        stk_nums_err: "Asegurate de ingresar valores numéricos válidos en precios y stock.",
        stk_sel_req: "Tocá primero un producto de la tabla.",
        col_codigo: "Código",
        col_desc: "Descripción",
        col_cat: "Categoría",
        col_prov_col: "Proveedor",
        col_stk_act: "Stock Actual",
        col_stk_min: "Stock Mínimo",
        col_costo: "Precio Costo",
        col_venta: "Precio Venta",
        col_ubic: "Ubicación",
        col_venc: "Vencimiento",

        // Facturación
        fac_header: "FACTURACIÓN Y OPERACIONES COMERCIALES",
        fac_vendedor: "Datos del Vendedor *",
        fac_cliente: "Datos del Cliente *",
        fac_producto: "Producto *",
        fac_cantidad: "Cantidad *",
        fac_valor: "Valor Unitario ($)",
        fac_desc_item: "Descuento por Ítem (%)",
        fac_sel_vend: "Seleccione vendedor...",
        fac_sel_cli: "Seleccione cliente...",
        fac_sel_prod: "Seleccione producto...",
        fac_btn_guardar: "Guardar Facturación",
        fac_btn_modificar: "Modificar Facturación",
        fac_btn_eliminar: "Eliminar Facturación",
        fac_total: "TOTAL FACTURA: $ {monto}",
        fac_total_desc: "Total con descuento ({pct}%): $ {monto}",
        fac_aplicar_desc: "APLICAR DESCUENTO GLOBAL",
        fac_desc_global: "Descuento Global (%):",
        fac_btn_calc: "Calcular Descuento Final",
        fac_req: "Vendedor, Cliente y Producto son obligatorios.",
        fac_nums_err: "Ingresá valores numéricos válidos en Cantidad y Descuento.",
        fac_rango_err: "El descuento debe estar entre 0 y 100% y la cantidad > 0.",
        fac_asoc_err: "Seleccioná un vendedor, cliente y producto válidos del menú.",
        fac_sel_req: "Tocá primero una factura de la tabla.",
        fac_rep_tit: "Alerta de Reposición",
        fac_rep_msg: "El producto llegó a su stock mínimo. Quedan {u} unidades.",
        fac_desc_rango: "El descuento global debe estar entre 0 y 100%.",
        col_prod: "Producto",
        col_cant: "Cantidad",
        col_valor: "Valor en $",
        col_desc_pct: "Descuento en %",
        col_total: "Total en $",

        // Consola SQL
        sql_header: "CONSOLA SQL — AUDITORÍA EN SANDBOX (SOLO LECTURA)",
        sql_ingrese: "Ingresá tu sentencia SQL (SELECT):",
        sql_btn_ejec: "Ejecutar Consulta",
        sql_btn_limp: "Limpiar Consola",
        sql_est_esp: "Estado: Esperando consulta...",
        sql_est_rbac: "Estado: Bloqueado por falta de privilegios RBAC.",
        sql_est_sbx: "Estado: Query bloqueada por Sandboxing.",
        sql_est_ok: "Estado: Ejecución exitosa. Filas recuperadas: {n}",
        sql_solo_admin: "Solo un Administrador activo puede ejecutar auditorías SQL.",
        sql_bloq_tit: "Bloqueo de Seguridad",
        sql_bloq_msg: "Transacción abortada. Operación destructiva detectada.\nEsta consola es de Solo Lectura (SELECT).",
        sql_solo_sel: "Error SQL: Solo se admiten sentencias que comiencen con SELECT.",

        // Analítica BI
        bi_header: "TABLERO DE CONTROL — ANALÍTICA BI / OLAP",
        bi_sub_ini: "Análisis estadístico en tiempo real",
        bi_sub_vacio: "Sin ventas registradas para analizar",
        bi_sub_top: "Más Vendido: {prod} | Categoría Top: {cat}",
        bi_btn_act: "Actualizar Análisis",
        bi_kpi_fac: "Facturación Total",
        bi_kpi_ops: "Operaciones",
        bi_kpi_uni: "Unidades Vendidas",
        bi_kpi_tkt: "Ticket Promedio",
        bi_graf_top10: "Top 10 Productos (Facturación)",
        bi_graf_mensual: "Evolución Mensual",
        bi_graf_cat: "Facturación por Categoría",
        bi_detalle_tit: "Detalle Histórico de Ventas",
        bi_sin_datos: "Sin datos",
        bi_info_vacio: "No hay ventas registradas para analizar.",
        col_id_venta: "ID Venta",
        col_precio_cong: "Precio Congelado",
        col_fecha: "Fecha",
        col_total_cob: "Total Cobrado"
    },
    en: {
        // Common & preferences
        btn_idioma: "ES",
        btn_tema_oscuro: "Dark",
        btn_tema_claro: "Light",
        btn_volver_panel: "⬅ Main Dashboard",
        btn_aceptar: "OK",
        btn_actualizar: "Refresh",
        btn_cerrar: "Close",
        btn_guardar: "Save",
        btn_modificar: "Update",
        btn_eliminar: "Delete",
        btn_limpiar: "Clear",
        buscar_ph: "Filter table (Ctrl+F)...",
        contador_filas: "Showing {visibles} of {total} records",
        atajos_web: "Shortcuts: Ctrl+F Search | Esc Back",
        sin_dato: "N/A",
        sin_cred: "[No Credentials]",
        sel_rol: "Select a role...",

        // Common alerts
        val_tit: "Validation",
        err_com_tit: "Communication Error",
        err_tx_tit: "Transaction Error",
        err_act_tit: "Update Error",
        err_gua_tit: "Save Error",
        err_acc_tit: "Access Denied",
        err_acc_err_tit: "Access Denied / Error",
        err_bloq_tit: "Operation Blocked",
        err_fmt_tit: "Format Error",
        err_sel_tit: "Selection Required",

        // Login
        login_sub: "Commercial Management System — LAN Access",
        login_usu: "Username",
        login_usu_ph: "e.g. admin",
        login_pass: "Password",
        login_btn: "Sign In",
        login_intentos: "Remaining attempts: {n}",
        login_bloqueado: "Access locked for security.",
        login_completar: "Please fill in all fields.",
        login_ok_tit: "Access Granted",
        login_ok_msg: "Welcome, {nombre} {apellido}.\nRole: {rol}",
        login_err_tit: "Authentication Error",
        login_err_msg: "Invalid credentials or disabled account. Remaining attempts: {n}",
        login_bloq_tit: "Security Lockout",
        login_bloq_msg: "Maximum failed attempts exceeded. Reload the page or contact an Administrator.",

        // Dashboard
        panel_saludo: "WELCOME, {nombre}",
        panel_sub: "Operations Dashboard — Enabled permissions for: {rol}",
        panel_clientes: "Customer Management",
        panel_facturacion: "Invoicing",
        panel_proveedores: "Supplier Management",
        panel_stock: "Inventory Control",
        panel_empleados: "Human Resources (HR)",
        panel_usuarios: "User Management (IAM)",
        panel_consola: "SQL Console (Audit)",
        panel_backup: "Generate JSON Backup",
        panel_analitica: "Sales Analytics (BI / OLAP Dashboard)",
        panel_salir: "Sign Out",
        bkp_ok_tit: "Backup Successful",
        bkp_ok_msg: "Backup downloaded to your device as:\n{archivo}",
        bkp_err_tit: "Backup Error",

        // Users
        usu_header: "USER & CREDENTIALS MANAGEMENT (IAM)",
        usu_nombres: "First Name *",
        usu_nombres_ph: "User first name",
        usu_apellidos: "Last Name *",
        usu_apellidos_ph: "User last name",
        usu_login: "Username (Login) *",
        usu_login_ph: "Account username",
        usu_pass: "Password",
        usu_pass_ph: "Leave empty on edit to keep",
        usu_rol: "Assigned Role *",
        usu_ayuda: "Tap a row to edit credentials or update the assigned role.",
        usu_todos_req: "All fields are required in this module.",
        usu_priv_err: "Insufficient privileges to create profiles at this hierarchy level.",
        usu_sel_req: "Tap a user row from the table first.",
        usu_mod_req: "First Name, Last Name, Username and Role are required.",
        col_usuario: "Username",
        col_rol_sis: "System Role",
        col_nombres: "First Name",
        col_apellidos: "Last Name",

        // Employees
        emp_header: "HUMAN RESOURCES — EMPLOYEE RECORDS",
        emp_dni: "ID / DNI",
        emp_tel: "Phone",
        emp_email: "Email",
        emp_dir: "Address",
        emp_ciudad: "City",
        emp_prov: "State / Province",
        emp_cp: "Postal Code",
        emp_rol: "Organizational Role *",
        emp_btn_guardar: "Save Profile",
        emp_btn_modificar: "Update Profile",
        emp_btn_eliminar: "Delete Profile",
        emp_ayuda: "Tap an employee row to complete or update their 3FN record.",
        emp_req: "First Name, Last Name and Organizational Role are required.",
        emp_priv_err: "Insufficient privileges to create profiles at this hierarchy level.",
        emp_sel_req: "Tap an employee row from the table first.",
        col_dni: "DNI",
        col_tel: "Phone",
        col_email: "Email",
        col_dir: "Address",
        col_ciudad: "City",
        col_prov: "Province",
        col_cp: "ZIP",
        col_rol: "Role",

        // Customers
        cli_header: "CUSTOMER MANAGEMENT",
        cli_cp: "Postal Code",
        cli_btn_guardar: "Save Customer",
        cli_btn_modificar: "Update Customer",
        cli_btn_eliminar: "Delete Customer",
        cli_ayuda: "Tap a customer row to load their details into the form.",
        cli_req: "First Name and Last Name are required.",
        cli_sel_req: "Tap a customer row from the table first.",

        // Suppliers
        prov_header: "SUPPLIER MANAGEMENT",
        prov_razon: "Company Name *",
        prov_cuit: "Tax ID (CUIT)",
        prov_contacto: "Contact Rep.",
        prov_btn_guardar: "Save Supplier",
        prov_btn_modificar: "Update Supplier",
        prov_btn_eliminar: "Delete Supplier",
        prov_ayuda: "Tap a supplier row to edit their details.",
        prov_req: "Company Name is required.",
        prov_sel_req: "Tap a supplier row from the table first.",
        col_razon: "Company Name",
        col_cuit: "CUIT",
        col_contacto: "Contact",

        // Stock
        stk_header: "INVENTORY & STOCK CONTROL",
        stk_codigo: "SKU / Code *",
        stk_desc: "Description *",
        stk_cat: "Category",
        stk_prov: "Supplier *",
        stk_ubic: "Location",
        stk_act: "Current Stock",
        stk_min: "Minimum Stock",
        stk_costo: "Cost Price ($)",
        stk_venta: "Sale Price ($)",
        stk_venc: "Expiration",
        stk_sel_prov: "Select supplier...",
        stk_btn_guardar: "Save Product",
        stk_btn_modificar: "Update Product",
        stk_btn_eliminar: "Delete Product",
        stk_semaforo: "Legend: Amber = Low Stock (<= Min) | Red = Out of Stock (0)",
        stk_req: "Code, Description and Supplier are required.",
        stk_prov_inv: "Selected supplier is invalid or inactive.",
        stk_nums_err: "Please enter valid numeric values for prices and stock.",
        stk_sel_req: "Tap a product row from the table first.",
        col_codigo: "Code",
        col_desc: "Description",
        col_cat: "Category",
        col_prov_col: "Supplier",
        col_stk_act: "Stock",
        col_stk_min: "Min Stock",
        col_costo: "Cost Price",
        col_venta: "Sale Price",
        col_ubic: "Location",
        col_venc: "Expiration",

        // Invoicing
        fac_header: "INVOICING & COMMERCIAL OPERATIONS",
        fac_vendedor: "Salesperson *",
        fac_cliente: "Customer *",
        fac_producto: "Product *",
        fac_cantidad: "Quantity *",
        fac_valor: "Unit Price ($)",
        fac_desc_item: "Item Discount (%)",
        fac_sel_vend: "Select salesperson...",
        fac_sel_cli: "Select customer...",
        fac_sel_prod: "Select product...",
        fac_btn_guardar: "Save Invoice",
        fac_btn_modificar: "Update Invoice",
        fac_btn_eliminar: "Delete Invoice",
        fac_total: "INVOICE TOTAL: $ {monto}",
        fac_total_desc: "Total with discount ({pct}%): $ {monto}",
        fac_aplicar_desc: "APPLY GLOBAL DISCOUNT",
        fac_desc_global: "Global Discount (%):",
        fac_btn_calc: "Calculate Final Total",
        fac_req: "Salesperson, Customer and Product are required.",
        fac_nums_err: "Enter valid numeric values for Quantity and Discount.",
        fac_rango_err: "Quantity must be > 0 and Discount between 0 and 100%.",
        fac_asoc_err: "Please select a valid salesperson, customer and product.",
        fac_sel_req: "Tap an invoice row from the table first.",
        fac_rep_tit: "Restock Alert",
        fac_rep_msg: "Product reached minimum stock level. {u} units remaining.",
        fac_desc_rango: "Global discount must be between 0 and 100%.",
        col_prod: "Product",
        col_cant: "Qty",
        col_valor: "Unit Price $",
        col_desc_pct: "Discount %",
        col_total: "Total $",

        // SQL Console
        sql_header: "SQL CONSOLE — SANDBOX AUDIT (READ-ONLY)",
        sql_ingrese: "Enter your SQL query (SELECT):",
        sql_btn_ejec: "Run Query",
        sql_btn_limp: "Clear Console",
        sql_est_esp: "Status: Waiting for query...",
        sql_est_rbac: "Status: Blocked due to insufficient RBAC privileges.",
        sql_est_sbx: "Status: Query blocked by Sandbox policy.",
        sql_est_ok: "Status: Query executed successfully. Rows returned: {n}",
        sql_solo_admin: "Only an active Administrator can run SQL audit queries.",
        sql_bloq_tit: "Security Block",
        sql_bloq_msg: "Transaction aborted. Destructive operation detected.\nThis console is Read-Only (SELECT).",
        sql_solo_sel: "SQL Error: Only SELECT statements are allowed.",

        // BI Analytics
        bi_header: "CONTROL DASHBOARD — BI / OLAP ANALYTICS",
        bi_sub_ini: "Real-time statistical analysis",
        bi_sub_vacio: "No sales records available for analysis",
        bi_sub_top: "Top Seller: {prod} | Top Category: {cat}",
        bi_btn_act: "Refresh Analytics",
        bi_kpi_fac: "Total Revenue",
        bi_kpi_ops: "Transactions",
        bi_kpi_uni: "Units Sold",
        bi_kpi_tkt: "Average Ticket",
        bi_graf_top10: "Top 10 Products (Revenue)",
        bi_graf_mensual: "Monthly Trend",
        bi_graf_cat: "Revenue by Category",
        bi_detalle_tit: "Sales History Detail",
        bi_sin_datos: "No data",
        bi_info_vacio: "No sales records available for analysis.",
        col_id_venta: "Sale ID",
        col_precio_cong: "Frozen Price",
        col_fecha: "Date",
        col_total_cob: "Total Charged"
    }
};

function tWeb(clave, vars = {}) {
    const dic = TRADUCCIONES_WEB[prefUI.idioma] || TRADUCCIONES_WEB.es;
    let texto = dic[clave] !== undefined ? dic[clave] : (TRADUCCIONES_WEB.es[clave] || clave);
    Object.entries(vars).forEach(([k, v]) => {
        texto = texto.replaceAll(`{${k}}`, String(v));
    });
    return texto;
}

function rolAUI(rolCanonico) {
    if (!rolCanonico) return tWeb("sin_dato");
    return prefUI.idioma === "en" ? (ROLES_A_EN[rolCanonico] || rolCanonico) : rolCanonico;
}

function valorVisual(valor) {
    return valor && valor !== "S/D" ? valor : tWeb("sin_dato");
}

function guardarPreferenciasSesion() {
    try {
        sessionStorage.setItem("frankie_ui_prefs", JSON.stringify(prefUI));
    } catch {
        // Entornos restringidos sin sessionStorage: continúa en memoria RAM.
    }
}

function cargarPreferenciasSesion() {
    try {
        const guardado = sessionStorage.getItem("frankie_ui_prefs");
        if (guardado) {
            const parsed = JSON.parse(guardado);
            if (parsed.tema === "dark" || parsed.tema === "light") prefUI.tema = parsed.tema;
            if (typeof parsed.altoContraste === "boolean") prefUI.altoContraste = parsed.altoContraste;
            if (parsed.idioma === "es" || parsed.idioma === "en") prefUI.idioma = parsed.idioma;
            if (ESCALAS_WEB.includes(String(parsed.escala))) prefUI.escala = String(parsed.escala);
        }
    } catch {
        // Ignora errores de acceso a sessionStorage.
    }
}

function aplicarPreferenciasUI() {
    const root = document.documentElement;
    root.lang = prefUI.idioma;
    root.setAttribute("data-theme", prefUI.tema);
    root.setAttribute("data-contrast", prefUI.altoContraste ? "high" : "normal");
    root.setAttribute("data-scale", prefUI.escala);

    const btnIdioma = document.getElementById("btn-pref-idioma");
    const btnTema = document.getElementById("btn-pref-tema");
    const btnHC = document.getElementById("btn-pref-hc");

    if (btnIdioma) btnIdioma.textContent = tWeb("btn_idioma");
    if (btnTema) {
        btnTema.textContent = prefUI.tema === "light" ? tWeb("btn_tema_oscuro") : tWeb("btn_tema_claro");
        btnTema.setAttribute("aria-pressed", String(prefUI.tema === "dark"));
    }
    if (btnHC) {
        btnHC.classList.toggle("activo", prefUI.altoContraste);
        btnHC.setAttribute("aria-pressed", String(prefUI.altoContraste));
    }

    // Traducción declarativa de textos y placeholders en todo el DOM.
    document.querySelectorAll("[data-i18n]").forEach(el => {
        el.textContent = tWeb(el.getAttribute("data-i18n"));
    });
    document.querySelectorAll("[data-i18n-ph]").forEach(el => {
        el.setAttribute("placeholder", tWeb(el.getAttribute("data-i18n-ph")));
    });

    // Traducción de opciones visibles en selects preservando values canónicos.
    traducirSelectRolesEstatico("emp-rol");
    if (sesionActiva.id) {
        configurarComboRolesUsuarios(true);
        actualizarEncabezadosSesion();
    }

    // Actualiza mensajes dinámicos de Login, Consola, Facturación y BI.
    const infoIntentos = document.getElementById("login-intentos-info");
    if (infoIntentos) {
        const restantes = 3 - intentosFallidosLogin;
        infoIntentos.textContent = restantes > 0 ? tWeb("login_intentos", { n: restantes }) : tWeb("login_bloqueado");
    }

    actualizarEstadoSQLVisual();
    actualizarEtiquetasTotalesFactura(totalAcumuladoFacturacion, porcentajeGlobalActivo);

    // Re-renderiza tablas activas en RAM para actualizar idioma y etiquetas.
    if (cacheUsuarios.length > 0) renderizarTablaUsuarios();
    if (cacheEmpleados.length > 0) renderizarTablaEmpleados();
    if (cacheClientes.length > 0) renderizarTablaClientes();
    if (cacheProveedores.length > 0) renderizarTablaProveedores();
    if (cacheProductos.length > 0) renderizarTablaStock();
    if (cacheFacturas.length > 0) renderizarTablaFacturacion();
    if (cacheRegistrosBI.length > 0) {
        renderizarTablaBI();
        actualizarSubtituloBI();
    }

    // Redibuja los 3 gráficos BI con los colores del tema activo.
    const vistaBI = document.getElementById("vista-analitica");
    if (vistaBI && vistaBI.classList.contains("activa")) {
        redibujarGraficosBI();
    }
}

function traducirSelectRolesEstatico(idSelect) {
    const sel = document.getElementById(idSelect);
    if (!sel) return;
    Array.from(sel.options).forEach(opt => {
        if (!opt.value) {
            opt.textContent = tWeb("sel_rol");
        } else {
            opt.textContent = rolAUI(opt.value);
        }
    });
}

function actualizarEncabezadosSesion() {
    if (!sesionActiva.id) return;
    const nombreCompleto = `${sesionActiva.nombres} ${sesionActiva.apellidos}`.toUpperCase();
    const rolVis = rolAUI(sesionActiva.rol);
    document.getElementById("panel-saludo").textContent = tWeb("panel_saludo", { nombre: nombreCompleto });
    document.getElementById("panel-rol").textContent = tWeb("panel_sub", { rol: rolVis });
    document.getElementById("info-operador-activo").textContent =
        `${sesionActiva.nombres} ${sesionActiva.apellidos} (${rolVis})`;
}

function alternarIdiomaWeb() {
    prefUI.idioma = prefUI.idioma === "es" ? "en" : "es";
    guardarPreferenciasSesion();
    aplicarPreferenciasUI();
}

function alternarTemaWeb() {
    prefUI.tema = prefUI.tema === "light" ? "dark" : "light";
    guardarPreferenciasSesion();
    aplicarPreferenciasUI();
}

function alternarAltoContrasteWeb() {
    prefUI.altoContraste = !prefUI.altoContraste;
    guardarPreferenciasSesion();
    aplicarPreferenciasUI();
}

function ajustarEscalaWeb(delta) {
    const idxActual = ESCALAS_WEB.indexOf(prefUI.escala);
    const nuevoIdx = Math.max(0, Math.min(ESCALAS_WEB.length - 1, idxActual + delta));
    if (nuevoIdx !== idxActual) {
        prefUI.escala = ESCALAS_WEB[nuevoIdx];
        guardarPreferenciasSesion();
        aplicarPreferenciasUI();
    }
}


// ==============================================================================
//  2. CLIENTE HTTP ASÍNCRONO CENTRALIZADO (EQUIVALENTE A CLIENTE_API.PY)
// ==============================================================================

async function peticionAPI(ruta, metodo = "GET", cuerpo = null) {
    const cabeceras = {
        "Content-Type": "application/json",
        "X-Operador-Id": String(sesionActiva.id || 1)
    };

    const opciones = {
        method: metodo,
        headers: cabeceras
    };

    if (cuerpo !== null) {
        opciones.body = JSON.stringify(cuerpo);
    }

    let respuesta;
    try {
        respuesta = await fetch(`${URL_BASE_API}${ruta}`, opciones);
    } catch {
        throw new Error(`No se pudo conectar con el servidor Backend en ${URL_BASE_API}.`);
    }

    let datos = null;
    try {
        datos = await respuesta.json();
    } catch {
        datos = null;
    }

    if (respuesta.ok) {
        return datos;
    }

    let mensajeError = "Error desconocido en el servidor.";
    if (datos) {
        if (typeof datos.detalle === "string") {
            mensajeError = datos.detalle;
        } else if (typeof datos.detail === "string") {
            mensajeError = datos.detail;
        } else if (Array.isArray(datos.detail)) {
            mensajeError = datos.detail.map(e => `${(e.loc || []).slice(-1)[0]}: ${e.msg}`).join("; ");
        }
    }
    throw new Error(mensajeError);
}


// ==============================================================================
//  3. SISTEMA DE CUADROS DE DIÁLOGO (EQUIVALENTE A MESSAGEBOX)
// ==============================================================================

function mostrarAlerta(titulo, mensaje, tipo = "info") {
    const modal = document.getElementById("modal-alerta");
    const cabecera = document.getElementById("modal-cabecera");
    const txtTitulo = document.getElementById("modal-titulo");
    const txtMensaje = document.getElementById("modal-mensaje");

    cabecera.className = `modal-cabecera ${tipo}`;
    txtTitulo.textContent = titulo;
    txtMensaje.textContent = mensaje;
    modal.classList.remove("oculto");
    document.getElementById("btn-cerrar-modal").focus();
}

function cerrarAlerta() {
    document.getElementById("modal-alerta").classList.add("oculto");
}


// ==============================================================================
//  4. NAVEGACIÓN ENTRE VISTAS (SPA) Y MATRIZ DE PERMISOS RBAC
// ==============================================================================

function navegarA(idVista) {
    document.querySelectorAll(".vista-app").forEach(seccion => {
        seccion.classList.remove("activa");
    });

    const vistaDestino = document.getElementById(idVista);
    if (vistaDestino) {
        vistaDestino.classList.add("activa");
    }

    const infoOp = document.getElementById("info-operador-activo");
    const badgeServ = document.getElementById("badge-servidor");
    const btnVolverTop = document.getElementById("btn-volver-panel-top");

    if (idVista === "vista-login") {
        infoOp.classList.add("oculto");
        badgeServ.classList.add("oculto");
        btnVolverTop.classList.add("oculto");
    } else {
        infoOp.classList.remove("oculto");
        badgeServ.classList.remove("oculto");
        if (idVista === "vista-panel") {
            btnVolverTop.classList.add("oculto");
        } else {
            btnVolverTop.classList.remove("oculto");
        }
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function abrirModulo(idVista) {
    navegarA(idVista);

    if (idVista === "vista-usuarios") {
        configurarComboRolesUsuarios(false);
        limpiarFormularioUsuarios();
        document.getElementById("buscar-usuarios").value = "";
        await cargarDatosUsuarios();
    } else if (idVista === "vista-empleados") {
        limpiarFormularioEmpleados();
        document.getElementById("buscar-empleados").value = "";
        await cargarDatosEmpleados();
    } else if (idVista === "vista-clientes") {
        limpiarFormularioClientes();
        document.getElementById("buscar-clientes").value = "";
        await cargarDatosClientes();
    } else if (idVista === "vista-proveedores") {
        limpiarFormularioProveedores();
        document.getElementById("buscar-proveedores").value = "";
        await cargarDatosProveedores();
    } else if (idVista === "vista-stock") {
        limpiarFormularioStock();
        document.getElementById("buscar-stock").value = "";
        await cargarDatosStock();
    } else if (idVista === "vista-facturacion") {
        limpiarFormularioFacturacion();
        document.getElementById("buscar-facturacion").value = "";
        await cargarDatosFacturacion();
    } else if (idVista === "vista-consola") {
        limpiarConsolaSQL();
    } else if (idVista === "vista-analitica") {
        document.getElementById("buscar-bi").value = "";
        await cargarDatosAnalitica();
    }
}

function aplicarMatrizRBACPanel(rolUsuario) {
    const pClientes = ["Administrador", "Gerente", "Empleado - Ventas"].includes(rolUsuario);
    const pFacturacion = ["Administrador", "Gerente", "Empleado - Ventas"].includes(rolUsuario);
    const pProveedores = ["Administrador", "Gerente", "Empleado - Compras"].includes(rolUsuario);
    const pStock = ["Administrador", "Gerente", "Empleado - Compras"].includes(rolUsuario);
    const pEmpleados = ["Administrador", "Gerente"].includes(rolUsuario);
    const pUsuarios = ["Administrador", "Gerente"].includes(rolUsuario);
    const pRoot = rolUsuario === "Administrador";
    const pAnalitica = ["Administrador", "Gerente"].includes(rolUsuario);

    document.getElementById("btn-nav-clientes").disabled = !pClientes;
    document.getElementById("btn-nav-facturacion").disabled = !pFacturacion;
    document.getElementById("btn-nav-proveedores").disabled = !pProveedores;
    document.getElementById("btn-nav-stock").disabled = !pStock;
    document.getElementById("btn-nav-empleados").disabled = !pEmpleados;
    document.getElementById("btn-nav-usuarios").disabled = !pUsuarios;
    document.getElementById("btn-nav-consola").disabled = !pRoot;
    document.getElementById("btn-nav-backup").disabled = !pRoot;
    document.getElementById("btn-nav-analitica").disabled = !pAnalitica;
}


// ==============================================================================
//  5. MÓDULO DE LOGIN, CIERRE DE SESIÓN Y BACKUP JSON
// ==============================================================================

async function validarIngreso(evento) {
    evento.preventDefault();

    const inputUsuario = document.getElementById("login-usuario");
    const inputPassword = document.getElementById("login-password");
    const btnIngresar = document.getElementById("btn-login-ingresar");
    const infoIntentos = document.getElementById("login-intentos-info");

    const usuario = inputUsuario.value.trim();
    const password = inputPassword.value;

    if (!usuario || !password) {
        mostrarAlerta(tWeb("val_tit"), tWeb("login_completar"), "warning");
        return;
    }

    try {
        const datosPerfil = await peticionAPI("/api/perfiles/login", "POST", {
            usuario: usuario,
            password: password
        });

        intentosFallidosLogin = 0;
        infoIntentos.textContent = tWeb("login_intentos", { n: 3 });

        sesionActiva = {
            id: datosPerfil.id,
            usuario: datosPerfil.usuario,
            rol: datosPerfil.rol,
            nombres: datosPerfil.nombres,
            apellidos: datosPerfil.apellidos
        };

        inputUsuario.value = "";
        inputPassword.value = "";

        document.getElementById("badge-servidor").textContent = `API ${HOST_LAN}:8000`;
        actualizarEncabezadosSesion();
        aplicarMatrizRBACPanel(datosPerfil.rol);
        navegarA("vista-panel");

        mostrarAlerta(
            tWeb("login_ok_tit"),
            tWeb("login_ok_msg", {
                nombre: datosPerfil.nombres,
                apellido: datosPerfil.apellidos,
                rol: rolAUI(datosPerfil.rol)
            }),
            "info"
        );
    } catch {
        intentosFallidosLogin += 1;
        const restantes = 3 - intentosFallidosLogin;

        inputUsuario.value = "";
        inputPassword.value = "";
        inputUsuario.focus();

        if (restantes > 0) {
            infoIntentos.textContent = tWeb("login_intentos", { n: restantes });
            mostrarAlerta(tWeb("login_err_tit"), tWeb("login_err_msg", { n: restantes }), "error");
        } else {
            infoIntentos.textContent = tWeb("login_bloqueado");
            inputUsuario.disabled = true;
            inputPassword.disabled = true;
            btnIngresar.disabled = true;
            mostrarAlerta(tWeb("login_bloq_tit"), tWeb("login_bloq_msg"), "error");
        }
    }
}

function cerrarSesion() {
    sesionActiva = { id: null, usuario: null, rol: null, nombres: null, apellidos: null };
    navegarA("vista-login");
}

async function generarBackupWeb() {
    try {
        const [perfiles, productos, facturas] = await Promise.all([
            peticionAPI("/api/perfiles"),
            peticionAPI("/api/productos"),
            peticionAPI("/api/facturas")
        ]);

        const respaldoJSON = {
            sistema: "Frankie Gestor",
            fecha_exportacion: new Date().toISOString(),
            operador_id: sesionActiva.id,
            datos: { perfiles, productos, facturas }
        };

        const blob = new Blob([JSON.stringify(respaldoJSON, null, 2)], { type: "application/json" });
        const urlDescarga = URL.createObjectURL(blob);
        const enlace = document.createElement("a");
        const marcaTiempo = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
        const nombreArchivo = `backup_frankie_${marcaTiempo}.json`;

        enlace.href = urlDescarga;
        enlace.download = nombreArchivo;
        document.body.appendChild(enlace);
        enlace.click();
        document.body.removeChild(enlace);
        URL.revokeObjectURL(urlDescarga);

        mostrarAlerta(tWeb("bkp_ok_tit"), tWeb("bkp_ok_msg", { archivo: nombreArchivo }), "info");
    } catch (error) {
        mostrarAlerta(tWeb("bkp_err_tit"), error.message, "error");
    }
}


// ==============================================================================
//  6. MÓDULO DE GESTIÓN DE USUARIOS (IAM)
// ==============================================================================

function configurarComboRolesUsuarios(conservarSeleccion = false) {
    const selectRol = document.getElementById("usu-rol");
    if (!selectRol) return;
    const valorPrevio = conservarSeleccion ? selectRol.value : "";

    selectRol.innerHTML = `<option value="">${tWeb("sel_rol")}</option>`;

    let rolesPermitidos = ["Empleado - Ventas", "Empleado - Compras"];
    if (sesionActiva.rol === "Administrador") {
        rolesPermitidos = ["Administrador", "Gerente", ...rolesPermitidos];
    }

    rolesPermitidos.forEach(rol => {
        const opt = document.createElement("option");
        opt.value = rol;
        opt.textContent = rolAUI(rol);
        selectRol.appendChild(opt);
    });

    if (valorPrevio) selectRol.value = valorPrevio;
}

function limpiarFormularioUsuarios() {
    document.getElementById("usu-id-seleccionado").value = "";
    document.getElementById("usu-nombres").value = "";
    document.getElementById("usu-apellidos").value = "";
    document.getElementById("usu-usuario").value = "";
    document.getElementById("usu-password").value = "";
    document.getElementById("usu-rol").value = "";
    desmarcarFilasTabla("tabla-usuarios");
}

function renderizarTablaUsuarios() {
    const tbody = document.querySelector("#tabla-usuarios tbody");
    const filtro = (document.getElementById("buscar-usuarios").value || "").trim().toLowerCase();
    tbody.innerHTML = "";
    let visibles = 0;

    cacheUsuarios.forEach(p => {
        const usuarioMostrar = p.usuario ? p.usuario : tWeb("sin_cred");
        const rolVis = rolAUI(p.rol);
        const texto = `${p.id} ${usuarioMostrar} ${rolVis} ${p.rol} ${p.nombres} ${p.apellidos}`.toLowerCase();
        if (filtro && !texto.includes(filtro)) return;

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${p.id}</td>
            <td>${usuarioMostrar}</td>
            <td>${rolVis}</td>
            <td>${p.nombres}</td>
            <td>${p.apellidos}</td>
        `;

        tr.addEventListener("click", () => {
            marcarFilaSeleccionada("tabla-usuarios", tr);
            document.getElementById("usu-id-seleccionado").value = p.id;
            document.getElementById("usu-usuario").value = p.usuario || "";
            document.getElementById("usu-rol").value = p.rol;
            document.getElementById("usu-nombres").value = p.nombres;
            document.getElementById("usu-apellidos").value = p.apellidos;
            document.getElementById("usu-password").value = "";
        });

        tbody.appendChild(tr);
        visibles += 1;
    });

    document.getElementById("contador-usuarios").textContent =
        tWeb("contador_filas", { visibles, total: cacheUsuarios.length });
}

async function cargarDatosUsuarios() {
    try {
        const perfiles = await peticionAPI("/api/perfiles");
        cacheUsuarios = perfiles.filter(p => !["Cliente", "Proveedor"].includes(p.rol));
        renderizarTablaUsuarios();
    } catch (error) {
        mostrarAlerta(tWeb("err_com_tit"), error.message, "error");
    }
}

async function guardarUsuario() {
    const nombres = document.getElementById("usu-nombres").value.trim();
    const apellidos = document.getElementById("usu-apellidos").value.trim();
    const usuario = document.getElementById("usu-usuario").value.trim();
    const password = document.getElementById("usu-password").value.trim();
    const rol = document.getElementById("usu-rol").value;

    if (!nombres || !apellidos || !usuario || !password || !rol) {
        mostrarAlerta(tWeb("val_tit"), tWeb("usu_todos_req"), "warning");
        return;
    }

    if (sesionActiva.rol === "Gerente" && ["Administrador", "Gerente"].includes(rol)) {
        mostrarAlerta(tWeb("err_acc_tit"), tWeb("usu_priv_err"), "error");
        limpiarFormularioUsuarios();
        return;
    }

    try {
        await peticionAPI("/api/perfiles", "POST", {
            nombres,
            apellidos,
            dni: "00000000",
            rol,
            usuario,
            password_plana: password
        });
        limpiarFormularioUsuarios();
        await cargarDatosUsuarios();
    } catch (error) {
        mostrarAlerta(tWeb("err_gua_tit"), error.message, "error");
    }
}

async function modificarUsuario() {
    const idDestino = document.getElementById("usu-id-seleccionado").value;
    if (!idDestino) {
        mostrarAlerta(tWeb("err_sel_tit"), tWeb("usu_sel_req"), "warning");
        return;
    }

    const nombres = document.getElementById("usu-nombres").value.trim();
    const apellidos = document.getElementById("usu-apellidos").value.trim();
    const usuario = document.getElementById("usu-usuario").value.trim();
    const password = document.getElementById("usu-password").value.trim();
    const rol = document.getElementById("usu-rol").value;

    if (!nombres || !apellidos || !usuario || !rol) {
        mostrarAlerta(tWeb("val_tit"), tWeb("usu_mod_req"), "warning");
        return;
    }

    const payload = { nombres, apellidos, rol, usuario };
    if (password) payload.password_plana = password;

    try {
        await peticionAPI(`/api/perfiles/${idDestino}`, "PUT", payload);
        limpiarFormularioUsuarios();
        await cargarDatosUsuarios();
    } catch (error) {
        mostrarAlerta(tWeb("err_acc_err_tit"), error.message, "error");
    }
}

async function eliminarUsuario() {
    const idDestino = document.getElementById("usu-id-seleccionado").value;
    if (!idDestino) {
        mostrarAlerta(tWeb("err_sel_tit"), tWeb("usu_sel_req"), "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idDestino}`, "DELETE");
        limpiarFormularioUsuarios();
        await cargarDatosUsuarios();
    } catch (error) {
        mostrarAlerta(tWeb("err_bloq_tit"), error.message, "error");
    }
}


// ==============================================================================
//  7. MÓDULO DE RECURSOS HUMANOS (EMPLEADOS — PERSISTENCIA 3FN)
// ==============================================================================

function limpiarFormularioEmpleados() {
    document.getElementById("emp-id-seleccionado").value = "";
    ["emp-nombres", "emp-apellidos", "emp-dni", "emp-telefono", "emp-email",
     "emp-direccion", "emp-ciudad", "emp-provincia", "emp-cp", "emp-rol"].forEach(id => {
        document.getElementById(id).value = "";
    });
    desmarcarFilasTabla("tabla-empleados");
}

function renderizarTablaEmpleados() {
    const tbody = document.querySelector("#tabla-empleados tbody");
    const filtro = (document.getElementById("buscar-empleados").value || "").trim().toLowerCase();
    tbody.innerHTML = "";
    let visibles = 0;

    cacheEmpleados.forEach(p => {
        const fila = {
            nombres: valorVisual(p.nombres),
            apellidos: valorVisual(p.apellidos),
            dni: valorVisual(p.dni),
            telefono: valorVisual(p.telefono),
            email: valorVisual(p.email),
            direccion: valorVisual(p.direccion),
            ciudad: valorVisual(p.ciudad),
            provincia: valorVisual(p.provincia),
            cp: valorVisual(p.cp),
            rolVis: rolAUI(p.rol)
        };
        const texto = `${p.id} ${Object.values(fila).join(" ")} ${p.rol || ""}`.toLowerCase();
        if (filtro && !texto.includes(filtro)) return;

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${p.id}</td>
            <td>${fila.nombres}</td>
            <td>${fila.apellidos}</td>
            <td>${fila.dni}</td>
            <td>${fila.telefono}</td>
            <td>${fila.email}</td>
            <td>${fila.direccion}</td>
            <td>${fila.ciudad}</td>
            <td>${fila.provincia}</td>
            <td>${fila.cp}</td>
            <td>${fila.rolVis}</td>
        `;

        tr.addEventListener("click", () => {
            marcarFilaSeleccionada("tabla-empleados", tr);
            document.getElementById("emp-id-seleccionado").value = p.id;
            document.getElementById("emp-nombres").value = p.nombres && p.nombres !== "S/D" ? p.nombres : "";
            document.getElementById("emp-apellidos").value = p.apellidos && p.apellidos !== "S/D" ? p.apellidos : "";
            document.getElementById("emp-dni").value = p.dni && p.dni !== "S/D" ? p.dni : "";
            document.getElementById("emp-telefono").value = p.telefono && p.telefono !== "S/D" ? p.telefono : "";
            document.getElementById("emp-email").value = p.email && p.email !== "S/D" ? p.email : "";
            document.getElementById("emp-direccion").value = p.direccion && p.direccion !== "S/D" ? p.direccion : "";
            document.getElementById("emp-ciudad").value = p.ciudad && p.ciudad !== "S/D" ? p.ciudad : "";
            document.getElementById("emp-provincia").value = p.provincia && p.provincia !== "S/D" ? p.provincia : "";
            document.getElementById("emp-cp").value = p.cp && p.cp !== "S/D" ? p.cp : "";
            document.getElementById("emp-rol").value = p.rol || "";
        });

        tbody.appendChild(tr);
        visibles += 1;
    });

    document.getElementById("contador-empleados").textContent =
        tWeb("contador_filas", { visibles, total: cacheEmpleados.length });
}

async function cargarDatosEmpleados() {
    try {
        const perfiles = await peticionAPI("/api/perfiles");
        cacheEmpleados = perfiles.filter(p => !["Cliente", "Proveedor"].includes(p.rol));
        renderizarTablaEmpleados();
    } catch (error) {
        mostrarAlerta(tWeb("err_com_tit"), error.message, "error");
    }
}

async function guardarEmpleado() {
    const nombres = document.getElementById("emp-nombres").value.trim();
    const apellidos = document.getElementById("emp-apellidos").value.trim();
    const dni = document.getElementById("emp-dni").value.trim() || "S/D";
    const telefono = document.getElementById("emp-telefono").value.trim() || "S/D";
    const email = document.getElementById("emp-email").value.trim() || "S/D";
    const direccion = document.getElementById("emp-direccion").value.trim() || "S/D";
    const ciudad = document.getElementById("emp-ciudad").value.trim() || "S/D";
    const provincia = document.getElementById("emp-provincia").value.trim() || "S/D";
    const cp = document.getElementById("emp-cp").value.trim() || "S/D";
    const rol = document.getElementById("emp-rol").value;

    if (!nombres || !apellidos || !rol) {
        mostrarAlerta(tWeb("val_tit"), tWeb("emp_req"), "warning");
        return;
    }

    if (sesionActiva.rol === "Gerente" && ["Administrador", "Gerente"].includes(rol)) {
        mostrarAlerta(tWeb("err_acc_tit"), tWeb("emp_priv_err"), "error");
        limpiarFormularioEmpleados();
        return;
    }

    try {
        await peticionAPI("/api/perfiles", "POST", {
            nombres, apellidos, dni, rol,
            telefono, email, direccion, ciudad, provincia, cp
        });
        limpiarFormularioEmpleados();
        await cargarDatosEmpleados();
    } catch (error) {
        mostrarAlerta(tWeb("err_tx_tit"), error.message, "error");
    }
}

async function modificarEmpleado() {
    const idEmpleado = document.getElementById("emp-id-seleccionado").value;
    if (!idEmpleado) {
        mostrarAlerta(tWeb("err_sel_tit"), tWeb("emp_sel_req"), "warning");
        return;
    }

    const nombres = document.getElementById("emp-nombres").value.trim();
    const apellidos = document.getElementById("emp-apellidos").value.trim();
    const dni = document.getElementById("emp-dni").value.trim() || "S/D";
    const telefono = document.getElementById("emp-telefono").value.trim() || "S/D";
    const email = document.getElementById("emp-email").value.trim() || "S/D";
    const direccion = document.getElementById("emp-direccion").value.trim() || "S/D";
    const ciudad = document.getElementById("emp-ciudad").value.trim() || "S/D";
    const provincia = document.getElementById("emp-provincia").value.trim() || "S/D";
    const cp = document.getElementById("emp-cp").value.trim() || "S/D";
    const rol = document.getElementById("emp-rol").value;

    if (!nombres || !apellidos || !rol) {
        mostrarAlerta(tWeb("val_tit"), tWeb("emp_req"), "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idEmpleado}`, "PUT", {
            nombres, apellidos, dni, rol,
            telefono, email, direccion, ciudad, provincia, cp
        });
        limpiarFormularioEmpleados();
        await cargarDatosEmpleados();
    } catch (error) {
        mostrarAlerta(tWeb("err_acc_err_tit"), error.message, "error");
    }
}

async function eliminarEmpleado() {
    const idEmpleado = document.getElementById("emp-id-seleccionado").value;
    if (!idEmpleado) {
        mostrarAlerta(tWeb("err_sel_tit"), tWeb("emp_sel_req"), "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idEmpleado}`, "DELETE");
        limpiarFormularioEmpleados();
        await cargarDatosEmpleados();
    } catch (error) {
        mostrarAlerta(tWeb("err_bloq_tit"), error.message, "error");
    }
}


// ==============================================================================
//  8. MÓDULO DE GESTIÓN DE CLIENTES (PERSISTENCIA 3FN)
// ==============================================================================

function limpiarFormularioClientes() {
    document.getElementById("cli-id-seleccionado").value = "";
    ["cli-nombres", "cli-apellidos", "cli-dni", "cli-telefono", "cli-email",
     "cli-direccion", "cli-ciudad", "cli-provincia", "cli-cp"].forEach(id => {
        document.getElementById(id).value = "";
    });
    desmarcarFilasTabla("tabla-clientes");
}

function renderizarTablaClientes() {
    const tbody = document.querySelector("#tabla-clientes tbody");
    const filtro = (document.getElementById("buscar-clientes").value || "").trim().toLowerCase();
    tbody.innerHTML = "";
    let visibles = 0;

    cacheClientes.forEach(c => {
        const fila = {
            nombres: valorVisual(c.nombres),
            apellidos: valorVisual(c.apellidos),
            dni: valorVisual(c.dni),
            telefono: valorVisual(c.telefono),
            email: valorVisual(c.email),
            direccion: valorVisual(c.direccion),
            ciudad: valorVisual(c.ciudad),
            provincia: valorVisual(c.provincia),
            cp: valorVisual(c.cp)
        };
        const texto = `${c.id} ${Object.values(fila).join(" ")}`.toLowerCase();
        if (filtro && !texto.includes(filtro)) return;

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${c.id}</td>
            <td>${fila.nombres}</td>
            <td>${fila.apellidos}</td>
            <td>${fila.dni}</td>
            <td>${fila.telefono}</td>
            <td>${fila.email}</td>
            <td>${fila.direccion}</td>
            <td>${fila.ciudad}</td>
            <td>${fila.provincia}</td>
            <td>${fila.cp}</td>
        `;

        tr.addEventListener("click", () => {
            marcarFilaSeleccionada("tabla-clientes", tr);
            document.getElementById("cli-id-seleccionado").value = c.id;
            document.getElementById("cli-nombres").value = c.nombres && c.nombres !== "S/D" ? c.nombres : "";
            document.getElementById("cli-apellidos").value = c.apellidos && c.apellidos !== "S/D" ? c.apellidos : "";
            document.getElementById("cli-dni").value = c.dni && c.dni !== "S/D" ? c.dni : "";
            document.getElementById("cli-telefono").value = c.telefono && c.telefono !== "S/D" ? c.telefono : "";
            document.getElementById("cli-email").value = c.email && c.email !== "S/D" ? c.email : "";
            document.getElementById("cli-direccion").value = c.direccion && c.direccion !== "S/D" ? c.direccion : "";
            document.getElementById("cli-ciudad").value = c.ciudad && c.ciudad !== "S/D" ? c.ciudad : "";
            document.getElementById("cli-provincia").value = c.provincia && c.provincia !== "S/D" ? c.provincia : "";
            document.getElementById("cli-cp").value = c.cp && c.cp !== "S/D" ? c.cp : "";
        });

        tbody.appendChild(tr);
        visibles += 1;
    });

    document.getElementById("contador-clientes").textContent =
        tWeb("contador_filas", { visibles, total: cacheClientes.length });
}

async function cargarDatosClientes() {
    try {
        cacheClientes = await peticionAPI("/api/perfiles/rol/Cliente");
        renderizarTablaClientes();
    } catch (error) {
        mostrarAlerta(tWeb("err_com_tit"), error.message, "error");
    }
}

async function guardarCliente() {
    const nombres = document.getElementById("cli-nombres").value.trim();
    const apellidos = document.getElementById("cli-apellidos").value.trim();
    const dni = document.getElementById("cli-dni").value.trim() || "S/D";
    const telefono = document.getElementById("cli-telefono").value.trim() || "S/D";
    const email = document.getElementById("cli-email").value.trim() || "S/D";
    const direccion = document.getElementById("cli-direccion").value.trim() || "S/D";
    const ciudad = document.getElementById("cli-ciudad").value.trim() || "S/D";
    const provincia = document.getElementById("cli-provincia").value.trim() || "S/D";
    const cp = document.getElementById("cli-cp").value.trim() || "S/D";

    if (!nombres || !apellidos) {
        mostrarAlerta(tWeb("val_tit"), tWeb("cli_req"), "warning");
        return;
    }

    try {
        await peticionAPI("/api/perfiles", "POST", {
            nombres, apellidos, dni, rol: "Cliente",
            telefono, email, direccion, ciudad, provincia, cp
        });
        limpiarFormularioClientes();
        await cargarDatosClientes();
    } catch (error) {
        mostrarAlerta(tWeb("err_tx_tit"), error.message, "error");
    }
}

async function modificarCliente() {
    const idCliente = document.getElementById("cli-id-seleccionado").value;
    if (!idCliente) {
        mostrarAlerta(tWeb("err_sel_tit"), tWeb("cli_sel_req"), "warning");
        return;
    }

    const nombres = document.getElementById("cli-nombres").value.trim();
    const apellidos = document.getElementById("cli-apellidos").value.trim();
    const dni = document.getElementById("cli-dni").value.trim() || "S/D";
    const telefono = document.getElementById("cli-telefono").value.trim() || "S/D";
    const email = document.getElementById("cli-email").value.trim() || "S/D";
    const direccion = document.getElementById("cli-direccion").value.trim() || "S/D";
    const ciudad = document.getElementById("cli-ciudad").value.trim() || "S/D";
    const provincia = document.getElementById("cli-provincia").value.trim() || "S/D";
    const cp = document.getElementById("cli-cp").value.trim() || "S/D";

    if (!nombres || !apellidos) {
        mostrarAlerta(tWeb("val_tit"), tWeb("cli_req"), "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idCliente}`, "PUT", {
            nombres, apellidos, dni, rol: "Cliente",
            telefono, email, direccion, ciudad, provincia, cp
        });
        limpiarFormularioClientes();
        await cargarDatosClientes();
    } catch (error) {
        mostrarAlerta(tWeb("err_act_tit"), error.message, "error");
    }
}

async function eliminarCliente() {
    const idCliente = document.getElementById("cli-id-seleccionado").value;
    if (!idCliente) {
        mostrarAlerta(tWeb("err_sel_tit"), tWeb("cli_sel_req"), "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idCliente}`, "DELETE");
        limpiarFormularioClientes();
        await cargarDatosClientes();
    } catch (error) {
        mostrarAlerta(tWeb("err_bloq_tit"), error.message, "error");
    }
}


// ==============================================================================
//  9. MÓDULO DE GESTIÓN DE PROVEEDORES (PERSISTENCIA 3FN)
// ==============================================================================

function limpiarFormularioProveedores() {
    document.getElementById("prov-id-seleccionado").value = "";
    ["prov-razon-social", "prov-cuit", "prov-telefono", "prov-email",
     "prov-direccion", "prov-ciudad", "prov-provincia", "prov-cp", "prov-contacto"].forEach(id => {
        document.getElementById(id).value = "";
    });
    desmarcarFilasTabla("tabla-proveedores");
}

function renderizarTablaProveedores() {
    const tbody = document.querySelector("#tabla-proveedores tbody");
    const filtro = (document.getElementById("buscar-proveedores").value || "").trim().toLowerCase();
    tbody.innerHTML = "";
    let visibles = 0;

    cacheProveedores.forEach(p => {
        const fila = {
            razonSocial: valorVisual(p.nombres),
            cuit: valorVisual(p.dni),
            telefono: valorVisual(p.telefono),
            email: valorVisual(p.email),
            direccion: valorVisual(p.direccion),
            ciudad: valorVisual(p.ciudad),
            provincia: valorVisual(p.provincia),
            cp: valorVisual(p.cp),
            contacto: valorVisual(p.apellidos)
        };
        const texto = `${p.id} ${Object.values(fila).join(" ")}`.toLowerCase();
        if (filtro && !texto.includes(filtro)) return;

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${p.id}</td>
            <td>${fila.razonSocial}</td>
            <td>${fila.cuit}</td>
            <td>${fila.telefono}</td>
            <td>${fila.email}</td>
            <td>${fila.direccion}</td>
            <td>${fila.ciudad}</td>
            <td>${fila.provincia}</td>
            <td>${fila.cp}</td>
            <td>${fila.contacto}</td>
        `;

        tr.addEventListener("click", () => {
            marcarFilaSeleccionada("tabla-proveedores", tr);
            document.getElementById("prov-id-seleccionado").value = p.id;
            document.getElementById("prov-razon-social").value = p.nombres && p.nombres !== "S/D" ? p.nombres : "";
            document.getElementById("prov-cuit").value = p.dni && p.dni !== "S/D" ? p.dni : "";
            document.getElementById("prov-telefono").value = p.telefono && p.telefono !== "S/D" ? p.telefono : "";
            document.getElementById("prov-email").value = p.email && p.email !== "S/D" ? p.email : "";
            document.getElementById("prov-direccion").value = p.direccion && p.direccion !== "S/D" ? p.direccion : "";
            document.getElementById("prov-ciudad").value = p.ciudad && p.ciudad !== "S/D" ? p.ciudad : "";
            document.getElementById("prov-provincia").value = p.provincia && p.provincia !== "S/D" ? p.provincia : "";
            document.getElementById("prov-cp").value = p.cp && p.cp !== "S/D" ? p.cp : "";
            document.getElementById("prov-contacto").value = p.apellidos && p.apellidos !== "S/D" ? p.apellidos : "";
        });

        tbody.appendChild(tr);
        visibles += 1;
    });

    document.getElementById("contador-proveedores").textContent =
        tWeb("contador_filas", { visibles, total: cacheProveedores.length });
}

async function cargarDatosProveedores() {
    try {
        cacheProveedores = await peticionAPI("/api/perfiles/rol/Proveedor");
        renderizarTablaProveedores();
    } catch (error) {
        mostrarAlerta(tWeb("err_com_tit"), error.message, "error");
    }
}

async function guardarProveedor() {
    const razonSocial = document.getElementById("prov-razon-social").value.trim();
    const cuit = document.getElementById("prov-cuit").value.trim() || "S/D";
    const telefono = document.getElementById("prov-telefono").value.trim() || "S/D";
    const email = document.getElementById("prov-email").value.trim() || "S/D";
    const direccion = document.getElementById("prov-direccion").value.trim() || "S/D";
    const ciudad = document.getElementById("prov-ciudad").value.trim() || "S/D";
    const provincia = document.getElementById("prov-provincia").value.trim() || "S/D";
    const cp = document.getElementById("prov-cp").value.trim() || "S/D";
    const contacto = document.getElementById("prov-contacto").value.trim() || "S/D";

    if (!razonSocial) {
        mostrarAlerta(tWeb("val_tit"), tWeb("prov_req"), "warning");
        return;
    }

    try {
        await peticionAPI("/api/perfiles", "POST", {
            nombres: razonSocial,
            apellidos: contacto,
            dni: cuit,
            rol: "Proveedor",
            telefono, email, direccion, ciudad, provincia, cp
        });
        limpiarFormularioProveedores();
        await cargarDatosProveedores();
    } catch (error) {
        mostrarAlerta(tWeb("err_tx_tit"), error.message, "error");
    }
}

async function modificarProveedor() {
    const idProveedor = document.getElementById("prov-id-seleccionado").value;
    if (!idProveedor) {
        mostrarAlerta(tWeb("err_sel_tit"), tWeb("prov_sel_req"), "warning");
        return;
    }

    const razonSocial = document.getElementById("prov-razon-social").value.trim();
    const cuit = document.getElementById("prov-cuit").value.trim() || "S/D";
    const telefono = document.getElementById("prov-telefono").value.trim() || "S/D";
    const email = document.getElementById("prov-email").value.trim() || "S/D";
    const direccion = document.getElementById("prov-direccion").value.trim() || "S/D";
    const ciudad = document.getElementById("prov-ciudad").value.trim() || "S/D";
    const provincia = document.getElementById("prov-provincia").value.trim() || "S/D";
    const cp = document.getElementById("prov-cp").value.trim() || "S/D";
    const contacto = document.getElementById("prov-contacto").value.trim() || "S/D";

    if (!razonSocial) {
        mostrarAlerta(tWeb("val_tit"), tWeb("prov_req"), "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idProveedor}`, "PUT", {
            nombres: razonSocial,
            apellidos: contacto,
            dni: cuit,
            rol: "Proveedor",
            telefono, email, direccion, ciudad, provincia, cp
        });
        limpiarFormularioProveedores();
        await cargarDatosProveedores();
    } catch (error) {
        mostrarAlerta(tWeb("err_act_tit"), error.message, "error");
    }
}

async function eliminarProveedor() {
    const idProveedor = document.getElementById("prov-id-seleccionado").value;
    if (!idProveedor) {
        mostrarAlerta(tWeb("err_sel_tit"), tWeb("prov_sel_req"), "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idProveedor}`, "DELETE");
        limpiarFormularioProveedores();
        await cargarDatosProveedores();
    } catch (error) {
        mostrarAlerta(tWeb("err_bloq_tit"), error.message, "error");
    }
}


// ==============================================================================
//  10. MÓDULO DE CONTROL DE STOCK E INVENTARIO (3FN + SEMÁFORO DE STOCK)
// ==============================================================================

function limpiarFormularioStock() {
    document.getElementById("stk-id-seleccionado").value = "";
    ["stk-codigo", "stk-descripcion", "stk-categoria", "stk-proveedor",
     "stk-actual", "stk-minimo", "stk-costo", "stk-venta",
     "stk-ubicacion", "stk-vencimiento"].forEach(id => {
        document.getElementById(id).value = "";
    });
    desmarcarFilasTabla("tabla-stock");
}

function renderizarTablaStock() {
    const tbody = document.querySelector("#tabla-stock tbody");
    const filtro = (document.getElementById("buscar-stock").value || "").trim().toLowerCase();
    tbody.innerHTML = "";
    let visibles = 0;

    cacheProductos.forEach(prod => {
        const nombreProv = mapaProveedoresIdANombre[prod.id_proveedor] || `ID ${prod.id_proveedor}`;
        const ubicacion = valorVisual(prod.ubicacion);
        const vencimiento = valorVisual(prod.vencimiento);
        const categoria = valorVisual(prod.categoria);
        const stAct = Number(prod.stock_actual || 0);
        const stMin = Number(prod.stock_minimo || 0);

        const texto = `${prod.id} ${prod.codigo} ${prod.descripcion} ${categoria} ${nombreProv} ${ubicacion} ${vencimiento}`.toLowerCase();
        if (filtro && !texto.includes(filtro)) return;

        const tr = document.createElement("tr");
        if (stAct <= 0) {
            tr.classList.add("fila-stock-agotado");
        } else if (stAct <= stMin) {
            tr.classList.add("fila-stock-bajo");
        }

        tr.innerHTML = `
            <td>${prod.id}</td>
            <td>${prod.codigo}</td>
            <td>${prod.descripcion}</td>
            <td>${categoria}</td>
            <td>${nombreProv}</td>
            <td>${prod.stock_actual}</td>
            <td>${prod.stock_minimo}</td>
            <td>$ ${Number(prod.precio_costo).toFixed(2)}</td>
            <td>$ ${Number(prod.precio_venta).toFixed(2)}</td>
            <td>${ubicacion}</td>
            <td>${vencimiento}</td>
        `;

        tr.addEventListener("click", () => {
            marcarFilaSeleccionada("tabla-stock", tr);
            document.getElementById("stk-id-seleccionado").value = prod.id;
            document.getElementById("stk-codigo").value = prod.codigo;
            document.getElementById("stk-descripcion").value = prod.descripcion;
            document.getElementById("stk-categoria").value = prod.categoria && prod.categoria !== "S/D" ? prod.categoria : "";
            document.getElementById("stk-proveedor").value = nombreProv;
            document.getElementById("stk-actual").value = prod.stock_actual;
            document.getElementById("stk-minimo").value = prod.stock_minimo;
            document.getElementById("stk-costo").value = prod.precio_costo;
            document.getElementById("stk-venta").value = prod.precio_venta;
            document.getElementById("stk-ubicacion").value = prod.ubicacion && prod.ubicacion !== "S/D" ? prod.ubicacion : "";
            document.getElementById("stk-vencimiento").value = prod.vencimiento && prod.vencimiento !== "S/D" ? prod.vencimiento : "";
        });

        tbody.appendChild(tr);
        visibles += 1;
    });

    document.getElementById("contador-stock").textContent =
        tWeb("contador_filas", { visibles, total: cacheProductos.length });
}

async function cargarDatosStock() {
    const selectProv = document.getElementById("stk-proveedor");
    selectProv.innerHTML = `<option value="">${tWeb("stk_sel_prov")}</option>`;

    mapaProveedoresNombreAId = {};
    mapaProveedoresIdANombre = {};
    stockPrevioPorId = {};

    try {
        const [proveedores, productos] = await Promise.all([
            peticionAPI("/api/perfiles/rol/Proveedor"),
            peticionAPI("/api/productos")
        ]);

        proveedores.forEach(prov => {
            const nombre = (prov.nombres || "").trim();
            if (nombre) {
                mapaProveedoresNombreAId[nombre] = prov.id;
                mapaProveedoresIdANombre[prov.id] = nombre;
                const opt = document.createElement("option");
                opt.value = nombre;
                opt.textContent = nombre;
                selectProv.appendChild(opt);
            }
        });

        productos.forEach(prod => {
            stockPrevioPorId[prod.id] = Number(prod.stock_actual || 0);
        });
        cacheProductos = productos;
        renderizarTablaStock();
    } catch (error) {
        mostrarAlerta(tWeb("err_com_tit"), error.message, "error");
    }
}

async function guardarProducto() {
    const codigo = document.getElementById("stk-codigo").value.trim();
    const descripcion = document.getElementById("stk-descripcion").value.trim();
    const categoria = document.getElementById("stk-categoria").value.trim() || "S/D";
    const proveedor = document.getElementById("stk-proveedor").value.trim();
    const stockActualStr = document.getElementById("stk-actual").value.trim();
    const stockMinimoStr = document.getElementById("stk-minimo").value.trim();
    const costoStr = document.getElementById("stk-costo").value.trim();
    const ventaStr = document.getElementById("stk-venta").value.trim();
    const ubicacion = document.getElementById("stk-ubicacion").value.trim() || "S/D";
    const vencimiento = document.getElementById("stk-vencimiento").value.trim() || "S/D";

    if (!codigo || !descripcion || !proveedor) {
        mostrarAlerta(tWeb("val_tit"), tWeb("stk_req"), "warning");
        return;
    }

    const idProveedor = mapaProveedoresNombreAId[proveedor];
    if (!idProveedor) {
        mostrarAlerta(tWeb("err_tx_tit"), tWeb("stk_prov_inv"), "error");
        return;
    }

    const stockActual = stockActualStr ? Number(stockActualStr) : 0.0;
    const stockMinimo = stockMinimoStr ? Number(stockMinimoStr) : 0.0;
    const precioCosto = costoStr ? Number(costoStr) : 0.0;
    const precioVenta = ventaStr ? Number(ventaStr) : 0.0;

    if ([stockActual, stockMinimo, precioCosto, precioVenta].some(isNaN)) {
        mostrarAlerta(tWeb("err_fmt_tit"), tWeb("stk_nums_err"), "error");
        return;
    }

    try {
        await peticionAPI("/api/productos", "POST", {
            codigo,
            descripcion,
            categoria,
            id_proveedor: idProveedor,
            precio_costo: precioCosto,
            precio_venta: precioVenta,
            stock_actual: stockActual,
            stock_minimo: stockMinimo,
            ubicacion,
            vencimiento
        });
        limpiarFormularioStock();
        await cargarDatosStock();
    } catch (error) {
        mostrarAlerta(tWeb("err_tx_tit"), error.message, "error");
    }
}

async function modificarProducto() {
    const idProducto = document.getElementById("stk-id-seleccionado").value;
    if (!idProducto) {
        mostrarAlerta(tWeb("err_sel_tit"), tWeb("stk_sel_req"), "warning");
        return;
    }

    const codigo = document.getElementById("stk-codigo").value.trim();
    const descripcion = document.getElementById("stk-descripcion").value.trim();
    const categoria = document.getElementById("stk-categoria").value.trim() || "S/D";
    const proveedor = document.getElementById("stk-proveedor").value.trim();
    const stockActualStr = document.getElementById("stk-actual").value.trim();
    const stockMinimoStr = document.getElementById("stk-minimo").value.trim();
    const costoStr = document.getElementById("stk-costo").value.trim();
    const ventaStr = document.getElementById("stk-venta").value.trim();
    const ubicacion = document.getElementById("stk-ubicacion").value.trim() || "S/D";
    const vencimiento = document.getElementById("stk-vencimiento").value.trim() || "S/D";

    if (!codigo || !descripcion || !proveedor) {
        mostrarAlerta(tWeb("val_tit"), tWeb("stk_req"), "warning");
        return;
    }

    const idProveedor = mapaProveedoresNombreAId[proveedor];
    if (!idProveedor) {
        mostrarAlerta(tWeb("err_tx_tit"), tWeb("stk_prov_inv"), "error");
        return;
    }

    const stockActual = stockActualStr ? Number(stockActualStr) : 0.0;
    const stockMinimo = stockMinimoStr ? Number(stockMinimoStr) : 0.0;
    const precioCosto = costoStr ? Number(costoStr) : 0.0;
    const precioVenta = ventaStr ? Number(ventaStr) : 0.0;

    if ([stockActual, stockMinimo, precioCosto, precioVenta].some(isNaN)) {
        mostrarAlerta(tWeb("err_fmt_tit"), tWeb("stk_nums_err"), "error");
        return;
    }

    try {
        await peticionAPI(`/api/productos/${idProducto}`, "PUT", {
            codigo,
            descripcion,
            categoria,
            id_proveedor: idProveedor,
            precio_costo: precioCosto,
            precio_venta: precioVenta,
            stock_minimo: stockMinimo,
            ubicacion,
            vencimiento
        });

        const stockPrevio = Number(stockPrevioPorId[idProducto] || 0);
        const diferencia = stockActual - stockPrevio;
        if (Math.abs(diferencia) > 1e-6) {
            await peticionAPI(`/api/productos/${idProducto}/stock`, "POST", { cantidad: diferencia });
        }

        limpiarFormularioStock();
        await cargarDatosStock();
    } catch (error) {
        mostrarAlerta(tWeb("err_tx_tit"), error.message, "error");
    }
}

async function eliminarProducto() {
    const idProducto = document.getElementById("stk-id-seleccionado").value;
    if (!idProducto) {
        mostrarAlerta(tWeb("err_sel_tit"), tWeb("stk_sel_req"), "warning");
        return;
    }

    try {
        await peticionAPI(`/api/productos/${idProducto}`, "DELETE");
        limpiarFormularioStock();
        await cargarDatosStock();
    } catch (error) {
        mostrarAlerta(tWeb("err_bloq_tit"), error.message, "error");
    }
}


// ==============================================================================
//  11. MÓDULO DE FACTURACIÓN Y OPERACIONES COMERCIALES
// ==============================================================================

function limpiarFormularioFacturacion() {
    document.getElementById("fac-id-seleccionado").value = "";
    document.getElementById("fac-producto").value = "";
    document.getElementById("fac-cantidad").value = "";
    document.getElementById("fac-valor").value = "";
    document.getElementById("fac-descuento").value = "0";
    facturaSeleccionadaCache = null;
    desmarcarFilasTabla("tabla-facturacion");
}

function autocompletarPrecioFactura() {
    const seleccion = document.getElementById("fac-producto").value;
    if (!seleccion) {
        document.getElementById("fac-valor").value = "";
        return;
    }
    const codigo = seleccion.split(" - ")[0];
    const prod = mapaProductosCodigoAObj[codigo];
    if (prod) {
        document.getElementById("fac-valor").value = prod.precio_venta;
    }
}

function renderizarTablaFacturacion() {
    const tbody = document.querySelector("#tabla-facturacion tbody");
    const filtro = (document.getElementById("buscar-facturacion").value || "").trim().toLowerCase();
    tbody.innerHTML = "";
    let visibles = 0;

    cacheFacturas.forEach(f => {
        const prod = mapaProductosIdAObj[f.id_producto];
        const etiquetaProd = prod ? `${prod.codigo} - ${prod.descripcion}` : `ID ${f.id_producto}`;
        const totalFila = f.total !== null && f.total !== undefined
            ? Number(f.total)
            : (Number(f.cantidad) * Number(f.valor)) * (1.0 - (Number(f.descuento || 0) / 100.0));

        const texto = `${f.id} ${etiquetaProd} ${f.cantidad} ${f.valor} ${f.descuento} ${totalFila.toFixed(2)}`.toLowerCase();
        if (filtro && !texto.includes(filtro)) return;

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${f.id}</td>
            <td>${etiquetaProd}</td>
            <td>${f.cantidad}</td>
            <td>$ ${Number(f.valor).toFixed(2)}</td>
            <td>${f.descuento}%</td>
            <td>$ ${totalFila.toFixed(2)}</td>
        `;

        tr.addEventListener("click", () => {
            marcarFilaSeleccionada("tabla-facturacion", tr);
            document.getElementById("fac-id-seleccionado").value = f.id;
            document.getElementById("fac-producto").value = etiquetaProd;
            document.getElementById("fac-cantidad").value = f.cantidad;
            document.getElementById("fac-valor").value = f.valor;
            document.getElementById("fac-descuento").value = f.descuento;
            facturaSeleccionadaCache = {
                id: f.id,
                id_vendedor: f.id_vendedor,
                id_cliente: f.id_cliente,
                id_producto: f.id_producto,
                etiquetaProd: etiquetaProd,
                cantidad: Number(f.cantidad),
                descuento: Number(f.descuento || 0)
            };
        });

        tbody.appendChild(tr);
        visibles += 1;
    });

    document.getElementById("contador-facturacion").textContent =
        tWeb("contador_filas", { visibles, total: cacheFacturas.length });
}

async function cargarDatosFacturacion() {
    const selVendedor = document.getElementById("fac-vendedor");
    const selCliente = document.getElementById("fac-cliente");
    const selProducto = document.getElementById("fac-producto");

    const vendedorPrevio = selVendedor.value;
    const clientePrevio = selCliente.value;

    selVendedor.innerHTML = `<option value="">${tWeb("fac_sel_vend")}</option>`;
    selCliente.innerHTML = `<option value="">${tWeb("fac_sel_cli")}</option>`;
    selProducto.innerHTML = `<option value="">${tWeb("fac_sel_prod")}</option>`;

    mapaProductosCodigoAObj = {};
    mapaProductosIdAObj = {};

    try {
        const [vendedores, clientes, productos, facturas] = await Promise.all([
            peticionAPI("/api/perfiles/rol/Empleado - Ventas"),
            peticionAPI("/api/perfiles/rol/Cliente"),
            peticionAPI("/api/productos"),
            peticionAPI("/api/facturas")
        ]);

        vendedores.forEach(v => {
            const etiqueta = `${v.nombres} ${v.apellidos} (ID: ${v.id})`;
            const opt = document.createElement("option");
            opt.value = etiqueta;
            opt.textContent = etiqueta;
            selVendedor.appendChild(opt);
        });

        clientes.forEach(c => {
            const etiqueta = `${c.nombres} ${c.apellidos} (ID: ${c.id})`;
            const opt = document.createElement("option");
            opt.value = etiqueta;
            opt.textContent = etiqueta;
            selCliente.appendChild(opt);
        });

        if (vendedorPrevio) selVendedor.value = vendedorPrevio;
        if (clientePrevio) selCliente.value = clientePrevio;

        productos.forEach(p => {
            mapaProductosCodigoAObj[p.codigo] = p;
            mapaProductosIdAObj[p.id] = p;
            const etiqueta = `${p.codigo} - ${p.descripcion}`;
            const opt = document.createElement("option");
            opt.value = etiqueta;
            opt.textContent = etiqueta;
            selProducto.appendChild(opt);
        });

        cacheFacturas = facturas;
        totalAcumuladoFacturacion = facturas.reduce((acc, f) => {
            const t = f.total !== null && f.total !== undefined
                ? Number(f.total)
                : (Number(f.cantidad) * Number(f.valor)) * (1.0 - (Number(f.descuento || 0) / 100.0));
            return acc + t;
        }, 0.0);

        renderizarTablaFacturacion();
        actualizarEtiquetasTotalesFactura(totalAcumuladoFacturacion, 0);
    } catch (error) {
        mostrarAlerta(tWeb("err_com_tit"), error.message, "error");
    }
}

function actualizarEtiquetasTotalesFactura(granTotal, porcentajeGlobal = 0) {
    porcentajeGlobalActivo = porcentajeGlobal;
    const totalFinal = granTotal * (1.0 - (porcentajeGlobal / 100.0));
    const montoFmt = formatearMoneda(totalFinal);
    const elTotal = document.getElementById("fac-total-general");
    const elDesc = document.getElementById("fac-total-con-descuento");
    if (elTotal) elTotal.textContent = tWeb("fac_total", { monto: montoFmt });
    if (elDesc) elDesc.textContent = tWeb("fac_total_desc", { pct: porcentajeGlobal, monto: montoFmt });
}

function calcularDescuentoGlobal() {
    const inputGlobal = document.getElementById("fac-descuento-global");
    const valorStr = inputGlobal.value.trim();
    const porcentaje = valorStr ? Number(valorStr) : 0.0;

    if (isNaN(porcentaje) || porcentaje < 0 || porcentaje > 100) {
        mostrarAlerta(tWeb("val_tit"), tWeb("fac_desc_rango"), "error");
        return;
    }

    actualizarEtiquetasTotalesFactura(totalAcumuladoFacturacion, porcentaje);
    inputGlobal.value = "";
}

function extraerIdDeEtiqueta(etiqueta) {
    const partes = etiqueta.split("ID: ");
    if (partes.length < 2) return null;
    return parseInt(partes[1].replace(")", ""), 10);
}

async function guardarFactura() {
    const vendedorSel = document.getElementById("fac-vendedor").value.trim();
    const clienteSel = document.getElementById("fac-cliente").value.trim();
    const productoSel = document.getElementById("fac-producto").value.trim();
    const cantidadStr = document.getElementById("fac-cantidad").value.trim();
    const descuentoStr = document.getElementById("fac-descuento").value.trim();

    if (!vendedorSel || !clienteSel || !productoSel) {
        mostrarAlerta(tWeb("val_tit"), tWeb("fac_req"), "warning");
        return;
    }

    const cantidad = Number(cantidadStr);
    const descuento = descuentoStr ? Number(descuentoStr) : 0.0;

    if (isNaN(cantidad) || cantidad <= 0 || isNaN(descuento)) {
        mostrarAlerta(tWeb("err_fmt_tit"), tWeb("fac_nums_err"), "error");
        return;
    }

    if (descuento < 0 || descuento > 100) {
        mostrarAlerta(tWeb("val_tit"), tWeb("fac_rango_err"), "error");
        return;
    }

    const idVendedor = extraerIdDeEtiqueta(vendedorSel);
    const idCliente = extraerIdDeEtiqueta(clienteSel);
    const codigoProd = productoSel.split(" - ")[0];
    const prod = mapaProductosCodigoAObj[codigoProd];

    if (!idVendedor || !idCliente || !prod) {
        mostrarAlerta(tWeb("err_tx_tit"), tWeb("fac_asoc_err"), "error");
        return;
    }

    try {
        await peticionAPI("/api/facturas", "POST", {
            id_vendedor: idVendedor,
            id_cliente: idCliente,
            id_producto: prod.id,
            cantidad: cantidad,
            descuento: descuento
        });

        const nuevoStock = Number(prod.stock_actual) - cantidad;
        const stockMinimo = Number(prod.stock_minimo);

        limpiarFormularioFacturacion();
        await cargarDatosFacturacion();

        if (nuevoStock <= stockMinimo) {
            mostrarAlerta(tWeb("fac_rep_tit"), tWeb("fac_rep_msg", { u: Math.trunc(nuevoStock) }), "warning");
        }
    } catch (error) {
        mostrarAlerta(tWeb("err_tx_tit"), error.message, "error");
    }
}

async function modificarFactura() {
    if (!facturaSeleccionadaCache) {
        mostrarAlerta(tWeb("err_sel_tit"), tWeb("fac_sel_req"), "warning");
        return;
    }

    const vendedorSel = document.getElementById("fac-vendedor").value.trim();
    const clienteSel = document.getElementById("fac-cliente").value.trim();
    const productoNuevoSel = document.getElementById("fac-producto").value.trim();
    const cantidadNueva = Number(document.getElementById("fac-cantidad").value.trim());
    const descuentoStr = document.getElementById("fac-descuento").value.trim();
    const descuentoNuevo = descuentoStr ? Number(descuentoStr) : 0.0;

    if (!vendedorSel || !clienteSel || !productoNuevoSel) {
        mostrarAlerta(tWeb("val_tit"), tWeb("fac_req"), "warning");
        return;
    }

    if (isNaN(cantidadNueva) || cantidadNueva <= 0 || isNaN(descuentoNuevo) || descuentoNuevo < 0 || descuentoNuevo > 100) {
        mostrarAlerta(tWeb("val_tit"), tWeb("fac_rango_err"), "error");
        return;
    }

    const idVendedor = extraerIdDeEtiqueta(vendedorSel);
    const idCliente = extraerIdDeEtiqueta(clienteSel);
    const codigoNuevo = productoNuevoSel.split(" - ")[0];
    const prodNuevo = mapaProductosCodigoAObj[codigoNuevo];

    if (!idVendedor || !idCliente || !prodNuevo) {
        mostrarAlerta(tWeb("err_tx_tit"), tWeb("fac_asoc_err"), "error");
        return;
    }

    const respaldoOriginal = { ...facturaSeleccionadaCache };

    try {
        await peticionAPI(`/api/facturas/${respaldoOriginal.id}`, "DELETE");

        try {
            await peticionAPI("/api/facturas", "POST", {
                id_vendedor: idVendedor,
                id_cliente: idCliente,
                id_producto: prodNuevo.id,
                cantidad: cantidadNueva,
                descuento: descuentoNuevo
            });
        } catch (errorEmision) {
            await peticionAPI("/api/facturas", "POST", {
                id_vendedor: respaldoOriginal.id_vendedor || idVendedor,
                id_cliente: respaldoOriginal.id_cliente || idCliente,
                id_producto: respaldoOriginal.id_producto,
                cantidad: respaldoOriginal.cantidad,
                descuento: respaldoOriginal.descuento
            });
            await cargarDatosFacturacion();
            mostrarAlerta(tWeb("err_tx_tit"), errorEmision.message, "error");
            return;
        }

        limpiarFormularioFacturacion();
        await cargarDatosFacturacion();
    } catch (error) {
        mostrarAlerta(tWeb("err_tx_tit"), error.message, "error");
    }
}

async function eliminarFactura() {
    if (!facturaSeleccionadaCache) {
        mostrarAlerta(tWeb("err_sel_tit"), tWeb("fac_sel_req"), "warning");
        return;
    }

    try {
        await peticionAPI(`/api/facturas/${facturaSeleccionadaCache.id}`, "DELETE");
        limpiarFormularioFacturacion();
        await cargarDatosFacturacion();
    } catch (error) {
        mostrarAlerta(tWeb("err_bloq_tit"), error.message, "error");
    }
}


// ==============================================================================
//  12. CONSOLA SQL DE AUDITORÍA (SANDBOX DE SOLO LECTURA EN NAVEGADOR)
// ==============================================================================

function actualizarEstadoSQLVisual() {
    const labelEstado = document.getElementById("sql-estado");
    if (!labelEstado) return;
    const texto = estadoSQLMeta.textoLibre !== null
        ? estadoSQLMeta.textoLibre
        : tWeb(estadoSQLMeta.clave, estadoSQLMeta.kwargs);
    labelEstado.textContent = texto;
    if (estadoSQLMeta.tipo === "ok") {
        labelEstado.style.color = "var(--color-verde)";
    } else if (estadoSQLMeta.tipo === "error") {
        labelEstado.style.color = "var(--color-rojo)";
    } else {
        labelEstado.style.color = "var(--texto-secundario)";
    }
}

function setEstadoSQL(clave, tipo = "muted", kwargs = {}, textoLibre = null) {
    estadoSQLMeta = { clave, kwargs, textoLibre, tipo };
    actualizarEstadoSQLVisual();
}

function cargarEjemploSQL(sentencia) {
    document.getElementById("sql-query").value = sentencia;
}

function limpiarConsolaSQL() {
    document.getElementById("sql-query").value = "";
    document.querySelector("#tabla-sql thead").innerHTML = "";
    document.querySelector("#tabla-sql tbody").innerHTML = "";
    setEstadoSQL("sql_est_esp", "muted");
}

async function ejecutarConsultaSQL() {
    const queryCruda = document.getElementById("sql-query").value.trim();
    if (!queryCruda) return;

    try {
        const perfilOperador = await peticionAPI(`/api/perfiles/${sesionActiva.id}`);
        if (perfilOperador.rol !== "Administrador") {
            mostrarAlerta(tWeb("err_acc_tit"), tWeb("sql_solo_admin"), "error");
            setEstadoSQL("sql_est_rbac", "error");
            return;
        }
    } catch (error) {
        mostrarAlerta(tWeb("err_com_tit"), error.message, "error");
        return;
    }

    const patronProhibido = /\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|GRANT|REVOKE|ATTACH|DETACH|PRAGMA)\b/i;
    if (patronProhibido.test(queryCruda)) {
        mostrarAlerta(tWeb("sql_bloq_tit"), tWeb("sql_bloq_msg"), "error");
        setEstadoSQL("sql_est_sbx", "error");
        return;
    }

    const queryLimpia = queryCruda.replace(/;$/, "").trim();
    if (!/^SELECT\b/i.test(queryLimpia)) {
        setEstadoSQL("sql_solo_sel", "error");
        return;
    }

    try {
        const [usuarios, productos, facturacion] = await Promise.all([
            peticionAPI("/api/perfiles"),
            peticionAPI("/api/productos"),
            peticionAPI("/api/facturas")
        ]);

        const tablasMemoria = {
            usuarios,
            perfiles: usuarios,
            productos,
            facturacion,
            facturas: facturacion,
            roles: [
                { id: 1, rol: "Administrador", habilitado: 1 },
                { id: 2, rol: "Gerente", habilitado: 1 },
                { id: 3, rol: "Empleado - Ventas", habilitado: 1 },
                { id: 4, rol: "Empleado - Compras", habilitado: 1 },
                { id: 5, rol: "Proveedor", habilitado: 1 },
                { id: 6, rol: "Cliente", habilitado: 1 }
            ]
        };

        const matchTabla = queryLimpia.match(/\bFROM\s+([a-zA-Z0-9_]+)/i);
        if (!matchTabla) {
            throw new Error("Sintaxis inválida: falta especificar la cláusula FROM <tabla>.");
        }

        const nombreTabla = matchTabla[1].toLowerCase();
        const origenDatos = tablasMemoria[nombreTabla];
        if (!origenDatos) {
            throw new Error(`Tabla no encontrada en el esquema auditable: ${nombreTabla}`);
        }

        let filas = [...origenDatos];

        const matchLimit = queryLimpia.match(/\bLIMIT\s+(\d+)/i);
        const limite = matchLimit ? Math.min(parseInt(matchLimit[1], 10), 1000) : 1000;
        filas = filas.slice(0, limite);

        const matchCols = queryLimpia.match(/^SELECT\s+(.+?)\s+FROM\b/i);
        const colsRaw = matchCols ? matchCols[1].trim() : "*";

        let nombresColumnas = [];
        if (filas.length > 0) {
            const todasLasCols = Object.keys(filas[0]);
            nombresColumnas = colsRaw === "*"
                ? todasLasCols
                : colsRaw.split(",").map(c => c.trim().split(".").pop());
        }

        renderizarGrillaSQL(nombresColumnas, filas);
        setEstadoSQL("sql_est_ok", "ok", { n: filas.length });
    } catch (error) {
        setEstadoSQL("sql_est_esp", "error", {}, `Error SQL: ${error.message}`);
    }
}

function renderizarGrillaSQL(columnas, filas) {
    const thead = document.querySelector("#tabla-sql thead");
    const tbody = document.querySelector("#tabla-sql tbody");
    thead.innerHTML = "";
    tbody.innerHTML = "";

    if (columnas.length === 0) return;

    const trHead = document.createElement("tr");
    columnas.forEach(col => {
        const th = document.createElement("th");
        th.textContent = col.toUpperCase();
        trHead.appendChild(th);
    });
    thead.appendChild(trHead);

    filas.forEach(fila => {
        const tr = document.createElement("tr");
        columnas.forEach(col => {
            const td = document.createElement("td");
            td.textContent = fila[col] !== undefined && fila[col] !== null ? fila[col] : "NULL";
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
}


// ==============================================================================
//  13. MÓDULO DE ANALÍTICA DE VENTAS (BI / OLAP Y CANVAS ANTI-SUPERPOSICIÓN)
// ==============================================================================

function actualizarSubtituloBI() {
    const elSub = document.getElementById("bi-subtitulo-estrella");
    if (!elSub) return;
    if (biEstrella.producto && biEstrella.categoria) {
        elSub.textContent = tWeb("bi_sub_top", { prod: biEstrella.producto, cat: biEstrella.categoria });
    } else if (cacheRegistrosBI.length === 0) {
        elSub.textContent = tWeb("bi_sub_vacio");
    } else {
        elSub.textContent = tWeb("bi_sub_ini");
    }
}

function renderizarTablaBI() {
    const tbody = document.querySelector("#tabla-bi tbody");
    const filtro = (document.getElementById("buscar-bi").value || "").trim().toLowerCase();
    tbody.innerHTML = "";
    let visibles = 0;

    cacheRegistrosBI.forEach(r => {
        const texto = `${r.id_venta} ${r.producto} ${r.categoria} ${r.fecha} ${r.facturacion.toFixed(2)}`.toLowerCase();
        if (filtro && !texto.includes(filtro)) return;

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${r.id_venta}</td>
            <td>${r.producto}</td>
            <td>${r.categoria}</td>
            <td>$ ${formatearMoneda(r.precio)}</td>
            <td>${r.cantidad}</td>
            <td>${r.fecha}</td>
            <td>$ ${formatearMoneda(r.facturacion)}</td>
        `;
        tbody.appendChild(tr);
        visibles += 1;
    });

    document.getElementById("contador-bi").textContent =
        tWeb("contador_filas", { visibles, total: cacheRegistrosBI.length });
}

function redibujarGraficosBI() {
    dibujarGraficoBarras("canvas-bi-barras", cacheTop10BI);
    dibujarGraficoLineas("canvas-bi-lineas", cacheMensualBI);
    dibujarGraficoTorta("canvas-bi-torta", cacheCategoriasBI);
}

async function cargarDatosAnalitica() {
    try {
        const [facturas, productos] = await Promise.all([
            peticionAPI("/api/facturas"),
            peticionAPI("/api/productos")
        ]);

        const mapaProd = {};
        productos.forEach(p => { mapaProd[p.id] = p; });

        const registros = facturas.map(f => {
            const prod = mapaProd[f.id_producto] || {};
            const totalCobrado = f.total !== null && f.total !== undefined
                ? Number(f.total)
                : (Number(f.cantidad) * Number(f.valor)) * (1.0 - (Number(f.descuento || 0) / 100.0));

            return {
                id_venta: f.id,
                producto: prod.descripcion || `Producto ID ${f.id_producto}`,
                categoria: prod.categoria || "S/D",
                precio: Number(f.valor),
                cantidad: Number(f.cantidad),
                fecha: (f.fecha || new Date().toISOString()).slice(0, 10),
                facturacion: Number(totalCobrado)
            };
        }).sort((a, b) => a.fecha.localeCompare(b.fecha));

        cacheRegistrosBI = registros;

        if (registros.length === 0) {
            cacheTop10BI = [];
            cacheMensualBI = [];
            cacheCategoriasBI = [];
            biEstrella = { producto: null, categoria: null };
            document.getElementById("kpi-facturacion").textContent = "$ 0.00";
            document.getElementById("kpi-operaciones").textContent = "0";
            document.getElementById("kpi-unidades").textContent = "0";
            document.getElementById("kpi-ticket").textContent = "$ 0.00";
            actualizarSubtituloBI();
            redibujarGraficosBI();
            renderizarTablaBI();
            mostrarAlerta(tWeb("val_tit"), tWeb("bi_info_vacio"), "info");
            return;
        }

        const totalFacturacion = registros.reduce((acc, r) => acc + r.facturacion, 0);
        const totalOperaciones = registros.length;
        const totalUnidades = registros.reduce((acc, r) => acc + r.cantidad, 0);
        const ticketPromedio = totalOperaciones > 0 ? totalFacturacion / totalOperaciones : 0;

        document.getElementById("kpi-facturacion").textContent = `$ ${formatearMoneda(totalFacturacion)}`;
        document.getElementById("kpi-operaciones").textContent = totalOperaciones.toLocaleString("es-AR");
        document.getElementById("kpi-unidades").textContent = Math.round(totalUnidades).toLocaleString("es-AR");
        document.getElementById("kpi-ticket").textContent = `$ ${formatearMoneda(ticketPromedio)}`;

        const cantPorProducto = {};
        const factPorProducto = {};
        const factPorMes = {};
        const factPorCategoria = {};

        registros.forEach(r => {
            cantPorProducto[r.producto] = (cantPorProducto[r.producto] || 0) + r.cantidad;
            factPorProducto[r.producto] = (factPorProducto[r.producto] || 0) + r.facturacion;
            const mes = r.fecha.slice(0, 7);
            factPorMes[mes] = (factPorMes[mes] || 0) + r.facturacion;
            factPorCategoria[r.categoria] = (factPorCategoria[r.categoria] || 0) + r.facturacion;
        });

        biEstrella = {
            producto: Object.entries(cantPorProducto).sort((a, b) => b[1] - a[1])[0][0],
            categoria: Object.entries(factPorCategoria).sort((a, b) => b[1] - a[1])[0][0]
        };
        actualizarSubtituloBI();

        cacheTop10BI = Object.entries(factPorProducto).sort((a, b) => b[1] - a[1]).slice(0, 10);
        cacheMensualBI = Object.entries(factPorMes).sort((a, b) => a[0].localeCompare(b[0]));
        cacheCategoriasBI = Object.entries(factPorCategoria).filter(x => x[1] > 0).sort((a, b) => b[1] - a[1]);

        redibujarGraficosBI();
        renderizarTablaBI();
    } catch (error) {
        mostrarAlerta(tWeb("err_com_tit"), error.message, "error");
    }
}

function obtenerTokensCanvas() {
    const css = getComputedStyle(document.documentElement);
    return {
        bg: css.getPropertyValue("--bg-tarjeta").trim() || "#FFFFFF",
        texto: css.getPropertyValue("--texto-primario").trim() || "#0F172A",
        muted: css.getPropertyValue("--texto-secundario").trim() || "#64748B",
        eje: css.getPropertyValue("--borde-suave").trim() || "#CBD5E1",
        grilla: css.getPropertyValue("--borde-fila").trim() || "#E2E8F0",
        barra: prefUI.tema === "dark" ? "#38BDF8" : "#2563EB",
        linea: prefUI.tema === "dark" ? "#4ADE80" : "#16A34A"
    };
}

function formatearEjeY(valor) {
    if (valor >= 1_000_000) return `$${(valor / 1_000_000).toFixed(1)}M`;
    if (valor >= 1_000) return `$${Math.round(valor / 1_000)}k`;
    return `$${Math.round(valor)}`;
}

function acortarEtiquetaBI(texto, maxLen = 11) {
    const limpio = String(texto || "").trim();
    if (limpio.length <= maxLen) return limpio;
    const inicio = Math.max(2, maxLen - 6);
    return `${limpio.slice(0, inicio)}..${limpio.slice(-4)}`;
}

function dibujarGrillaY(ctx, padIzq, padDer, padArr, padAba, ancho, alto, maxValor, tokens) {
    const altoUtil = alto - padArr - padAba;
    [0.0, 0.5, 1.0].forEach(frac => {
        const y = alto - padAba - frac * altoUtil;
        if (frac > 0) {
            ctx.save();
            ctx.setLineDash([3, 3]);
            ctx.strokeStyle = tokens.grilla;
            ctx.beginPath();
            ctx.moveTo(padIzq, y);
            ctx.lineTo(ancho - padDer, y);
            ctx.stroke();
            ctx.restore();
        }
        ctx.fillStyle = tokens.muted;
        ctx.font = "10px Segoe UI, Arial";
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        ctx.fillText(formatearEjeY(maxValor * frac), padIzq - 6, y);
    });

    ctx.strokeStyle = tokens.eje;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padIzq, padArr);
    ctx.lineTo(padIzq, alto - padAba);
    ctx.lineTo(ancho - padDer, alto - padAba);
    ctx.stroke();
}

function dibujarGraficoBarras(idCanvas, datos) {
    const canvas = document.getElementById(idCanvas);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const tokens = obtenerTokensCanvas();
    const ancho = canvas.width;
    const alto = canvas.height;
    ctx.clearRect(0, 0, ancho, alto);

    if (datos.length === 0) {
        ctx.fillStyle = tokens.muted;
        ctx.font = "12px Segoe UI, Arial";
        ctx.textAlign = "center";
        ctx.fillText(tWeb("bi_sin_datos"), ancho / 2, alto / 2);
        return;
    }

    const padIzq = 54, padDer = 14, padArr = 16, padAba = 66;
    const anchoUtil = ancho - padIzq - padDer;
    const altoUtil = alto - padArr - padAba;
    const maxValor = Math.max(...datos.map(d => d[1]), 1);

    dibujarGrillaY(ctx, padIzq, padDer, padArr, padAba, ancho, alto, maxValor, tokens);

    const pasoX = anchoUtil / datos.length;
    const anchoBarra = Math.max(pasoX * 0.60, 8);

    datos.forEach(([etiqueta, valor], i) => {
        const altoBarra = (valor / maxValor) * altoUtil;
        const x = padIzq + i * pasoX + (pasoX - anchoBarra) / 2;
        const y = alto - padAba - altoBarra;

        ctx.fillStyle = tokens.barra;
        ctx.fillRect(x, y, anchoBarra, altoBarra);

        ctx.save();
        ctx.translate(x + anchoBarra / 2, alto - padAba + 8);
        ctx.rotate(-Math.PI / 4.5);
        ctx.fillStyle = tokens.texto;
        ctx.font = "10px Segoe UI, Arial";
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        ctx.fillText(acortarEtiquetaBI(etiqueta, 11), 0, 0);
        ctx.restore();
    });
}

function dibujarGraficoLineas(idCanvas, datos) {
    const canvas = document.getElementById(idCanvas);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const tokens = obtenerTokensCanvas();
    const ancho = canvas.width;
    const alto = canvas.height;
    ctx.clearRect(0, 0, ancho, alto);

    if (datos.length === 0) {
        ctx.fillStyle = tokens.muted;
        ctx.font = "12px Segoe UI, Arial";
        ctx.textAlign = "center";
        ctx.fillText(tWeb("bi_sin_datos"), ancho / 2, alto / 2);
        return;
    }

    const padIzq = 54, padDer = 18, padArr = 16, padAba = 64;
    const anchoUtil = ancho - padIzq - padDer;
    const altoUtil = alto - padArr - padAba;
    const maxValor = Math.max(...datos.map(d => d[1]), 1);

    dibujarGrillaY(ctx, padIzq, padDer, padArr, padAba, ancho, alto, maxValor, tokens);

    const n = datos.length;
    const puntos = datos.map(([mes, valor], i) => {
        const x = n === 1 ? padIzq + anchoUtil / 2 : padIzq + (i / (n - 1)) * anchoUtil;
        const y = alto - padAba - (valor / maxValor) * altoUtil;
        return { x, y, mes };
    });

    ctx.strokeStyle = tokens.linea;
    ctx.lineWidth = 2.4;
    ctx.beginPath();
    puntos.forEach((p, i) => {
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
    });
    ctx.stroke();

    const radio = n > 14 ? 2.6 : 4.0;
    puntos.forEach(p => {
        ctx.fillStyle = tokens.linea;
        ctx.beginPath();
        ctx.arc(p.x, p.y, radio, 0, Math.PI * 2);
        ctx.fill();
    });

    // Submuestreo dinámico del eje X idéntico a analitica.py para evitar superposición.
    let indicesVisibles = [0];
    if (n > 1) {
        const maxEtiquetas = Math.max(2, Math.floor(anchoUtil / 54));
        const paso = Math.max(1, Math.ceil((n - 1) / (maxEtiquetas - 1)));
        indicesVisibles = [];
        for (let i = 0; i < n; i += paso) indicesVisibles.push(i);
        if (indicesVisibles[indicesVisibles.length - 1] !== n - 1) {
            if (puntos[n - 1].x - puntos[indicesVisibles[indicesVisibles.length - 1]].x < 38) {
                indicesVisibles[indicesVisibles.length - 1] = n - 1;
            } else {
                indicesVisibles.push(n - 1);
            }
        }
    }

    const yEje = alto - padAba;
    indicesVisibles.forEach(idx => {
        const p = puntos[idx];
        ctx.strokeStyle = tokens.eje;
        ctx.beginPath();
        ctx.moveTo(p.x, yEje);
        ctx.lineTo(p.x, yEje + 4);
        ctx.stroke();

        ctx.save();
        ctx.translate(p.x, yEje + 10);
        ctx.rotate(-Math.PI / 5);
        ctx.fillStyle = tokens.texto;
        ctx.font = "10px Segoe UI, Arial";
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        ctx.fillText(p.mes.length >= 7 ? p.mes.slice(-5) : p.mes, 0, 0);
        ctx.restore();
    });
}

function dibujarGraficoTorta(idCanvas, datos) {
    const canvas = document.getElementById(idCanvas);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const tokens = obtenerTokensCanvas();
    const ancho = canvas.width;
    const alto = canvas.height;
    ctx.clearRect(0, 0, ancho, alto);

    if (datos.length === 0) {
        ctx.fillStyle = tokens.muted;
        ctx.font = "12px Segoe UI, Arial";
        ctx.textAlign = "center";
        ctx.fillText(tWeb("bi_sin_datos"), ancho / 2, alto / 2);
        return;
    }

    const colores = [
        "#2563EB", "#16A34A", "#D97706", "#7C3AED", "#0D9488",
        "#DC2626", "#475569", "#0284C7", "#CA8A04", "#9333EA"
    ];

    const total = datos.reduce((acc, d) => acc + d[1], 0) || 1;
    const cx = ancho * 0.32;
    const cy = alto * 0.5;
    const radio = Math.min(cx, cy) - 16;

    let anguloInicial = -Math.PI / 2;

    datos.forEach(([, valor], i) => {
        const porcion = (valor / total) * (Math.PI * 2);
        ctx.fillStyle = colores[i % colores.length];
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, radio, anguloInicial, anguloInicial + porcion);
        ctx.closePath();
        ctx.fill();
        ctx.strokeStyle = tokens.bg;
        ctx.lineWidth = 1;
        ctx.stroke();
        anguloInicial += porcion;
    });

    const xLeyenda = ancho * 0.60;
    datos.slice(0, 8).forEach(([categoria, valor], i) => {
        const y = 24 + i * 26;
        const pct = ((valor / total) * 100).toFixed(1);

        ctx.fillStyle = colores[i % colores.length];
        ctx.fillRect(xLeyenda, y - 6, 12, 12);

        ctx.fillStyle = tokens.texto;
        ctx.font = "11px Segoe UI, Arial";
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        ctx.fillText(`${categoria.slice(0, 11)} (${pct}%)`, xLeyenda + 16, y);
    });
}


// ==============================================================================
//  14. UTILIDADES VISUALES, ATAJOS DE TECLADO WCAG E INICIALIZACIÓN
// ==============================================================================

function marcarFilaSeleccionada(idTabla, filaActiva) {
    desmarcarFilasTabla(idTabla);
    filaActiva.classList.add("seleccionada");
}

function desmarcarFilasTabla(idTabla) {
    document.querySelectorAll(`#${idTabla} tbody tr`).forEach(tr => {
        tr.classList.remove("seleccionada");
    });
}

function formatearMoneda(numero) {
    return Number(numero || 0).toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Atajos globales de accesibilidad: Esc (cerrar modal / volver al panel), Ctrl+F (buscar en tabla), Ctrl+Enter (SQL).
document.addEventListener("keydown", evento => {
    const modal = document.getElementById("modal-alerta");
    const modalAbierto = modal && !modal.classList.contains("oculto");

    if (evento.key === "Escape") {
        if (modalAbierto) {
            cerrarAlerta();
            return;
        }
        const vistaActiva = document.querySelector(".vista-app.activa");
        if (vistaActiva && vistaActiva.id !== "vista-login" && vistaActiva.id !== "vista-panel") {
            navegarA("vista-panel");
        }
        return;
    }

    if ((evento.ctrlKey || evento.metaKey) && evento.key.toLowerCase() === "f") {
        const vistaActiva = document.querySelector(".vista-app.activa");
        if (vistaActiva) {
            const buscador = vistaActiva.querySelector(".input-busqueda");
            if (buscador) {
                evento.preventDefault();
                buscador.focus();
                buscador.select();
            }
        }
        return;
    }

    if ((evento.ctrlKey || evento.metaKey) && evento.key === "Enter") {
        const vistaSQL = document.getElementById("vista-consola");
        if (vistaSQL && vistaSQL.classList.contains("activa")) {
            evento.preventDefault();
            ejecutarConsultaSQL();
        }
    }
});

document.addEventListener("DOMContentLoaded", () => {
    cargarPreferenciasSesion();
    aplicarPreferenciasUI();
});