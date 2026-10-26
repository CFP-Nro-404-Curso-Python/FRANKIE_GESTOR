# ==============================================================================
#  PAQUETE DE PRUEBAS AUTOMATIZADAS (SUITE TDD)
# ==============================================================================
#  DECISIÓN DE DISEÑO:
#  Al igual que en 'src', la existencia de este archivo __init__.py convierte 
#  a la carpeta 'tests' en un paquete formal de Python.
#  
#  Esto es fundamental para la infraestructura de testing, ya que permite que 
#  el framework 'pytest' descubra automáticamente todos los subdirectorios 
#  (unitarios, integracion) y resuelva limpiamente las importaciones hacia 
#  el código de producción en la carpeta 'src', sin tener que hacer parches 
#  oscuros sobre las rutas del sistema operativo (sys.path).
# ==============================================================================