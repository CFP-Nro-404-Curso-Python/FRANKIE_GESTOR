// =================================================================================================================
//  CLIENTE WEB SPA Y ADAPTADOR FETCH (CAPA 4 - PRESENTACIÓN WEB)
// =================================================================================================================
//  DECISIÓN DE DISEÑO (MULTI-DISPOSITIVO EN RED LOCAL Y CERO DEPENDENCIAS):
//
//   1. Detecta automáticamente la IP de la computadora servidor en la red WiFi usando 'window.location.hostname', 
//      permitiendo operar desde celulares, tablets o cualquier PC conectada a la misma red local (LAN).

//   2. Consume exactamente los mismos endpoints de FastAPI (puerto 8000) que la aplicación de escritorio Tkinter, 
//      enviando la cabecera 'X-Operador-Id'.

//   3. Dibuja los gráficos de Business Intelligence en HTML5 Canvas nativo para no depender de conexión a Internet 
//      externa.
// =================================================================================================================

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

// Diccionarios en memoria para traducir nombres, códigos e IDs en Stock y Facturación.
let mapaProveedoresNombreAId = {};
let mapaProveedoresIdANombre = {};
let mapaProductosCodigoAObj = {};
let mapaProductosIdAObj = {};
let cacheStockAnterior = {};

// Almacenamiento local del navegador para conservar datos de contacto/ubicación en la sesión.
function obtenerCacheLocal(clave) {
    try {
        return JSON.parse(localStorage.getItem(clave) || "{}");
    } catch {
        return {};
    }
}

function guardarCacheLocal(clave, objeto) {
    try {
        localStorage.setItem(clave, JSON.stringify(objeto));
    } catch {
        // Ignoramos si el navegador restringe localStorage en modo incógnito.
    }
}



