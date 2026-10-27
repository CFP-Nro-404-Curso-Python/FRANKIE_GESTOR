from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# -------------------------------------------------------------------------------------
# CAMBIO APLICADO: 
#  Se agregó ErrorCredencialesInvalidas a la importación desde src.dominio.excepciones
# -------------------------------------------------------------------------------------

from src.dominio.excepciones import (
    ErrorJerarquiaRBAC, 
    ErrorStockInsuficiente, 
    ErrorCredencialesInvalidas
)
from src.infraestructura.api.rutas_perfiles import router as router_perfiles
from src.infraestructura.api.rutas_operaciones import router as router_operaciones

# ===================================================================================
#  SERVIDOR FASTAPI Y MANEJADOR GLOBAL DE EXCEPCIONES (CAPA 3 - INFRAESTRUCTURA)
# ===================================================================================
#  DECISIÓN DE DISEÑO (MANEJADOR DE EXCEPCIONES CENTRALIZADO):
#
#   Para mantener limpios los casos de uso y las rutas, atrapamos las excepciones 
#   puras de negocio acá a nivel global. El servidor las intercepta en el aire y 
#   las traduce automáticamente a códigos HTTP (400, 403, etc.) antes de responderle 
#   al cliente (Frontend Web o Tkinter).
# ===================================================================================



app = FastAPI(
    title="API REST - Frankie Gestor",
    description="Backend transaccional para el Sistema de Gestión Comercial",
    version="1.0.0"
)


# ----------------------------------------------------------
#  1. CONFIGURACIÓN DE CORS (CROSS-ORIGIN RESOURCE SHARING)
# ----------------------------------------------------------

# Permite que nuestro cliente web (HTML/JS) consuma esta API incluso si está 
# corriendo en un puerto diferente al del backend.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción, esto se restringe a la IP del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
#  2. CONEXIÓN DE ENRUTADORES
# ----------------------------

# Ensamblamos las rutas HTTP modularizadas en nuestra aplicación principal.

app.include_router(router_perfiles)
app.include_router(router_operaciones)


# ------------------------------------------------------------
#  3. TRADUCTORES DE EXCEPCIONES DE DOMINIO -> PROTOCOLO HTTP
# ------------------------------------------------------------

# --------------------------------------------------------------------------------------
# CAMBIO APLICADO:
#  
#  Se agregó el manejador específico para ErrorCredencialesInvalidas que traduce
#  el error de la Capa de Aplicación a un código HTTP 401 Unauthorized para el cliente.
# --------------------------------------------------------------------------------------

@app.exception_handler(ErrorCredencialesInvalidas)
async def manejador_error_credenciales(request: Request, exc: ErrorCredencialesInvalidas):
    """
     Atrapa los fallos de autenticación lanzados por el caso de uso y 
     devuelve HTTP 401 Unauthorized de forma segura.
    """
    return JSONResponse(
        status_code=401,
        content={"detalle": str(exc)}
    )

@app.exception_handler(ErrorJerarquiaRBAC)
async def manejador_error_rbac(request: Request, exc: ErrorJerarquiaRBAC):
    """
     Atrapa intentos de violar la jerarquía de roles (ej. un Empleado intentando 
     crear un Administrador) y devuelve HTTP 403 Forbidden.
    """
    return JSONResponse(
        status_code=403,
        content={"detalle": str(exc)}
    )

@app.exception_handler(ErrorStockInsuficiente)
async def manejador_error_stock(request: Request, exc: ErrorStockInsuficiente):
    """
     Atrapa bloqueos comerciales (ej. vender 10 unidades de algo que tiene 5) 
     y devuelve HTTP 400 Bad Request.
    """
    return JSONResponse(
        status_code=400,
        content={"detalle": str(exc)}
    )

@app.exception_handler(ValueError)
async def manejador_value_error(request: Request, exc: ValueError):
    """
     Atrapa errores genéricos de validación disparados por las entidades del Dominio 
     (ej. precios negativos, formatos inválidos) y devuelve HTTP 400 Bad Request.
    """
    return JSONResponse(
        status_code=400,
        content={"detalle": str(exc)}
    )