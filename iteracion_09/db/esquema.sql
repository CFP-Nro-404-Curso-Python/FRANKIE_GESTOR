-- ======================================================================================= --
--    ESQUEMA RELACIONAL NORMALIZADO (ITERACIÓN 08) - ADAPTACIÓN DE CÁTEDRA PARA SQLITE    --
-- ======================================================================================= --
--  En SQLite, las tablas deben crearse en un orden jerárquico estricto.                   --
--  Primero se crean las "Tablas Maestras" (las que no dependen de nadie).                 --
--  Luego se crean las "Tablas Centrales" y finalmente las "Tablas Intermedias o Pivot",   --
--  que son las que contienen las Claves Foráneas (Foreign Keys) que conectan todo.        --
--                                                                                         --
--  NOTA ARQUITECTÓNICA: Se eliminaron las "referencias circulares" del script original    --
--  de la cátedra porque SQLite no las soporta de forma nativa. La integridad se mantiene  --
--  conectando las tablas hijas hacia las tablas maestras, garantizando un flujo limpio.   --
-- ======================================================================================= --



-- ---------------------------------------------------------------------------------------
--  FASE 1: TABLAS MAESTRAS (CATÁLOGOS ATOMIZADOS)
--
--  Estas tablas reemplazan los viejos campos de texto libre. Guardan la palabra una sola 
--  vez para evitar redundancia y errores de tipeo.
-- ---------------------------------------------------------------------------------------

-- Catálogos de Ubicación.

CREATE TABLE IF NOT EXISTS paises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pais TEXT NOT NULL,
    habilitado INTEGER DEFAULT 1 -- 1 = Activo, 0 = Baja Lógica (Eliminado).
);

CREATE TABLE IF NOT EXISTS provincias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provincia TEXT NOT NULL,
    habilitado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ciudades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ciudad TEXT NOT NULL,
    habilitado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS codigopostales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cp TEXT NOT NULL,
    habilitado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS direcciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    direccion TEXT NOT NULL,
    habilitado INTEGER DEFAULT 1
);

-- Catálogos de Contacto.

CREATE TABLE IF NOT EXISTS telefonos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telefono TEXT NOT NULL,
    habilitado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail TEXT NOT NULL,
    habilitado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS redessociales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    redsocial TEXT NOT NULL,
    habilitado INTEGER DEFAULT 1
);

-- Catálogos de Roles y Estados.

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rol TEXT NOT NULL,
    habilitado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS estados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estado TEXT NOT NULL, -- Ej: "Disponible", "Agotado", "En Tránsito".
    habilitado INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ubicaciones_stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ubicacion TEXT NOT NULL, -- Ej: "Depósito A", "Vitrina B".
    habilitado INTEGER DEFAULT 1
);



-- ------------------------------------------------------------------------------------------
--  FASE 2: TABLA CENTRAL DEL SISTEMA (UNIFICACIÓN DE ENTIDADES)
--
--  Ya no existen clientes, empleados o proveedores por separado. Todos son "usuarios".
--  Fusionamos los requisitos de la cátedra con nuestro sistema de login de la Iteración 07.
-- ------------------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE,       -- Credencial de Login (Puede ser nulo para clientes).
    password TEXT,             -- Hash Bcrypt (Iteración 07).
    nombres TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    dni TEXT,                  -- Único dato personal que queda en la tabla central.
    habilitado INTEGER DEFAULT 1
);



-- -------------------------------------------------------------------------------------------
--  FASE 3: TABLAS INTERMEDIAS DE USUARIOS (ROMPIENDO LA RELACIÓN MUCHOS A MUCHOS)
--
--  Estas tablas conectan al usuario central con sus múltiples roles, contactos y domicilios.
-- -------------------------------------------------------------------------------------------

-- 1. Vinculación de Roles (Permite que un usuario sea Empleado y a la vez Cliente).
CREATE TABLE IF NOT EXISTS usuxroles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    id_rol INTEGER NOT NULL,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
    FOREIGN KEY (id_rol) REFERENCES roles(id)
);