// =======================================================================
//  1. CLIENTE HTTP ASÍNCRONO CENTRALIZADO (EQUIVALENTE A CLIENTE_API.PY)
// =======================================================================

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
    } catch (errorRed) {
        throw new Error(`No se pudo conectar con el servidor Backend en ${URL_BASE_API}. Verificá que el sistema esté iniciado.`);
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

    // Extraemos el mensaje de error enviado por el Dominio ('detalle') o por FastAPI ('detail').
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



// ========================================================================
//  2. SISTEMA DE CUADROS DE DIÁLOGO (EQUIVALENTE A MESSAGEBOX DE TKINTER)
// ========================================================================

function mostrarAlerta(titulo, mensaje, tipo = "info") {
    const modal = document.getElementById("modal-alerta");
    const cabecera = document.getElementById("modal-cabecera");
    const txtTitulo = document.getElementById("modal-titulo");
    const txtMensaje = document.getElementById("modal-mensaje");

    cabecera.className = `modal-cabecera ${tipo}`;
    txtTitulo.textContent = titulo;
    txtMensaje.textContent = mensaje;
    modal.classList.remove("oculto");
}

function cerrarAlerta() {
    document.getElementById("modal-alerta").classList.add("oculto");
}



// ============================================================
//  3. NAVEGACIÓN ENTRE VISTAS (SPA) Y MATRIZ DE PERMISOS RBAC
// ============================================================

function navegarA(idVista) {
    document.querySelectorAll(".vista-app").forEach(seccion => {
        seccion.classList.remove("activa");
    });

    const vistaDestino = document.getElementById(idVista);
    if (vistaDestino) {
        vistaDestino.classList.add("activa");
    }

    const barraSuperior = document.getElementById("barra-superior");
    const btnVolverTop = document.getElementById("btn-volver-panel-top");

    if (idVista === "vista-login") {
        barraSuperior.classList.add("oculto");
    } else {
        barraSuperior.classList.remove("oculto");
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
        configurarComboRolesUsuarios();
        limpiarFormularioUsuarios();
        await cargarDatosUsuarios();
    } else if (idVista === "vista-empleados") {
        limpiarFormularioEmpleados();
        await cargarDatosEmpleados();
    } else if (idVista === "vista-clientes") {
        limpiarFormularioClientes();
        await cargarDatosClientes();
    } else if (idVista === "vista-proveedores") {
        limpiarFormularioProveedores();
        await cargarDatosProveedores();
    } else if (idVista === "vista-stock") {
        limpiarFormularioStock();
        await cargarDatosStock();
    } else if (idVista === "vista-facturacion") {
        limpiarFormularioFacturacion();
        await cargarDatosFacturacion();
    } else if (idVista === "vista-consola") {
        limpiarConsolaSQL();
    } else if (idVista === "vista-analitica") {
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



// =======================================
//  4. MÓDULO DE LOGIN Y CIERRE DE SESIÓN
// =======================================

async function validarIngreso(evento) {
    evento.preventDefault();

    const inputUsuario = document.getElementById("login-usuario");
    const inputPassword = document.getElementById("login-password");
    const btnIngresar = document.getElementById("btn-login-ingresar");
    const infoIntentos = document.getElementById("login-intentos-info");

    const usuario = inputUsuario.value.trim();
    const password = inputPassword.value;

    if (!usuario || !password) {
        mostrarAlerta("Validación", "Completá todos los campos.", "warning");
        return;
    }

    try {
        const datosPerfil = await peticionAPI("/api/perfiles/login", "POST", {
            usuario: usuario,
            password: password
        });

        intentosFallidosLogin = 0;
        infoIntentos.textContent = "Intentos disponibles: 3";

        sesionActiva = {
            id: datosPerfil.id,
            usuario: datosPerfil.usuario,
            rol: datosPerfil.rol,
            nombres: datosPerfil.nombres,
            apellidos: datosPerfil.apellidos
        };

        inputUsuario.value = "";
        inputPassword.value = "";

        // Configuramos encabezados del Panel de Control.
        const nombreCompleto = `${datosPerfil.nombres} ${datosPerfil.apellidos}`.toUpperCase();
        document.getElementById("panel-saludo").textContent = `BIENVENIDO/A, ${nombreCompleto}`;
        document.getElementById("panel-rol").textContent = `Rol Activo: ${datosPerfil.rol}`;
        document.getElementById("info-operador-activo").textContent = `${datosPerfil.nombres} ${datosPerfil.apellidos} (${datosPerfil.rol})`;

        aplicarMatrizRBACPanel(datosPerfil.rol);
        navegarA("vista-panel");
        mostrarAlerta("Acceso Concedido", `Bienvenido/a, ${datosPerfil.nombres} ${datosPerfil.apellidos}.\nRol: ${datosPerfil.rol}`, "info");

    } catch (error) {
        intentosFallidosLogin += 1;
        const restantes = 3 - intentosFallidosLogin;

        inputUsuario.value = "";
        inputPassword.value = "";
        inputUsuario.focus();

        if (restantes > 0) {
            infoIntentos.textContent = `Intentos disponibles: ${restantes}`;
            mostrarAlerta(
                "Error de Autenticación",
                `Credenciales incorrectas o usuario inhabilitado. Intentos restantes: ${restantes}`,
                "error"
            );
        } else {
            infoIntentos.textContent = "Acceso bloqueado por seguridad.";
            inputUsuario.disabled = true;
            inputPassword.disabled = true;
            btnIngresar.disabled = true;
            mostrarAlerta(
                "Bloqueo de Seguridad",
                "Superaste el límite de intentos fallidos. Recargá la página o contactá al Administrador.",
                "error"
            );
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

        enlace.href = urlDescarga;
        enlace.download = `backup_frankie_${marcaTiempo}.json`;
        document.body.appendChild(enlace);
        enlace.click();
        document.body.removeChild(enlace);
        URL.revokeObjectURL(urlDescarga);

        mostrarAlerta("Backup Exitoso", `Copia de seguridad descargada en tu dispositivo como:\nbackup_frankie_${marcaTiempo}.json`, "info");
    } catch (error) {
        mostrarAlerta("Error de Backup", `Fallo al generar la copia: ${error.message}`, "error");
    }
}



// ==================================
//  5. MÓDULO DE GESTIÓN DE USUARIOS
// ==================================

function configurarComboRolesUsuarios() {
    const selectRol = document.getElementById("usu-rol");
    selectRol.innerHTML = '<option value="">Seleccione un rol...</option>';

    let rolesPermitidos = ["Empleado - Ventas", "Empleado - Compras"];
    if (sesionActiva.rol === "Administrador") {
        rolesPermitidos = ["Administrador", "Gerente", ...rolesPermitidos];
    }

    rolesPermitidos.forEach(rol => {
        const opt = document.createElement("option");
        opt.value = rol;
        opt.textContent = rol;
        selectRol.appendChild(opt);
    });
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

async function cargarDatosUsuarios() {
    const tbody = document.querySelector("#tabla-usuarios tbody");
    tbody.innerHTML = "";

    try {
        const perfiles = await peticionAPI("/api/perfiles");
        perfiles.forEach(p => {
            if (!["Cliente", "Proveedor"].includes(p.rol)) {
                const tr = document.createElement("tr");
                const usuarioMostrar = p.usuario ? p.usuario : "[Sin Credenciales]";

                tr.innerHTML = `
                    <td>${p.id}</td>
                    <td>${usuarioMostrar}</td>
                    <td>${p.rol}</td>
                    <td>${p.nombres}</td>
                    <td>${p.apellidos}</td>
                `;

                tr.addEventListener("click", () => {
                    marcarFilaSeleccionada("tabla-usuarios", tr);
                    document.getElementById("usu-id-seleccionado").value = p.id;
                    document.getElementById("usu-usuario").value = usuarioMostrar;
                    document.getElementById("usu-rol").value = p.rol;
                    document.getElementById("usu-nombres").value = p.nombres;
                    document.getElementById("usu-apellidos").value = p.apellidos;
                    document.getElementById("usu-password").value = "";
                });

                tbody.appendChild(tr);
            }
        });
    } catch (error) {
        mostrarAlerta("Error de Comunicación", error.message, "error");
    }
}

async function guardarUsuario() {
    const nombres = document.getElementById("usu-nombres").value.trim();
    const apellidos = document.getElementById("usu-apellidos").value.trim();
    const usuario = document.getElementById("usu-usuario").value.trim();
    const password = document.getElementById("usu-password").value.trim();
    const rol = document.getElementById("usu-rol").value;

    if (!nombres || !apellidos || !usuario || !password || !rol) {
        mostrarAlerta("Validación", "Todos los campos son obligatorios en este módulo.", "warning");
        return;
    }

    if (sesionActiva.rol === "Gerente" && ["Administrador", "Gerente"].includes(rol)) {
        mostrarAlerta("Acceso Denegado", "Privilegios insuficientes para crear perfiles de esta jerarquía.", "error");
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
        mostrarAlerta("Error al Guardar", error.message, "error");
    }
}

async function modificarUsuario() {
    const idDestino = document.getElementById("usu-id-seleccionado").value;
    if (!idDestino) {
        mostrarAlerta("Selección Requerida", "Tocá primero un usuario de la tabla para modificarlo.", "warning");
        return;
    }

    const nombres = document.getElementById("usu-nombres").value.trim();
    const apellidos = document.getElementById("usu-apellidos").value.trim();
    const usuario = document.getElementById("usu-usuario").value.trim();
    const password = document.getElementById("usu-password").value.trim();
    const rol = document.getElementById("usu-rol").value;

    if (!nombres || !apellidos || !usuario || !rol) {
        mostrarAlerta("Validación", "Nombres, Apellidos, Usuario y Rol son obligatorios.", "warning");
        return;
    }

    const payload = { nombres, apellidos, rol, usuario };
    if (password) {
        payload.password_plana = password;
    }

    try {
        await peticionAPI(`/api/perfiles/${idDestino}`, "PUT", payload);
        limpiarFormularioUsuarios();
        await cargarDatosUsuarios();
    } catch (error) {
        mostrarAlerta("Acceso Denegado / Error", error.message, "error");
    }
}

async function eliminarUsuario() {
    const idDestino = document.getElementById("usu-id-seleccionado").value;
    if (!idDestino) {
        mostrarAlerta("Selección Requerida", "Tocá primero un usuario de la tabla para eliminarlo.", "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idDestino}`, "DELETE");
        limpiarFormularioUsuarios();
        await cargarDatosUsuarios();
    } catch (error) {
        mostrarAlerta("Operación Bloqueada", error.message, "error");
    }
}



// ===========================================
//  6. MÓDULO DE RECURSOS HUMANOS (EMPLEADOS)
// ===========================================

function limpiarFormularioEmpleados() {
    document.getElementById("emp-id-seleccionado").value = "";
    ["emp-nombres", "emp-apellidos", "emp-dni", "emp-telefono", "emp-email",
     "emp-direccion", "emp-ciudad", "emp-provincia", "emp-cp", "emp-rol"].forEach(id => {
        document.getElementById(id).value = "";
    });
    desmarcarFilasTabla("tabla-empleados");
}

async function cargarDatosEmpleados() {
    const tbody = document.querySelector("#tabla-empleados tbody");
    tbody.innerHTML = "";
    const cacheRRHH = obtenerCacheLocal("cache_rrhh");

    try {
        const perfiles = await peticionAPI("/api/perfiles");
        perfiles.forEach(p => {
            if (!["Cliente", "Proveedor"].includes(p.rol)) {
                const extras = cacheRRHH[p.id] || {};
                const fila = {
                    nombres: p.nombres || "S/D",
                    apellidos: p.apellidos || "S/D",
                    dni: p.dni || "S/D",
                    telefono: extras.telefono || "S/D",
                    email: extras.email || "S/D",
                    direccion: extras.direccion || "S/D",
                    ciudad: extras.ciudad || "S/D",
                    provincia: extras.provincia || "S/D",
                    cp: extras.cp || "S/D",
                    rol: p.rol || "S/D"
                };

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
                    <td>${fila.rol}</td>
                `;

                tr.addEventListener("click", () => {
                    marcarFilaSeleccionada("tabla-empleados", tr);
                    document.getElementById("emp-id-seleccionado").value = p.id;
                    document.getElementById("emp-nombres").value = fila.nombres !== "S/D" ? fila.nombres : "";
                    document.getElementById("emp-apellidos").value = fila.apellidos !== "S/D" ? fila.apellidos : "";
                    document.getElementById("emp-dni").value = fila.dni !== "S/D" ? fila.dni : "";
                    document.getElementById("emp-telefono").value = fila.telefono !== "S/D" ? fila.telefono : "";
                    document.getElementById("emp-email").value = fila.email !== "S/D" ? fila.email : "";
                    document.getElementById("emp-direccion").value = fila.direccion !== "S/D" ? fila.direccion : "";
                    document.getElementById("emp-ciudad").value = fila.ciudad !== "S/D" ? fila.ciudad : "";
                    document.getElementById("emp-provincia").value = fila.provincia !== "S/D" ? fila.provincia : "";
                    document.getElementById("emp-cp").value = fila.cp !== "S/D" ? fila.cp : "";
                    document.getElementById("emp-rol").value = fila.rol;
                });

                tbody.appendChild(tr);
            }
        });
    } catch (error) {
        mostrarAlerta("Error de Comunicación", error.message, "error");
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
        mostrarAlerta("Validación", "Nombres, Apellidos y Rol Organizacional son obligatorios.", "warning");
        return;
    }

    if (sesionActiva.rol === "Gerente" && ["Administrador", "Gerente"].includes(rol)) {
        mostrarAlerta("Acceso Denegado", "Privilegios insuficientes para crear perfiles de esta jerarquía organizativa.", "error");
        limpiarFormularioEmpleados();
        return;
    }

    try {
        const res = await peticionAPI("/api/perfiles", "POST", { nombres, apellidos, dni, rol });
        if (res && res.id) {
            const cacheRRHH = obtenerCacheLocal("cache_rrhh");
            cacheRRHH[res.id] = { telefono, email, direccion, ciudad, provincia, cp };
            guardarCacheLocal("cache_rrhh", cacheRRHH);
        }
        limpiarFormularioEmpleados();
        await cargarDatosEmpleados();
    } catch (error) {
        mostrarAlerta("Error de Transacción", error.message, "error");
    }
}

async function modificarEmpleado() {
    const idEmpleado = document.getElementById("emp-id-seleccionado").value;
    if (!idEmpleado) {
        mostrarAlerta("Selección Requerida", "Tocá primero un empleado de la tabla para modificarlo.", "warning");
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
        mostrarAlerta("Validación", "Nombres, Apellidos y Rol Organizacional son obligatorios.", "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idEmpleado}`, "PUT", { nombres, apellidos, dni, rol });
        const cacheRRHH = obtenerCacheLocal("cache_rrhh");
        cacheRRHH[idEmpleado] = { telefono, email, direccion, ciudad, provincia, cp };
        guardarCacheLocal("cache_rrhh", cacheRRHH);

        limpiarFormularioEmpleados();
        await cargarDatosEmpleados();
    } catch (error) {
        mostrarAlerta("Acceso Denegado / Error", error.message, "error");
    }
}

async function eliminarEmpleado() {
    const idEmpleado = document.getElementById("emp-id-seleccionado").value;
    if (!idEmpleado) {
        mostrarAlerta("Selección Requerida", "Tocá primero un empleado de la tabla para eliminarlo.", "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idEmpleado}`, "DELETE");
        limpiarFormularioEmpleados();
        await cargarDatosEmpleados();
    } catch (error) {
        mostrarAlerta("Operación Bloqueada", error.message, "error");
    }
}



// ==================================
//  7. MÓDULO DE GESTIÓN DE CLIENTES
// ==================================

function limpiarFormularioClientes() {
    document.getElementById("cli-id-seleccionado").value = "";
    ["cli-nombres", "cli-apellidos", "cli-dni", "cli-telefono", "cli-email",
     "cli-direccion", "cli-ciudad", "cli-provincia", "cli-cp"].forEach(id => {
        document.getElementById(id).value = "";
    });
    desmarcarFilasTabla("tabla-clientes");
}

async function cargarDatosClientes() {
    const tbody = document.querySelector("#tabla-clientes tbody");
    tbody.innerHTML = "";
    const cacheCli = obtenerCacheLocal("cache_clientes");

    try {
        const clientes = await peticionAPI("/api/perfiles/rol/Cliente");
        clientes.forEach(c => {
            const extras = cacheCli[c.id] || {};
            const fila = {
                nombres: c.nombres || "S/D",
                apellidos: c.apellidos || "S/D",
                dni: c.dni || "S/D",
                telefono: extras.telefono || "S/D",
                email: extras.email || "S/D",
                direccion: extras.direccion || "S/D",
                ciudad: extras.ciudad || "S/D",
                provincia: extras.provincia || "S/D",
                cp: extras.cp || "S/D"
            };

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
                document.getElementById("cli-nombres").value = fila.nombres !== "S/D" ? fila.nombres : "";
                document.getElementById("cli-apellidos").value = fila.apellidos !== "S/D" ? fila.apellidos : "";
                document.getElementById("cli-dni").value = fila.dni !== "S/D" ? fila.dni : "";
                document.getElementById("cli-telefono").value = fila.telefono !== "S/D" ? fila.telefono : "";
                document.getElementById("cli-email").value = fila.email !== "S/D" ? fila.email : "";
                document.getElementById("cli-direccion").value = fila.direccion !== "S/D" ? fila.direccion : "";
                document.getElementById("cli-ciudad").value = fila.ciudad !== "S/D" ? fila.ciudad : "";
                document.getElementById("cli-provincia").value = fila.provincia !== "S/D" ? fila.provincia : "";
                document.getElementById("cli-cp").value = fila.cp !== "S/D" ? fila.cp : "";
            });

            tbody.appendChild(tr);
        });
    } catch (error) {
        mostrarAlerta("Error de Comunicación", error.message, "error");
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
        mostrarAlerta("Validación", "Nombres y Apellidos son obligatorios.", "warning");
        return;
    }

    try {
        const res = await peticionAPI("/api/perfiles", "POST", {
            nombres,
            apellidos,
            dni,
            rol: "Cliente"
        });
        if (res && res.id) {
            const cacheCli = obtenerCacheLocal("cache_clientes");
            cacheCli[res.id] = { telefono, email, direccion, ciudad, provincia, cp };
            guardarCacheLocal("cache_clientes", cacheCli);
        }
        limpiarFormularioClientes();
        await cargarDatosClientes();
    } catch (error) {
        mostrarAlerta("Error de Transacción", error.message, "error");
    }
}

async function modificarCliente() {
    const idCliente = document.getElementById("cli-id-seleccionado").value;
    if (!idCliente) {
        mostrarAlerta("Selección Requerida", "Tocá primero un cliente de la tabla para modificarlo.", "warning");
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
        mostrarAlerta("Validación", "Nombres y Apellidos son obligatorios.", "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idCliente}`, "PUT", {
            nombres,
            apellidos,
            dni,
            rol: "Cliente"
        });
        const cacheCli = obtenerCacheLocal("cache_clientes");
        cacheCli[idCliente] = { telefono, email, direccion, ciudad, provincia, cp };
        guardarCacheLocal("cache_clientes", cacheCli);

        limpiarFormularioClientes();
        await cargarDatosClientes();
    } catch (error) {
        mostrarAlerta("Error al Actualizar", error.message, "error");
    }
}

async function eliminarCliente() {
    const idCliente = document.getElementById("cli-id-seleccionado").value;
    if (!idCliente) {
        mostrarAlerta("Selección Requerida", "Tocá primero un cliente de la tabla para eliminarlo.", "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idCliente}`, "DELETE");
        limpiarFormularioClientes();
        await cargarDatosClientes();
    } catch (error) {
        mostrarAlerta("Operación Bloqueada", error.message, "error");
    }
}



// =====================================
//  8. MÓDULO DE GESTIÓN DE PROVEEDORES
// =====================================

function limpiarFormularioProveedores() {
    document.getElementById("prov-id-seleccionado").value = "";
    ["prov-razon-social", "prov-cuit", "prov-telefono", "prov-email",
     "prov-direccion", "prov-ciudad", "prov-provincia", "prov-cp", "prov-contacto"].forEach(id => {
        document.getElementById(id).value = "";
    });
    desmarcarFilasTabla("tabla-proveedores");
}

async function cargarDatosProveedores() {
    const tbody = document.querySelector("#tabla-proveedores tbody");
    tbody.innerHTML = "";
    const cacheProv = obtenerCacheLocal("cache_proveedores");

    try {
        const proveedores = await peticionAPI("/api/perfiles/rol/Proveedor");
        proveedores.forEach(p => {
            const extras = cacheProv[p.id] || {};
            const fila = {
                razonSocial: p.nombres || "S/D",
                cuit: p.dni || "S/D",
                telefono: extras.telefono || "S/D",
                email: extras.email || "S/D",
                direccion: extras.direccion || "S/D",
                ciudad: extras.ciudad || "S/D",
                provincia: extras.provincia || "S/D",
                cp: extras.cp || "S/D",
                contacto: p.apellidos || "S/D"
            };

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
                document.getElementById("prov-razon-social").value = fila.razonSocial !== "S/D" ? fila.razonSocial : "";
                document.getElementById("prov-cuit").value = fila.cuit !== "S/D" ? fila.cuit : "";
                document.getElementById("prov-telefono").value = fila.telefono !== "S/D" ? fila.telefono : "";
                document.getElementById("prov-email").value = fila.email !== "S/D" ? fila.email : "";
                document.getElementById("prov-direccion").value = fila.direccion !== "S/D" ? fila.direccion : "";
                document.getElementById("prov-ciudad").value = fila.ciudad !== "S/D" ? fila.ciudad : "";
                document.getElementById("prov-provincia").value = fila.provincia !== "S/D" ? fila.provincia : "";
                document.getElementById("prov-cp").value = fila.cp !== "S/D" ? fila.cp : "";
                document.getElementById("prov-contacto").value = fila.contacto !== "S/D" ? fila.contacto : "";
            });

            tbody.appendChild(tr);
        });
    } catch (error) {
        mostrarAlerta("Error de Comunicación", error.message, "error");
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
        mostrarAlerta("Validación", "La Razón Social es obligatoria.", "warning");
        return;
    }

    try {
        const res = await peticionAPI("/api/perfiles", "POST", {
            nombres: razonSocial,
            apellidos: contacto,
            dni: cuit,
            rol: "Proveedor"
        });
        if (res && res.id) {
            const cacheProv = obtenerCacheLocal("cache_proveedores");
            cacheProv[res.id] = { telefono, email, direccion, ciudad, provincia, cp };
            guardarCacheLocal("cache_proveedores", cacheProv);
        }
        limpiarFormularioProveedores();
        await cargarDatosProveedores();
    } catch (error) {
        mostrarAlerta("Error de Transacción", error.message, "error");
    }
}

async function modificarProveedor() {
    const idProveedor = document.getElementById("prov-id-seleccionado").value;
    if (!idProveedor) {
        mostrarAlerta("Selección Requerida", "Tocá primero un proveedor de la tabla para modificarlo.", "warning");
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
        mostrarAlerta("Validación", "La Razón Social es obligatoria.", "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idProveedor}`, "PUT", {
            nombres: razonSocial,
            apellidos: contacto,
            dni: cuit,
            rol: "Proveedor"
        });
        const cacheProv = obtenerCacheLocal("cache_proveedores");
        cacheProv[idProveedor] = { telefono, email, direccion, ciudad, provincia, cp };
        guardarCacheLocal("cache_proveedores", cacheProv);

        limpiarFormularioProveedores();
        await cargarDatosProveedores();
    } catch (error) {
        mostrarAlerta("Error al Actualizar", error.message, "error");
    }
}

async function eliminarProveedor() {
    const idProveedor = document.getElementById("prov-id-seleccionado").value;
    if (!idProveedor) {
        mostrarAlerta("Selección Requerida", "Tocá primero un proveedor de la tabla para eliminarlo.", "warning");
        return;
    }

    try {
        await peticionAPI(`/api/perfiles/${idProveedor}`, "DELETE");
        limpiarFormularioProveedores();
        await cargarDatosProveedores();
    } catch (error) {
        mostrarAlerta("Operación Bloqueada", error.message, "error");
    }
}



// ============================================
//  9. MÓDULO DE CONTROL DE STOCK E INVENTARIO
// ============================================

function limpiarFormularioStock() {
    document.getElementById("stk-id-seleccionado").value = "";
    ["stk-codigo", "stk-descripcion", "stk-categoria", "stk-proveedor",
     "stk-actual", "stk-minimo", "stk-costo", "stk-venta",
     "stk-ubicacion", "stk-vencimiento"].forEach(id => {
        document.getElementById(id).value = "";
    });
    desmarcarFilasTabla("tabla-stock");
}

async function cargarDatosStock() {
    const tbody = document.querySelector("#tabla-stock tbody");
    const selectProv = document.getElementById("stk-proveedor");
    tbody.innerHTML = "";
    selectProv.innerHTML = '<option value="">Seleccione proveedor...</option>';

    mapaProveedoresNombreAId = {};
    mapaProveedoresIdANombre = {};
    cacheStockAnterior = {};
    const cacheUbicaciones = obtenerCacheLocal("cache_ubicaciones_stock");

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
            cacheStockAnterior[prod.id] = Number(prod.stock_actual || 0);
            const nombreProv = mapaProveedoresIdANombre[prod.id_proveedor] || `ID ${prod.id_proveedor}`;
            const ubicacion = cacheUbicaciones[prod.id] || "S/D";
            const vencimiento = prod.vencimiento || "S/D";

            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${prod.id}</td>
                <td>${prod.codigo}</td>
                <td>${prod.descripcion}</td>
                <td>${prod.categoria || "S/D"}</td>
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
                document.getElementById("stk-categoria").value = prod.categoria !== "S/D" ? prod.categoria : "";
                document.getElementById("stk-proveedor").value = nombreProv;
                document.getElementById("stk-actual").value = prod.stock_actual;
                document.getElementById("stk-minimo").value = prod.stock_minimo;
                document.getElementById("stk-costo").value = prod.precio_costo;
                document.getElementById("stk-venta").value = prod.precio_venta;
                document.getElementById("stk-ubicacion").value = ubicacion !== "S/D" ? ubicacion : "";
                document.getElementById("stk-vencimiento").value = vencimiento !== "S/D" ? vencimiento : "";
            });

            tbody.appendChild(tr);
        });
    } catch (error) {
        mostrarAlerta("Error de Comunicación", error.message, "error");
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
        mostrarAlerta("Validación", "Código, Descripción y Proveedor son campos obligatorios.", "warning");
        return;
    }

    const idProveedor = mapaProveedoresNombreAId[proveedor];
    if (!idProveedor) {
        mostrarAlerta("Error", "El proveedor seleccionado no es válido o fue dado de baja.", "error");
        return;
    }

    const stockActual = stockActualStr ? Number(stockActualStr) : 0.0;
    const stockMinimo = stockMinimoStr ? Number(stockMinimoStr) : 0.0;
    const precioCosto = costoStr ? Number(costoStr) : 0.0;
    const precioVenta = ventaStr ? Number(ventaStr) : 0.0;

    if ([stockActual, stockMinimo, precioCosto, precioVenta].some(isNaN)) {
        mostrarAlerta("Error de Formato", "Asegúrese de ingresar valores numéricos válidos en precios y stock.", "error");
        return;
    }

    try {
        const res = await peticionAPI("/api/productos", "POST", {
            codigo,
            descripcion,
            categoria,
            id_proveedor: idProveedor,
            precio_costo: precioCosto,
            precio_venta: precioVenta,
            stock_actual: stockActual,
            stock_minimo: stockMinimo,
            vencimiento
        });

        if (res && res.id) {
            const cacheUbicaciones = obtenerCacheLocal("cache_ubicaciones_stock");
            cacheUbicaciones[res.id] = ubicacion;
            guardarCacheLocal("cache_ubicaciones_stock", cacheUbicaciones);
        }

        limpiarFormularioStock();
        await cargarDatosStock();
    } catch (error) {
        mostrarAlerta("Error Transaccional", error.message, "error");
    }
}

