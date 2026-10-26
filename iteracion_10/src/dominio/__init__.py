# ===================================================================================
#  NÚCLEO DE DOMINIO - FRONTERA DE AISLAMIENTO (CAPA 1)
# ===================================================================================
#  DECISIÓN DE DISEÑO (KISS Y BAJO ACOPLAMIENTO): 
#  1. Se mantiene este inicializador libre de importaciones ansiosas (eager imports) 
#     hacia los submódulos (entidades, excepciones, politicas_rbac, puertos). 
#     Esto previene dependencias circulares en tiempo de carga y obliga a que 
#     las capas externas declaren explícitamente qué contrato consumen.
#  2. Regla de oro arquitectónica: Ningún archivo dentro de este paquete puede 
#     importar librerías de infraestructura (sqlite3, bcrypt, fastapi, requests).
# ===================================================================================



__capa_arquitectura__ = "Dominio Puro (Reglas de Negocio)"