-- 2. Vinculación de Contactos (Árbol de Contacto).
CREATE TABLE IF NOT EXISTS usuarioxcontactos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS contactoxtelefonos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_contacto INTEGER NOT NULL,
    id_telefono INTEGER NOT NULL,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_contacto) REFERENCES usuarioxcontactos(id),
    FOREIGN KEY (id_telefono) REFERENCES telefonos(id)
);

CREATE TABLE IF NOT EXISTS contactoxmails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_contacto INTEGER NOT NULL,
    id_mail INTEGER NOT NULL,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_contacto) REFERENCES usuarioxcontactos(id),
    FOREIGN KEY (id_mail) REFERENCES mails(id)
);

CREATE TABLE IF NOT EXISTS contactoxredes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_contacto INTEGER NOT NULL,
    id_redes INTEGER NOT NULL,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_contacto) REFERENCES usuarioxcontactos(id),
    FOREIGN KEY (id_redes) REFERENCES redessociales(id)
);

-- 3. Vinculación de Ubicaciones (Árbol Geográfico según requerimiento estricto de cátedra).
CREATE TABLE IF NOT EXISTS usuarioxubicaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS ubicacionxdireccion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_ubicacion INTEGER NOT NULL,
    id_direccion INTEGER NOT NULL,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_ubicacion) REFERENCES usuarioxubicaciones(id),
    FOREIGN KEY (id_direccion) REFERENCES direcciones(id)
);

CREATE TABLE IF NOT EXISTS ubicacionxlocalidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_ubicacion INTEGER NOT NULL,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_ubicacion) REFERENCES usuarioxubicaciones(id)
);

CREATE TABLE IF NOT EXISTS localidadxpaises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_localidad INTEGER NOT NULL,
    id_pais INTEGER NOT NULL,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_localidad) REFERENCES ubicacionxlocalidades(id),
    FOREIGN KEY (id_pais) REFERENCES paises(id)
);

CREATE TABLE IF NOT EXISTS localidadxprovincias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_localidad INTEGER NOT NULL,
    id_provincia INTEGER NOT NULL,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_localidad) REFERENCES ubicacionxlocalidades(id),
    FOREIGN KEY (id_provincia) REFERENCES provincias(id)
);

CREATE TABLE IF NOT EXISTS localidadxciudades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_localidad INTEGER NOT NULL,
    id_ciudad INTEGER NOT NULL,
    id_cp INTEGER NOT NULL,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_localidad) REFERENCES ubicacionxlocalidades(id),
    FOREIGN KEY (id_ciudad) REFERENCES ciudades(id),
    FOREIGN KEY (id_cp) REFERENCES codigopostales(id)
);



-- ------------------------------------------------------------------------------
--  FASE 4: GESTIÓN DE PRODUCTOS E INVENTARIO
--
--  Adaptado para relacionar el proveedor con el nuevo ID unificado de usuarios.
-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    descripcion TEXT NOT NULL,
    categoria TEXT,
    id_proveedor INTEGER NOT NULL,  -- Clave foránea hacia tabla usuarios (filtrado por rol en app).
    stock_actual REAL DEFAULT 0,
    stock_minimo REAL DEFAULT 0,
    precio_costo REAL DEFAULT 0,
    precio_venta REAL DEFAULT 0,
    vencimiento TEXT,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_proveedor) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS productoxestados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto INTEGER NOT NULL,
    id_estado INTEGER NOT NULL,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_producto) REFERENCES productos(id),
    FOREIGN KEY (id_estado) REFERENCES estados(id)
);

CREATE TABLE IF NOT EXISTS productoxubicaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto INTEGER NOT NULL,
    id_ubicacion INTEGER NOT NULL,
    habilitado INTEGER DEFAULT 1,
    FOREIGN KEY (id_producto) REFERENCES productos(id),
    FOREIGN KEY (id_ubicacion) REFERENCES ubicaciones_stock(id)
);