async function modificarProducto() {
    const idProducto = document.getElementById("stk-id-seleccionado").value;
    if (!idProducto) {
        mostrarAlerta("Selección Requerida", "Tocá primero un producto de la tabla para modificarlo.", "warning");
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
        mostrarAlerta("Validación", "Código, Descripción y Proveedor son campos obligatorios.", "warning");
        return;
    }

    const idProveedor = mapaProveedoresNombreAId[proveedor];
    if (!idProveedor) {
        mostrarAlerta("Error", "El proveedor seleccionado no es válido o fue dado de baja.", "error");
        return;
    }

    const stockActual = stockActualStr ? Number(stockActualStr) : 0.0;
    const stockMinimo = stockMinimoStr ? Number(stockMinimoStr) : 0.0;
    const precioCosto = costoStr ? Number(costoStr) : 0.0;
    const precioVenta = ventaStr ? Number(ventaStr) : 0.0;

    if ([stockActual, stockMinimo, precioCosto, precioVenta].some(isNaN)) {
        mostrarAlerta("Error de Formato", "Asegúrese de ingresar valores numéricos válidos en precios y stock.", "error");
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
            vencimiento
        });

        const stockPrevio = Number(cacheStockAnterior[idProducto] || 0);
        const diferencia = stockActual - stockPrevio;
        if (Math.abs(diferencia) > 1e-6) {
            await peticionAPI(`/api/productos/${idProducto}/stock`, "POST", { cantidad: diferencia });
        }

        const cacheUbicaciones = obtenerCacheLocal("cache_ubicaciones_stock");
        cacheUbicaciones[idProducto] = ubicacion;
        guardarCacheLocal("cache_ubicaciones_stock", cacheUbicaciones);

        limpiarFormularioStock();
        await cargarDatosStock();
    } catch (error) {
        mostrarAlerta("Error Transaccional", error.message, "error");
    }
}

