# ==============================================================================
#  PAQUETE ADAPTADOR API REST FASTAPI (CAPA 3 - INFRAESTRUCTURA)
# ==============================================================================
#  DECISIÓN DE DISEÑO (PREVENCIÓN DE IMPORTACIONES CIRCULARES / LAZY LOADING):
#
#   Este archivo inicializa el paquete HTTP sin importar de forma ansiosa
#   'servidor.py' ni los enrutadores. Esto permite que 'inyector_dependencias',
#   'esquemas_validacion' y los overrides de la suite Pytest (TestClient) se
#   carguen de manera independiente sin disparar referencias circulares.
# ==============================================================================

__all__ = [
    "esquemas_validacion",
    "inyector_dependencias",
    "rutas_perfiles",
    "rutas_operaciones",
    "servidor",
]