# =================================================================================
#  POLÍTICAS DE ACCESO Y SEGURIDAD RBAC (CAPA 1 - NÚCLEO DE NEGOCIO)
# =================================================================================
#  DECISIÓN DE DISEÑO (PATRÓN ESTRATEGIA Y PRINCIPIO OCP DE S.O.L.I.D.):
#
#  En lugar de llenar los Casos de Uso con condicionales "if rol == X", creamos
#  una estrategia separada para cada rol. Si mañana el negocio suma un rol de 
#  "Auditor", simplemente agregamos una clase nueva sin tocar el código existente.
# =================================================================================



from abc import ABC, abstractmethod
from src.dominio.excepciones import ErrorJerarquiaRBAC

class PoliticaAcceso(ABC):
    """
     Clase Abstracta (Interfaz). Define el contrato obligatorio que debe cumplir
     cualquier estrategia de rol en el sistema.
    """
    @abstractmethod
    def validar_creacion(self, rol_destino: str) -> None:
        pass

    @abstractmethod
    def validar_modificacion(self, rol_destino: str, id_destino: int, id_operador: int) -> None:
        pass

    @abstractmethod
    def validar_baja(self, rol_destino: str, id_destino: int, id_operador: int) -> None:
        pass


class EstrategiaAdministrador(PoliticaAcceso):
    """
     El Administrador tiene control total. 
     Las validaciones pasan sin lanzar excepciones (pass).
     Nota: La protección para no borrar al último Administrador se delega 
     intencionalmente al Trigger de SQLite en la base de datos.
    """
    def validar_creacion(self, rol_destino: str) -> None:
        pass

    def validar_modificacion(self, rol_destino: str, id_destino: int, id_operador: int) -> None:
        pass

    def validar_baja(self, rol_destino: str, id_destino: int, id_operador: int) -> None:
        pass


class EstrategiaGerente(PoliticaAcceso):
    """
     El Gerente puede gestionar Operadores, Clientes y Proveedores, pero tiene 
     bloqueos estrictos sobre jerarquías superiores o iguales.
    """
    def validar_creacion(self, rol_destino: str) -> None:
        if rol_destino in ["Administrador", "Gerente"]:
            raise ErrorJerarquiaRBAC("Privilegios insuficientes para crear perfiles de esta jerarquía.")

    def validar_modificacion(self, rol_destino: str, id_destino: int, id_operador: int) -> None:
        # Puede modificarse a sí mismo, pero no a otros gerentes ni a administradores.
        if rol_destino == "Administrador" or (rol_destino == "Gerente" and id_destino != id_operador):
            raise ErrorJerarquiaRBAC("Privilegios insuficientes para modificar a este usuario.")

    def validar_baja(self, rol_destino: str, id_destino: int, id_operador: int) -> None:
        if rol_destino in ["Administrador", "Gerente"]:
            if id_destino == id_operador:
                raise ErrorJerarquiaRBAC("Por políticas de seguridad, no podés darte de baja a vos mismo. Contactá a RRHH.")
            raise ErrorJerarquiaRBAC("Privilegios insuficientes para eliminar a este empleado o usuario.")


class EstrategiaEmpleado(PoliticaAcceso):
    """
     Estrategia restrictiva por defecto para cualquier empleado de Ventas/Compras.
     Los empleados no tienen acceso al ABM de usuarios/empleados, solo operan con Clientes y Proveedores.
    """
    def validar_creacion(self, rol_destino: str) -> None:
        if rol_destino not in ["Cliente", "Proveedor"]:
            raise ErrorJerarquiaRBAC("Privilegios insuficientes. Solo podés registrar Clientes o Proveedores.")

    def validar_modificacion(self, rol_destino: str, id_destino: int, id_operador: int) -> None:
        if rol_destino not in ["Cliente", "Proveedor"]:
            raise ErrorJerarquiaRBAC("Privilegios insuficientes. Solo podés modificar Clientes o Proveedores.")

    def validar_baja(self, rol_destino: str, id_destino: int, id_operador: int) -> None:
        if rol_destino not in ["Cliente", "Proveedor"]:
            raise ErrorJerarquiaRBAC("Privilegios insuficientes. Solo podés eliminar Clientes o Proveedores.")



# ==================================
#  FÁBRICA DE ESTRATEGIAS (FACTORY)
# ==================================

def obtener_estrategia_rbac(rol_operador: str) -> PoliticaAcceso:
    """
    Inyecta la política de seguridad correspondiente al rol del usuario autenticado.
    Evita que los Casos de Uso instancien las clases manualmente (Bajo Acoplamiento).
    """
    estrategias = {
        "Administrador": EstrategiaAdministrador(),
        "Gerente": EstrategiaGerente()
    }
    
    # Si el rol es Empleado (Ventas o Compras) u otro no mapeado, aplica la política restrictiva.
    return estrategias.get(rol_operador, EstrategiaEmpleado())