async function eliminarProducto() {
    const idProducto = document.getElementById("stk-id-seleccionado").value;
    if (!idProducto) {
        mostrarAlerta("Selección Requerida", "Tocá primero un producto de la tabla para eliminarlo.", "warning");
        return;
    }

    try {
        await peticionAPI(`/api/productos/${idProducto}`, "DELETE");
        limpiarFormularioStock();
        await cargarDatosStock();
    } catch (error) {
        mostrarAlerta("Operación Bloqueada", error.message, "error");
    }
}



// =====================================================
//  10. MÓDULO DE FACTURACIÓN Y OPERACIONES COMERCIALES
// =====================================================

let facturaSeleccionadaCache = null;

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

async function cargarDatosFacturacion() {
    const selVendedor = document.getElementById("fac-vendedor");
    const selCliente = document.getElementById("fac-cliente");
    const selProducto = document.getElementById("fac-producto");
    const tbody = document.querySelector("#tabla-facturacion tbody");

    const vendedorPrevio = selVendedor.value;
    const clientePrevio = selCliente.value;

    selVendedor.innerHTML = '<option value="">Seleccione vendedor...</option>';
    selCliente.innerHTML = '<option value="">Seleccione cliente...</option>';
    selProducto.innerHTML = '<option value="">Seleccione producto...</option>';
    tbody.innerHTML = "";

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

        let granTotal = 0.0;

        facturas.forEach(f => {
            const prod = mapaProductosIdAObj[f.id_producto];
            const etiquetaProd = prod ? `${prod.codigo} - ${prod.descripcion}` : `ID ${f.id_producto}`;
            const totalFila = f.total !== null && f.total !== undefined
                ? Number(f.total)
                : (Number(f.cantidad) * Number(f.valor)) * (1.0 - (Number(f.descuento || 0) / 100.0));

            granTotal += totalFila;

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
                    etiquetaProd: etiquetaProd,
                    cantidad: Number(f.cantidad)
                };
            });

            tbody.appendChild(tr);
        });

        actualizarEtiquetasTotalesFactura(granTotal, 0);
    } catch (error) {
        mostrarAlerta("Error de Comunicación", error.message, "error");
    }
}

