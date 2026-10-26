# ===============================================================================
#  PAQUETE RAÍZ DE PRODUCCIÓN (ARQUITECTURA HEXAGONAL)
# ===============================================================================
#  DECISIÓN DE DISEÑO: Este archivo convierte al directorio 'src' en un paquete 
#  formal de Python. Su existencia permite que tanto el servidor de aplicaciones 
#  (Uvicorn) como el motor de pruebas automatizadas (Pytest) resuelvan las 
#  importaciones absolutas (ej. 'from src.dominio...') de manera determinista, 
#  evitando parches frágiles sobre 'sys.path' en los módulos internos.
# ===============================================================================



__version_sistema__ = "10.0.0"
__patron_arquitectonico__ = "Hexagonal (Puertos y Adaptadores)"