-- --------------------------------------------------------------------------------
--  FASE 5: MÓDULO TRANSACCIONAL (FACTURACIÓN)
--
--  Se eliminan los campos de texto plano. Ahora todo se vincula mediante IDs para 
--  garantizar la integridad referencial de los comprobantes.
-- ---------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS facturacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP, -- Guardamos el momento exacto de la venta.
    id_vendedor INTEGER NOT NULL,             -- Quien vendió (ID de usuario).
    id_cliente INTEGER NOT NULL,              -- A quien se le vendió (ID de usuario).
    id_producto INTEGER NOT NULL,             -- Qué se vendió (ID de producto).
    cantidad REAL NOT NULL,
    valor REAL NOT NULL,                      -- Precio congelado al momento de la venta.
    descuento REAL DEFAULT 0,

    -- COLUMNA GENERADA AUTOMÁTICAMENTE (Calculadora Integrada)
    -- Le pasammos la fórmula que  antes estaba en Python.
    -- 'GENERATED ALWAYS AS' le dice a SQLite que calcule este valor solo.
    -- 'STORED' significa que el resultado se guarda físicamente en el disco para no gastar procesador recalculando 
    -- cada vez que miramos la tabla.
    total REAL GENERATED ALWAYS AS ((cantidad * valor) * (1 - (descuento / 100.0))) STORED,

    habilitado INTEGER DEFAULT 1,             -- Permite anular facturas (Baja Lógica).
    FOREIGN KEY (id_vendedor) REFERENCES usuarios(id),
    FOREIGN KEY (id_cliente) REFERENCES usuarios(id),
    FOREIGN KEY (id_producto) REFERENCES productos(id)
);



-- -----------------------------------------------------------------------------------------
--  FASE 6: REGLAS DE NEGOCIO (TRIGGERS) Y VISTAS (VIEWS)
--
--  REFACTORIZACIÓN: Se agregan capas de seguridad a nivel base de datos y se preparan
--  objetos virtuales (Vistas) para desacoplar la lógica de negocio de la interfaz gráfica,
--  apuntando a un modelo MVC puro en futuras iteraciones.
-- -----------------------------------------------------------------------------------------

-- 1. TRIGGER DE SUPERVIVENCIA (Prevención de DoS Lógico)

-- Este disparador intercepta cualquier UPDATE en la tabla usuarios. Si se intenta deshabilitar 
-- (baja lógica) a un Administrador y es el último que queda activo, el motor de SQLite aborta 
-- la transacción automáticamente, blindando el sistema contra errores de la aplicación o 
-- acciones maliciosas.

CREATE TRIGGER IF NOT EXISTS trg_proteger_ultimo_admin
BEFORE UPDATE OF habilitado ON usuarios
FOR EACH ROW
WHEN NEW.habilitado = 0 AND OLD.habilitado = 1
BEGIN
    SELECT CASE
        -- Verifica si el rol del usuario afectado es 'Administrador'.

        WHEN (SELECT r.rol FROM usuxroles ur JOIN roles r ON ur.id_rol = r.id WHERE ur.id_usuario = OLD.id) = 'Administrador'
        
        -- Verifica si el conteo total de Administradores activos caerá a 0.

        AND (SELECT COUNT(*) FROM usuarios u JOIN usuxroles ur ON u.id = ur.id_usuario JOIN roles r ON ur.id_rol = r.id WHERE r.rol = 'Administrador' AND u.habilitado = 1) <= 1
        
        -- Aborta y devuelve un mensaje de error nativo.

        THEN RAISE(ABORT, 'Violación de Integridad: No se puede dar de baja al último Administrador del sistema.')
    END;
END;

-- 2. VISTA (VIEW) DE EMPLEADOS: Desacoplamiento de Lógica de UI
-- CAMBIO CRÍTICO: Se inyecta la validación 'habilitado = 1' en TODOS los JOINs para evitar
-- filas duplicadas por historial de modificaciones, y se hace un DROP previo para forzar a SQLite
-- a aplicar estos cambios sobre la base de datos existente.