function actualizarEtiquetasTotalesFactura(granTotal, porcentajeGlobal = 0) {
    const totalFinal = granTotal * (1.0 - (porcentajeGlobal / 100.0));
    document.getElementById("fac-total-general").textContent = `TOTAL FACTURA: $ ${totalFinal.toFixed(2)}`;
    document.getElementById("fac-total-con-descuento").textContent =
        `Total con descuento (${porcentajeGlobal}%): $ ${totalFinal.toFixed(2)}`;
}

function calcularDescuentoGlobal() {
    const inputGlobal = document.getElementById("fac-descuento-global");
    const valorStr = inputGlobal.value.trim();
    const porcentaje = valorStr ? Number(valorStr) : 0.0;

    if (isNaN(porcentaje) || porcentaje < 0 || porcentaje > 100) {
        mostrarAlerta("Validación", "El descuento global debe estar entre 0 y 100%.", "error");
        return;
    }

    let sumaTabla = 0.0;
    document.querySelectorAll("#tabla-facturacion tbody tr").forEach(tr => {
        const textoTotal = tr.children[5].textContent.replace("$", "").trim();
        sumaTabla += Number(textoTotal || 0);
    });

    actualizarEtiquetasTotalesFactura(sumaTabla, porcentaje);
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
        mostrarAlerta("Validación", "Vendedor, Cliente y Producto son obligatorios.", "warning");
        return;
    }

    const cantidad = Number(cantidadStr);
    const descuento = descuentoStr ? Number(descuentoStr) : 0.0;

    if (isNaN(cantidad) || cantidad <= 0 || isNaN(descuento)) {
        mostrarAlerta("Error de Formato", "Ingrese valores numéricos válidos en Cantidad y Descuento.", "error");
        return;
    }

    if (descuento < 0 || descuento > 100) {
        mostrarAlerta("Validación", "El descuento por producto debe estar entre 0 y 100%.", "error");
        return;
    }

    const idVendedor = extraerIdDeEtiqueta(vendedorSel);
    const idCliente = extraerIdDeEtiqueta(clienteSel);
    const codigoProd = productoSel.split(" - ")[0];
    const prod = mapaProductosCodigoAObj[codigoProd];

    if (!idVendedor || !idCliente || !prod) {
        mostrarAlerta("Error de Asociación", "Seleccione un vendedor, cliente y producto válidos del menú.", "error");
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
            mostrarAlerta(
                "Alerta de Reposición",
                `El producto llegó a su stock mínimo. Quedan ${Math.trunc(nuevoStock)} unidades.`,
                "warning"
            );
        }
    } catch (error) {
        mostrarAlerta("Transacción Rechazada", error.message, "error");
    }
}

