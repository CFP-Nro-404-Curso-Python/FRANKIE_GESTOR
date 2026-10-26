# ================================================================================
#  PRUEBAS UNITARIAS: POLÍTICAS RBAC (TDD CICLO 1 - DOMINIO)
# ================================================================================
#  DECISIÓN DE DISEÑO (TDD / ALTA COHESIÓN):
#
#   Probamos las reglas de negocio de forma aislada, sin levantar bases de datos 
#   ni servidores web. Estas pruebas validan el Patrón Estrategia. Se ejecutan en 
#   milisegundos, garantizando que el núcleo de seguridad es impenetrable.
# ================================================================================



import pytest
from src.dominio.excepciones import ErrorJerarquiaRBAC
from src.dominio.politicas_rbac import (
    EstrategiaAdministrador,
    EstrategiaGerente,
    EstrategiaEmpleado,
    obtener_estrategia_rbac
)


# -----------------------------------
#  1. TESTS ESTRATEGIA ADMINISTRADOR
# -----------------------------------

def test_administrador_tiene_acceso_total():
    """
     Un Administrador no debe sufrir bloqueos lógicos por parte del RBAC.
     La protección contra auto-baja se delega al motor SQLite (Trigger).
    """
    estrategia = EstrategiaAdministrador()
    
    # Si estas llamadas lanzan excepción, la prueba fallará automáticamente.
    estrategia.validar_creacion(rol_destino="Gerente")
    estrategia.validar_modificacion(rol_destino="Administrador", id_destino=1, id_operador=2)
    estrategia.validar_baja(rol_destino="Gerente", id_destino=3, id_operador=1)


# -----------------------------
#  2. TESTS ESTRATEGIA GERENTE
# -----------------------------

def test_gerente_puede_operar_sobre_empleados_y_clientes():
    estrategia = EstrategiaGerente()
    
    # Operaciones válidas (No deben lanzar excepción).
    estrategia.validar_creacion(rol_destino="Empleado - Ventas")
    estrategia.validar_modificacion(rol_destino="Cliente", id_destino=10, id_operador=2)
    estrategia.validar_baja(rol_destino="Proveedor", id_destino=5, id_operador=2)


def test_gerente_no_puede_crear_perfiles_superiores():
    estrategia = EstrategiaGerente()
    
    # Verificamos que se intercepte correctamente el intento de escalar privilegios.
    with pytest.raises(ErrorJerarquiaRBAC, match="Privilegios insuficientes"):
        estrategia.validar_creacion(rol_destino="Administrador")
        
    with pytest.raises(ErrorJerarquiaRBAC):
        estrategia.validar_creacion(rol_destino="Gerente")


def test_gerente_puede_modificarse_a_si_mismo_pero_no_a_otros_gerentes():
    estrategia = EstrategiaGerente()
    
    # Auto-modificación válida (Mismo ID).
    estrategia.validar_modificacion(rol_destino="Gerente", id_destino=5, id_operador=5)
    
    # Modificar a un par inválido (Distinto ID).
    with pytest.raises(ErrorJerarquiaRBAC):
        estrategia.validar_modificacion(rol_destino="Gerente", id_destino=6, id_operador=5)


def test_gerente_no_puede_darse_de_baja_a_si_mismo():
    estrategia = EstrategiaGerente()
    
    with pytest.raises(ErrorJerarquiaRBAC, match="no podés darte de baja a vos mismo"):
        estrategia.validar_baja(rol_destino="Gerente", id_destino=3, id_operador=3)


# -------------------------------------------------
#  3. TESTS ESTRATEGIA EMPLEADO (VENTAS / COMPRAS)
# -------------------------------------------------

def test_empleado_solo_puede_operar_clientes_y_proveedores():
    estrategia = EstrategiaEmpleado()
    
    # Operaciones válidas.
    estrategia.validar_creacion(rol_destino="Cliente")
    estrategia.validar_modificacion(rol_destino="Proveedor", id_destino=8, id_operador=15)
    
    # Intentos de operar sobre RRHH (Operaciones Bloqueadas).
    with pytest.raises(ErrorJerarquiaRBAC):
        estrategia.validar_creacion(rol_destino="Empleado - Ventas")
        
    with pytest.raises(ErrorJerarquiaRBAC):
        estrategia.validar_baja(rol_destino="Gerente", id_destino=2, id_operador=15)


# -------------------------------------------
#  4. TESTS FÁBRICA DE ESTRATEGIAS (FACTORY)
# -------------------------------------------

def test_fabrica_devuelve_estrategia_correcta_segun_rol():
    """
     Garantiza que la inyección de dependencias asigne la política correcta 
     al operador, cayendo en la política más restrictiva por defecto.
    """
    assert isinstance(obtener_estrategia_rbac("Administrador"), EstrategiaAdministrador)
    assert isinstance(obtener_estrategia_rbac("Gerente"), EstrategiaGerente)
    
    # Empleados específicos y roles no mapeados caen en EstrategiaEmpleado.
    assert isinstance(obtener_estrategia_rbac("Empleado - Ventas"), EstrategiaEmpleado)
    assert isinstance(obtener_estrategia_rbac("Empleado - Compras"), EstrategiaEmpleado)
    assert isinstance(obtener_estrategia_rbac("RolInexistente"), EstrategiaEmpleado)