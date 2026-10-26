# ==================================================================================
#  EXCEPCIONES DE DOMINIO (CAPA 1 - NÚCLEO DE NEGOCIO)
# ==================================================================================
#  DECISIÓN DE DISEÑO (KISS / SOLID):
#  
#   En lugar de usar diccionarios o mezclar códigos HTTP (400, 403, 404) en la 
#   lógica central, modelamos los errores de negocio como clases puras de Python.
#  
#   De esta manera, el dominio desconoce por completo que existe una API o una web.
#   Luego, en la Capa 3, FastAPI interceptará estas clases y las traducirá al 
#   código HTTP correspondiente de forma centralizada.
# ==================================================================================



class ErrorDominio(Exception):
    """
     Excepción base para todos los errores de negocio de Frankie Gestor.
     Aplicando Polimorfismo, esto permite a los controladores de la API atrapar 
     cualquier falla predecible usando un solo bloque 'except ErrorDominio:'.
    """
    pass


class ErrorJerarquiaRBAC(ErrorDominio):
    """
     Lanzada por las Políticas de Acceso (Patrón Estrategia) cuando un usuario
     intenta realizar una acción sobre un rol superior o darse de baja a sí mismo.
     Se traduce arquitectónicamente a un HTTP 403 (Forbidden).
    """
    pass


class ErrorCredencialesInvalidas(ErrorDominio):
    """
     Lanzada cuando la contraseña no coincide con el hash o el usuario no existe.
     Se traduce arquitectónicamente a un HTTP 401 (Unauthorized).
    """
    pass


class ErrorEntidadNoEncontrada(ErrorDominio):
    """
     Lanzada por los repositorios cuando se busca un ID (producto, usuario, venta)
     que no existe físicamente o que tiene baja lógica (habilitado = 0).
     Se traduce arquitectónicamente a un HTTP 404 (Not Found).
    """
    pass


class ErrorReglaNegocio(ErrorDominio):
    """
     Lanzada cuando un dato es estructuralmente válido (ej. es un número), pero 
     rompe una regla comercial (ej. un descuento mayor al 100% o un precio negativo).
     Se traduce arquitectónicamente a un HTTP 422 (Unprocessable Entity).
    """
    pass


class ErrorStockInsuficiente(ErrorReglaNegocio):
    """
     Lanzada específicamente en los Casos de Uso Comerciales cuando la cantidad 
     a facturar supera al 'stock_actual' del producto en inventario.
     Hereda de ErrorReglaNegocio por principio de jerarquía de clases.
    """
    pass