async function modificarFactura() {
    if (!facturaSeleccionadaCache) {
        mostrarAlerta("Selección Requerida", "Tocá primero una factura de la tabla para modificarla.", "warning");
        return;
    }

    const vendedorSel = document.getElementById("fac-vendedor").value.trim();
    const clienteSel = document.getElementById("fac-cliente").value.trim();
    const productoNuevoSel = document.getElementById("fac-producto").value.trim();
    const cantidadNueva = Number(document.getElementById("fac-cantidad").value.trim());
    const descuentoStr = document.getElementById("fac-descuento").value.trim();
    const descuento = descuentoStr ? Number(descuentoStr) : 0.0;

    if (!vendedorSel || !clienteSel || !productoNuevoSel) {
        mostrarAlerta("Error de Carga", "Vendedor, Cliente y Producto son obligatorios.", "error");
        return;
    }

    if (isNaN(cantidadNueva) || cantidadNueva <= 0 || isNaN(descuento) || descuento < 0 || descuento > 100) {
        mostrarAlerta("Validación", "Verificá que la Cantidad y el Descuento (0 a 100%) sean válidos.", "error");
        return;
    }

    const idVendedor = extraerIdDeEtiqueta(vendedorSel);
    const idCliente = extraerIdDeEtiqueta(clienteSel);
    const codigoViejo = facturaSeleccionadaCache.etiquetaProd.split(" - ")[0];
    const codigoNuevo = productoNuevoSel.split(" - ")[0];

    const prodViejo = mapaProductosCodigoAObj[codigoViejo];
    const prodNuevo = mapaProductosCodigoAObj[codigoNuevo];

    if (!prodViejo || !prodNuevo) {
        mostrarAlerta("Error", "No se pudo identificar el producto en el catálogo.", "error");
        return;
    }

    try {
        // 1. Restituimos el stock del comprobante anterior.
        await peticionAPI(`/api/productos/${prodViejo.id}/stock`, "POST", {
            cantidad: facturaSeleccionadaCache.cantidad
        });

        try {
            // 2. Emitimos el nuevo comprobante.
            await peticionAPI("/api/facturas", "POST", {
                id_vendedor: idVendedor,
                id_cliente: idCliente,
                id_producto: prodNuevo.id,
                cantidad: cantidadNueva,
                descuento: descuento
            });
        } catch (errorEmision) {
            // Si no alcanza el stock nuevo, revertimos la devolución previa.
            await peticionAPI(`/api/productos/${prodViejo.id}/stock`, "POST", {
                cantidad: -facturaSeleccionadaCache.cantidad
            });
            mostrarAlerta(
                "Transacción Rechazada",
                `No se pudo modificar la facturación (${errorEmision.message}). Se ha deshecho el cambio.`,
                "error"
            );
            return;
        }

        // 3. Anulamos el comprobante anterior reemplazado.
        await peticionAPI(`/api/facturas/${facturaSeleccionadaCache.id}`, "DELETE");

        limpiarFormularioFacturacion();
        await cargarDatosFacturacion();
    } catch (error) {
        mostrarAlerta("Error Transaccional", error.message, "error");
    }
}