DROP VIEW IF EXISTS vista_empleados_activos;

CREATE VIEW vista_empleados_activos AS
SELECT u.id, u.nombres, u.apellidos, u.dni, t.telefono, m.mail, d.direccion, c.ciudad, p.provincia, cp.cp, r.rol
FROM usuarios u
JOIN usuxroles ur ON u.id = ur.id_usuario AND ur.habilitado = 1
JOIN roles r ON ur.id_rol = r.id AND r.habilitado = 1
LEFT JOIN usuarioxcontactos uc ON u.id = uc.id_usuario AND uc.habilitado = 1
LEFT JOIN contactoxtelefonos ct ON uc.id = ct.id_contacto AND ct.habilitado = 1
LEFT JOIN telefonos t ON ct.id_telefono = t.id AND t.habilitado = 1
LEFT JOIN contactoxmails cm ON uc.id = cm.id_contacto AND cm.habilitado = 1
LEFT JOIN mails m ON cm.id_mail = m.id AND m.habilitado = 1
LEFT JOIN usuarioxubicaciones uu ON u.id = uu.id_usuario AND uu.habilitado = 1
LEFT JOIN ubicacionxdireccion ud ON uu.id = ud.id_ubicacion AND ud.habilitado = 1
LEFT JOIN direcciones d ON ud.id_direccion = d.id AND d.habilitado = 1
LEFT JOIN ubicacionxlocalidades ul ON uu.id = ul.id_ubicacion AND ul.habilitado = 1
LEFT JOIN localidadxciudades lc ON ul.id = lc.id_localidad AND lc.habilitado = 1
LEFT JOIN ciudades c ON lc.id_ciudad = c.id AND c.habilitado = 1
LEFT JOIN codigopostales cp ON lc.id_cp = cp.id AND cp.habilitado = 1
LEFT JOIN localidadxprovincias lp ON ul.id = lp.id_localidad AND lp.habilitado = 1
LEFT JOIN provincias p ON lp.id_provincia = p.id AND p.habilitado = 1
WHERE r.rol NOT IN ('Cliente', 'Proveedor') AND u.habilitado = 1;

-- 3. TRIGGERS DE BLOQUEO DE BORRADO FÍSICO (HARD DELETE LOCK)
-- Estos disparadores interceptan cualquier instrucción DELETE en tablas críticas.
-- Garantizan que ni un error de backend ni una inyección SQL puedan destruir datos físicos, forzando a todo el 
-- ecosistema a usar obligatoriamente UPDATE habilitado = 0.

CREATE TRIGGER IF NOT EXISTS trg_bloquear_delete_usuarios
BEFORE DELETE ON usuarios
BEGIN
    SELECT RAISE(ABORT, 'Violación de Seguridad Nivel 1: Prohibido eliminar usuarios físicamente. Utilice la baja lógica (habilitado = 0).');
END;

CREATE TRIGGER IF NOT EXISTS trg_bloquear_delete_facturacion
BEFORE DELETE ON facturacion
BEGIN
    SELECT RAISE(ABORT, 'Violación de Auditoría: Prohibido eliminar comprobantes de facturación históricos.');
END;

CREATE TRIGGER IF NOT EXISTS trg_bloquear_delete_productos
BEFORE DELETE ON productos
BEGIN
    SELECT RAISE(ABORT, 'Violación de Integridad: Prohibido eliminar productos del catálogo. Utilice la baja lógica.');
END;

CREATE TRIGGER IF NOT EXISTS trg_bloquear_delete_roles
BEFORE DELETE ON roles
BEGIN
    SELECT RAISE(ABORT, 'Violación de Arquitectura: Prohibido eliminar roles del sistema.');
END;



-- ======================================================================================= --
--  FIN DEL ESQUEMA RELACIONAL                                                             --
--                                                                                         --
--  Al ejecutar este archivo completo, SQLite construirá la base de datos perfecta,        --
--  con todas sus reglas, catálogos vacíos y relaciones preparadas para recibir datos.     --
-- ======================================================================================= --