async function eliminarFactura() {
    if (!facturaSeleccionadaCache) {
        mostrarAlerta("Selección Requerida", "Tocá primero una factura de la tabla para eliminarla.", "warning");
        return;
    }

    try {
        const codigoProd = facturaSeleccionadaCache.etiquetaProd.split(" - ")[0];
        const prod = mapaProductosCodigoAObj[codigoProd];
        if (prod) {
            await peticionAPI(`/api/productos/${prod.id}/stock`, "POST", {
                cantidad: facturaSeleccionadaCache.cantidad
            });
        }

        await peticionAPI(`/api/facturas/${facturaSeleccionadaCache.id}`, "DELETE");
        limpiarFormularioFacturacion();
        await cargarDatosFacturacion();
    } catch (error) {
        mostrarAlerta("Operación Bloqueada", error.message, "error");
    }
}



// =====================================================================
//  11. CONSOLA SQL DE AUDITORÍA (SANDBOX DE SOLO LECTURA EN NAVEGADOR)
// =====================================================================

function cargarEjemploSQL(sentencia) {
    document.getElementById("sql-query").value = sentencia;
}

function limpiarConsolaSQL() {
    document.getElementById("sql-query").value = "";
    document.querySelector("#tabla-sql thead").innerHTML = "";
    document.querySelector("#tabla-sql tbody").innerHTML = "";
    const estado = document.getElementById("sql-estado");
    estado.textContent = "Estado: Esperando consulta...";
    estado.style.color = "#333333";
}

async function ejecutarConsultaSQL() {
    const queryCruda = document.getElementById("sql-query").value.trim();
    const labelEstado = document.getElementById("sql-estado");

    if (!queryCruda) return;

    // 1. Verificación RBAC contra la API REST antes de ejecutar.
    try {
        const perfilOperador = await peticionAPI(`/api/perfiles/${sesionActiva.id}`);
        if (perfilOperador.rol !== "Administrador") {
            mostrarAlerta("Acceso Denegado", "Solo un Administrador activo puede ejecutar auditorías SQL.", "error");
            labelEstado.textContent = "Estado: Bloqueado por falta de privilegios RBAC.";
            labelEstado.style.color = "red";
            return;
        }
    } catch (error) {
        mostrarAlerta("Error de Verificación", error.message, "error");
        return;
    }

    // 2. Filtro Restrictivo de Solo Lectura (Sandboxing idéntico a consola.py).
    const patronProhibido = /\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|GRANT|REVOKE|ATTACH|DETACH|PRAGMA)\b/i;
    if (patronProhibido.test(queryCruda)) {
        mostrarAlerta(
            "Bloqueo de Seguridad",
            "Transacción abortada. Operación destructiva detectada.\nEsta consola es de Solo Lectura (SELECT).",
            "error"
        );
        labelEstado.textContent = "Estado: Query bloqueada por Sandboxing.";
        labelEstado.style.color = "red";
        return;
    }

    const queryLimpia = queryCruda.replace(/;$/, "").trim();
    if (!/^SELECT\b/i.test(queryLimpia)) {
        labelEstado.textContent = "Error SQL: Solo se admiten sentencias que comiencen con SELECT.";
        labelEstado.style.color = "red";
        return;
    }

    try {
        // 3. Obtenemos los catálogos vivos desde la API REST para proyectar la consulta.
        const [usuarios, productos, facturacion] = await Promise.all([
            peticionAPI("/api/perfiles"),
            peticionAPI("/api/productos"),
            peticionAPI("/api/facturas")
        ]);

        const tablasMemoria = {
            usuarios: usuarios,
            perfiles: usuarios,
            productos: productos,
            facturacion: facturacion,
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

        // Evaluación opcional de LIMIT.
        const matchLimit = queryLimpia.match(/\bLIMIT\s+(\d+)/i);
        const limite = matchLimit ? Math.min(parseInt(matchLimit[1], 10), 1000) : 1000;
        filas = filas.slice(0, limite);

        // Selección de columnas solicitadas.
        const matchCols = queryLimpia.match(/^SELECT\s+(.+?)\s+FROM\b/i);
        const colsRaw = matchCols ? matchCols[1].trim() : "*";

        let nombresColumnas = [];
        if (filas.length > 0) {
            const todasLasCols = Object.keys(filas[0]);
            if (colsRaw === "*") {
                nombresColumnas = todasLasCols;
            } else {
                nombresColumnas = colsRaw.split(",").map(c => c.trim().split(".").pop());
            }
        }

        renderizarGrillaSQL(nombresColumnas, filas);
        labelEstado.textContent = `Estado: Ejecución exitosa. Filas recuperadas: ${filas.length}`;
        labelEstado.style.color = "green";
    } catch (error) {
        labelEstado.textContent = `Error SQL: ${error.message}`;
        labelEstado.style.color = "red";
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


// =========================================================================
//  12. MÓDULO DE ANALÍTICA DE VENTAS (TABLERO BI - OLAP Y GRÁFICOS CANVAS)
// =========================================================================

async function cargarDatosAnalitica() {
    try {
        const [facturas, productos] = await Promise.all([
            peticionAPI("/api/facturas"),
            peticionAPI("/api/productos")
        ]);

        const mapaProd = {};
        productos.forEach(p => {
            mapaProd[p.id] = p;
        });

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

        if (registros.length === 0) {
            document.getElementById("kpi-facturacion").textContent = "$ 0.00";
            document.getElementById("kpi-operaciones").textContent = "0";
            document.getElementById("kpi-unidades").textContent = "0";
            document.getElementById("kpi-ticket").textContent = "$ 0.00";
            document.getElementById("bi-subtitulo-estrella").textContent = "Sin ventas registradas para analizar";
            document.querySelector("#tabla-bi tbody").innerHTML = "";
            limpiarCanvas("canvas-bi-barras");
            limpiarCanvas("canvas-bi-lineas");
            limpiarCanvas("canvas-bi-torta");
            mostrarAlerta("Información", "No hay ventas registradas para analizar.", "info");
            return;
        }

        // 1. Cálculo de KPIs Generales.
        const totalFacturacion = registros.reduce((acc, r) => acc + r.facturacion, 0);
        const totalOperaciones = registros.length;
        const totalUnidades = registros.reduce((acc, r) => acc + r.cantidad, 0);
        const ticketPromedio = totalOperaciones > 0 ? totalFacturacion / totalOperaciones : 0;

        document.getElementById("kpi-facturacion").textContent = `$ ${formatearMoneda(totalFacturacion)}`;
        document.getElementById("kpi-operaciones").textContent = totalOperaciones.toLocaleString("es-AR");
        document.getElementById("kpi-unidades").textContent = Math.round(totalUnidades).toLocaleString("es-AR");
        document.getElementById("kpi-ticket").textContent = `$ ${formatearMoneda(ticketPromedio)}`;

        // 2. Agrupaciones para Producto Estrella, Categoría Top y Gráficos.
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

        const productoEstrella = Object.entries(cantPorProducto).sort((a, b) => b[1] - a[1])[0][0];
        const categoriaEstrella = Object.entries(factPorCategoria).sort((a, b) => b[1] - a[1])[0][0];

        document.getElementById("bi-subtitulo-estrella").textContent =
            `Más Vendido: ${productoEstrella} | Categoría Top: ${categoriaEstrella}`;

        // 3. Dibujo de los 3 Gráficos en HTML5 Canvas.
        const top10Productos = Object.entries(factPorProducto)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);
        dibujarGraficoBarras("canvas-bi-barras", top10Productos);

        const serieMensual = Object.entries(factPorMes).sort((a, b) => a[0].localeCompare(b[0]));
        dibujarGraficoLineas("canvas-bi-lineas", serieMensual);

        const serieCategorias = Object.entries(factPorCategoria).filter(x => x[1] > 0);
        dibujarGraficoTorta("canvas-bi-torta", serieCategorias);

        // 4. Poblado de la tabla histórica.
        const tbody = document.querySelector("#tabla-bi tbody");
        tbody.innerHTML = "";
        registros.forEach(r => {
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
        });

    } catch (error) {
        mostrarAlerta("Error Analítico", `Fallo al procesar los datos: ${error.message}`, "error");
    }
}

function limpiarCanvas(idCanvas) {
    const canvas = document.getElementById(idCanvas);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function dibujarGraficoBarras(idCanvas, datos) {
    const canvas = document.getElementById(idCanvas);
    const ctx = canvas.getContext("2d");
    const ancho = canvas.width;
    const alto = canvas.height;
    ctx.clearRect(0, 0, ancho, alto);

    if (datos.length === 0) return;

    const padIzq = 55;
    const padDer = 15;
    const padArr = 20;
    const padAba = 65;
    const anchoUtil = ancho - padIzq - padDer;
    const altoUtil = alto - padArr - padAba;

    const maxValor = Math.max(...datos.map(d => d[1]), 1);
    const pasoX = anchoUtil / datos.length;
    const anchoBarra = Math.max(pasoX * 0.62, 8);

    // Ejes base
    ctx.strokeStyle = "#cccccc";
    ctx.beginPath();
    ctx.moveTo(padIzq, padArr);
    ctx.lineTo(padIzq, alto - padAba);
    ctx.lineTo(ancho - padDer, alto - padAba);
    ctx.stroke();

    datos.forEach(([etiqueta, valor], i) => {
        const altoBarra = (valor / maxValor) * altoUtil;
        const x = padIzq + i * pasoX + (pasoX - anchoBarra) / 2;
        const y = alto - padAba - altoBarra;

        ctx.fillStyle = "#2196F3";
        ctx.fillRect(x, y, anchoBarra, altoBarra);

        ctx.save();
        ctx.translate(x + anchoBarra / 2, alto - padAba + 8);
        ctx.rotate(-Math.PI / 4);
        ctx.fillStyle = "#333333";
        ctx.font = "10px Arial";
        ctx.textAlign = "right";
        ctx.fillText(etiqueta.slice(0, 12), 0, 0);
        ctx.restore();
    });
}

function dibujarGraficoLineas(idCanvas, datos) {
    const canvas = document.getElementById(idCanvas);
    const ctx = canvas.getContext("2d");
    const ancho = canvas.width;
    const alto = canvas.height;
    ctx.clearRect(0, 0, ancho, alto);

    if (datos.length === 0) return;

    const padIzq = 55;
    const padDer = 20;
    const padArr = 20;
    const padAba = 55;
    const anchoUtil = ancho - padIzq - padDer;
    const altoUtil = alto - padArr - padAba;

    const maxValor = Math.max(...datos.map(d => d[1]), 1);

    ctx.strokeStyle = "#cccccc";
    ctx.beginPath();
    ctx.moveTo(padIzq, padArr);
    ctx.lineTo(padIzq, alto - padAba);
    ctx.lineTo(ancho - padDer, alto - padAba);
    ctx.stroke();

    const puntos = datos.map(([mes, valor], i) => {
        const x = datos.length === 1
            ? padIzq + anchoUtil / 2
            : padIzq + (i / (datos.length - 1)) * anchoUtil;
        const y = alto - padAba - (valor / maxValor) * altoUtil;
        return { x, y, mes };
    });

    ctx.strokeStyle = "#4CAF50";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    puntos.forEach((p, i) => {
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
    });
    ctx.stroke();

    puntos.forEach(p => {
        ctx.fillStyle = "#4CAF50";
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
        ctx.fill();

        ctx.save();
        ctx.translate(p.x, alto - padAba + 10);
        ctx.rotate(-Math.PI / 4);
        ctx.fillStyle = "#333333";
        ctx.font = "10px Arial";
        ctx.textAlign = "right";
        ctx.fillText(p.mes, 0, 0);
        ctx.restore();
    });
}

function dibujarGraficoTorta(idCanvas, datos) {
    const canvas = document.getElementById(idCanvas);
    const ctx = canvas.getContext("2d");
    const ancho = canvas.width;
    const alto = canvas.height;
    ctx.clearRect(0, 0, ancho, alto);

    if (datos.length === 0) return;

    const colores = [
        "#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#009688",
        "#F44336", "#607D8B", "#3F51B5", "#FFC107", "#795548"
    ];

    const total = datos.reduce((acc, d) => acc + d[1], 0);
    const cx = ancho * 0.34;
    const cy = alto * 0.5;
    const radio = Math.min(cx, cy) - 18;

    let anguloInicial = -Math.PI / 2;

    datos.forEach(([categoria, valor], i) => {
        const porcion = (valor / total) * (Math.PI * 2);
        const color = colores[i % colores.length];

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, radio, anguloInicial, anguloInicial + porcion);
        ctx.closePath();
        ctx.fill();

        anguloInicial += porcion;
    });

    // Leyenda lateral con porcentajes.
    const xLeyenda = ancho * 0.64;
    datos.slice(0, 8).forEach(([categoria, valor], i) => {
        const y = 26 + i * 28;
        const pct = ((valor / total) * 100).toFixed(1);

        ctx.fillStyle = colores[i % colores.length];
        ctx.fillRect(xLeyenda, y - 9, 12, 12);

        ctx.fillStyle = "#333333";
        ctx.font = "11px Arial";
        ctx.textAlign = "left";
        ctx.fillText(`${categoria.slice(0, 11)} (${pct}%)`, xLeyenda + 16, y);
    });
}


// =============================================
//  13. UTILIDADES VISUALES DE TABLAS Y FORMATO
// =============================================

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